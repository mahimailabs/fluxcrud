from typing import Any

from fluxcrud.cache.backends import InMemoryCache, RedisCache
from fluxcrud.types.protocols import CacheProtocol


class CacheManager:
    """Manages the cache implementation."""

    def __init__(self, backend: str = "memory", redis_url: str | None = None):
        self.backend: CacheProtocol
        if backend == "redis":
            if not redis_url:
                raise ValueError("redis_url is required for redis backend")
            self.backend = RedisCache(redis_url)
        else:
            self.backend = InMemoryCache()

    async def get(self, key: str) -> Any | None:
        return await self.backend.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Set a value in cache.
        Note: Value usually needs to be serializable (json/pickle) for real apps,
        but for in-memory it's python objects. For Redis, we might need pre-serialization.
        For now simple pass-through.
        """
        await self.backend.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        await self.backend.delete(key)

    async def clear(self) -> None:
        await self.backend.clear()
