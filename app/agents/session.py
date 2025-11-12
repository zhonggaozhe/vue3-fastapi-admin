from datetime import datetime, timedelta, timezone
from uuid import uuid4

from redis.asyncio import Redis

from app.core.settings import get_settings

settings = get_settings()


class SessionAgent:
    async def create_session(
        self,
        redis: Redis,
        user_id: int,
        refresh_jti: str,
        device_id: str | None,
    ) -> dict:
        sid = f"sess_{uuid4().hex}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.refresh_token_ttl_minutes)
        session_key = f"sess:{sid}"
        payload = {
            "user_id": user_id,
            "refresh_jti": refresh_jti,
            "device_id": device_id,
            "expires_at": expires_at.isoformat(),
        }
        clean_payload = {k: v for k, v in payload.items() if v is not None}
        await redis.hset(session_key, mapping=clean_payload)
        await redis.expireat(session_key, int(expires_at.timestamp()))
        return {"sid": sid, "expires_at": expires_at}

    async def invalidate_session(self, redis: Redis, sid: str) -> None:
        await redis.delete(f"sess:{sid}")
