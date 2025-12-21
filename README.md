<p align="center">
  <a href="https://fluxcrud.mahimai.dev">
    <img src="https://github.com/mahimailabs/fluxcrud/blob/main/assets/logo.png?raw=true" width="400" alt="FluxCRUD Logo">
  </a>
</p>

<p align="center">
    <em>Modern, High-Performance, Async-First CRUD Framework for FastAPI ⚡</em>
</p>

<p align="center">
  <a href="https://github.com/mahimailabs/fluxcrud/actions/workflows/ci.yml">
    <img src="https://github.com/mahimailabs/fluxcrud/actions/workflows/ci.yml/badge.svg" alt="CI Status">
  </a>
  <a href="https://codecov.io/gh/mahimailabs/fluxcrud">
    <img src="https://codecov.io/gh/mahimailabs/fluxcrud/branch/main/graph/badge.svg" alt="Coverage">
  </a>
  <a href="https://pypi.org/project/fluxcrud/">
    <img src="https://img.shields.io/pypi/v/fluxcrud" alt="PyPI Version">
  </a>
  <a href="https://github.com/mahimailabs/fluxcrud/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/mahimailabs/fluxcrud" alt="License">
  </a>
</p>

---

**FluxCRUD** is a developer-friendly framework designed to eliminate boilerplate when building efficient, scalable APIs with **FastAPI** and **SQLAlchemy 2.0**. It provides a fully typed, async-first experience with built-in best practices like **caching**, **N+1 query prevention (DataLoaders)**, and **automatic extensive pagination**.

## ✨ Features

- **🚀 Async & Fast**: Built on top of `asyncpg`, `aiosqlite`, and `SQLAlchemy 2.0`.
- **🛠️ Zero Boilerplate**: Auto-generates fully typed CRUD routes (Create, Read, Update, Delete, List).
- **⚡ Smart Caching**: Integrated support for **Redis**, **Memcached**, and **In-Memory** caching.
- **🔍 Query Optimization**: Built-in **DataLoaders** to solve N+1 query problems automatically.
- **📄 Advanced Pagination**: Cursor-based and limit-offset pagination out of the box.
- **🛡️ Type Safe**: Deep integration with **Pydantic v2** for robust data validation.
- **📦 Modular**: Use what you need—Router, Repository, or the full Framework.

## 📦 Installation

```bash
pip install fluxcrud

# OR with standard extras
pip install "fluxcrud[postgresql,redis]"
```

## 🚀 Quick Start

Build a comprehensive API in less than 30 lines of code.

```python
from fastapi import FastAPI
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel
from fluxcrud import Flux, Base

# 1. Define your Database Model
class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    price: Mapped[float]

# 2. Define Pydantic Schemas
class ItemSchema(BaseModel):
    id: int
    name: str
    price: float

class CreateItemSchema(BaseModel):
    name: str
    price: float

# 3. Initialize App & Flux
app = FastAPI()
flux = Flux(app, db_url="sqlite+aiosqlite:///:memory:")
flux.attach_base(Base)

# 4. Register Routes
# Auto-generates: GET /items, POST /items, GET /items/{id}, PATCH /items/{id}, DELETE /items/{id}
flux.register(
    model=Item,
    schema=ItemSchema,
    create_schema=CreateItemSchema
)
```

Run it locally:

```bash
uvicorn main:app --reload
```

## 🧩 Advanced Usage

### Customizing the Repository

Need custom logic? Extend `FluxRepository` seamlessly.

```python
from fluxcrud.core import FluxRepository

class ItemRepository(FluxRepository[Item]):
    async def get_expensive_items(self, min_price: float):
        query = select(Item).where(Item.price > min_price)
        return await self.all(query)
```

### Enabling Caching

FluxCRUD makes caching trivial.

```python
from fluxcrud.cache import RedisBackend

# Configure Redis cache with 60s TTL
flux = Flux(
    app,
    db_url="...",
    cache_backend=RedisBackend("redis://localhost"),
    cache_ttl=60
)
```

## 🤝 Contributing

We welcome contributions! Please check out our [Contributing Guide](CONTRIBUTING.md) to get started.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
