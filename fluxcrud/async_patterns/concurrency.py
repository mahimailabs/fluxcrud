import asyncio
from collections.abc import Callable
from typing import Any, Generic, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class Batcher(Generic[T, R]):
    """
    Groups individual items into batches for efficient processing.

    Useful for grouping massive Insert/Update operations or batched API calls.
    Similar to DataLoader but focused on generic processing/dispatching rather than just loading.

    Usage:
        async def process_batch(items: list[int]) -> None:
             # insert items to DB in one query
             ...

        batcher = Batcher(process_batch, batch_size=100)
        await batcher.add(1)
        await batcher.add(2)
        ...
        await batcher.flush()
    """

    def __init__(
        self,
        batch_processor: Callable[[list[T]], Any],
        batch_size: int = 100,
        flush_interval: float = 0.0,
    ):
        self.batch_processor = batch_processor
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        self._batch: list[T] = []
        self._lock = asyncio.Lock()
        self._flush_task: asyncio.Task | None = None

    async def add(self, item: T) -> None:
        """Add item to batch and flush if full."""
        async with self._lock:
            self._batch.append(item)

            if len(self._batch) >= self.batch_size:
                await self._flush_locked()
            elif self.flush_interval > 0 and not self._flush_task:
                self._flush_task = asyncio.create_task(self._auto_flush())

    async def flush(self) -> None:
        """Manually flush the current batch."""
        async with self._lock:
            await self._flush_locked()

    async def _flush_locked(self) -> None:
        if not self._batch:
            return

        batch_to_process = list(self._batch)
        self._batch.clear()

        if self._flush_task:
            self._flush_task.cancel()
            self._flush_task = None

        # Run processor (not holding lock ideally, but ensuring strict ordering?
        # For simple batching we might want to hold lock to preserve order if needed,
        # or we can release. Let's run it.
        # Ideally we want to await the processor.
        await self.batch_processor(batch_to_process)

    async def _auto_flush(self) -> None:
        await asyncio.sleep(self.flush_interval)
        await self.flush()

    async def __aenter__(self) -> "Batcher[T, R]":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.flush()


class ParallelExecutor:
    """
    Helper to run generic tasks safely in parallel with a concurrency limit.
    """

    def __init__(self, limit: int = 10):
        self.sem = asyncio.Semaphore(limit)

    async def run(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Run a function with concurrency limit."""
        async with self.sem:
            return await func(*args, **kwargs)

    @staticmethod
    async def gather_limited(limit: int, tasks: list[Callable[[], Any]]) -> list[Any]:
        """
        Execute a list of callables in parallel but with a limit on concurrent execution.
        """
        sem = asyncio.Semaphore(limit)

        async def _wrapped(task_func: Callable[[], Any]) -> Any:
            async with sem:
                return await task_func()

        return await asyncio.gather(*[_wrapped(t) for t in tasks])
