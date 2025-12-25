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

    def __init__(self) -> None:
        """
        Initialize a UnitOfWork instance.

        Initializes:
        - session: the AsyncSession bound to this unit of work (None until the context is entered).
        - repositories: a cache mapping (model type, schema type) tuples to Repository instances created for the current session.
        """
        self.session: AsyncSession | None = None
        self.repositories: dict[tuple[type, type], Repository] = {}

    async def __aenter__(self) -> "UnitOfWork":
        """
        Enter the unit-of-work context by acquiring a new database session and beginning a transaction.

        Ensures the global database session factory is initialized, creates a new AsyncSession from it, begins a transaction on that session, and returns the UnitOfWork instance bound to the active transactional session.

        Returns:
            UnitOfWork: The context manager instance with an active transactional session.

        Raises:
            RuntimeError: If the global database session factory has not been initialized.
        """
        if not db.session_factory:
            raise RuntimeError("Database not initialized. Call db.init() first.")

        # Get a new session directly from factory for manual control
        self.session = db.session_factory()
        # Explicitly begin transaction
        await self.session.begin()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Finalize the transaction and close the session when exiting the UnitOfWork context.

        If there is no active session, no action is taken. If an exception occurred during the managed block (exc_type is not None), the transaction is rolled back; otherwise the transaction is committed. The session is always closed afterwards.

        Parameters:
            exc_type: The exception type supplied by the context manager, or None.
            exc_val: The exception instance supplied by the context manager, or None.
            exc_tb: The traceback supplied by the context manager, or None.
        """
        if not self.session:
            return

        try:
            if exc_type:
                await self.session.rollback()
            else:
                await self.session.commit()
        finally:
            await self.session.close()

    def repository(
        self, model: type[ModelT], schema: type[SchemaT]
    ) -> Repository[ModelT, SchemaT]:
        """
        Get a Repository for the given model and schema bound to the UnitOfWork's active transaction session.

        Parameters:
                model (type[ModelT]): ORM model class for the repository.
                schema (type[SchemaT]): Schema type used by the repository.

        Returns:
                Repository[ModelT, SchemaT]: Repository instance bound to the current session; instances are cached per (model, schema) key.

        Raises:
                RuntimeError: If the UnitOfWork context is not active (no session).
        """
        if not self.session:
            raise RuntimeError(
                "UnitOfWork context not active. Use 'async with uow: ...'"
            )

        key = (model, schema)
        if key not in self.repositories:
            # We create a transient repository bound to this session
            self.repositories[key] = Repository(
                session=self.session,
                model=model,
                auto_commit=False,
            )

        return self.repositories[key]  # type: ignore
