from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from fluxcrud.core import ConfigurationError


class Database:
    """Database connection manager."""

    def __init__(self, url: str | None = None, **kwargs):
        self.url = url
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        self._kwargs = kwargs

    def init(self, url: str, **kwargs) -> None:
        """Initialize the database connection."""
        self.url = url
        self._kwargs.update(kwargs)
        self.engine = create_async_engine(self.url, **self._kwargs)
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def close(self) -> None:
        """Close the database connection."""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session."""
        if not self.session_factory:
            raise ConfigurationError("Database not initialized. Call init() first.")

        async with self.session_factory() as session:
            yield session


db = Database()
