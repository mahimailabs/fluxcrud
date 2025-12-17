import asyncio
import time
from uuid import uuid4

from examples.helper import (
    Base,
    Metric,
    MetricRepository,
)
from fluxcrud.async_patterns import ParallelExecutor
from fluxcrud.database import db

NUM_ITEMS = 500
WORK_DELAY = 0.01


async def seed_data(repo, session) -> list[str]:
    items = [
        {"id": str(uuid4()), "name": f"item_{i}", "value": i} for i in range(NUM_ITEMS)
    ]
    await repo.create_many(session, items)

    return [str(i) for i in range(NUM_ITEMS)]


async def main():
    db.init("sqlite+aiosqlite:///parallel_example.db")
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_gen = db.get_session()
    session = await anext(session_gen)
    repo = MetricRepository(session, Metric)

    ids = await seed_data(repo, session)

    async def heavy_work(item_id: str):
        await asyncio.sleep(WORK_DELAY)
        return item_id

    # 1. Sequential Processing
    start = time.time()

    for i in ids:
        await heavy_work(i)

    seq_time = time.time() - start
    print(f"Sequential: {seq_time:.3f}s")

    # 2. Parallel Processing
    start = time.time()

    tasks = [lambda id=i: heavy_work(id) for i in ids]
    await ParallelExecutor.gather_limited(limit=50, tasks=tasks)

    par_time = time.time() - start
    print(f"Parallel:   {par_time:.3f}s")
    print(f"Speedup:    {seq_time / par_time:.1f}x")

    await db.close()


if __name__ == "__main__":
    asyncio.run(main())


# Sequential: 5.403s
# Parallel:   0.117s
# Speedup:    46.2x
