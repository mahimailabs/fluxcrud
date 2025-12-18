from typing import Any, Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from fluxcrud.types import ModelProtocol, SchemaProtocol

ModelT = TypeVar("ModelT", bound=ModelProtocol)
SchemaT = TypeVar("SchemaT", bound=SchemaProtocol)


class CreateMixin(Generic[ModelT, SchemaT]):
    """Create operation mixin."""

    model: type[ModelT]

    session: AsyncSession

    async def create(self, obj_in: SchemaT | dict[str, Any]) -> ModelT:
        """Create a new record."""
        if isinstance(obj_in, dict):
            create_data = obj_in
        else:
            create_data = obj_in.model_dump()

        db_obj = self.model(**create_data)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj
