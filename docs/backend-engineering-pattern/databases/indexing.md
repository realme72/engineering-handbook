# Indexing

# Why Does Indexing Exist?

Database Fundamentals mentioned that a table isn't one giant file — it's organized into pages, and a query without help has to scan them all.

```sql
SELECT * FROM users WHERE email = 'alice@example.com';
```

```
Table: 10,000,000 rows, no index on email

↓

Database has no way to know where a matching row might be

↓

Scans every single row, checking each one against the WHERE clause

↓

10,000,000 comparisons to find 1 row
```

This is a **sequential scan** — the database equivalent of reading every page of a phone book to find one number, because nobody organized it alphabetically. It's not a bug or a missing optimization; it's the only option the database has when there's no structure telling it where to look first.

An index is that structure. It's a separate, ordered data structure that lets the database jump almost directly to the matching rows instead of checking every single one.

```
With an index on email:

↓

Look up 'alice@example.com' in the index  →  O(log n), not O(n)

↓

Index points directly to the exact page(s) containing that row

↓

~3-4 comparisons instead of 10,000,000
```

---

# What Problem It Actually Solves

- **Lookup speed** — turning an `O(n)` full scan into an `O(log n)` lookup for equality and range queries.
- **Sorting for free** — a `B-tree` index keeps entries in sorted order, so `ORDER BY` on an indexed column often doesn't need a separate, expensive sort step.
- **Enforcing uniqueness efficiently** — a unique index both indexes a column and rejects duplicate values, in one structure.
- **Making joins fast** — a join between two tables is, underneath, a repeated lookup of one table's key against the other — exactly the operation an index accelerates.

---

# The B-Tree, Conceptually

Most general-purpose database indexes (Postgres and MySQL's default) are **B-trees** — balanced, sorted tree structures.

```
                    [ M ]
                   /      \
              [ D, H ]    [ R, W ]
              /  |  \      /  |   \
           A-C  E-G  I-L  N-Q S-V  X-Z
```

Every lookup starts at the root and follows one branch at a time, narrowing the search range by roughly an order of magnitude at each level — which is why a tree holding a billion entries typically needs only around 30 comparisons to find any one of them (`log₂(1,000,000,000) ≈ 30`), not a billion.

```sql
CREATE INDEX idx_users_email ON users (email);
```

```sql
EXPLAIN SELECT * FROM users WHERE email = 'alice@example.com';

-- Before the index:
Seq Scan on users  (cost=0.00..180000.00 rows=1 width=64)

-- After the index:
Index Scan using idx_users_email on users  (cost=0.42..8.44 rows=1 width=64)
```

The `cost` numbers in `EXPLAIN` are the database's own internal estimate of how expensive the query plan is — going from `180000` to `8.44` is the concrete, measurable difference an index makes, not just a conceptual one. (Reading `EXPLAIN` output in depth is covered in Query Optimization.)

---

# Composite (Multi-Column) Indexes and the Leftmost Prefix Rule

```sql
CREATE INDEX idx_orders_user_status ON orders (user_id, status);
```

A composite index is sorted first by `user_id`, and *within* each `user_id`, sorted by `status`. This has a specific, easy-to-miss consequence: the index is only useful if your query filters on a **leftmost prefix** of the indexed columns.

```sql
-- Uses the index efficiently — filters on user_id (the leftmost column),
-- optionally narrowed further by status
WHERE user_id = 42
WHERE user_id = 42 AND status = 'pending'

-- Does NOT use this index efficiently — status alone isn't a leftmost prefix
WHERE status = 'pending'
```

```
Index sorted by (user_id, status):

user_id=1, status=active
user_id=1, status=pending
user_id=2, status=active
user_id=2, status=cancelled
...
```

Searching by `user_id` alone is trivial — jump straight to that `user_id`'s block. Searching by `status` alone means the index can't help at all, because matching `status` values are scattered across every `user_id` block, not grouped together. This is one of the most common "why isn't my index being used?" surprises in real production debugging — the index exists, it's just not shaped for the query being run.

---

# Covering Indexes (Index-Only Scans)

Normally, an index only tells the database *where* a row lives — it still has to go fetch the actual row from the table (the "heap") to read any column not in the index itself.

```sql
CREATE INDEX idx_orders_user_id ON orders (user_id);

SELECT status FROM orders WHERE user_id = 42;
-- Index finds matching rows, then still has to visit the table to read `status`
```

If the index itself already contains every column the query needs, the database can skip visiting the table entirely — an **index-only scan**.

```sql
CREATE INDEX idx_orders_covering ON orders (user_id, status);

SELECT status FROM orders WHERE user_id = 42;
-- Both user_id and status live in the index — no heap lookup needed at all
```

```
Index Scan          →  index lookup + table (heap) lookup
Index-Only Scan     →  index lookup only, data never leaves the index
```

This is a meaningful, measurable performance win on hot, narrow queries — but it comes at the cost of a larger index (more columns stored redundantly) and isn't worth engineering deliberately for every query, only the ones that matter enough to profile and tune specifically.

---

# The Cost of an Index (It's Not Free)

Every index has to be updated on every `INSERT`, `UPDATE`, or `DELETE` that touches an indexed column — an index speeds up reads by doing extra work on every write.

```
INSERT INTO users (...) VALUES (...);

↓

Insert the row itself

↓

Update EVERY index on this table to include the new row
```

A table with 8 indexes pays that update cost 8 times on every single write. This is the actual, concrete reason "just index everything" is bad advice — indexes trade write throughput and storage for read speed, and that trade is only worth making for columns that are actually queried often enough, and selectively enough, to earn it back.

## When Not to Index

```
Low-cardinality columns   →  a boolean flag, a column with 3 possible values
                              (an index barely narrows the search at all)

Small tables              →  a full scan of 500 rows is already fast;
                              an index adds write overhead for no real gain

Rarely-queried columns    →  paying write overhead for a lookup that almost never happens
```

A column like `is_active` (true/false) rarely benefits from its own index — with only two possible values, an index lookup still has to sift through roughly half the table, which isn't meaningfully better than scanning it directly.

---

# Clustered vs Non-Clustered Indexes

```
Clustered Index      →  the table's actual rows are physically stored in
                         index order (there can only be one per table)

Non-Clustered Index   →  a separate structure pointing back to the table's
                          rows, wherever they physically live
```

In MySQL's InnoDB engine, the primary key **is** the clustered index — the table's rows are physically stored sorted by primary key, which is why looking up a row by primary key in InnoDB is especially fast, and why every secondary (non-clustered) index in InnoDB actually stores the primary key value as its pointer back to the row, rather than a raw physical address. PostgreSQL, by contrast, has no true clustered index by default — all indexes, including the primary key's, are non-clustered structures pointing back to the heap (though Postgres does offer a one-time `CLUSTER` command to physically reorder a table by an index, which doesn't stay maintained automatically afterward).

