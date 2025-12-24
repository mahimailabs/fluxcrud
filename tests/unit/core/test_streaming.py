import pytest
import pytest_asyncio
from pydantic import BaseModel
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    selectinload,
)

from fluxcrud.core.repository import Repository


class Base(DeclarativeBase):
    pass


class Parent(Base):
    __tablename__ = "parents"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)

    children: Mapped[list["Child"]] = relationship(back_populates="parent")


class Child(Base):
    __tablename__ = "children"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    parent_id: Mapped[str] = mapped_column(ForeignKey("parents.id"))

    parent: Mapped["Parent"] = relationship(back_populates="children")


class ParentSchema(BaseModel):
    id: str
    name: str


class ChildSchema(BaseModel):
    id: str
    name: str
    parent_id: str


class ParentRepo(Repository[Parent, ParentSchema]):
    pass


class ChildRepo(Repository[Child, ChildSchema]):
    pass


@pytest_asyncio.fixture
async def streaming_tables(db_engine):
    """Create and drop tables for this test module."""
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_stream_multi(session, streaming_tables):
    repo = ParentRepo(session, Parent)

    # Seed Data
    parents = [ParentSchema(id=str(i), name=f"Parent {i}") for i in range(10)]
    await repo.create_many(parents)

    # Test Streaming
    count = 0
    async for item in repo.stream_multi(limit=5):
        count += 1
        assert isinstance(item, Parent)

    assert count == 5


@pytest.mark.asyncio
async def test_eager_loading(session, streaming_tables):
    parent_repo = ParentRepo(session, Parent)
    child_repo = ChildRepo(session, Child)

    # Seed Data
    p1 = await parent_repo.create(ParentSchema(id="p1", name="Parent 1"))  # noqa: F841
    await child_repo.create(ChildSchema(id="c1", name="Child 1", parent_id="p1"))

    # Test get with eager load
    # Note: selectinload is often preferred for async
    loaded_parent = await parent_repo.get("p1", selectinload(Parent.children))
    assert loaded_parent is not None

    # Access children (should not raise MissingGreenlet or similar if loaded)
    # Since we used selectinload, children populate a list
    assert len(loaded_parent.children) == 1
    assert loaded_parent.children[0].name == "Child 1"

    # Test get_multi with eager load
    loaded_parents = await parent_repo.get_multi(
        options=[selectinload(Parent.children)]
    )
    assert len(loaded_parents) == 1
    assert len(loaded_parents[0].children) == 1
