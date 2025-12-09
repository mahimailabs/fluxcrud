from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession


class TransactionManager:
    """Manages database transactions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager for a transaction."""
        if not self.session.in_transaction():
            async with self.session.begin():
                yield self.session
        else:
            yield self.session
