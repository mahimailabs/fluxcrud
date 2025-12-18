import asyncio
import logging
from uuid import uuid4

from examples.helper import (
    Base,
    Post,
    PostRepository,
)
from examples.helper import (
    SocialUser as User,
)
from examples.helper import (
    SocialUserRepository as UserRepository,
)
from fluxcrud.database import db
from fluxcrud.query import QueryAnalyzer

logging.basicConfig(level=logging.INFO)
nl_logger = logging.getLogger("fluxcrud.query.optimizer")
nl_logger.setLevel(logging.WARNING)


def seed_data(session):
    users = []
    posts = []

    for i in range(10):
        u = User(id=str(uuid4()), name=f"User {i}")
        session.add(u)
        users.append(u)

        for j in range(5):
            p = Post(id=str(uuid4()), title=f"Post {i}-{j}", user_id=u.id)
            session.add(p)
            posts.append(p)

    return users, posts


async def main():
    db.init("sqlite+aiosqlite:///dataloader_demo.db")

    # Enable Query Analyzer manually
    # We access the internal query counter for demonstration
    analyzer = QueryAnalyzer()
    analyzer.enable(db.engine)

    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # --- 1: The N+1 Problem (Naive Loop) ---
    session_gen = db.get_session()
    session = await anext(session_gen)

    user_repo = UserRepository(session, User)
    post_repo = PostRepository(session, Post)

    users, posts = seed_data(session)
    await session.commit()

    analyzer._query_count = 0
    all_posts = await post_repo.get_multi(limit=50)

    users = []
    for post in all_posts:
        # Without DataLoader, this would be N queries
        users.append(await user_repo.get(post.user_id))

    count_naive = analyzer._query_count
    print(f"Naive Loop:     {count_naive} queries")

    # --- 2: Optimized (DataLoader Batching) ---
    session_gen = db.get_session()
    session = await anext(session_gen)

    user_repo = UserRepository(session, User)
    post_repo = PostRepository(session, Post)

    analyzer._query_count = 0
    all_posts = await post_repo.get_multi(limit=50)

    user_ids = [p.user_id for p in all_posts]
    users = await user_repo.get_many_by_ids(user_ids)  # noqa: F841

    count_opt = analyzer._query_count

    print(f"DataLoader:     {count_opt} queries")
    print(f"Reduction:      {count_naive} -> {count_opt}")

    await db.close()


if __name__ == "__main__":
    asyncio.run(main())

# Naive Loop:     11 queries
# DataLoader:     2 queries
# Reduction:      11 -> 2
