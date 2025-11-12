from app.core.errors import raise_error


class RateLimitAgent:
    async def check(self, redis, key: str, limit: int, window_seconds: int) -> None:
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, window_seconds)
        if current > limit:
            raise_error("AUTH.RATE_LIMIT")

