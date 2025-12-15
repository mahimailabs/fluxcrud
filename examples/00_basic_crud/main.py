import asyncio

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fluxcrud.core.repository import Repository
from fluxcrud.database import db


# 1. Define Model
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]


# 2. Define Schema
class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str


class UserCreate(BaseModel):
    name: str
    email: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None


# 3. Define Repository
class UserRepository(Repository[User, UserSchema]):
    pass


async def main():
    # Initialize DB (In-memory SQLite)
    db.init("sqlite+aiosqlite:///:memory:")

    # Create Tables
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Use Repository
    async with db.session_factory() as session:
        repo = UserRepository(session, User)

        # Create
        print("--- Creating User ---")
        user_in = UserCreate(name="Alice", email="alice@example.com")
        user = await repo.create(session, user_in)
        print(f"Created: {user.name} ({user.email})")

        # Read
        print("\n--- Reading User ---")
        fetched_user = await repo.get(session, user.id)
        if fetched_user:
            print(f"Fetched: {fetched_user.name}")

        # Update
        print("\n--- Updating User ---")
        update_data = UserUpdate(name="Alice Smith")
        updated_user = await repo.update(session, user, update_data)
        print(f"Updated: {updated_user.name}")

        # List
        print("\n--- Listing Users ---")
        users = await repo.get_multi(session)
        print(f"Total Users: {len(users)}")
        for u in users:
            print(f"- {u.name}")

        # Delete
        print("\n--- Deleting User ---")
        deleted_user = await repo.delete(session, user)
        print(f"Deleted: {deleted_user.name}")

        # Verify Deletion
        repo.id_loader.clear(user.id)
        missing_user = await repo.get(session, user.id)
        print(f"Exists? {missing_user is not None}")


if __name__ == "__main__":
    asyncio.run(main())
