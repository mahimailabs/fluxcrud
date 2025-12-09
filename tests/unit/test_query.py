import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fluxcrud.query import QueryPipeline


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


@pytest.mark.asyncio
async def test_query_pipeline_initialization(session: AsyncSession):
    """Test QueryPipeline initialization."""
    query = QueryPipeline(User, session)
    assert query.model == User
    assert query.session == session
    assert query._select is not None


@pytest.mark.asyncio
async def test_query_pipeline_chaining(session: AsyncSession):
    """Test QueryPipeline method chaining."""
    query = QueryPipeline(User, session)
    query = query.limit(10).offset(5)
    assert query._limit == 10
    assert query._offset == 5
