import pytest
import pytest_asyncio
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fluxcrud.core.base import BaseCRUD
from fluxcrud.database import db

app = FastAPI()


class Base(DeclarativeBase):
    pass


class AdvancedItem(Base):
    __tablename__ = "advanced_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    status: Mapped[str]


class ItemCreate(BaseModel):
    name: str
    status: str


class ItemUpdate(BaseModel):
    name: str | None = None
    status: str | None = None


class ItemResponse(BaseModel):
    id: int
    name: str
    status: str


class CRUDAdvancedItem(BaseCRUD[AdvancedItem, ItemCreate]):
    pass


@app.post("/items", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    async for session in db.get_session():
        crud = CRUDAdvancedItem(AdvancedItem, session=session)
        obj = await crud.create(item)
        return ItemResponse.model_validate(obj, from_attributes=True)


@app.get("/items", response_model=list[ItemResponse])
async def list_items(skip: int = 0, limit: int = 10):
    async for session in db.get_session():
        crud = CRUDAdvancedItem(AdvancedItem, session=session)
        items = await crud.get_multi(skip=skip, limit=limit)
        return [ItemResponse.model_validate(i, from_attributes=True) for i in items]


@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    async for session in db.get_session():
        crud = CRUDAdvancedItem(AdvancedItem, session=session)
        item = await crud.get(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return ItemResponse.model_validate(item, from_attributes=True)


@app.patch("/items/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, item_in: ItemUpdate):
    async for session in db.get_session():
        crud = CRUDAdvancedItem(AdvancedItem, session=session)
        db_item = await crud.get(item_id)
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        obj = await crud.update(db_item, item_in.model_dump(exclude_unset=True))
        return ItemResponse.model_validate(obj, from_attributes=True)


@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    async for session in db.get_session():
        crud = CRUDAdvancedItem(AdvancedItem, session=session)
        db_item = await crud.get(item_id)
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        await crud.delete(db_item)
        return {"ok": True}


@pytest_asyncio.fixture(autouse=True)
async def setup_db(db_engine):
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
async def test_list_pagination(client):
    is_postgres = db.engine.dialect.name == "postgresql"
    loop_count = 15 if is_postgres else 1

    # Seed
    for i in range(loop_count):
        await client.post("/items", json={"name": f"Item {i}", "status": "active"})

    limit = 5
    resp = await client.get(f"/items?limit={limit}")
    assert resp.status_code == 200
    expected_count = min(limit, loop_count)
    assert len(resp.json()) == expected_count

    skip = 1
    limit = 10
    resp = await client.get(f"/items?skip={skip}&limit={limit}")
    assert resp.status_code == 200
    data = resp.json()
    expected_remaining = max(0, loop_count - skip)
    assert len(data) == min(limit, expected_remaining)


@pytest.mark.asyncio
async def test_update_flow(client):
    resp = await client.post("/items", json={"name": "Old Name", "status": "draft"})
    item_id = resp.json()["id"]
    resp = await client.patch(f"/items/{item_id}", json={"name": "New Name"})

    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"
    assert resp.json()["status"] == "draft"

    resp = await client.get(f"/items/{item_id}")
    assert resp.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_flow(client):
    resp = await client.post("/items", json={"name": "To Delete", "status": "trash"})
    item_id = resp.json()["id"]

    resp = await client.delete(f"/items/{item_id}")
    assert resp.status_code == 200

    resp = await client.get(f"/items/{item_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_error_handling(client):
    resp = await client.get("/items/99999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Item not found"
