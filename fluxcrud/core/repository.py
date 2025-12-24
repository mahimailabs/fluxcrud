import pickle
from collections.abc import AsyncGenerator, Sequence
from typing import Any, Generic, TypeVar, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fluxcrud.async_patterns import Batcher, DataLoader
from fluxcrud.cache.manager import CacheManager
from fluxcrud.core.base import BaseCRUD
from fluxcrud.plugins.base import LifecycleHook, Plugin, PluginManager
from fluxcrud.types import ModelProtocol, SchemaProtocol

ModelT = TypeVar("ModelT", bound=ModelProtocol)
SchemaT = TypeVar("SchemaT", bound=SchemaProtocol)


class Repository(BaseCRUD[ModelT, SchemaT], Generic[ModelT, SchemaT]):
    """Repository pattern implementation with DataLoader integration and Caching."""

    __slots__ = (
        "session",
        "cache_manager",
        "use_loader",
        "id_loader",
        "model",
        "plugin_manager",
        "auto_commit",
    )

    def __init__(
        self,
        session: AsyncSession,
        model: type[ModelT],
        cache_manager: CacheManager | None = None,
        use_loader: bool = False,
        plugins: list[Plugin] | None = None,
        auto_commit: bool = True,
    ):
        """
        Initialize the repository with session, model, optional caching, dataloader usage, plugins, and commit behavior.
        
        Parameters:
            session (AsyncSession): Async SQLAlchemy session used for DB operations.
            model (type[ModelT]): ORM model class managed by this repository.
            cache_manager (CacheManager | None): Optional cache manager used to read/write cached model instances.
            use_loader (bool): If True, enable an ID-based DataLoader for batched/optimized ID fetches.
            plugins (list[Plugin] | None): Optional list of plugin instances to attach via the repository's PluginManager.
            auto_commit (bool): If True, repository write operations will commit (and refresh) automatically; otherwise they will only flush.
        """
        super().__init__(model)
        self.session = session
        self.cache_manager = cache_manager
        self.use_loader = use_loader
        self.plugin_manager = PluginManager(plugins)
        self.auto_commit = auto_commit
        if self.use_loader:
            self._setup_dataloaders()

    def _setup_dataloaders(self) -> None:
        """Create DataLoaders for this repository."""
        self.id_loader = DataLoader(self._batch_load_by_ids)

    def _get_cache_key(self, id: Any) -> str:
        """Generate cache key for an ID."""
        return f"{self.model.__tablename__}:{id}"

    async def _batch_load_by_ids(self, ids: list[Any]) -> list[ModelT | None]:
        """
        Batch load model instances for the given primary key values preserving input order.
        
        Parameters:
            ids (list[Any]): Sequence of primary key values to fetch; order determines output order.
        
        Returns:
            list[ModelT | None]: A list of model instances or `None` for missing entries, aligned with the input `ids` order.
        """
        stmt = select(self.model).where(self.model.id.in_(ids))
        result = await self.session.execute(stmt)
        records = result.scalars().all()

        # Maintain order and handle missing
        record_map = {r.id: r for r in records}
        return [record_map.get(id) for id in ids]

    async def get(self, id: Any, *options: Any) -> ModelT | None:
        """
        Retrieve a model instance by primary key, preferring a cached value and falling back to the DataLoader or direct DB query.
        
        If plugins are configured, BEFORE_GET and AFTER_GET lifecycle hooks may be executed. If a CacheManager is configured, a found instance will be stored in cache.
        
        Parameters:
            *options (Any): Optional SQLAlchemy loader options (for example `joinedload(...)`) applied to the select statement when provided.
        
        Returns:
            The model instance for the given id, or `None` if no matching record exists.
        """
        if self.cache_manager:
            key = self._get_cache_key(id)
            cached_bytes = await self.cache_manager.get(key)
            if cached_bytes:
                return cast(ModelT, pickle.loads(cached_bytes))

        # Cache miss or no cache:
        if self.plugin_manager.plugins:
            await self.plugin_manager.execute_hook(
                LifecycleHook.BEFORE_GET, self.model, id
            )

        if self.use_loader and not options:
            obj = await self.id_loader.load(id)
        elif options:
            stmt = select(self.model).where(self.model.id == id).options(*options)
            result = await self.session.execute(stmt)
            obj = result.scalars().first()
        else:
            obj = await self.session.get(self.model, id)

        if self.plugin_manager.plugins and obj:
            await self.plugin_manager.execute_hook(
                LifecycleHook.AFTER_GET, self.model, obj
            )

        if self.cache_manager and obj:
            key = self._get_cache_key(id)
            # We pickle the object. Note: Cached objects are detached.
            await self.cache_manager.set(key, pickle.dumps(obj))

        return obj

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        options: Sequence[Any] | None = None,
        **kwargs: Any,
    ) -> Sequence[ModelT]:
        """
        Query multiple model instances with pagination and optional loader options.
        
        If plugins are registered, the BEFORE_QUERY lifecycle hook may modify the SQL statement before execution and the AFTER_QUERY hook may modify the returned results.
        
        Parameters:
            skip (int): Number of rows to skip (offset).
            limit (int): Maximum number of rows to return.
            options (Sequence[Any] | None): Optional SQLAlchemy loader/option objects to apply to the statement (e.g., eager-loading options).
            **kwargs: Ignored; kept for compatibility.
        
        Returns:
            Sequence[ModelT]: Sequence of model instances matching the query in result order.
        """
        stmt = select(self.model).offset(skip).limit(limit)

        if options:
            stmt = stmt.options(*options)

        if self.plugin_manager.plugins:
            # Allow plugins to modify the query (filtering, etc)
            stmt = await self.plugin_manager.execute_hook(
                LifecycleHook.BEFORE_QUERY, stmt
            )

        result = await self.session.execute(stmt)
        results = result.scalars().all()

        if self.plugin_manager.plugins:
            results = await self.plugin_manager.execute_hook(
                LifecycleHook.AFTER_QUERY, results
            )

        return results

    async def stream_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        options: Sequence[Any] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[ModelT, None]:
        """
        Stream model instances from the database in a memory-efficient asynchronous generator.
        
        Executes the `BEFORE_QUERY` plugin hook if plugins are registered; any hook-modified statement is used for streaming.
        
        Parameters:
            skip (int): Number of rows to skip.
            limit (int): Maximum number of rows to return.
            options (Sequence[Any] | None): Optional SQLAlchemy statement options (e.g., loader options) to apply to the query.
            **kwargs: Reserved for future use / compatibility and ignored by this method.
        
        Returns:
            AsyncGenerator[ModelT, None]: Yields model instances that match the query, in result order.
        """
        stmt = select(self.model).offset(skip).limit(limit)

        if options:
            stmt = stmt.options(*options)

        if self.plugin_manager.plugins:
            stmt = await self.plugin_manager.execute_hook(
                LifecycleHook.BEFORE_QUERY, stmt
            )

        result = await self.session.stream(stmt)
        async for row in result.scalars():
            yield row

    async def get_many_by_ids(self, ids: list[Any]) -> list[ModelT | None]:
        """
        Retrieve multiple model instances by their primary keys, preserving the input order.
        
        When a cache manager is configured, cached entries are used when available; missing items are loaded from the database and any newly retrieved instances are written back to the cache. When no cache manager is configured, objects are loaded directly (optionally via the repository's DataLoader).
        
        Parameters:
            ids (list[Any]): Sequence of primary key values to fetch.
        
        Returns:
            list[ModelT | None]: A list aligned with `ids` where each element is the model instance for that id or `None` if no record exists.
        """
        if not self.cache_manager:
            if self.use_loader:
                return await self.id_loader.load_many(ids)
            return await self._batch_load_by_ids(ids)

        keys = [self._get_cache_key(id) for id in ids]
        cached_data = await self.cache_manager.get_many(keys)

        results: list[ModelT | None] = []
        missing_ids = []
        missing_indices = []

        for i, (id, key) in enumerate(zip(ids, keys, strict=True)):
            val = cached_data.get(key)
            if val:
                results.append(cast(ModelT, pickle.loads(val)))
            else:
                results.append(None)
                missing_ids.append(id)
                missing_indices.append(i)

        if not missing_ids:
            return results

        if self.use_loader:
            db_objects = await self.id_loader.load_many(missing_ids)
        else:
            db_objects = await self._batch_load_by_ids(missing_ids)

        cache_update = {}
        for i, obj in zip(missing_indices, db_objects, strict=True):
            results[i] = obj
            if obj:
                key = self._get_cache_key(obj.id)
                cache_update[key] = pickle.dumps(obj)

        if cache_update:
            await self.cache_manager.set_many(cache_update)

        return results

    async def create(self, obj_in: SchemaT | dict[str, Any]) -> ModelT:
        """
        Create and persist a new model instance, run lifecycle hooks, and cache the result when applicable.
        
        Parameters:
            obj_in (SchemaT | dict[str, Any]): Input data for the new record; may be a schema instance or a plain dict.
        
        Returns:
            ModelT: The created and persisted model instance.
        """
        # Inline creation for performance
        if isinstance(obj_in, dict):
            create_data = obj_in
        else:
            create_data = obj_in.model_dump()

        if self.plugin_manager.plugins:
            create_data = await self.plugin_manager.execute_hook(
                LifecycleHook.BEFORE_CREATE, self.model, create_data
            )

        obj = self.model(**create_data)
        self.session.add(obj)
        if self.auto_commit:
            await self.session.commit()
            await self.session.refresh(obj)
        else:
            await self.session.flush()

        if self.plugin_manager.plugins:
            await self.plugin_manager.execute_hook(
                LifecycleHook.AFTER_CREATE, self.model, obj
            )

        if self.auto_commit and self.cache_manager:
            key = self._get_cache_key(obj.id)
            await self.cache_manager.set(key, pickle.dumps(obj))
        return obj

    async def update(
        self,
        db_obj: ModelT,
        obj_in: SchemaT | dict[str, Any],
    ) -> ModelT:
        """
        Update fields on an existing model instance and persist the change.
        
        Parameters:
            db_obj (ModelT): Existing model instance to update.
            obj_in (SchemaT | dict[str, Any]): Update data as a schema instance or a plain dict. When a schema is provided, only fields explicitly set on the schema are applied.
        
        Returns:
            ModelT: The updated model instance.
        
        Notes:
            - Executes BEFORE_UPDATE and AFTER_UPDATE lifecycle hooks when plugins are configured.
            - If `auto_commit` is true, the change is committed and the instance refreshed; otherwise the session is flushed.
            - When `auto_commit` is true and a `cache_manager` is configured, the cache entry for the updated object is replaced.
        """
        # Inline update for performance
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        if self.plugin_manager.plugins:
            update_data = await self.plugin_manager.execute_hook(
                LifecycleHook.BEFORE_UPDATE, self.model, db_obj, update_data
            )

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.session.add(db_obj)
        if self.auto_commit:
            await self.session.commit()
            await self.session.refresh(db_obj)
        else:
            await self.session.flush()

        obj = db_obj

        if self.plugin_manager.plugins:
            await self.plugin_manager.execute_hook(
                LifecycleHook.AFTER_UPDATE, self.model, obj
            )

        if self.auto_commit and self.cache_manager:
            key = self._get_cache_key(obj.id)
            await self.cache_manager.set(key, pickle.dumps(obj))
        return obj

    async def delete(self, db_obj: ModelT) -> ModelT:
        """
        Delete a model instance and perform configured post-delete side effects.
        
        If plugins are registered, executes the BEFORE_DELETE and AFTER_DELETE lifecycle hooks.
        Commits the transaction when the repository is configured with auto_commit=True; otherwise flushes the session.
        If auto_commit is True and a cache manager is configured, removes the instance's cache entry.
        If DataLoader is enabled, clears the instance id from the id loader.
        
        Returns:
            The deleted model instance.
        """
        # Inline delete for performance
        if self.plugin_manager.plugins:
            await self.plugin_manager.execute_hook(
                LifecycleHook.BEFORE_DELETE, self.model, db_obj
            )

        await self.session.delete(db_obj)
        if self.auto_commit:
            await self.session.commit()
        else:
            await self.session.flush()

        obj = db_obj

        if self.plugin_manager.plugins:
            await self.plugin_manager.execute_hook(
                LifecycleHook.AFTER_DELETE, self.model, obj
            )

        if self.auto_commit and self.cache_manager:
            key = self._get_cache_key(obj.id)
            await self.cache_manager.delete(key)

        if self.use_loader:
            self.id_loader.clear(obj.id)
        return obj

    async def create_many(
        self, objs_in: list[SchemaT | dict[str, Any]]
    ) -> list[ModelT]:
        """
        Create multiple model instances from schemas or dictionaries and persist them to the database.
        
        Each input may be a schema instance (converted to a dict) or a plain dict of field values. If plugins are registered, the repository executes BEFORE_CREATE for each item before instantiation and AFTER_CREATE for each instance after persistence. When auto_commit is True the session is committed; otherwise the session is flushed. If auto_commit is True and a cache manager is configured, newly created instances with an `id` are written to the cache.
        
        Parameters:
            objs_in (list[SchemaT | dict[str, Any]]): Items to create, each either a schema object (will be converted to a dict) or a dict of field values.
        
        Returns:
            list[ModelT]: The list of persisted model instances.
        """
        data_list = []
        for obj_in in objs_in:
            if isinstance(obj_in, dict):
                data_list.append(obj_in)
            else:
                data_list.append(obj_in.model_dump())

        processed_data_list = []
        if self.plugin_manager.plugins:
            for data in data_list:
                processed_data = await self.plugin_manager.execute_hook(
                    LifecycleHook.BEFORE_CREATE, self.model, data
                )
                processed_data_list.append(processed_data)
        else:
            processed_data_list = data_list

        instances = [self.model(**data) for data in processed_data_list]
        self.session.add_all(instances)

        if self.auto_commit:
            await self.session.commit()
        else:
            await self.session.flush()

        if self.plugin_manager.plugins:
            for obj in instances:
                await self.plugin_manager.execute_hook(
                    LifecycleHook.AFTER_CREATE, self.model, obj
                )

        if self.auto_commit and self.cache_manager:
            cache_data = {}
            for obj in instances:
                if hasattr(obj, "id") and obj.id:
                    key = self._get_cache_key(obj.id)
                    cache_data[key] = pickle.dumps(obj)

            if cache_data:
                await self.cache_manager.set_many(cache_data)

        return instances

    def batch_writer(
        self, batch_size: int = 100, flush_interval: float = 0.0
    ) -> Batcher[SchemaT | dict[str, Any], None]:
        """
        Get a Batcher instance for streaming inserts.

        Usage:
            async with repo.batch_writer() as writer:
                await writer.add(item)
        """

        async def _processor(items: list[SchemaT | dict[str, Any]]) -> None:
            await self.create_many(items)

        return Batcher(_processor, batch_size=batch_size, flush_interval=flush_interval)