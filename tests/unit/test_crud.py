import pytest
import pytest_asyncio
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fluxcrud.core.base import BaseCRUD
from fluxcrud.database import db


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]


class UserCreate(BaseModel):
    name: str
    email: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None


class CRUDUser(BaseCRUD[User, UserCreate]):
    pass


@pytest_asyncio.fixture(autouse=True)
async def create_tables(db_engine):
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def crud_user(session):
    return CRUDUser(User, session=session)


@pytest.mark.asyncio
async def test_create_user(crud_user):
    user_in = UserCreate(name="Alice", email="alice@example.com")
    user = await crud_user.create(user_in)
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
    assert user.id is not None


@pytest.mark.asyncio
async def test_get_user(crud_user):
    user_in = UserCreate(name="Bob", email="bob@example.com")
    created_user = await crud_user.create(user_in)

    fetched_user = await crud_user.get(created_user.id)
    assert fetched_user is not None
    assert fetched_user.id == created_user.id
    assert fetched_user.name == "Bob"


@pytest.mark.asyncio
async def test_update_user(crud_user):
    user_in = UserCreate(name="Charlie", email="charlie@example.com")
    user = await crud_user.create(user_in)

    update_in = UserUpdate(name="Charles")
    updated_user = await crud_user.update(user, update_in)
    assert updated_user.name == "Charles"
    assert updated_user.email == "charlie@example.com"


@pytest.mark.asyncio
async def test_delete_user(crud_user):
    user_in = UserCreate(name="David", email="david@example.com")
    user = await crud_user.create(user_in)

    await crud_user.delete(user)
    fetched_user = await crud_user.get(user.id)
    assert fetched_user is None
