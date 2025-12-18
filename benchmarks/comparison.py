import asyncio
import time

# FastCRUD
from fastcrud import FastCRUD
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fluxcrud.core import Repository

NUM_ITEMS = 1000
DB_URL = "sqlite+aiosqlite:///benchmark_comparison.db"


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]


class UserSchema(BaseModel):
    id: int
    name: str
    email: str


class UserCreate(BaseModel):
    name: str
    email: str


class UserRepository(Repository[User, UserSchema]):
    pass


user_crud: FastCRUD = FastCRUD(User)


async def time_it(label, coro):
    start = time.time()
    await coro
    end = time.time()
    duration = end - start
    print(f"{label:<25} | {duration:.4f}s | {NUM_ITEMS / duration:.0f} ops/s")
    return duration


async def main():
    print(f"Benchmarking {NUM_ITEMS} items on {DB_URL}...\n")

    engine = create_async_engine(DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)

    data = [
        UserCreate(name=f"User {i}", email=f"user{i}@test.com")
        for i in range(NUM_ITEMS)
    ]
    print(f"--- INSERT ({NUM_ITEMS} ops) ---")

    # Raw SQLAlchemy
    async def raw_insert():
        async with async_session() as session:
            for d in data:
                session.add(User(name=d.name, email=d.email))
            await session.commit()

    # Reset DB
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    await time_it("Raw SQLAlchemy (Bulk)", raw_insert())

    # FluxCRUD
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async def flux_insert_single():
        async with async_session() as session:
            repo = UserRepository(session, User)
            for d in data:
                await repo.create(d)

    await time_it("FluxCRUD (Loop)", flux_insert_single())

    # Batcher Optimization
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async def flux_insert_batch():
        async with async_session() as session:
            repo = UserRepository(session, User)
            async with repo.batch_writer() as writer:
                for d in data:
                    await writer.add(d)

    await time_it("FluxCRUD (Batcher)", flux_insert_batch())

    # FastCRUD
    # Reset DB
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async def fastcrud_insert():
        async with async_session() as session:
            for d in data:
                await user_crud.create(session, d)

    await time_it("FastCRUD (Loop)", fastcrud_insert())

    # --- READ BENCHMARK ---
    print("\n--- READ (1000 ops by ID) ---")

    # Reset DB
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Populate DB first
    async with async_session() as session:
        for i, d in enumerate(data, 1):
            session.add(User(id=i, name=d.name, email=d.email))
        await session.commit()

    ids = list(range(1, NUM_ITEMS + 1))

    # Raw
    async def raw_read():
        async with async_session() as session:
            for i in ids:
                stmt = select(User).where(User.id == i)
                await session.execute(stmt)

    await time_it("Raw SQLAlchemy", raw_read())

    # FluxCRUD
    async def flux_read():
        async with async_session() as session:
            repo = UserRepository(session, User)
            for i in ids:
                await repo.get(i)

    await time_it("FluxCRUD (Direct)", flux_read())

    async def flux_read_loader():
        async with async_session() as session:
            repo = UserRepository(session, User, use_loader=True)
            for i in ids:
                await repo.get(i)

    await time_it("FluxCRUD (Loader)", flux_read_loader())

    # FastCRUD
    async def fastcrud_read():
        async with async_session() as session:
            for i in ids:
                await user_crud.get(session, id=i)

    await time_it("FastCRUD", fastcrud_read())

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
