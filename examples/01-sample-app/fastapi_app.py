from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fluxcrud.database import db
from fluxcrud.web.middleware import ValidationMiddleware
from fluxcrud.web.router import CRUDRouter


# 1. Define Model
class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    completed: Mapped[bool] = mapped_column(default=False)


# 2. Define Schemas
class TaskSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    completed: bool


class TaskCreate(BaseModel):
    title: str
    completed: bool = False


class TaskUpdate(BaseModel):
    title: str | None = None
    completed: bool | None = None


# 3. Setup Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db.init("sqlite+aiosqlite:///tasks.db")
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    # (Cleanup if needed)


# 4. Create App
app = FastAPI(lifespan=lifespan)
app.add_middleware(ValidationMiddleware)


# 5. Create Router
router = CRUDRouter(
    model=Task,
    schema=TaskSchema,
    create_schema=TaskCreate,
    update_schema=TaskUpdate,
    prefix="/tasks",
    tags=["Tasks"],
)

app.include_router(router.router)


@app.get("/")
def root():
    return {"message": "Welcome to FluxCRUD Task API! Visit /docs for Swagger UI."}
