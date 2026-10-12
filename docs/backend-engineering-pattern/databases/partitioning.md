# Partitioning

# Why Does Partitioning Exist?

Imagine a single `orders` table that's been collecting rows for six years and now holds 500 million of them. Even with good indexes, this table is unwieldy in ways that have nothing to do with query speed alone:

```
A single 500,000,000-row table:

- An index on it is enormous, and maintaining it costs more with every insert
- Deleting old data (a retention policy: "keep 2 years of orders")
  means a slow, expensive DELETE scanning and removing rows one at a time
- Backups, vacuuming, and maintenance operations all have to deal with
  the entire table as one giant unit
```

Partitioning splits one large logical table into multiple smaller physical pieces, **on the same database instance**, based on some column's value — while the application still queries it as if it were one table.

```
orders (logical table, one name, one schema)

├── orders_2024_01   (physical partition: January 2024's rows)
├── orders_2024_02   (physical partition: February 2024's rows)
├── orders_2024_03   (physical partition: March 2024's rows)
└── ...
```

```sql
SELECT * FROM orders WHERE created_at >= '2024-02-01' AND created_at < '2024-03-01';
```

The application still just queries `orders`. Underneath, the database only has to look inside the one partition (`orders_2024_02`) that could possibly contain matching rows — the other partitions are never touched at all.

---

# Partitioning vs Sharding — The Distinction That Actually Matters

This is the single most common point of confusion in interviews, and getting it right is a strong, immediate signal of real understanding.

```
Partitioning  →  splits a table into smaller pieces WITHIN one database instance,
                  on one machine

Sharding      →  splits data across MULTIPLE independent database instances,
                  on multiple machines
```

| | Partitioning | Sharding |
|---|---|---|
| Where the pieces live | Same machine, same database instance | Different machines, independent instances |
| Solves | Manageability, query performance on huge single-machine tables | Scaling writes/storage past what one machine can handle |
| Cross-piece joins | Still trivial — it's all one database engine | Genuinely hard — spans separate engines |
| Adding more capacity | Doesn't add machines, just reorganizes existing storage | Directly adds machines and capacity |

A useful way to hold the distinction: partitioning is an internal organizational technique a single database uses to manage a table that's grown too large to treat as one physical unit efficiently. Sharding is an architectural decision to spread data across genuinely separate machines because one machine's ceiling has been reached. **You can partition without ever sharding, and you can shard tables that are also individually partitioned within each shard** — they're solving different problems and are not mutually exclusive.

---

# Partitioning Strategies

## Range Partitioning

```sql
CREATE TABLE orders (
    id BIGINT,
    created_at DATE,
    amount NUMERIC
) PARTITION BY RANGE (created_at);

CREATE TABLE orders_2024_01 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE orders_2024_02 PARTITION OF orders
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

Each partition holds a contiguous range of values — overwhelmingly the most common choice for time-series data, since most real queries on time-series data ("last week's orders," "this month's signups") naturally filter by a date range anyway.

## List Partitioning

```sql
CREATE TABLE orders (
    id BIGINT,
    region TEXT,
    amount NUMERIC
) PARTITION BY LIST (region);

CREATE TABLE orders_north_america PARTITION OF orders
    FOR VALUES IN ('US', 'CA', 'MX');

CREATE TABLE orders_europe PARTITION OF orders
    FOR VALUES IN ('UK', 'DE', 'FR');
```

Each partition holds an explicit, discrete set of values — a natural fit when data is naturally grouped into a known, bounded set of categories (regions, tenant tiers, statuses) rather than a continuous range.

## Hash Partitioning

```sql
CREATE TABLE orders (
    id BIGINT,
    user_id BIGINT
) PARTITION BY HASH (user_id);

CREATE TABLE orders_p0 PARTITION OF orders FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE orders_p1 PARTITION OF orders FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE orders_p2 PARTITION OF orders FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE orders_p3 PARTITION OF orders FOR VALUES WITH (MODULUS 4, REMAINDER 3);
```

Distributes rows evenly across a fixed number of partitions regardless of the data's natural distribution — useful specifically when there's no natural range or category to partition by, but you still want to break one enormous table into more manageable physical pieces.

---

# Partition Pruning — Where the Real Performance Win Comes From

```sql
EXPLAIN SELECT * FROM orders WHERE created_at >= '2024-02-01' AND created_at < '2024-03-01';
```

```
Append
  ->  Seq Scan on orders_2024_02
      Filter: (created_at >= '2024-02-01' AND created_at < '2024-03-01')
```

Notice what's **not** in that plan — `orders_2024_01`, `orders_2024_03`, and every other month's partition never get touched at all. The planner looks at the query's filter, recognizes it can only possibly match rows in one specific partition, and skips every other partition entirely — this is **partition pruning**, and it's the actual mechanism behind partitioning's performance benefit, not just a side effect of smaller tables.

This benefit only materializes if queries actually filter on the partition key. A query on the same table with no filter on `created_at` at all gets no pruning benefit whatsoever — the database still has to check every partition, which is exactly why picking the partition key correctly (matching real, dominant query patterns) matters here just as much as it does for choosing a shard key.

---

# The Underrated Win: Cheap Data Retention

```sql
-- Deleting old data the slow way — scans and removes matching rows one at a time,
-- generates a huge amount of transaction log activity, still leaves bloat behind
DELETE FROM orders WHERE created_at < '2022-01-01';

