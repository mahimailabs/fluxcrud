import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from fluxcrud.database import db


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine() -> AsyncGenerator[None, None]:
    """Initialize database engine."""
    db.init("sqlite+aiosqlite:///:memory:")
    yield
    await db.close()


@pytest_asyncio.fixture(scope="function")
async def session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    async for session in db.get_session():
        yield session
