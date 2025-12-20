import os

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import StaticPool

from fluxcrud.flux import Flux


class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class ItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


def get_db_config():
    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    kwargs = {}
    if "sqlite" in db_url:
        kwargs = {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
    return db_url, kwargs


def test_flux_initialization():
    app = FastAPI()
    db_url, kwargs = get_db_config()
    flux = Flux(app, db_url, **kwargs)
    flux.attach_base(Base)
    assert flux.app == app
    assert flux.db_url == db_url
    assert flux.base == Base
    assert app.router.lifespan_context is not None


def test_flux_register():
    app = FastAPI()
    db_url, kwargs = get_db_config()
    flux = Flux(app, db_url, **kwargs)
    flux.attach_base(Base)

    flux.register(Item, ItemSchema)

    # Verify router is added to app
    routes = [r.path for r in app.routes]
    assert "/items/" in routes
    assert "/items/{id}" in routes
    assert "/items/ws" in routes


def test_flux_wraps_lifespan():
    from contextlib import asynccontextmanager

    from fastapi.testclient import TestClient

    startup_called = False
    shutdown_called = False

    @asynccontextmanager
    async def my_lifespan(app: FastAPI):
        nonlocal startup_called, shutdown_called
        startup_called = True
        yield
        shutdown_called = True

    app = FastAPI(lifespan=my_lifespan)
    # Initialize Flux
    db_url, kwargs = get_db_config()
    Flux(app, db_url, **kwargs)

    # Trigger lifespan via TestClient
    with TestClient(app):
        assert startup_called

    assert shutdown_called
