import asyncio
import time
from uuid import uuid4

from examples.helper import (
    Base,
    Metric,
    MetricRepository,
)
from fluxcrud.database import db


async def main():
    db.init("sqlite+aiosqlite:///batch_example.db")
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_gen = db.get_session()
    session = await anext(session_gen)
    repo = MetricRepository(session, Metric)

    NUM_ITEMS = 500

    # 1. Sequential Insert
    start = time.time()
    for i in range(NUM_ITEMS):
        await repo.create(session, {"id": str(uuid4()), "name": f"seq_{i}", "value": i})

    seq_time = time.time() - start
    print(f"Sequential: {seq_time:.3f}s")

    # 2. Batched Insert
    start = time.time()
    async with repo.batch_writer(session, batch_size=100) as writer:
        for i in range(NUM_ITEMS):
            await writer.add({"id": str(uuid4()), "name": f"batch_{i}", "value": i})
    batch_time = time.time() - start
    print(f"Batched: {batch_time:.3f}s")

    await db.close()
    print(f"Speedup: {seq_time / batch_time:.1f}x faster")


if __name__ == "__main__":
    asyncio.run(main())

# Sequential: 0.359s
# Batched: 0.012s
# Speedup: 30.8x faster
