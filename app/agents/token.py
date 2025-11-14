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
