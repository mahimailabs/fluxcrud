from typing import Generic, TypeVar

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

    def __init__(self, model: type[ModelT]):
        self.model = model
