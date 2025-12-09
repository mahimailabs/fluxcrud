from typing import Any, Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from fluxcrud.types import ModelProtocol, SchemaProtocol

ModelT = TypeVar("ModelT", bound=ModelProtocol)
SchemaT = TypeVar("SchemaT", bound=SchemaProtocol)


class ReadMixin(Generic[ModelT, SchemaT]):
    """Read operation mixin."""

    model: type[ModelT]

    async def get(self, session: AsyncSession, id: Any) -> ModelT | None:
        """Get a record by ID."""
        return await session.get(self.model, id)
