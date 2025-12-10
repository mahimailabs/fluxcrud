from collections.abc import Sequence
from contextlib import asynccontextmanager
from enum import Enum
from typing import TypeVar

from fastapi import FastAPI
from sqlalchemy.orm import DeclarativeBase

from fluxcrud.database import db
from fluxcrud.types import ModelProtocol, SchemaProtocol
from fluxcrud.web.router import CRUDRouter

ModelT = TypeVar("ModelT", bound=ModelProtocol)
SchemaT = TypeVar("SchemaT", bound=SchemaProtocol)


class Flux:
    """
    High-level helper for FluxCRUD to improve Developer Experience.
    Automates database setup, lifecycle management, and router registration.
    """

    def __init__(self, app: FastAPI, db_url: str, base: type[DeclarativeBase]):
        self.app = app
        self.db_url = db_url
        self.base = base
        self._setup_lifecycle()

    def _setup_lifecycle(self) -> None:
        """Attach database lifecycle events to the FastAPI app."""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            db.init(self.db_url)
            assert db.engine is not None
            async with db.engine.begin() as conn:
                await conn.run_sync(self.base.metadata.create_all)
            yield
            # Shutdown (if needed)

        # If app already has a lifespan, we might need to wrap it.
        # For simplicity, we assume Flux controls the lifespan or users use Flux's lifespan.
        # But FastAPI only accepts one lifespan.
        # A better approach: Flux provides the lifespan, user passes it to FastAPI.
        # Or Flux wraps the app's existing lifespan?
        # Let's override it for now, assuming Flux is the main driver.
        self.app.router.lifespan_context = lifespan

    def register(
        self,
        model: type[ModelT],
        schema: type[SchemaT],
        create_schema: type[SchemaT] | None = None,
        update_schema: type[SchemaT] | None = None,
        prefix: str | None = None,
        tags: Sequence[str | Enum] | None = None,
    ) -> CRUDRouter[ModelT, SchemaT]:
        """
        Register a model with FluxCRUD.
        Creates a CRUDRouter and includes it in the FastAPI app.
        """
        router = CRUDRouter(
            model=model,
            schema=schema,
            create_schema=create_schema,
            update_schema=update_schema,
            prefix=prefix if prefix is not None else f"/{model.__tablename__}",
            tags=tags,
        )
        self.app.include_router(router.router)
        return router
