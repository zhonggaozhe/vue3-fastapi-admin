from dataclasses import dataclass
from hashlib import sha256

from redis.asyncio import Redis

from app.core.security import create_jwt_token
from app.core.settings import get_settings
from app.agents.identity import AuthenticatedUser

settings = get_settings()


@dataclass(slots=True)
class IssuedTokens:
    access_token: str
    refresh_token: str
    expires_in: int
    access_payload: dict
    refresh_payload: dict


class TokenAgent:
    async def issue_pair(
        self, redis: Redis, user: AuthenticatedUser, device_id: str | None = None
    ) -> IssuedTokens:
        primary_role = user.primary_role
        access = create_jwt_token(
            sub=str(user.id),
            expires_minutes=settings.access_token_ttl_minutes,
            token_type="access",
            username=user.username,
            role=primary_role.code if primary_role else "",
            role_id=str(primary_role.id) if primary_role else "",
            permissions=user.permissions,
            device_id=device_id,
        )
        refresh = create_jwt_token(
            sub=str(user.id),
            expires_minutes=settings.refresh_token_ttl_minutes,
            token_type="refresh",
            rotation="single",
            device_id=device_id,
        )
        tokens = IssuedTokens(
            access_token=access["token"],
            refresh_token=refresh["token"],
            expires_in=settings.access_token_ttl_minutes * 60,
            access_payload=access["payload"],
            refresh_payload=refresh["payload"],
        )
        await self._persist_tokens(redis, tokens, user, device_id)
        return tokens

    async def _persist_tokens(
        self, redis: Redis, tokens: IssuedTokens, user: AuthenticatedUser, device_id: str | None
    ) -> None:
        await self._store_access_token(redis, tokens.access_payload, user, device_id)
        await self._store_refresh_token(redis, tokens.refresh_token, tokens.refresh_payload, user, device_id)

    async def _store_access_token(
        self, redis: Redis, payload: dict, user: AuthenticatedUser, device_id: str | None
    ) -> None:
        permissions = payload.get("permissions") or []
        key = f"token:access:{payload['jti']}"
        mapping = self._prepare_mapping(
            {
                "user_id": user.id,
                "username": user.username,
                "role": payload.get("role"),
                "role_id": payload.get("role_id"),
                "permissions": ",".join(permissions) if permissions else None,
                "device_id": device_id,
                "exp": payload.get("exp"),
                "type": "access",
            }
        )
        await redis.hset(key, mapping=mapping)
        if payload.get("exp"):
            await redis.expireat(key, int(payload["exp"]))

    async def _store_refresh_token(
        self,
        redis: Redis,
        refresh_token: str,
        payload: dict,
        user: AuthenticatedUser,
        device_id: str | None,
    ) -> None:
        key = self._refresh_key(refresh_token)
        mapping = self._prepare_mapping(
            {
                "user_id": user.id,
                "username": user.username,
                "jti": payload.get("jti"),
                "rotation": payload.get("rotation"),
                "device_id": device_id,
                "exp": payload.get("exp"),
                "status": "active",
            }
        )
        await redis.hset(key, mapping=mapping)
        if payload.get("exp"):
            await redis.expireat(key, int(payload["exp"]))

    @staticmethod
    def _refresh_key(token: str) -> str:
        token_hash = sha256(token.encode("utf-8")).hexdigest()
        return f"rt:{token_hash}"

    @staticmethod
    def _prepare_mapping(values: dict) -> dict[str, str]:
        clean: dict[str, str] = {}
        for key, value in values.items():
            if value in (None, "", []):
                continue
            clean[key] = str(value)
        return clean

    async def verify_refresh_token(self, redis: Redis, refresh_token: str) -> dict | None:
        """
        验证 refresh token 是否有效
        返回 refresh token 的 Redis 数据，如果无效返回 None
        """
        refresh_key = self._refresh_key(refresh_token)
        data = await redis.hgetall(refresh_key)
        if not data:
            return None
        if data.get("status") != "active":
            return None
        return data

    async def is_token_blacklisted(self, redis: Redis, jti: str) -> bool:
        """检查 token 是否在黑名单中"""
        key = f"jti:black:{jti}"
        exists = await redis.exists(key)
        return exists > 0

    async def blacklist_token(self, redis: Redis, jti: str, exp: int | None = None) -> None:
        """
        将 token 加入黑名单
        exp: token 的过期时间（Unix timestamp），用于设置黑名单的 TTL
        """
        key = f"jti:black:{jti}"
        await redis.set(key, "1")
        if exp:
            # 设置黑名单的过期时间为原 token 的过期时间
            await redis.expireat(key, int(exp))

    async def revoke_refresh_token(self, redis: Redis, refresh_token: str) -> None:
        """撤销 refresh token（标记为已使用）"""
        refresh_key = self._refresh_key(refresh_token)
        await redis.hset(refresh_key, mapping={"status": "revoked"})
