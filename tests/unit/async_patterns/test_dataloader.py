import asyncio

import pytest

from fluxcrud.async_patterns import DataLoader


@pytest.mark.asyncio
async def test_dataloader_batching():
    """Test that DataLoader batches requests."""
    batch_calls = []

    async def batch_fn(keys: list[int]) -> list[int]:
        batch_calls.append(keys)
        return [k * 2 for k in keys]

    loader = DataLoader(batch_fn)

    # Load multiple items concurrently
    results = await asyncio.gather(loader.load(1), loader.load(2), loader.load(3))

    assert results == [2, 4, 6]
    assert len(batch_calls) == 1
    assert batch_calls[0] == [1, 2, 3]


@pytest.mark.asyncio
async def test_dataloader_caching():
    """Test that DataLoader caches results."""
    call_count = 0

    async def batch_fn(keys: list[int]) -> list[int]:
        nonlocal call_count
        call_count += 1
        return [k * 2 for k in keys]

    loader = DataLoader(batch_fn)

    # First load
    await loader.load(1)
    assert call_count == 1

    # Second load (should be cached)
    await loader.load(1)
    assert call_count == 1


@pytest.mark.asyncio
async def test_dataloader_load_many():
    """Test load_many convenience method."""

    async def batch_fn(keys: list[int]) -> list[int]:
        return [k * 2 for k in keys]

    loader = DataLoader(batch_fn)
    results = await loader.load_many([1, 2, 3])
    assert results == [2, 4, 6]
