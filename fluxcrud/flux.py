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

    def __init__(
        self,
        app: FastAPI,
        db_url: str,
        base: type[DeclarativeBase] | None = None,
        **engine_options,
    ):
        self.app = app
        self.db_url = db_url
        self.base = base
        self.engine_options = engine_options
        self._setup_lifecycle()

    def attach_base(self, base: type[DeclarativeBase]) -> None:
        """Attach the declarative base model to Flux."""
        self.base = base

    def _setup_lifecycle(self) -> None:
        """Attach database lifecycle events to the FastAPI app."""
        original_lifespan = self.app.router.lifespan_context

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            db.init(self.db_url, **self.engine_options)
            assert db.engine is not None
            if self.base:
                async with db.engine.begin() as conn:
                    await conn.run_sync(self.base.metadata.create_all)

            if original_lifespan:
                async with original_lifespan(app) as state:
                    yield state
            else:
                yield
            await db.close()

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
