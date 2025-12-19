import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import DeclarativeBase

from fluxcrud.database import db
from fluxcrud.query.optimizer import QueryAnalyzer, with_hints


class Base(DeclarativeBase):
    pass


@pytest.mark.asyncio
async def test_query_analyzer_context(db_engine):
    async with QueryAnalyzer() as analyzer:  # noqa: F841
        async for session in db.get_session():
            await session.execute(text("SELECT 1"))
            await session.execute(text("SELECT 2"))
            break

    async with QueryAnalyzer() as ctx_analyzer:
        assert ctx_analyzer._query_count == 0


@pytest.mark.asyncio
async def test_with_hints():
    stmt = select(text("1"))

    hinted_stmt = with_hints(stmt, {"dialect": "suggested_index"})
    assert hinted_stmt is not None
