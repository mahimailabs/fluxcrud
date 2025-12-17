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

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        result = {}
        for key in keys:
            val = await self.get(key)
            if val is not None:
                result[key] = val
        return result

    async def set_many(self, mapping: dict[str, Any], ttl: int | None = None) -> None:
        expiry = time.time() + ttl if ttl else None
        for key, value in mapping.items():
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

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        if not keys:
            return {}
        values = await self.redis.mget(keys)
        return {k: v for k, v in zip(keys, values, strict=True) if v is not None}

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if ttl:
            await self.redis.setex(key, ttl, value)
        else:
            await self.redis.set(key, value)

    async def set_many(self, mapping: dict[str, Any], ttl: int | None = None) -> None:
        if not mapping:
            return
        if ttl:
            async with self.redis.pipeline() as pipe:
                for key, value in mapping.items():
                    pipe.setex(key, ttl, value)
                await pipe.execute()
        else:
            await self.redis.mset(mapping)

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)

    async def clear(self) -> None:
        await self.redis.flushdb()


try:
    import aiomcache
except ImportError:
    aiomcache = None  # type: ignore


class MemcachedCache(CacheProtocol):
    """Memcached cache backend."""

    def __init__(self, memcached_url: str):
        if aiomcache is None:
            raise ImportError(
                "aiomcache is required for MemcachedCache. Install with 'pip install aiomcache'"
            )

        if "://" in memcached_url:
            memcached_url = memcached_url.split("://")[1]

        parts = memcached_url.split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 11211

        self.host = host
        self.port = port
        self.client = aiomcache.Client(host, port)

    async def get(self, key: str) -> Any | None:
        value = await self.client.get(key.encode())
        return value

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        if not keys:
            return {}
        encoded_keys = [k.encode() for k in keys]
        values = await self.client.multi_get(*encoded_keys)
        return {k: v for k, v in zip(keys, values, strict=True) if v is not None}

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if not isinstance(value, bytes):
            if isinstance(value, str):
                value = value.encode()
            elif not isinstance(value, (bytes, bytearray)):
                value = str(value).encode()

        await self.client.set(key.encode(), value, exptime=ttl or 0)

    async def set_many(self, mapping: dict[str, Any], ttl: int | None = None) -> None:
        import asyncio

        tasks = []
        for key, value in mapping.items():
            tasks.append(self.set(key, value, ttl))

        if tasks:
            await asyncio.gather(*tasks)

    async def delete(self, key: str) -> None:
        await self.client.delete(key.encode())

    async def clear(self) -> None:
        import asyncio

        try:
            reader, writer = await asyncio.open_connection(self.host, self.port)
            writer.write(b"flush_all\r\n")
            await writer.drain()

            response = await reader.readline()

            writer.close()
            await writer.wait_closed()

            if response.strip() != b"OK":
                pass

        except Exception:
            raise
