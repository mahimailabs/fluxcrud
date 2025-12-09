from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.pool import StaticPool

from fluxcrud.database import db


@pytest_asyncio.fixture(scope="function")
async def db_engine() -> AsyncGenerator[None, None]:
    """Initialize database engine."""
    db.init(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield
    await db.close()


@pytest_asyncio.fixture(scope="function")
async def session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    async for session in db.get_session():
        yield session
