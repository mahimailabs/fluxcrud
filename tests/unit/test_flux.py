from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

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


def test_flux_initialization():
    app = FastAPI()
    flux = Flux(app, "sqlite+aiosqlite:///:memory:")
    flux.attach_base(Base)
    assert flux.app == app
    assert flux.db_url == "sqlite+aiosqlite:///:memory:"
    assert flux.base == Base
    assert app.router.lifespan_context is not None


def test_flux_register():
    app = FastAPI()
    flux = Flux(app, "sqlite+aiosqlite:///:memory:")
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
    Flux(app, "sqlite+aiosqlite:///:memory:")

    # Trigger lifespan via TestClient
    with TestClient(app):
        assert startup_called

    assert shutdown_called
