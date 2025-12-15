from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fluxcrud import Flux
from fluxcrud.web.middleware import ValidationMiddleware


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


# 3. Create App
app = FastAPI()
app.add_middleware(ValidationMiddleware)

# 4. Initialize Flux
flux = Flux(app, db_url="sqlite+aiosqlite:///tasks.db")
flux.attach_base(Base)

# 5. Register Resources
flux.register(
    model=Task,
    schema=TaskSchema,
    create_schema=TaskCreate,
    update_schema=TaskUpdate,
    tags=["Tasks"],
)


@app.get("/")
def root():
    return {"message": "Welcome to FluxCRUD Task API! Visit /docs for Swagger UI."}
