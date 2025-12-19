from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fluxcrud.web.deps import get_session
from fluxcrud.web.router import CRUDRouter

app = FastAPI()


class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str]


class ItemCreate(BaseModel):
    name: str
    description: str


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str


router = CRUDRouter(
    Item, ItemResponse, create_schema=ItemCreate, update_schema=ItemCreate
)
app.include_router(router.router, prefix="/items")

mock_repo = AsyncMock()
mock_repo.create.return_value = Item(id=1, name="WS Item", description="WS Desc")
mock_repo.update.return_value = Item(id=1, name="Updated WS", description="WS Desc")
mock_repo.delete.return_value = Item(id=1, name="Deleted Item", description="Desc")
mock_session = AsyncMock()


async def get_mock_session():
    yield mock_session


app.dependency_overrides[get_session] = get_mock_session


def test_websocket_broadcast():
    # Override get_repo in the router's deps
    router.deps.get_repo = MagicMock(return_value=mock_repo)

    client = TestClient(app)
    with client.websocket_connect("/items/ws") as websocket:
        # Trigger create via HTTP
        response = client.post(
            "/items/", json={"name": "WS Item", "description": "WS Desc"}
        )
        assert response.status_code == 200

        # Receive broadcast
        data = websocket.receive_json()
        assert data["type"] == "create"
        assert data["data"]["name"] == "WS Item"

        item_id = 1

        # Trigger update
        response = client.put(
            f"/items/{item_id}",
            json={"name": "Updated WS", "description": "WS Desc", "id": item_id},
        )
        assert response.status_code == 200

        # Receive broadcast
        data = websocket.receive_json()
        assert data["type"] == "update"
        assert data["data"]["name"] == "Updated WS"

        # Trigger delete
        response = client.delete(f"/items/{item_id}")
        assert response.status_code == 200

        # Receive broadcast
        data = websocket.receive_json()
        assert data["type"] == "delete"
        assert data["data"]["id"] == item_id
