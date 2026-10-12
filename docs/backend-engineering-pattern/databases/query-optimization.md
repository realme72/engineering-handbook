# Query Optimization

# Why Does Query Optimization Exist?

Indexing gives the database the *tools* to find data quickly. It doesn't guarantee those tools actually get used correctly for a given query — and it says nothing about queries that are structurally wasteful regardless of what indexes exist.

```sql
SELECT * FROM orders WHERE LOWER(email) = 'alice@example.com';
```

An index on `email` exists. This query still ignores it completely, because the index is sorted by the raw value of `email`, not by `LOWER(email)` — as far as the index is concerned, `LOWER(email)` is a different, uncomputed value it has never seen, on every single row.

Having the right index is necessary but not sufficient. Query optimization is the discipline of figuring out **why a specific query is slow**, and either rewriting the query, adding the right index, or restructuring the schema so the database's planner can actually take the fast path it has available.

---

# EXPLAIN — Seeing What the Database Actually Decided to Do

This is the single most important tool in this entire chapter, and the one most engineers underuse until something is already on fire in production.

```sql
EXPLAIN SELECT * FROM orders WHERE user_id = 42;
```

```
Seq Scan on orders  (cost=0.00..18000.00 rows=1 width=120)
  Filter: (user_id = 42)
```

`EXPLAIN` shows the query plan the database *intends* to run, with estimated costs — but those are estimates, based on statistics, not what actually happened.

```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 42;
```

```
Seq Scan on orders  (cost=0.00..18000.00 rows=1 width=120)
                    (actual time=45.201..312.884 rows=1 loops=1)
  Filter: (user_id = 42)
```

`EXPLAIN ANALYZE` actually **runs** the query and reports real elapsed time and real row counts alongside the plan — which is what you need when the estimated cost and the actual behavior disagree, a strong signal the planner's assumptions about the data are wrong.

```
EXPLAIN          →  "here's what I plan to do" (estimate only, safe to run on prod)
EXPLAIN ANALYZE  →  "here's what actually happened" (executes the query for real)
```

A useful habit: run `EXPLAIN` first on anything you're about to run against a large table, and reach for `EXPLAIN ANALYZE` specifically once you suspect the planner's estimate and reality have diverged.

---

# Why the Planner Sometimes Ignores a Perfectly Good Index

This surprises people the first time it happens — the index exists, `EXPLAIN` still shows a sequential scan.

## Low Selectivity

```sql
SELECT * FROM orders WHERE status = 'completed';
-- 95% of all orders are 'completed'
```

If a query would match most of the table anyway, a sequential scan is often genuinely *cheaper* than an index scan — jumping around the index and then fetching each matching row individually from scattered locations in the table can cost more than just reading the table straight through once. The planner isn't broken here; it correctly recognizes the index wouldn't actually help for this specific, unselective condition.

## Stale Statistics

```sql
ANALYZE orders;
```

The planner's cost estimates are based on statistics about the data's distribution — how many rows, how values are spread out — gathered the last time `ANALYZE` ran (or auto-triggered). If a table has grown or changed shape dramatically since those statistics were last collected, the planner can make a genuinely bad decision based on genuinely outdated information. This is a real, recurring production issue after a large bulk load or delete, not a one-time setup concern.

## Functions Wrapped Around Indexed Columns

```sql
-- Index on `email` is USELESS here
WHERE LOWER(email) = 'alice@example.com'

-- Fix: index the expression itself
CREATE INDEX idx_orders_lower_email ON orders (LOWER(email));
```

A **functional index** (or "expression index") solves this directly — instead of indexing the raw column, you index the exact expression the query actually filters on, so the planner has a structure that matches what's really being searched for.

## Implicit Type Casting

```sql
-- user_id is an INTEGER column
WHERE user_id = '42'   -- comparing against a STRING
```

Depending on the database, comparing an indexed integer column against a string literal can force an implicit cast on every row, which silently defeats the index the same way a wrapping function does — the planner can no longer just compare raw stored values directly against the sorted index structure.

---

# The N+1 Query Problem (Beyond GraphQL)

This isn't only a GraphQL issue — it's one of the most common ORM-driven performance bugs across any stack.

```python
orders = Order.objects.all()   # 1 query

for order in orders:
    print(order.user.name)     # 1 additional query PER ORDER
```

```
1 query to fetch 100 orders

+ 100 separate queries, one per order, to fetch each order's user

= 101 queries to render one page
```

```python
# Fixed — a single JOIN-based fetch instead of 100 lazy follow-up queries
orders = Order.objects.select_related("user").all()
```

The fix, across virtually every ORM (Django's `select_related`/`prefetch_related`, SQLAlchemy's `joinedload`), is the same idea: tell the ORM upfront which related data you'll need, so it fetches everything in one query (or one batched query) instead of lazily issuing a new query every time your code touches a relationship inside a loop.

---

# Common Anti-Patterns and Rewrites

## SELECT * When You Only Need Two Columns

```sql
-- wasteful: fetches every column, defeats covering indexes, more network bytes
SELECT * FROM orders WHERE user_id = 42;

-- targeted: can be satisfied by a covering index, less data transferred
SELECT id, status FROM orders WHERE user_id = 42;
```

## Large OFFSET Pagination

```sql
-- gets progressively slower as OFFSET grows — must scan and discard every skipped row
SELECT * FROM orders ORDER BY id LIMIT 20 OFFSET 500000;

-- cursor-based: jumps directly via an index lookup, regardless of depth
SELECT * FROM orders WHERE id > 500000 ORDER BY id LIMIT 20;
```

