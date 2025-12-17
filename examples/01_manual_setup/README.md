# Manual FastAPI Setup

This example demonstrates how to integrate FluxCRUD into a **FastAPI** application manually, giving you full control over the lifecycle and router configuration.

## 🎯 Concepts Covered

*   **Lifespan Events**: Managing DB connection startup/shutdown.
*   **CRUDRouter**: Automatically generating API endpoints (`GET /`, `POST /`, `GET /{id}`, etc.).
*   **ValidationMiddleware**: Handling repository exceptions and converting them to HTTP 404/400 errors.

## 💻 Code Highlight

```python
# Create Router
router = CRUDRouter(
    model=Task,
    schema=TaskSchema,
    create_schema=TaskCreate,
    update_schema=TaskUpdate,
    prefix="/tasks",
    tags=["Tasks"],
)
app.include_router(router.router)
```

## Try now:

```bash
$ python examples/01_manual_setup/main.py
```
*Then open http://localhost:8000/docs to see the Swagger UI used by FastAPI!*
