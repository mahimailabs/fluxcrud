import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fluxcrud.core.base import BaseCRUD
from fluxcrud.database import db

# Setup FastAPI app
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
    id: int
    name: str
    description: str


class CRUDItem(BaseCRUD[Item, ItemCreate]):
    pass


@app.post("/items", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    async for session in db.get_session():
        crud_item = CRUDItem(Item, session=session)
        return await crud_item.create(item)


@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    async for session in db.get_session():
        crud_item = CRUDItem(Item, session=session)
        item = await crud_item.get(item_id)
        if not item:
            raise Exception("Item not found")
        return item


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
async def test_create_and_get_item(client):
    # Create
    response = await client.post(
        "/items", json={"name": "Test Item", "description": "A test item"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Item"
    item_id = data["id"]

    # Get
    response = await client.get(f"/items/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["description"] == "A test item"
