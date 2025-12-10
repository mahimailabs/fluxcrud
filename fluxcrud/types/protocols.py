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

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]: ...

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, Any] | None = None,
    ) -> Any: ...
