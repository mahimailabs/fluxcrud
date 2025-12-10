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
    flux = Flux(app, "sqlite+aiosqlite:///:memory:", Base)
    assert flux.app == app
    assert flux.db_url == "sqlite+aiosqlite:///:memory:"
    assert app.router.lifespan_context is not None


def test_flux_register():
    app = FastAPI()
    flux = Flux(app, "sqlite+aiosqlite:///:memory:", Base)

    flux.register(Item, ItemSchema)

    # Verify router is added to app
    routes = [r.path for r in app.routes]
    assert "/items/" in routes
    assert "/items/{id}" in routes
