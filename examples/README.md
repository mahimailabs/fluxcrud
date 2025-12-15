# FluxCRUD Examples

This directory contains examples demonstrating how to use FluxCRUD in various scenarios.

| Example | Description | How to Run |
| :--- | :--- | :--- |
| **[00_basic_crud](./00_basic_crud)** | **Standalone Script**<br>Demonstrates basic CRUD operations using `Repository` directly with an in-memory database. No web framework involved. | `uv run python examples/00_basic_crud/main.py` |
| **[01_manual_setup](./01_manual_setup)** | **FastAPI Manual Integration**<br>Shows how to integrate FluxCRUD with FastAPI manually, managing the database lifecycle and dependencies yourself. Useful for understanding the internals. | `uv run uvicorn examples.01_manual_setup.main:app --reload` |
| **[02_flux_setup](./02_flux_setup)** | **FastAPI + Flux Helper (Recommended)**<br>Demonstrates the recommended way to use FluxCRUD with the `Flux` helper class. Automates DB setup and router registration for a great DX. | `uv run uvicorn examples.02_flux_setup.main:app --reload` |

## Real-time Updates (WebSockets)

Both FastAPI examples (01 and 02) support real-time updates via WebSockets. To see it in action:

1.  Run the example app (e.g., `uv run uvicorn examples.02_flux_setup.main:app --reload`).
2.  Open `examples/02_flux_setup/index.html` in your browser.
3.  Use the Swagger UI at `http://localhost:8000/docs` to create, update, or delete tasks.
4.  Watch the changes appear instantly in the browser!
