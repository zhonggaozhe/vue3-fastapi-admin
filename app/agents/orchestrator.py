from dataclasses import dataclass

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.audit import AuditAgent
from app.agents.identity import IdentityAgent
from app.agents.ratelimit import RateLimitAgent
from app.agents.rbac import RBACAgent
from app.agents.session import SessionAgent
from app.agents.token import TokenAgent
from app.core.errors import raise_error
from app.core.security import decode_jwt_token
from app.schemas.auth import LoginRequest, LoginResponse, RefreshRequest, SessionInfo, TokenPair


@dataclass(slots=True)
class AuthOrchestrator:
    identity_agent: IdentityAgent
    token_agent: TokenAgent
    rbac_agent: RBACAgent
    session_agent: SessionAgent
    audit_agent: AuditAgent
    rate_limit_agent: RateLimitAgent

    async def login(self, db: AsyncSession, redis: Redis, payload: LoginRequest) -> LoginResponse:
        await self.rate_limit_agent.check(
            redis, key=f"rl:login:{payload.username}", limit=5, window_seconds=60
        )
        user = await self.identity_agent.authenticate(db, payload)
        tokens = await self.token_agent.issue_pair(user, payload.device_id)
        session_info = await self.session_agent.create_session(
            redis, user_id=user.id, refresh_jti=tokens.refresh_payload["jti"], device_id=payload.device_id
        )
        await self.audit_agent.log_event(
            db, event_type="login_success", user_id=user.id, detail={"device_id": payload.device_id}
        )
        principal = await self.rbac_agent.build_principal(user)
        token_pair = TokenPair(
            accessToken=tokens.access_token,
            refreshToken=tokens.refresh_token,
            token_type="Bearer",
            expires_in=tokens.expires_in,
            payload=tokens.access_payload,
        )
        session_payload = SessionInfo(sid=session_info["sid"], expires_at=session_info["expires_at"])
        return LoginResponse(tokens=token_pair, session=session_payload, user=principal)

    async def refresh(self, db: AsyncSession, redis: Redis, payload: RefreshRequest) -> LoginResponse:
        try:
            refresh_claims = decode_jwt_token(payload.refresh_token)
        except ValueError:
            raise_error("AUTH.REFRESH_INVALID")

        if refresh_claims.get("type") != "refresh":
            raise_error("AUTH.REFRESH_INVALID")

        user_id = refresh_claims.get("sub")
        if not user_id:
            raise_error("AUTH.REFRESH_INVALID")
        user = await self.identity_agent.load_user(db, int(user_id))
        tokens = await self.token_agent.issue_pair(user, payload.device_id)
        session_info = await self.session_agent.create_session(
            redis, user_id=user.id, refresh_jti=tokens.refresh_payload["jti"], device_id=payload.device_id
        )
        await self.audit_agent.log_event(
            db, event_type="token_refresh", user_id=user.id, detail={"device_id": payload.device_id}
        )
        principal = await self.rbac_agent.build_principal(user)
        token_pair = TokenPair(
            accessToken=tokens.access_token,
            refreshToken=tokens.refresh_token,
            token_type="Bearer",
            expires_in=tokens.expires_in,
            payload=tokens.access_payload,
        )
        session_payload = SessionInfo(sid=session_info["sid"], expires_at=session_info["expires_at"])
        return LoginResponse(tokens=token_pair, session=session_payload, user=principal)

    async def logout(self, db: AsyncSession, redis: Redis, token_sub: str | None) -> dict:
        await self.audit_agent.log_event(
            db, event_type="logout", user_id=int(token_sub) if token_sub else None, detail=None
        )
        return {"ok": True}
