# Parallel Execution

This example demonstrates how to process tasks concurrently using FluxCRUD's `ParallelExecutor`, which is significantly faster than sequential processing for IO-bound work.

## 🎯 Concepts Covered

*   **ParallelExecutor**: A helper to run async tasks in parallel with a concurrency limit.
*   **gather_limited**: The core method that manages the semaphore to prevent overloading resources (e.g., DB connections).

## 💻 Code Highlight

```python
# Sequential
for item in items:
    await process(item)

# Parallel (Limit concurrency to 50)
tasks = [lambda: process(item) for item in items]
await ParallelExecutor.gather_limited(limit=50, tasks=tasks)
```

## Try now:

```bash
$ python examples/04_parallel_execution/main.py
```
*Observe the massive speedup for IO-bound delays!*
