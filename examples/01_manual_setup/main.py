from contextlib import asynccontextmanager

from fastapi import FastAPI

from examples.helper import (
    Base,
    Task,
    TaskCreate,
    TaskSchema,
    TaskUpdate,
)
from fluxcrud.database import db
from fluxcrud.web.middleware import ValidationMiddleware
from fluxcrud.web.router import CRUDRouter


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init("sqlite+aiosqlite:///tasks.db")
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await db.close()


app = FastAPI(lifespan=lifespan)
app.add_middleware(ValidationMiddleware)


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
