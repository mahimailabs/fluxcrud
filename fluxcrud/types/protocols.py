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


@runtime_checkable
class CacheProtocol(Protocol):
    """Protocol for cache backends."""

    async def get(self, key: str) -> Any | None:
        """Get a value from the cache."""
        ...

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in the cache."""
        ...

    async def delete(self, key: str) -> None:
        """Delete a value from the cache."""
        ...

    async def clear(self) -> None:
        """Clear the entire cache."""
        ...
