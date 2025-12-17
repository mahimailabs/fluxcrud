from fastapi import FastAPI

from examples.helper import (
    Base,
    Task,
    TaskCreate,
    TaskSchema,
    TaskUpdate,
)
from fluxcrud import Flux
from fluxcrud.web.middleware import ValidationMiddleware

app = FastAPI()
app.add_middleware(ValidationMiddleware)

flux = Flux(app, db_url="sqlite+aiosqlite:///tasks.db")
flux.attach_base(Base)

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
