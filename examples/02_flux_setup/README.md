# Flux Helper Setup

This example demonstrates the **"Flux" Helper**, which provides the best Developer Experience (DX) for setting up FluxCRUD in a FastAPI app.

## 🎯 Concepts Covered

*   **Flux Helper**: A wrapper that handles database initialization, lifecycle management, and router registration in fewer lines of code.
*   **One-liner Registration**: `flux.register` handles everything needed to expose a resource.

## 💻 Code Highlight

```python
# Initialize
flux = Flux(app, db_url="sqlite+aiosqlite:///tasks.db")
flux.attach_base(Base)

# Register Resource (Done!)
flux.register(
    model=Task,
    schema=TaskSchema,
    create_schema=TaskCreate,
    update_schema=TaskUpdate,
    tags=["Tasks"],
)
```

## Try now:

```bash
$ python examples/02_flux_setup/main.py
```
*Then open http://localhost:8000/docs*
