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
        """
        Adjust input data before a model instance is created.

        Parameters:
            model (type[Any]): The model class for which an instance will be created.
            data (dict[str, Any]): The incoming attribute dictionary for the new instance.

        Returns:
            dict[str, Any]: The data dictionary to be used for creation (may be modified).
        """
        ...

    async def on_after_create(self, model: type[Any], instance: Any) -> None:
        """
        Perform side-effect actions after a model instance is created.

        This hook is invoked after a new instance for `model` has been persisted; implementations may perform tasks such as logging, notifications, caching, or additional persistence.

        Parameters:
            model (type[Any]): The model class that was created.
            instance (Any): The newly created model instance.
        """
        ...

    async def on_before_update(
        self, model: type[Any], db_obj: Any, data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Prepare and return the update data to apply to the given model instance.

        Parameters:
            model (type[Any]): The model class of the instance being updated.
            db_obj (Any): The existing database object instance being updated.
            data (dict[str, Any]): Incoming update fields and values.

        Returns:
            dict[str, Any]: The update data to use for the operation (may be modified).
        """
        ...

    async def on_after_update(self, model: type[Any], instance: Any) -> None:
        """
        Called after a model instance has been updated.

        Parameters:
            model (type[Any]): The model class whose instance was updated.
            instance (Any): The updated model instance.
        """
        ...

    async def on_before_delete(self, model: type[Any], instance: Any) -> None:
        """
        Run custom logic before an instance of a model is deleted.

        Parameters:
            model (type[Any]): The model class of the instance being deleted.
            instance (Any): The instance that will be deleted.
        """
        ...

    async def on_after_delete(self, model: type[Any], instance: Any) -> None:
        """
        Called after an instance has been deleted.

        Parameters:
            model (type[Any]): The model class of the deleted instance.
            instance (Any): The deleted model instance.
        """
        ...

    async def on_before_query(self, query: Select) -> Select:
        """
        Allow the plugin to adjust a SQLAlchemy Select before it is executed.

        Parameters:
            query (Select): The SELECT statement to modify.

        Returns:
            Select: The (possibly modified) SELECT statement to use.
        """
        ...

    async def on_after_query(self, results: Sequence[Any]) -> Sequence[Any]:
        """
        Modify or post-process a sequence of query results.

        Parameters:
            results (Sequence[Any]): The sequence of items returned by a query.

        Returns:
            Sequence[Any]: The (possibly modified) sequence of results.
        """
        ...

    async def on_before_get(self, model: type[Any], id: Any) -> None:
        """
        Called before a single model instance is retrieved.

        Parameters:
            model (type[Any]): The model class being queried.
            id (Any): The identifier value used to locate the instance.
        """
        ...

    async def on_after_get(self, model: type[Any], instance: Any) -> None:
        """
        Called after a single model instance is retrieved.

        Parameters:
            model (type[Any]): The model class for the retrieved instance.
            instance (Any): The retrieved model instance.
        """
        ...


class BasePlugin:
    """Base implementation of Plugin protocol with default no-op behavior."""

    name: str = "base"

    async def on_before_create(
        self, model: type[Any], data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Provide a no-op before-create hook that returns the create payload unchanged.

        Parameters:
            model (type[Any]): The model class for which an instance will be created.
            data (dict[str, Any]): Field values intended for the new instance.

        Returns:
            dict[str, Any]: The create payload to pass to subsequent plugins or the creator (unchanged by this default implementation).
        """
        return data

    async def on_after_create(self, model: type[Any], instance: Any) -> None:
        """
        Hook invoked after a model instance has been created.

        Parameters:
            model (type[Any]): The model class for which an instance was created.
            instance (Any): The newly created model instance.
        """
        pass

    async def on_before_update(
        self, model: type[Any], db_obj: Any, data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Allow modification of the update payload before it is applied.

        Parameters:
            model (type[Any]): The model class being updated.
            db_obj (Any): The existing database object targeted by the update.
            data (dict[str, Any]): Incoming update values.

        Returns:
            dict[str, Any]: The update data to apply (may be the original or a modified mapping).
        """
        return data

    async def on_after_update(self, model: type[Any], instance: Any) -> None:
        """
        Called after an instance of the given model has been updated to allow plugins to perform side effects.

        Parameters:
            model (type[Any]): The model class that was updated.
            instance (Any): The updated model instance.
        """
        pass

    async def on_before_delete(self, model: type[Any], instance: Any) -> None:
        """
        Hook invoked before a model instance is deleted.

        Parameters:
            model (type[Any]): The model class of the instance being deleted.
            instance (Any): The instance that will be deleted; plugins may inspect or act on it.
        """
        pass

    async def on_after_delete(self, model: type[Any], instance: Any) -> None:
        """
        Called after an instance of a model has been deleted.

        Parameters:
            model: The model class of the deleted instance.
            instance: The deleted model instance.

        Notes:
            Default implementation performs no action; override to implement post-delete behavior.
        """
        pass

    async def on_before_query(self, query: Select) -> Select:
        """
        Provide a no-op before-query hook that returns the query unchanged.

        Parameters:
            query (Select): The query object to inspect or modify.

        Returns:
            Select: The same `query` instance unchanged.
        """
        return query

    async def on_after_query(self, results: Sequence[Any]) -> Sequence[Any]:
        """
        Allow a plugin to inspect or transform query results after execution.

        Parameters:
            results (Sequence[Any]): The sequence of objects returned by the query.

        Returns:
            Sequence[Any]: The (possibly modified) sequence of results to be used by callers.
        """
        return results

    async def on_before_get(self, model: type[Any], id: Any) -> None:
        """
        Called before a single model instance is retrieved by its identifier; default implementation does nothing.

        Parameters:
            model (type[Any]): The model class being queried.
            id (Any): The identifier value used to fetch the instance.
        """
        pass

    async def on_after_get(self, model: type[Any], instance: Any) -> None:
        """
        Hook called after a model instance is retrieved.

        Parameters:
            model (type[Any]): The model class the instance belongs to.
            instance (Any): The retrieved instance.
        """
        pass


class PluginManager:
    """Manages plugin registration and execution."""

    def __init__(self, plugins: list[Plugin] | None = None):
        """
        Initialize the PluginManager and optionally register an initial list of plugins.

        If `plugins` is provided, each item is validated and added via `add_plugin`, which enforces that objects conform to the Plugin protocol.

        Parameters:
            plugins (list[Plugin] | None): Optional list of plugins to register during initialization.
        """
        self.plugins: list[Plugin] = []
        if plugins:
            for plugin in plugins:
                self.add_plugin(plugin)

    def add_plugin(self, plugin: Any) -> None:
        """
        Register a plugin with the manager after verifying it implements the Plugin protocol.

        Parameters:
            plugin (Any): Object implementing the Plugin protocol to register.

        Raises:
            TypeError: If the provided object does not implement the Plugin protocol.
        """
        if not isinstance(plugin, Plugin):
            raise TypeError(f"Object {plugin} does not implement the Plugin protocol")
        self.plugins.append(plugin)

    async def execute_hook(self, hook: LifecycleHook, *args: Any, **kwargs: Any) -> Any:
        """
        Run the given lifecycle hook on each registered plugin, applying plugin transformations where hooks return replacement values and invoking side-effect hooks.

        Parameters:
            hook (LifecycleHook): Which lifecycle hook to execute; determines which `on_<hook.value>` plugin method is called.
            *args: Positional arguments forwarded to each plugin method (may be updated between plugins for hooks that return new data).
            **kwargs: Keyword arguments forwarded to plugin methods for side-effect hooks.

        Returns:
            The final value produced after all plugins have been processed:
              - For BEFORE_CREATE: the `data` dict returned by the last plugin.
              - For BEFORE_UPDATE: the `data` dict returned by the last plugin.
              - For BEFORE_QUERY: the `Select`/query object returned by the last plugin.
              - For AFTER_QUERY: the sequence of results returned by the last plugin.
              - For AFTER_CREATE, AFTER_UPDATE, BEFORE_DELETE, AFTER_DELETE, BEFORE_GET, AFTER_GET: the initial first positional argument if provided, otherwise None.
        """
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

                elif hook in (
                    LifecycleHook.AFTER_CREATE,
                    LifecycleHook.AFTER_UPDATE,
                    LifecycleHook.BEFORE_DELETE,
                    LifecycleHook.AFTER_DELETE,
                    LifecycleHook.BEFORE_GET,
                    LifecycleHook.AFTER_GET,
                ):
                    # Side-effect hooks (return None)
                    await method(*args, **kwargs)

                else:
                    # Should be unreachable if all hooks are handled
                    pass

        return result
