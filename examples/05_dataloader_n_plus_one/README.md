# N+1 Problem & DataLoader

This example demonstrates the **N+1 Query Problem** and how FluxCRUD's `DataLoader` pattern solves it efficiently.

## 🛑 The N+1 Problem

When fetching a list of items (e.g., 50 Posts) and then fetching a related item for each (e.g., the Author), a naive implementation executes **51 database queries**:

1.  One query to get 50 Posts.
2.  **50 separate queries** to get the Author for each Post.

```python
# Naive Approach
posts = await post_repo.get_multi(session, limit=50) # Query 1
for post in posts:
    # Query 2...51 (Performance Killer!)
    author = await user_repo.get(session, post.user_id)
```

## ✅ The FluxCRUD Solution

FluxCRUD integrates the **DataLoader** pattern directly into the `Repository`. It batches multiple individual requests into a **single query**.

The `Repository` exposes `get_many_by_ids` (and internally `get`), which utilizes this batching mechanism.

```python
# Optimized Approach
posts = await post_repo.get_multi(session, limit=50) # Query 1

# Collect IDs
user_ids = [p.user_id for p in posts]

# Query 2 (Batched!)
# FluxCRUD fetches all 50 authors in ONE SELECT statement
authors = await user_repo.get_many_by_ids(user_ids)
```

**Result:** 51 Queries ➡️ **2 Queries**.

## Try now:

```bash
$ python examples/05_dataloader_n_plus_one/main.py
```
