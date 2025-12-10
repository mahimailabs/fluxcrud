from collections.abc import AsyncGenerator
from typing import Annotated, Generic, TypeVar

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from fluxcrud.core.repository import Repository
from fluxcrud.database import db
from fluxcrud.types import ModelProtocol, SchemaProtocol

ModelT = TypeVar("ModelT", bound=ModelProtocol)
SchemaT = TypeVar("SchemaT", bound=SchemaProtocol)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async for session in db.get_session():
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


class Deps(Generic[ModelT, SchemaT]):
    """Dependency injection factory for repositories."""

    def __init__(self, model: type[ModelT]):
        self.model = model

    def get_repo(self, session: SessionDep) -> Repository[ModelT, SchemaT]:
        """Get repository instance."""
        return Repository(session, self.model)
