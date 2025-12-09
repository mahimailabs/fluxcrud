from typing import Any, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class ModelProtocol(Protocol):
    """Protocol for SQLAlchemy models."""

    __tablename__: str
    id: Any


@runtime_checkable
class SchemaProtocol(Protocol):
    """Protocol for Pydantic schemas."""

    def model_dump(self, **kwargs) -> dict[str, Any]: ...
