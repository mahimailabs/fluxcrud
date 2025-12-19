import pytest
import pytest_asyncio
from pydantic import BaseModel
from sqlalchemy import Column, String
from sqlalchemy.orm import DeclarativeBase

from fluxcrud.cache.backends import InMemoryCache
from fluxcrud.cache.manager import CacheManager
from fluxcrud.core.repository import Repository


class Base(DeclarativeBase):
    pass


class MockItem(Base):
    __tablename__ = "test_items"
    id = Column(String, primary_key=True)
    name = Column(String)


class MockSchema(BaseModel):
    id: str
    name: str


class MockRepo(Repository[MockItem, MockSchema]):
    pass


@pytest.fixture
def cache_manager():
    return CacheManager(InMemoryCache())


@pytest_asyncio.fixture
async def cache_repo(session, cache_manager):
    from fluxcrud.database import db

    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return MockRepo(session, MockItem, cache_manager=cache_manager, use_loader=False)


@pytest.mark.asyncio
async def test_repository_create_with_cache(cache_repo, session):
    item_in = MockSchema(id="1", name="Test 1")
    await cache_repo.create(item_in)

    db_item = await session.get(MockItem, "1")
    assert db_item.name == "Test 1"

    cached_bytes = await cache_repo.cache_manager.get(cache_repo._get_cache_key("1"))
    assert cached_bytes is not None


@pytest.mark.asyncio
async def test_repository_get_with_cache(cache_repo, session):
    item_in = MockSchema(id="2", name="Test 2")
    await cache_repo.create(item_in)

    await cache_repo.cache_manager.clear()

    item = await cache_repo.get("2")
    assert item.name == "Test 2"

    cached_bytes = await cache_repo.cache_manager.get(cache_repo._get_cache_key("2"))
    assert cached_bytes is not None

    item.name = "Changed in DB"
    await session.commit()

    cached_item = await cache_repo.get("2")
    assert cached_item.name == "Test 2"


@pytest.mark.asyncio
async def test_repository_update_with_cache(cache_repo, session):
    item_in = MockSchema(id="3", name="Test 3")
    created = await cache_repo.create(item_in)

    update_data = MockSchema(id="3", name="Updated")
    await cache_repo.update(created, update_data)

    cached_bytes = await cache_repo.cache_manager.get(cache_repo._get_cache_key("3"))
    import pickle

    cached_obj = pickle.loads(cached_bytes)
    assert cached_obj.name == "Updated"


@pytest.mark.asyncio
async def test_repository_delete_with_cache(cache_repo, session):
    item_in = MockSchema(id="4", name="Test 4")
    created = await cache_repo.create(item_in)

    await cache_repo.delete(created)

    cached_bytes = await cache_repo.cache_manager.get(cache_repo._get_cache_key("4"))
    assert cached_bytes is None


@pytest.mark.asyncio
async def test_repository_get_many_by_ids_caching(cache_repo, session):
    item1 = MockSchema(id="c1", name="Cached")
    item2 = MockSchema(id="c2", name="Uncached")

    await cache_repo.create(item1)
    await cache_repo.create(item2)

    await cache_repo.cache_manager.delete(cache_repo._get_cache_key("c2"))

    results = await cache_repo.get_many_by_ids(["c1", "c2", "missing"])

    assert len(results) == 3
    assert results[0].name == "Cached"
    assert results[1].name == "Uncached"
    assert results[2] is None

    cached_bytes = await cache_repo.cache_manager.get(cache_repo._get_cache_key("c2"))
    assert cached_bytes is not None
