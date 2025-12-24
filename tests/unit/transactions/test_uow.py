import pytest
import pytest_asyncio
from pydantic import BaseModel
from sqlalchemy import Column, String
from sqlalchemy.orm import DeclarativeBase

from fluxcrud.transactions.uow import UnitOfWork


class Base(DeclarativeBase):
    pass


class UoWItem(Base):
    __tablename__ = "uow_items"
    id = Column(String(255), primary_key=True)
    name = Column(String(255))


class UoWSchema(BaseModel):
    id: str
    name: str


@pytest_asyncio.fixture
async def managed_uow_tables(db_engine):
    """Create and drop tables for this test module."""
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_uow_commit(db_engine, managed_uow_tables):
    uow = UnitOfWork()

    async with uow:
        repo = uow.repository(UoWItem, UoWSchema)
        await repo.create(UoWSchema(id="1", name="UoW 1"))
        await repo.create(UoWSchema(id="2", name="UoW 2"))

    # Verify outside UoW (new session)
    verification_uow = UnitOfWork()
    async with verification_uow:
        repo = verification_uow.repository(UoWItem, UoWSchema)
        item1 = await repo.get("1")
        item2 = await repo.get("2")
        assert item1 is not None
        assert item2 is not None


@pytest.mark.asyncio
async def test_uow_rollback(db_engine, managed_uow_tables):
    uow = UnitOfWork()

    try:
        async with uow:
            repo = uow.repository(UoWItem, UoWSchema)
            await repo.create(UoWSchema(id="3", name="UoW 3"))
            raise RuntimeError("Force Rollback")
    except RuntimeError:
        pass

    # Verify rollback
    verification_uow = UnitOfWork()
    async with verification_uow:
        repo = verification_uow.repository(UoWItem, UoWSchema)
        item3 = await repo.get("3")
        assert item3 is None
