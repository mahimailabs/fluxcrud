from unittest.mock import AsyncMock, patch

import pytest

from fluxcrud.cache.backends import InMemoryCache, RedisCache
from fluxcrud.cache.manager import CacheManager


@pytest.mark.asyncio
async def test_in_memory_cache():
    cache = InMemoryCache()

    await cache.set("foo", "bar")
    assert await cache.get("foo") == "bar"

    await cache.set("expired", "value", ttl=1)

    await cache.delete("foo")
    assert await cache.get("foo") is None

    await cache.set("a", 1)
    await cache.set("b", 2)
    await cache.clear()
    assert await cache.get("a") is None
    assert await cache.get("b") is None


@pytest.mark.asyncio
async def test_cache_manager_memory():
    manager = CacheManager(backend="memory")
    await manager.set("key", "value")
    assert await manager.get("key") == "value"
    await manager.delete("key")
    assert await manager.get("key") is None


@pytest.mark.asyncio
async def test_cache_manager_redis_missing_url():
    with pytest.raises(ValueError, match="redis_url is required"):
        CacheManager(backend="redis")


@pytest.mark.asyncio
async def test_redis_backend_import_error():
    try:
        import redis.asyncio  # noqa: F401
    except ImportError:
        with pytest.raises(ImportError):
            RedisCache("redis://localhost")
    else:
        with patch("fluxcrud.cache.backends.Redis") as MockRedis:
            mock_client = AsyncMock()
            MockRedis.from_url.return_value = mock_client

            cache = RedisCache("redis://localhost")
            mock_client.get.return_value = "val"

            val = await cache.get("k")
            assert val == "val"
            mock_client.get.assert_called_with("k")
