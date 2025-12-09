from typing import Any, Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from fluxcrud.types import ModelProtocol, SchemaProtocol

ModelT = TypeVar("ModelT", bound=ModelProtocol)
SchemaT = TypeVar("SchemaT", bound=SchemaProtocol)


class UpdateMixin(Generic[ModelT, SchemaT]):
    """Update operation mixin."""

    async def update(
        self, session: AsyncSession, db_obj: ModelT, obj_in: SchemaT | dict[str, Any]
    ) -> ModelT:
        """Update a record."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
