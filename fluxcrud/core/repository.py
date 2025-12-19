import pickle
from collections.abc import Sequence
from typing import Any, Generic, TypeVar, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fluxcrud.async_patterns import Batcher, DataLoader
from fluxcrud.cache.manager import CacheManager
from fluxcrud.core.base import BaseCRUD
from fluxcrud.types import ModelProtocol, SchemaProtocol

ModelT = TypeVar("ModelT", bound=ModelProtocol)
SchemaT = TypeVar("SchemaT", bound=SchemaProtocol)


class Repository(BaseCRUD[ModelT, SchemaT], Generic[ModelT, SchemaT]):
    """Repository pattern implementation with DataLoader integration and Caching."""

    __slots__ = ("session", "cache_manager", "use_loader", "id_loader", "model")

    def __init__(
        self,
        session: AsyncSession,
        model: type[ModelT],
        cache_manager: CacheManager | None = None,
        use_loader: bool = False,
    ):
        super().__init__(model)
        self.session = session
        self.cache_manager = cache_manager
        self.use_loader = use_loader
        if self.use_loader:
            self._setup_dataloaders()

    def _setup_dataloaders(self) -> None:
        """Create DataLoaders for this repository."""
        self.id_loader = DataLoader(self._batch_load_by_ids)

    def _get_cache_key(self, id: Any) -> str:
        """Generate cache key for an ID."""
        return f"{self.model.__tablename__}:{id}"

    async def _batch_load_by_ids(self, ids: list[Any]) -> list[ModelT | None]:
        """Batch load records by IDs."""
        stmt = select(self.model).where(self.model.id.in_(ids))
        result = await self.session.execute(stmt)
        records = result.scalars().all()

        # Maintain order and handle missing
        record_map = {r.id: r for r in records}
        return [record_map.get(id) for id in ids]

    async def get(self, id: Any) -> ModelT | None:
        """Get by ID with Cache -> DataLoader (DB) fallback."""
        if self.cache_manager:
            key = self._get_cache_key(id)
            cached_bytes = await self.cache_manager.get(key)
            if cached_bytes:
                return cast(ModelT, pickle.loads(cached_bytes))

        # Cache miss or no cache:
        if self.use_loader:
            obj = await self.id_loader.load(id)
        else:
            obj = await self.session.get(self.model, id)

        if self.cache_manager and obj:
            key = self._get_cache_key(id)
            # We pickle the object. Note: Cached objects are detached.
            await self.cache_manager.set(key, pickle.dumps(obj))

        return obj

    async def get_multi(
        self, skip: int = 0, limit: int = 100, **kwargs: Any
    ) -> Sequence[ModelT]:
        """Get multiple records."""
        return await super().get_multi(skip=skip, limit=limit, **kwargs)

    async def get_many_by_ids(self, ids: list[Any]) -> list[ModelT | None]:
        """Get multiple by IDs."""
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
        """Create new record and handle cache."""
        # Inline creation for performance
        if isinstance(obj_in, dict):
            create_data = obj_in
        else:
            create_data = obj_in.model_dump()

        obj = self.model(**create_data)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)

        if self.cache_manager:
            key = self._get_cache_key(obj.id)
            await self.cache_manager.set(key, pickle.dumps(obj))
        return obj

    async def update(
        self,
        db_obj: ModelT,
        obj_in: SchemaT | dict[str, Any],
    ) -> ModelT:
        """Update record and invalidate/update cache."""
        # Inline update for performance
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        obj = db_obj
        if self.cache_manager:
            key = self._get_cache_key(obj.id)
            await self.cache_manager.set(key, pickle.dumps(obj))
        return obj

    async def delete(self, db_obj: ModelT) -> ModelT:
        """Delete record and invalidate cache."""
        # Inline delete for performance
        await self.session.delete(db_obj)
        await self.session.commit()
        obj = db_obj
        if self.cache_manager:
            key = self._get_cache_key(obj.id)
            await self.cache_manager.delete(key)

        if self.use_loader:
            self.id_loader.clear(obj.id)
        return obj

    async def create_many(
        self, objs_in: list[SchemaT | dict[str, Any]]
    ) -> list[ModelT]:
        """Create multiple records efficiently."""
        data_list = []
        for obj_in in objs_in:
            if isinstance(obj_in, dict):
                data_list.append(obj_in)
            else:
                data_list.append(obj_in.model_dump())

        instances = [self.model(**data) for data in data_list]
        self.session.add_all(instances)
        await self.session.commit()

        if self.cache_manager:
            for obj in instances:
                if hasattr(obj, "id") and obj.id:
                    key = self._get_cache_key(obj.id)
                    await self.cache_manager.set(key, pickle.dumps(obj))

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