---

# Other Index Types (Briefly)

```
Hash Index    →  extremely fast for exact equality (=), useless for ranges (<, >, BETWEEN)
GIN / GiST    →  Postgres indexes for full-text search, JSONB, arrays, geometric data
Full-Text     →  specialized indexing for natural-language search relevance
```

The default B-tree handles the overwhelming majority of real query patterns (equality and range queries). Reach for a specialized index type only when the data or query shape genuinely calls for it — searching inside a JSONB column, full-text relevance ranking, geospatial proximity — not as a default first choice.

---

# Real-World Examples

### PostgreSQL

B-tree by default; GIN indexes specifically for JSONB columns and full-text search, letting you index and efficiently query semi-structured data without giving up relational guarantees elsewhere in the schema.

---

### MySQL (InnoDB)

The clustered-index-on-primary-key design described above means choosing a good primary key (small, sequential, rarely updated) has an outsized impact on write performance in InnoDB specifically, more so than in databases without a true clustered index.

---

### Elasticsearch

An entire database built around the idea of an index as the primary structure (inverted indexes, specifically) rather than a bolt-on optimization — the right tool when full-text search and relevance ranking, not transactional correctness, is the primary access pattern.

---

# Common Interview Questions

## How does a B-tree index actually speed up a lookup?

It replaces a linear scan through every row with a balanced tree traversal — each step narrows the search by roughly an order of magnitude, so a table of a billion rows needs only around 30 comparisons instead of up to a billion, turning an `O(n)` scan into an `O(log n)` lookup.

---

## Why does column order matter in a composite index?

Because a composite index is sorted by its first column, then by its second column within each value of the first, and so on. A query has to filter on a **leftmost prefix** of those columns to actually benefit — filtering only on a later column in the index (skipping the first) can't use the sorted structure at all, because matching values for that later column are scattered across every value of the earlier ones.

---

## Why shouldn't you just index every column?

Because every index adds overhead to every write that touches it — an `INSERT` or `UPDATE` has to update every index on the table, not just modify the row once. Indexes are a deliberate trade of write cost and storage for read speed, worth making only for columns actually queried often and selectively enough to earn that cost back.

---

## What's the difference between a clustered and non-clustered index?

A clustered index determines the actual physical storage order of the table's rows — there can only be one per table (MySQL InnoDB uses the primary key for this). A non-clustered index is a separate structure that points back to wherever the rows actually live, and a table can have many of them.

---

## What is a covering index, and why does it matter?

An index that contains every column a specific query needs, letting the database satisfy the query directly from the index without a separate lookup into the table itself (an index-only scan). It's a targeted optimization for specific hot queries, not something to apply universally, since it means storing more data redundantly inside the index.

---

# Common Mistakes

❌ Indexing every column "just in case."

Pays write overhead on every insert/update for columns that may never actually benefit a real query — indexes should be added deliberately, based on actual query patterns, not defensively.

---

❌ Creating a composite index without understanding the leftmost prefix rule.

`(user_id, status)` doesn't help a query filtering only on `status` — a surprisingly common cause of "I have an index, why is this still slow?" confusion.

---

❌ Indexing a low-cardinality column expecting a big win.

A boolean or few-value column barely narrows the search space — the index adds write cost with minimal read benefit.

---

❌ Assuming an index exists just because you created it once.

Query patterns change over time; an index that was useful a year ago might no longer match how the table is actually queried today. Periodically checking real query plans (`EXPLAIN`) against real indexes matters more than trusting a static schema decision made once.

---

# Key Takeaways

- Without an index, a query has no way to know where matching rows might live and must scan the entire table — an index replaces that with a sorted structure (typically a B-tree) enabling near-logarithmic lookups.
- Composite indexes only help queries that filter on a leftmost prefix of their columns — column order in the index definition is a deliberate design decision, not a cosmetic one.
- A covering index lets a query be satisfied entirely from the index, skipping a separate lookup into the table — useful for specific hot queries, not a universal default.
- Every index adds write overhead on every insert/update/delete that touches it — indexing is a deliberate trade of write cost for read speed, not something to apply everywhere reflexively.
- Clustered indexes (MySQL InnoDB's primary key) determine physical row storage order; non-clustered indexes are separate structures pointing back to the rows — understanding which your database uses affects real design decisions like primary key choice.
