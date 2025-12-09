from typing import Generic, TypeVar

from fluxcrud.types import ModelProtocol, SchemaProtocol

ModelT = TypeVar("ModelT", bound=ModelProtocol)
SchemaT = TypeVar("SchemaT", bound=SchemaProtocol)


class BaseCRUD(Generic[ModelT, SchemaT]):
    """Base class for CRUD operations."""

    pass
