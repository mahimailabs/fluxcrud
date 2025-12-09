import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from fluxcrud.database import db


@pytest.mark.asyncio
async def test_database_connection(session: AsyncSession):
    """Test database connection."""
    result = await session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_session_factory(db_engine):
    """Test session factory."""
    assert db.session_factory is not None
    async for session in db.get_session():
        assert isinstance(session, AsyncSession)
