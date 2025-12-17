import asyncio

import pytest

from fluxcrud.async_patterns.concurrency import Batcher, ParallelExecutor


@pytest.mark.asyncio
async def test_batcher_size_flush():
    processed_batches = []

    async def processor(items: list[int]):
        processed_batches.append(items)

    batcher = Batcher[int, None](processor, batch_size=3)

    # Add 2 items (should not flush)
    await batcher.add(1)
    await batcher.add(2)
    assert len(processed_batches) == 0

    # Add 1 item (should flush)
    await batcher.add(3)
    assert len(processed_batches) == 1
    assert processed_batches[0] == [1, 2, 3]

    # Remaining
    await batcher.add(4)
    await batcher.flush()
    assert len(processed_batches) == 2
    assert processed_batches[1] == [4]


@pytest.mark.asyncio
async def test_batcher_time_flush():
    processed_batches = []

    async def processor(items: list[int]):
        processed_batches.append(items)

    batcher = Batcher[int, None](processor, batch_size=10, flush_interval=0.1)

    await batcher.add(1)
    assert len(processed_batches) == 0

    # Wait for auto flush
    await asyncio.sleep(0.2)

    assert len(processed_batches) == 1
    assert processed_batches[0] == [1]


@pytest.mark.asyncio
async def test_parallel_executor_gather_limited():
    active_count = 0
    max_concurrent = 0

    async def task():
        nonlocal active_count, max_concurrent
        active_count += 1
        max_concurrent = max(max_concurrent, active_count)
        await asyncio.sleep(0.01)
        active_count -= 1
        return "done"

    tasks = [task for _ in range(10)]

    results = await ParallelExecutor.gather_limited(2, tasks)

    assert len(results) == 10
    assert all(r == "done" for r in results)
    assert max_concurrent <= 2
