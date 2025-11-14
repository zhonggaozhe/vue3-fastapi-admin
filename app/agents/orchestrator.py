from dataclasses import dataclass

from fastapi import Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.audit import AuditAgent
from app.agents.identity import AuthenticatedUser, IdentityAgent
from app.agents.ratelimit import RateLimitAgent
from app.agents.rbac import RBACAgent
from app.agents.session import SessionAgent
from app.agents.token import TokenAgent
from app.core.errors import raise_error
from app.core.security import decode_jwt_token
from app.repositories.menu_repository import MenuRepository
from app.schemas.auth import LoginRequest, LoginResponse, RefreshRequest, SessionInfo, TokenPair


@dataclass(slots=True)
class AuthOrchestrator:
    identity_agent: IdentityAgent
    token_agent: TokenAgent
    rbac_agent: RBACAgent
    session_agent: SessionAgent
    audit_agent: AuditAgent
    rate_limit_agent: RateLimitAgent

    async def login(
        self,
        db: AsyncSession,
        redis: Redis,
        payload: LoginRequest,
        request: Request | None = None,
    ) -> LoginResponse:
        await self.rate_limit_agent.check(
            redis, key=f"rl:login:{payload.username}", limit=5, window_seconds=60
        )
        user = await self.identity_agent.authenticate(db, redis, payload)
        tokens = await self.token_agent.issue_pair(redis, user, payload.device_id)
        session_info = await self.session_agent.create_session(
            redis, user_id=user.id, refresh_jti=tokens.refresh_payload["jti"], device_id=payload.device_id
        )
        principal = await self.rbac_agent.build_principal(user)
        routes = await self._load_routes(db, user)
        session_snapshot = {
            "sid": session_info["sid"],
            "expires_at": session_info["expires_at"].isoformat(),
        }
        await self.audit_agent.log_event(
            action="AUTH_LOGIN",
            resource_type="SESSION",
            resource_id=session_info["sid"],
            operator_id=user.id,
            operator_name=user.username,
            after_state={"session": session_snapshot, "principal": principal},
            params={"username": payload.username, "device_id": payload.device_id},
            request=request,
        )
        token_pair = TokenPair(
            accessToken=tokens.access_token,
            refreshToken=tokens.refresh_token,
            token_type="Bearer",
            expires_in=tokens.expires_in,
            payload=tokens.access_payload,
        )
        session_payload = SessionInfo(sid=session_info["sid"], expires_at=session_info["expires_at"])
        return LoginResponse(tokens=token_pair, session=session_payload, user=principal, routes=routes)

    async def refresh(
        self,
        db: AsyncSession,
        redis: Redis,
        payload: RefreshRequest,
        request: Request | None = None,
    ) -> LoginResponse:
        # 1. 解码并验证 refresh_token JWT
        try:
            refresh_claims = decode_jwt_token(payload.refresh_token)
        except ValueError:
            raise_error("AUTH.REFRESH_INVALID")

        # 2. 验证 token 类型
        if refresh_claims.get("type") != "refresh":
            raise_error("AUTH.REFRESH_INVALID")

        # 3. 检查黑名单（防止重复使用）
        old_jti = refresh_claims.get("jti")
        if old_jti and await self.token_agent.is_token_blacklisted(redis, old_jti):
            raise_error("AUTH.REFRESH_INVALID", detail="Refresh token has been used")

        # 4. 验证 Redis 中的 refresh token 状态
        refresh_data = await self.token_agent.verify_refresh_token(redis, payload.refresh_token)
        if not refresh_data:
            raise_error("AUTH.REFRESH_INVALID", detail="Refresh token not found or inactive")

        # 5. 加载用户信息
        user_id = refresh_claims.get("sub")
        if not user_id:
            raise_error("AUTH.REFRESH_INVALID")
        user = await self.identity_agent.load_user(db, int(user_id))

        # 6. 将旧的 refresh_token 加入黑名单（Token 轮换）
        if old_jti:
            old_exp = refresh_claims.get("exp")
            await self.token_agent.blacklist_token(redis, old_jti, old_exp)
            # 同时标记 Redis 中的 refresh token 为已撤销
            await self.token_agent.revoke_refresh_token(redis, payload.refresh_token)

        # 7. 生成新的 token 对
        tokens = await self.token_agent.issue_pair(redis, user, payload.device_id)

        # 8. 创建/更新会话
        session_info = await self.session_agent.create_session(
            redis, user_id=user.id, refresh_jti=tokens.refresh_payload["jti"], device_id=payload.device_id
        )

        # 9. 构建用户主体信息
        principal = await self.rbac_agent.build_principal(user)
        routes = await self._load_routes(db, user)

        # 10. 记录审计日志
        session_snapshot = {
            "sid": session_info["sid"],
            "expires_at": session_info["expires_at"].isoformat(),
        }
        await self.audit_agent.log_event(
            action="AUTH_REFRESH",
            resource_type="SESSION",
            resource_id=session_info["sid"],
            operator_id=user.id,
            operator_name=user.username,
            after_state={"session": session_snapshot, "principal": principal},
            params={"device_id": payload.device_id, "old_jti": old_jti},
            request=request,
        )

        # 11. 返回新的 token 对
        token_pair = TokenPair(
            accessToken=tokens.access_token,
            refreshToken=tokens.refresh_token,
            token_type="Bearer",
            expires_in=tokens.expires_in,
            payload=tokens.access_payload,
        )
        session_payload = SessionInfo(sid=session_info["sid"], expires_at=session_info["expires_at"])
        return LoginResponse(tokens=token_pair, session=session_payload, user=principal, routes=routes)

    async def logout(
        self,
        db: AsyncSession,
        redis: Redis,
        token_sub: str | None,
        request: Request | None = None,
    ) -> dict:
        operator_id = int(token_sub) if token_sub else None
        await self.audit_agent.log_event(
            action="AUTH_LOGOUT",
            resource_type="SESSION",
            resource_id=token_sub,
            operator_id=operator_id,
            request=request,
        )
        return {"ok": True}

    async def _load_routes(self, db: AsyncSession, user: AuthenticatedUser) -> list[dict]:
        menu_repo = MenuRepository(db)
        role_ids = [role.id for role in user.roles]
        return await menu_repo.fetch_routes_for_roles(role_ids, include_all=user.is_superuser)
