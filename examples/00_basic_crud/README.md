# Basic CRUD

This example demonstrates the core **Repository Pattern** in FluxCRUD without any web framework integration.

## 🎯 Concepts Covered

*   **Repository**: Type-safe encapsulation of DB operations (`get`, `create`, `update`, `delete`, `get_multi`).
*   **Schemas**: Pydantic models for input/output validation.
*   **Database**: Automatic session management.

## 💻 Code Highlight

```python
# Create a user
user = await repo.create(session, UserCreate(name="Alice", email="alice@example.com"))

# Read it back (automatically cached if caching enabled)
fetched_user = await repo.get(session, user.id)
```

## Try now:

```bash
$ python examples/00_basic_crud/main.py
```
