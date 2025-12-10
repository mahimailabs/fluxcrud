import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fluxcrud.database import db
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


@pytest_asyncio.fixture(autouse=True)
async def create_tables(db_engine):
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_router_create_and_get(client):
    # Create
    response = await client.post(
        "/items/", json={"name": "Router Item", "description": "Created via router"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Router Item"
    item_id = data["id"]

    # Get
    response = await client.get(f"/items/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Router Item"


@pytest.mark.asyncio
async def test_router_list(client):
    # Create multiple
    await client.post("/items/", json={"name": "Item 1", "description": "Desc 1"})
    await client.post("/items/", json={"name": "Item 2", "description": "Desc 2"})

    # List
    response = await client.get("/items/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_router_update(client):
    # Create
    response = await client.post(
        "/items/", json={"name": "Update Me", "description": "Original"}
    )
    item_id = response.json()["id"]

    # Update
    response = await client.put(
        f"/items/{item_id}",
        json={"name": "Updated", "description": "Original", "id": item_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"


@pytest.mark.asyncio
async def test_router_delete(client):
    # Create
    response = await client.post(
        "/items/", json={"name": "Delete Me", "description": "To be deleted"}
    )
    item_id = response.json()["id"]

    # Delete
    response = await client.delete(f"/items/{item_id}")
    assert response.status_code == 200

    # Verify deleted
    response = await client.get(f"/items/{item_id}")
    assert response.status_code == 404
