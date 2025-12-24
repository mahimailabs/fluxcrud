from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from fluxcrud.core.repository import Repository
from fluxcrud.database import db
from fluxcrud.types import ModelProtocol, SchemaProtocol

ModelT = TypeVar("ModelT", bound=ModelProtocol)
SchemaT = TypeVar("SchemaT", bound=SchemaProtocol)


class UnitOfWork:
    """
    Unit of Work pattern for transaction management.
    Groups multiple operations into a single atomic transaction.
    """

    def __init__(self):
        self.session: AsyncSession | None = None
        self.repositories: dict[type, Repository] = {}

    async def __aenter__(self) -> "UnitOfWork":
        if not db.session_factory:
            raise RuntimeError("Database not initialized. Call db.init() first.")

        # Get a new session directly from factory for manual control
        self.session = db.session_factory()
        # Explicitly begin transaction
        await self.session.begin()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self.session:
            return

        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()

        await self.session.close()

    def repository(
        self, model: type[ModelT], schema: type[SchemaT]
    ) -> Repository[ModelT, SchemaT]:
        """
        Get a repository instance bound to the current transaction session.
        """
        if not self.session:
            raise RuntimeError(
                "UnitOfWork context not active. Use 'async with uow: ...'"
            )

        if model not in self.repositories:
            # We create a transient repository bound to this session
            self.repositories[model] = Repository(
                session=self.session,
                model=model,
                auto_commit=False,
            )

        return self.repositories[model]  # type: ignore
