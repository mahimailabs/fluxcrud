from dataclasses import dataclass, field
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from fluxcrud.types import ModelProtocol

ModelT = TypeVar("ModelT", bound=ModelProtocol)


@dataclass
class QueryPipeline(Generic[ModelT]):
    """Composable query builder."""

    model: type[ModelT]
    session: AsyncSession
    _select: Select | None = None
    _filters: list = field(default_factory=list)
    _limit: int | None = None
    _offset: int | None = None

    def __post_init__(self):
        if self._select is None:
            self._select = select(self.model)

    def limit(self, n: int) -> "QueryPipeline[ModelT]":
        """Set limit."""
        self._limit = n
        return self

    def offset(self, n: int) -> "QueryPipeline[ModelT]":
        """Set offset."""
        self._offset = n
        return self

    def _build(self) -> Select:
        """Build the final query."""
        if self._select is None:
            self._select = select(self.model)

        stmt = self._select

        if self._limit:
            stmt = stmt.limit(self._limit)

        if self._offset:
            stmt = stmt.offset(self._offset)

        return stmt

    async def all(self) -> list[ModelT]:
        """Execute and get all results."""
        stmt = self._build()
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
