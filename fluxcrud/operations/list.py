from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fluxcrud.types import ModelProtocol, SchemaProtocol

ModelT = TypeVar("ModelT", bound=ModelProtocol)
SchemaT = TypeVar("SchemaT", bound=SchemaProtocol)


class ListMixin(Generic[ModelT, SchemaT]):
    """List operation mixin with pagination."""

    model: type[ModelT]

    async def get_multi(
        self, session: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> Sequence[ModelT]:
        """Get multiple records with pagination."""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()
