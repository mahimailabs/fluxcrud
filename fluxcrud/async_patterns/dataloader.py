import asyncio
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class DataLoader(Generic[K, V]):
    """
    Batches and caches database requests automatically.
    Inspired by Facebook's DataLoader pattern.
    """

    def __init__(
        self,
        batch_load_fn: Callable[[list[K]], Awaitable[list[V]]],
        cache: bool = True,
        max_batch_size: int = 100,
    ):
        self.batch_load_fn = batch_load_fn
        self.cache = cache
        self.max_batch_size = max_batch_size
        self._cache: dict[K, V] = {}
        self._queue: list[tuple[K, asyncio.Future[V]]] = []
        self._dispatched = False

    def clear(self, key: K) -> None:
        """Clear a key from cache."""
        if key in self._cache:
            del self._cache[key]

    def clear_all(self) -> None:
        """Clear entire cache."""
        self._cache.clear()

    async def load(self, key: K) -> V:
        """Load a single item, batched with other loads in same tick."""
        if self.cache and key in self._cache:
            return self._cache[key]

        future: asyncio.Future[V] = asyncio.Future()
        self._queue.append((key, future))

        if not self._dispatched:
            self._dispatched = True
            asyncio.create_task(self._dispatch())

        return await future

    async def load_many(self, keys: list[K]) -> list[V]:
        """Load multiple items concurrently."""
        return await asyncio.gather(*[self.load(key) for key in keys])

    async def _dispatch(self) -> None:
        """Dispatch batched load on next tick."""
        await asyncio.sleep(0)  # Wait for event loop tick

        if not self._queue:
            self._dispatched = False
            return

        # Get batch
        batch = self._queue[: self.max_batch_size]
        self._queue = self._queue[self.max_batch_size :]

        keys = [k for k, _ in batch]
        futures = [f for _, f in batch]

        try:
            # Execute batched query
            results = await self.batch_load_fn(keys)

            # Cache and resolve futures
            for key, result, future in zip(keys, results, futures, strict=True):
                if self.cache:
                    self._cache[key] = result
                future.set_result(result)

        except Exception as e:
            for future in futures:
                if not future.done():
                    future.set_exception(e)

        # Schedule next batch if queue not empty
        if self._queue:
            asyncio.create_task(self._dispatch())
        else:
            self._dispatched = False
