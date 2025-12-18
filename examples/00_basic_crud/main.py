import asyncio

from examples.helper import (
    Base,
    User,
    UserCreate,
    UserRepository,
    UserUpdate,
)
from fluxcrud.database import db


async def main():
    db.init("sqlite+aiosqlite:///basic_crud.db")

    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with db.session_factory() as session:
        repo = UserRepository(session, User)

        # Create
        user_in = UserCreate(name="Alice", email="alice@example.com")
        user = await repo.create(user_in)

        # Read
        fetched_user = await repo.get(user.id)
        if fetched_user:
            print(f"Fetched: {fetched_user.name}")

        # Update
        update_data = UserUpdate(name="Alice Smith")
        await repo.update(user, update_data)

        # List
        users = await repo.get_multi()
        for u in users:
            print(f"- {u.name}")

        # Delete
        await repo.delete(user)


if __name__ == "__main__":
    asyncio.run(main())
