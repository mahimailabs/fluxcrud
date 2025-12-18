from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from fluxcrud.types import ModelProtocol, SchemaProtocol

ModelT = TypeVar("ModelT", bound=ModelProtocol)
SchemaT = TypeVar("SchemaT", bound=SchemaProtocol)


class DeleteMixin(Generic[ModelT, SchemaT]):
    """Delete operation mixin."""

    session: AsyncSession

    async def delete(self, db_obj: ModelT) -> ModelT:
        """Delete a record."""
        await self.session.delete(db_obj)
        await self.session.commit()
        return db_obj
