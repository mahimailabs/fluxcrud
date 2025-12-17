from unittest.mock import AsyncMock, MagicMock, patch

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


@pytest.mark.asyncio
async def test_cache_bulk_ops():
    cache = InMemoryCache()
    await cache.set_many({"k1": "v1", "k2": "v2"})

    results = await cache.get_many(["k1", "k2", "k3"])
    assert results == {"k1": "v1", "k2": "v2"}

    await cache.set_many({"k3": "v3"}, ttl=1)
    results = await cache.get_many(["k1", "k3"])
    assert results == {"k1": "v1", "k3": "v3"}

    await cache.clear()
    assert await cache.get_many(["k1"]) == {}


@pytest.mark.asyncio
async def test_memcached_backend_initialization():
    with patch("fluxcrud.cache.backends.aiomcache", None):
        with pytest.raises(ImportError, match="aiomcache is required"):
            from fluxcrud.cache.backends import MemcachedCache

            MemcachedCache("memcached://localhost")

    with patch("fluxcrud.cache.backends.aiomcache") as MockMcache:
        from fluxcrud.cache.backends import MemcachedCache

        MemcachedCache("memcached://localhost:11211")
        MockMcache.Client.assert_called_with("localhost", 11211)

        MemcachedCache("localhost")
        MockMcache.Client.assert_called_with("localhost", 11211)


@pytest.mark.asyncio
async def test_memcached_operations():
    with patch("fluxcrud.cache.backends.aiomcache") as MockMcache:
        mock_client = AsyncMock()

        mock_client.get.return_value = b"value"
        mock_client.multi_get.return_value = [b"v1", b"v2"]

        MockMcache.Client.return_value = mock_client

        from fluxcrud.cache.backends import MemcachedCache

        cache = MemcachedCache("localhost")

        # Get
        val = await cache.get("key")
        assert val == b"value"
        mock_client.get.assert_called_with(b"key")

        # Set
        await cache.set("key", b"val", ttl=60)
        mock_client.set.assert_called_with(b"key", b"val", exptime=60)

        # Get Many
        res = await cache.get_many(["k1", "k2"])
        assert res == {"k1": b"v1", "k2": b"v2"}
        mock_client.multi_get.assert_called_with(b"k1", b"k2")

        await cache.delete("d")
        mock_client.delete.assert_called_with(b"d")

        with patch("asyncio.open_connection") as mock_open:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()

            mock_writer.write = MagicMock()
            mock_writer.close = MagicMock()

            mock_open.return_value = (mock_reader, mock_writer)
            mock_reader.readline.return_value = b"OK\r\n"

            await cache.clear()

            mock_writer.write.assert_called_with(b"flush_all\r\n")
            mock_writer.close.assert_called()
