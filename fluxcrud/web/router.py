from collections.abc import Sequence
from enum import Enum
from typing import Any, Generic, TypeVar

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from fluxcrud.types import ModelProtocol, SchemaProtocol
from fluxcrud.web.deps import Deps, SessionDep
from fluxcrud.web.websockets import WebSocketManager

ModelT = TypeVar("ModelT", bound=ModelProtocol)
SchemaT = TypeVar("SchemaT", bound=SchemaProtocol)


class CRUDRouter(Generic[ModelT, SchemaT]):
    """Auto-router generator for CRUD operations."""

    def __init__(
        self,
        model: type[ModelT],
        schema: type[SchemaT],
        create_schema: type[SchemaT] | None = None,
        update_schema: type[SchemaT] | None = None,
        prefix: str = "",
        tags: Sequence[str | Enum] | None = None,
    ):
        self.model = model
        self.schema = schema
        self.create_schema = create_schema or schema
        self.update_schema = update_schema or schema
        self.router = APIRouter(
            prefix=prefix,
            tags=list(tags) if tags else [model.__tablename__],
        )
        self.deps = Deps[ModelT, SchemaT](model)
        self.ws_manager = WebSocketManager()
        self._register_routes()

    def _register_routes(self) -> None:
        """Register all CRUD routes."""

        # WebSocket endpoint
        @self.router.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket) -> None:
            await self.ws_manager.connect(websocket)
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.ws_manager.disconnect(websocket)

        # Create
        @self.router.post("/", response_model=self.schema)
        async def create(
            item: self.create_schema,  # type: ignore
            session: SessionDep,
        ) -> Any:
            repo = self.deps.get_repo(session)
            created_item = await repo.create(session, item)
            data = self.schema.model_validate(created_item).model_dump()
            await self.ws_manager.broadcast({"type": "create", "data": data})
            return created_item

        # Read
        @self.router.get("/{id}", response_model=self.schema)
        async def get(
            id: int,
            session: SessionDep,
        ) -> Any:
            repo = self.deps.get_repo(session)
            item = await repo.get(session, id)
            if not item:
                # TODO: Use proper exception handler
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="Item not found")
            return item

        # List
        schema = self.schema

        @self.router.get("/", response_model=list[schema])  # type: ignore
        async def list_items(
            session: SessionDep,
            skip: int = 0,
            limit: int = 100,
        ) -> Any:
            repo = self.deps.get_repo(session)
            return await repo.get_multi(session, skip=skip, limit=limit)

        # Update
        @self.router.put("/{id}", response_model=self.schema)
        async def update(
            id: int,
            item_in: self.update_schema,  # type: ignore
            session: SessionDep,
        ) -> Any:
            repo = self.deps.get_repo(session)
            db_obj = await repo.get(session, id)
            if not db_obj:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="Item not found")
            updated_item = await repo.update(session, db_obj, item_in)
            data = self.schema.model_validate(updated_item).model_dump()
            await self.ws_manager.broadcast({"type": "update", "data": data})
            return updated_item

        # Delete
        @self.router.delete("/{id}", response_model=self.schema)
        async def delete(
            id: int,
            session: SessionDep,
        ) -> Any:
            repo = self.deps.get_repo(session)
            db_obj = await repo.get(session, id)
            if not db_obj:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="Item not found")
            deleted_item = await repo.delete(session, db_obj)
            data = self.schema.model_validate(deleted_item).model_dump()
            await self.ws_manager.broadcast({"type": "delete", "data": data})
            return deleted_item
