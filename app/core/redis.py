from collections.abc import AsyncGenerator

from redis.asyncio import Redis

from app.core.settings import get_settings

settings = get_settings()

_redis_client: Redis | None = None


async def get_redis() -> AsyncGenerator[Redis, None]:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True, max_connections=100)
    try:
        yield _redis_client
    finally:
        # Keep connection open for reuse
        pass

