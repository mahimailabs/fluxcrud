from collections.abc import Sequence
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from sqlalchemy.sql import Select


class LifecycleHook(Enum):
    """Hooks for CRUD operations."""

    BEFORE_CREATE = "before_create"
    AFTER_CREATE = "after_create"
    BEFORE_UPDATE = "before_update"
    AFTER_UPDATE = "after_update"
    BEFORE_DELETE = "before_delete"
    AFTER_DELETE = "after_delete"
    BEFORE_QUERY = "before_query"  # Modify SELECT statements
    AFTER_QUERY = "after_query"  # Modify results (list)
    BEFORE_GET = "before_get"
    AFTER_GET = "after_get"


@runtime_checkable
class Plugin(Protocol):
    """Protocol that plugins must implement."""

    name: str

    async def on_before_create(
        self, model: type[Any], data: dict[str, Any]
    ) -> dict[str, Any]:
        """Modify data before creation."""
        ...

    async def on_after_create(self, model: type[Any], instance: Any) -> None:
        """React after creation."""
        ...

    async def on_before_update(
        self, model: type[Any], db_obj: Any, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Modify data before update."""
        ...

    async def on_after_update(self, model: type[Any], instance: Any) -> None:
        """React after update."""
        ...

    async def on_before_delete(self, model: type[Any], instance: Any) -> None:
        """React before deletion."""
        ...

    async def on_after_delete(self, model: type[Any], instance: Any) -> None:
        """React after deletion."""
        ...

    async def on_before_query(self, query: Select) -> Select:
        """Modify the SQLAlchemy SELECT statement."""
        ...

    async def on_after_query(self, results: Sequence[Any]) -> Sequence[Any]:
        """Modify the results of a query."""
        ...

    async def on_before_get(self, model: type[Any], id: Any) -> None:
        """React before getting a single record."""
        ...

    async def on_after_get(self, model: type[Any], instance: Any) -> None:
        """React after getting a single record."""
        ...


class PluginManager:
    """Manages plugin registration and execution."""

    def __init__(self, plugins: list[Plugin] | None = None):
        self.plugins = []
        if plugins:
            for plugin in plugins:
                self.add_plugin(plugin)

    def add_plugin(self, plugin: Any) -> None:
        if not isinstance(plugin, Plugin):
            raise TypeError(f"Object {plugin} does not implement the Plugin protocol")
        self.plugins.append(plugin)

    async def execute_hook(self, hook: LifecycleHook, *args: Any, **kwargs: Any) -> Any:
        """Execute a hook across all plugins."""
        result = args[0] if args else None

        # Mapping hook enum to method names
        method_name = f"on_{hook.value}"

        for plugin in self.plugins:
            if hasattr(plugin, method_name):
                method = getattr(plugin, method_name)
                # Helper to handle different signature requirements if needed
                # For now assume signature match based on Protocol

                if hook == LifecycleHook.BEFORE_CREATE:
                    # method(model, data) -> data
                    result = await method(*args)
                    if result is None:
                        raise ValueError(
                            f"Plugin {plugin.name} returned None from {method_name}"
                        )
                    # Update args for next plugin
                    args = (args[0], result)

                elif hook == LifecycleHook.BEFORE_UPDATE:
                    # method(model, db_obj, data) -> data
                    result = await method(*args)
                    if result is None:
                        raise ValueError(
                            f"Plugin {plugin.name} returned None from {method_name}"
                        )
                    # Update data arg (last arg) for next plugin
                    args = (args[0], args[1], result)

                elif hook == LifecycleHook.BEFORE_QUERY:
                    # method(query) -> query
                    result = await method(result)

                elif hook == LifecycleHook.AFTER_QUERY:
                    # method(results) -> results
                    result = await method(result)

                else:
                    # Side-effect hooks (return None)
                    await method(*args, **kwargs)

        return result
