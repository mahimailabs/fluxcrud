# Batch Operations

This example benchmarks the performance difference between **Sequential Inserts** and **Batch Inserts** using FluxCRUD's `Batcher`.

## 🎯 Concepts Covered

*   **Batcher**: Collects individual items and commits them in chunks.
*   **Performance**: Demonstrates significant speedup (often 20x-50x) when writing large datasets.

## 💻 Code Highlight

The `batch_writer` context manager handles flushing automatically:

```python
async with repo.batch_writer(session, batch_size=100) as writer:
    for i in range(5000):
        # Queues item, flushes when buffer hits 100
        await writer.add({"name": f"Item {i}", ...})
```

## Try now:

```bash
$ python examples/03_batch_operations/main.py
```
*Observe the speedup factor in the console output!*
