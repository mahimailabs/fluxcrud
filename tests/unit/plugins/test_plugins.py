from datetime import datetime
from typing import Any

import pytest
import pytest_asyncio
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import DeclarativeBase

from fluxcrud.core.repository import Repository
from fluxcrud.plugins.base import BasePlugin


class Base(DeclarativeBase):
    pass


class PluginItem(Base):
    __tablename__ = "plugin_items"
    id = Column(String, primary_key=True)
    name = Column(String)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)


class PluginSchema(BaseModel):
    id: str
    name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TimestampPlugin(BasePlugin):
    name = "timestamp"

    async def on_before_create(
        self, model: type[Any], data: dict[str, Any]
    ) -> dict[str, Any]:
        now = datetime.now()
        data["created_at"] = now
        data["updated_at"] = now
        return data

    async def on_before_update(
        self, model: type[Any], db_obj: Any, data: dict[str, Any]
    ) -> dict[str, Any]:
        data["updated_at"] = datetime.now()
        return data

    async def on_after_query(self, results: Any) -> Any:
        for item in results:
            item.name = f"{item.name} (Processed)"
        return results


class MockPluginRepo(Repository[PluginItem, PluginSchema]):
    pass


@pytest_asyncio.fixture
async def managed_plugin_tables(db_engine):
    """Create and drop tables for this test module."""
    from fluxcrud.database import db

    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_plugin_lifecycle(session, managed_plugin_tables):
    repo = MockPluginRepo(
        session=session, model=PluginItem, plugins=[TimestampPlugin()]
    )

    # Test Create Hook
    item_in = PluginSchema(id="1", name="Test Plugin")
    created_item = await repo.create(item_in)

    assert created_item.created_at is not None
    assert created_item.updated_at is not None
    assert created_item.created_at == created_item.updated_at

    # Test Update Hook
    update_data = {"name": "Updated Plugin"}
    updated_item = await repo.update(created_item, update_data)

    assert updated_item.name == "Updated Plugin"
    assert updated_item.updated_at > updated_item.created_at


@pytest.mark.asyncio
async def test_plugin_query_hooks(session, managed_plugin_tables):
    repo = MockPluginRepo(
        session=session, model=PluginItem, plugins=[TimestampPlugin()]
    )

    # Create items
    await repo.create(PluginSchema(id="q1", name="Query 1"))
    await repo.create(PluginSchema(id="q2", name="Query 2"))

    # Test get_multi -> calls on_after_query
    results = await repo.get_multi()

    assert len(results) == 2
    assert results[0].name.endswith("(Processed)")
    assert results[1].name.endswith("(Processed)")
