import time
from typing import Any

from fluxcrud.types.protocols import CacheProtocol

try:
    from redis.asyncio import Redis
except ImportError:
    Redis = None  # type: ignore


class InMemoryCache(CacheProtocol):
    """Simple in-memory cache backend using a dictionary."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[Any, float | None]] = {}

    async def get(self, key: str) -> Any | None:
        if key not in self._cache:
            return None

        value, expiry = self._cache[key]
        if expiry and time.time() > expiry:
            del self._cache[key]
            return None

        return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        expiry = time.time() + ttl if ttl else None
        self._cache[key] = (value, expiry)

    async def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]

    async def clear(self) -> None:
        self._cache.clear()


class RedisCache(CacheProtocol):
    """Redis cache backend."""

    def __init__(self, redis_url: str):
        if Redis is None:
            raise ImportError(
                "redis-py is required for RedisCache. Install with 'pip install redis'"
            )
        self.redis = Redis.from_url(
            redis_url, decode_responses=False
        )  # We might handle serialization ourselves or let user handle bytes

    async def get(self, key: str) -> Any | None:
        return await self.redis.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if ttl:
            await self.redis.setex(key, ttl, value)
        else:
            await self.redis.set(key, value)

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)

    async def clear(self) -> None:
        await self.redis.flushdb()
