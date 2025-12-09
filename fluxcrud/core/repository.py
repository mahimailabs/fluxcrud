from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fluxcrud.async_patterns import DataLoader
from fluxcrud.core.base import BaseCRUD
from fluxcrud.types import ModelProtocol, SchemaProtocol

ModelT = TypeVar("ModelT", bound=ModelProtocol)
SchemaT = TypeVar("SchemaT", bound=SchemaProtocol)


class Repository(BaseCRUD[ModelT, SchemaT], Generic[ModelT, SchemaT]):
    """Repository pattern implementation with DataLoader integration."""

    def __init__(self, session: AsyncSession, model: type[ModelT]):
        super().__init__(model)
        self.session = session
        self._setup_dataloaders()

    def _setup_dataloaders(self) -> None:
        """Create DataLoaders for this repository."""
        self.id_loader = DataLoader(self._batch_load_by_ids)

    async def _batch_load_by_ids(self, ids: list[Any]) -> list[ModelT | None]:
        """Batch load records by IDs."""
        stmt = select(self.model).where(self.model.id.in_(ids))
        result = await self.session.execute(stmt)
        records = result.scalars().all()

        # Maintain order and handle missing
        record_map = {r.id: r for r in records}
        return [record_map.get(id) for id in ids]

    async def get(self, session: AsyncSession, id: Any) -> ModelT | None:
        """Get by ID using DataLoader (automatic batching)."""
        # Note: We ignore the passed session as we use the bound session
        # This overrides BaseCRUD.get to use DataLoader
        return await self.id_loader.load(id)

    async def get_many_by_ids(self, ids: list[Any]) -> list[ModelT | None]:
        """Get multiple by IDs (single query via DataLoader)."""
        return await self.id_loader.load_many(ids)