-- Deleting old data the partitioned way — instant, regardless of how many
-- rows the partition contains
DROP TABLE orders_2022_01;
```

For any system with a data retention policy ("keep 2 years, discard the rest" — common for logs, metrics, and time-series data generally), this difference is enormous. A `DELETE` against a huge table is a slow, resource-intensive operation that scans matching rows and leaves behind dead space that needs to be reclaimed afterward (`VACUUM` in Postgres). Dropping an entire partition is close to instantaneous, because it's a metadata operation — detaching and removing a whole physical table — not a row-by-row deletion.

This single benefit is why so much time-series and log data (application logs, IoT sensor readings, metrics) gets partitioned by time even in systems that never come close to needing sharding for scale reasons — the retention story alone justifies it.

---

# Tiered Storage: Hot vs Cold Partitions

Because each partition is its own physical table, different partitions can, in more advanced setups, be placed on different underlying storage.

```
orders_2024_06  (this month, frequently queried)   →  fast SSD storage
orders_2023_01  (over a year old, rarely queried)  →  cheaper, slower storage
```

Recent, "hot" data that's queried constantly stays on fast, expensive storage, while old, "cold" data that's rarely touched (but still needs to exist for historical/compliance reasons) moves to cheaper storage — a cost optimization that a single undivided table has no natural way to express, since it's all one physical unit with no way to split its storage tier internally.

---

# Real-World Examples

### Time-Series and IoT Data

Sensor readings, application logs, and metrics are the textbook partitioning use case — enormous volume, almost every query filters by a recent time range, and old data typically needs to be discarded on a retention schedule rather than kept forever. Range partitioning by day or month, combined with dropping expired partitions, is close to the default architecture for this kind of data.

---

### PostgreSQL Declarative Partitioning

Native, first-class partitioning support (as shown in the SQL examples above) — the application queries the parent table (`orders`) as if it were one table, and Postgres transparently routes each query to the correct partition(s) and applies pruning automatically, without the application needing to know partitions exist at all.

---

### Application Logs and Audit Trails

Systems with compliance or audit requirements often need to retain data for a specific regulated period and then are required (or simply choose) to discard it — partitioning by time makes that retention policy a cheap `DROP TABLE` per period instead of a recurring, expensive bulk deletion job.

---

# Common Interview Questions

## What's the actual difference between partitioning and sharding?

Partitioning splits one large table into smaller physical pieces within the same database instance, on one machine — it's an internal organizational technique. Sharding splits data across multiple independent database instances, on multiple machines — an architectural decision to scale past one machine's ceiling. Getting this distinction right immediately is one of the strongest, quickest signals of real understanding in an interview; the two are often confused casually but solve genuinely different problems and aren't mutually exclusive.

---

## What is partition pruning, and why does it matter?

The query planner's ability to recognize, from a query's filter condition, that only certain partitions could possibly contain matching rows, and skip every other partition entirely rather than scanning them. It's the actual mechanism behind partitioning's performance benefit — and it only kicks in if queries actually filter on the partition key; a query with no filter on that column gets no pruning benefit at all.

---

## Why would you partition a table even if you never need to shard it?

Two big reasons independent of write-scaling concerns: query performance via partition pruning on tables too large for indexing alone to keep fast, and cheap data retention — dropping an entire expired partition is close to instantaneous, versus a slow, resource-intensive `DELETE` against a huge unpartitioned table.

---

## How would you choose between range, list, and hash partitioning?

Range for naturally continuous data most often queried by range — time-series data being the dominant case. List for data that falls into a known, bounded set of discrete categories (specific regions, tenant tiers). Hash when there's no natural range or category to partition by, but you still want to break a huge table into more manageable, evenly-sized physical pieces.

---

## Can a table be both partitioned and sharded?

Yes — they operate at different levels and aren't mutually exclusive. A large system might shard data by `user_id` across multiple machines for write scalability, while each individual shard's largest tables are separately partitioned by time for query performance and retention management within that shard.

---

# Common Mistakes

❌ Confusing partitioning with sharding in an interview or in design discussions.

The single most common mix-up on this topic — mistaking an internal, single-machine organizational technique for a multi-machine scaling architecture (or vice versa) signals a real gap in understanding, not just imprecise terminology.

---

❌ Partitioning a table without queries that actually filter on the partition key.

Without a matching filter, the planner gets no pruning benefit and has to check every partition anyway — all the complexity of partitioning with none of the performance win.

---

❌ Creating far too many small partitions.

Each partition carries its own metadata and maintenance overhead — an excessively fine-grained partitioning scheme (partitioning by hour instead of by month, for a moderately-sized table) can add more overhead than it saves.

---

❌ Using slow, row-by-row `DELETE` statements for time-based data retention instead of dropping expired partitions.

Ignoring the single biggest practical win partitioning offers for exactly this kind of workload — a full retention policy implemented as recurring `DROP TABLE` statements instead of expensive scheduled bulk deletes.

---

# Key Takeaways

- Partitioning splits one large table into smaller physical pieces within a single database instance — an internal organizational technique, not a way to scale across multiple machines (that's sharding).
- Partition pruning — the planner skipping partitions that can't possibly match a query's filter — is the actual mechanism behind partitioning's performance benefit, and it only helps when queries filter on the partition key.
- Cheap data retention (dropping an entire expired partition instead of a slow bulk `DELETE`) is often partitioning's single biggest practical win, independent of any query performance concern.
- Range, list, and hash partitioning each fit a different natural data shape — time-series data for range, bounded categories for list, no natural grouping at all for hash.
- Partitioning and sharding are not mutually exclusive — a system can shard across machines for write scale while also partitioning each shard's largest tables internally for query performance and retention.
