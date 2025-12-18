from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from fluxcrud.operations import (
    CreateMixin,
    DeleteMixin,
    ListMixin,
    ReadMixin,
    UpdateMixin,
)
from fluxcrud.types import ModelProtocol, SchemaProtocol

ModelT = TypeVar("ModelT", bound=ModelProtocol)
SchemaT = TypeVar("SchemaT", bound=SchemaProtocol)


class BaseCRUD(
    CreateMixin[ModelT, SchemaT],
    ReadMixin[ModelT, SchemaT],
    UpdateMixin[ModelT, SchemaT],
    DeleteMixin[ModelT, SchemaT],
    ListMixin[ModelT, SchemaT],
    Generic[ModelT, SchemaT],
):
    """Base class for CRUD operations."""

    session: AsyncSession

    def __init__(self, model: type[ModelT], session: AsyncSession | None = None):
        self.model = model
        if session:
            self.session = session