This is the exact same offset-vs-cursor trade-off covered in depth in the Pagination chapter — it's worth remembering that "pagination" and "query optimization" are really the same underlying database mechanics viewed from two different angles.

## IN vs EXISTS for Subqueries

```sql
-- can be inefficient if the subquery result set is large
SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE amount > 1000);

-- often better: the database can stop as soon as it confirms ONE match per user,
-- rather than materializing the entire subquery result set
SELECT * FROM users u WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.user_id = u.id AND o.amount > 1000
);
```

Modern query planners are increasingly good at rewriting one into the other automatically, but this isn't guaranteed across every database and every query shape — it's still worth knowing the difference exists rather than assuming the planner will always save you.

---

# Real-World Examples

### Django / SQLAlchemy N+1s

The single most common performance bug reported in real production Django and Rails applications isn't a missing index — it's a template or view that lazily accesses a related object inside a loop, generating dozens or hundreds of unplanned queries per request without anyone writing a single line of raw SQL.

---

### Postgres `pg_stat_statements`

A built-in extension that tracks every query executed against a Postgres instance, aggregated by query shape, with total and average execution time — the standard first stop in production for answering "what's actually slow across our whole system," rather than only investigating queries someone happened to notice.

---

### Netflix / large-scale query governance

Companies operating databases at extreme scale often build automated tooling that runs `EXPLAIN` against new queries in CI, or flags queries whose actual execution time diverges significantly from their estimated cost — treating query performance as something to catch before it ships, not something discovered after a page gets slow in production.

---

# Common Interview Questions

## How would you diagnose a slow query in production?

Start with `EXPLAIN ANALYZE` to see the actual plan and real execution time versus the planner's estimate. If they diverge significantly, check whether statistics are stale (`ANALYZE`). Check whether the `WHERE` clause wraps an indexed column in a function or an implicit cast, which silently defeats the index. If the query legitimately needs to scan a large portion of the table (low selectivity), the fix is often schema or query redesign, not just another index.

---

## What's the difference between EXPLAIN and EXPLAIN ANALYZE?

`EXPLAIN` shows the planner's intended execution plan and cost estimates without actually running the query — safe to use on a live, sensitive query. `EXPLAIN ANALYZE` actually executes the query and reports real elapsed time and real row counts alongside the plan, which is what you need to compare the planner's assumptions against what genuinely happened.

---

## Why would a query ignore an index that clearly exists on the filtered column?

Several possibilities: the condition has low selectivity (matches most of the table, making a sequential scan genuinely cheaper), the column is wrapped in a function or subject to an implicit type cast that the index can't match against, or the table's statistics are stale and the planner is working from an outdated picture of the data's distribution.

---

## What is the N+1 query problem, and how do you fix it in an ORM?

A query fetches a list of N records, and then a separate query is lazily issued for each record's related data — N+1 total queries where 1 or 2 would have sufficed. Fixed by explicitly telling the ORM to eagerly fetch the related data in the same or one additional batched query (`select_related`/`prefetch_related` in Django, `joinedload` in SQLAlchemy) instead of letting it lazily issue a query per related access inside a loop.

---

## Why does large-offset pagination get slower over time, and how do you fix it?

`OFFSET` still requires the database to scan and discard every skipped row before returning the next page — the cost grows with the offset itself. The fix is cursor-based pagination, which uses an indexed condition (`WHERE id > last_seen_id`) to jump directly to the right position regardless of how deep into the dataset that position is. Covered in full depth in the Pagination chapter.

---

# Common Mistakes

❌ Adding an index without checking `EXPLAIN` to confirm it's actually being used.

An index that the planner ignores for a specific query provides zero benefit while still paying the full write-side cost.

---

❌ Wrapping indexed columns in functions without a matching functional index.

`WHERE LOWER(email) = ...` silently defeats a plain index on `email` — the fix is a functional index on the exact expression used, not just an index on the raw column.

---

❌ Never re-running `ANALYZE` after a large bulk load or delete.

Stale statistics can lead the planner to make decisions based on a data distribution that no longer reflects reality.

---

❌ Letting an ORM's lazy loading silently generate N+1 queries inside a loop.

The query count explosion is invisible in the code itself — it only shows up as a slow endpoint or, worse, a spike in database load that's hard to trace back to a single innocent-looking line of application code.

---

❌ Assuming a query is fine because it "looks simple" in the code.

Nothing about how a query reads in source code tells you whether the planner is doing an index scan or a full table scan — that's a question only `EXPLAIN` can actually answer.

---

# Key Takeaways

- `EXPLAIN` shows the planner's intended plan without running the query; `EXPLAIN ANALYZE` actually executes it and reports real timing — use the former to preview, the latter to diagnose a genuine discrepancy.
- A planner ignoring an existing index usually means one of: low selectivity, a function or implicit cast wrapped around the column, or stale statistics — not a broken database.
- The N+1 query problem is the most common real-world ORM performance bug — fixed by explicitly eager-loading relationships instead of letting the ORM lazily issue one query per related access inside a loop.
- Large-offset pagination is a query optimization problem as much as a pagination one — the fix (cursor-based pagination) is the same underlying mechanism either way.
- Query optimization is never guesswork done from reading the SQL alone — it's a discipline of measuring with `EXPLAIN`/`EXPLAIN ANALYZE` first, then acting on what the database actually reports.
