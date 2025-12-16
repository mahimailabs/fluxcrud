from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, StaticPool

from fluxcrud.core import ConfigurationError


class Database:
    """Database connection manager."""

    def __init__(self, url: str | None = None, **kwargs):
        self.url = url
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        self._kwargs = kwargs

    def init(
        self,
        url: str,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_recycle: int = 3600,
        pool_timeout: int = 30,
        **kwargs,
    ) -> None:
        """
        Initialize the database connection.

        Args:
            url: The database connection URL.
            pool_size: The number of connections to keep open inside the connection pool.
            max_overflow: The number of connections to allow in overflow.
            pool_recycle: Recycle connections after the given number of seconds.
            pool_timeout: Number of seconds to wait before giving up on getting a connection from the pool.
            **kwargs: Additional arguments to pass to `create_async_engine`.
        """
        self.url = url
        self._kwargs.update(kwargs)

        pool_class = self._kwargs.get("poolclass")
        pool_args = {}

        if not (pool_class and (pool_class == StaticPool or pool_class == NullPool)):
            pool_args = {
                "pool_size": pool_size,
                "max_overflow": max_overflow,
                "pool_recycle": pool_recycle,
                "pool_timeout": pool_timeout,
            }

        self.engine = create_async_engine(
            self.url,
            **pool_args,
            **self._kwargs,
        )
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
