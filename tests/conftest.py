import os
from collections.abc import AsyncGenerator
from typing import Any

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.pool import StaticPool

from fluxcrud.database import db


@pytest_asyncio.fixture(scope="function")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Initialize database engine."""
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

    init_kwargs: dict[str, Any] = {}
    if "sqlite" in database_url:
        init_kwargs = {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }

    db.init(database_url, **init_kwargs)
    assert db.engine is not None
    yield db.engine
    await db.close()


@pytest_asyncio.fixture(scope="function")
async def session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    async for session in db.get_session():
        yield session
