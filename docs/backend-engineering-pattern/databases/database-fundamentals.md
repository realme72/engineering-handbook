# Database Fundamentals

# Why Do Databases Exist?

Every application eventually hits the same wall: it needs to remember something after the process restarts.

```
In-memory dict  →  fast, simple  →  server restarts  →  everything is gone
Flat file       →  survives restarts  →  no concurrent writers, no queries, no integrity
```

A database solves one unglamorous problem: **store data durably, let many processes read and write it at once without corrupting it, and let you ask questions about it you never planned for when you wrote the data down.**

That last part is the one people underestimate. You don't just need to store an order — later you need to ask "which orders shipped last week for customers in Mumbai with a total over ₹5,000?" without ever having designed a file format around that question. That's the actual difference between a database and a filesystem.

---

# What Problem It Actually Solves

- **Durability** — data survives a crash, a restart, a power cut.
- **Concurrency** — hundreds of application servers can read and write the same data at once without corrupting it.
- **Structure and integrity** — a schema (or at least a shape) that the system can enforce, so "every order has a customer" isn't just a convention your application code has to remember to honor everywhere.
- **Arbitrary querying** — the ability to ask new questions of existing data without redesigning the storage format.
- **Efficient access at scale** — finding one row out of a billion in milliseconds, via indexing, instead of scanning the entire dataset every time.

---

# Relational vs Non-Relational

## Relational (SQL)

Data lives in tables with a fixed schema, related to each other through keys.

```
users                    orders
┌────┬────────┐          ┌────┬─────────┬────────┐
│ id │ name   │          │ id │ user_id │ amount │
├────┼────────┤          ├────┼─────────┼────────┤
│ 1  │ Alice  │  ◄────── │ 101│ 1       │ 500    │
└────┴────────┘          └────┴─────────┴────────┘
```

```sql
SELECT orders.amount, users.name
FROM orders
JOIN users ON orders.user_id = users.id
WHERE users.name = 'Alice';
```

The relationships between entities are first-class — `JOIN` lets you combine data across tables at query time, and the schema itself enforces that `orders.user_id` must reference a real user (a foreign key constraint), so "an order pointing at a customer that doesn't exist" is something the database refuses to let happen, not just something your application is supposed to remember to check.

Examples: PostgreSQL, MySQL, SQL Server, Oracle.

## Non-Relational (NoSQL)

A blanket term for anything that isn't the classic relational-table model, covering a few genuinely different shapes:

```
Document Store (MongoDB)
{
    "user": "Alice",
    "orders": [
        { "id": 101, "amount": 500 },
        { "id": 102, "amount": 300 }
    ]
}

Key-Value Store (Redis)
"session:abc123"  →  "{ user_id: 42, expires: ... }"

Wide-Column Store (Cassandra)
Row key: user_42
    column: name = Alice
    column: last_login = 2026-07-21

Graph Database (Neo4j)
(Alice) -[:FOLLOWS]-> (Bob) -[:FOLLOWS]-> (Carol)
```

Each shape trades away something the relational model gives you for free, in exchange for something else:

- **Document stores** trade strict schema and cross-document joins for flexible, nested, denormalized documents that map naturally onto how an application actually uses the data.
- **Key-value stores** trade any querying beyond "get by key" for extreme simplicity and raw speed.
- **Wide-column stores** trade joins and ad-hoc queries for horizontal write scalability across huge datasets.
- **Graph databases** trade general-purpose querying for extremely fast traversal of deeply connected relationships (who's connected to whom, how) that would require many expensive joins in a relational model.

## The Real Decision Isn't "SQL vs NoSQL"

That framing is already out of date. The real question is: **what does my access pattern look like, and what am I willing to give up for it?**

- Need strong consistency, complex relationships, and ad-hoc queries you can't fully predict in advance? Relational.
- Need to store deeply nested, self-contained objects with variable shape, read mostly by ID? Document store.
- Need blazing-fast lookups by a single key, with no relationships to speak of? Key-value store.
- Need to traverse a graph-shaped relationship — social networks, recommendation engines, fraud rings? Graph database.

A surprising number of production incidents trace back to picking a NoSQL store for "scale" reasons before hitting an actual scale problem, then discovering the application badly needed the joins, transactions, or ad-hoc querying that choice gave up.

---

# What Actually Happens When You Run a Query

```sql
SELECT * FROM orders WHERE user_id = 42;
```

```
Your Query

↓

Parser           →  checks SQL syntax is valid

↓

Query Planner /
Optimizer        →  decides HOW to execute it
                     (use an index on user_id? scan the whole table?)

↓

Execution Engine →  actually runs the chosen plan

↓

Storage Engine   →  reads the relevant pages/blocks from disk (or cache)

↓

Result Set       →  rows returned to your application
```

The planner step is the one most engineers never think about until something is slow. The same query can run in wildly different ways depending on what indexes exist, how much data there is, and what statistics the database has gathered about the table. That's why `EXPLAIN` (covered in depth in Query Optimization) exists — it shows you the plan the database actually chose, not the one you assumed it would.

---

# Storage: Why Data on Disk Isn't Just "A File"

Databases don't store your table as one giant flat file scanned start to finish. They organize data into fixed-size **pages** (typically 4KB–16KB), and build **indexes** — typically B-tree structures — on top of those pages specifically so a lookup can jump almost directly to the right page instead of scanning every page in the table.

```
Table on disk:  [ Page 1 ][ Page 2 ][ Page 3 ] ... [ Page 100,000 ]

Without an index:  scan pages 1 → 100,000 looking for a match

With an index:      jump almost directly to the 3 pages that could match
```

This is why a missing index on a large table can turn a millisecond query into a multi-second one — the deep mechanics live in the Indexing chapter, but the idea to hold onto here is simple: "querying" is never magic. It's always some concrete strategy for finding the right pages on disk (or in a buffer cache in memory) as cheaply as possible.

---

# Real-World Examples

### PostgreSQL

The default choice for most new relational workloads: strong ACID guarantees, an excellent query planner, native JSON columns for when you need document-store flexibility, and full-text search built in. A lot of "Postgres or a specialized NoSQL store" debates just end with "use Postgres," because one well-run instance handles far more than its reputation as "just a relational database" suggests.

---

### MongoDB

The default reach for a document store. Works best where data is naturally hierarchical and self-contained — a product catalog entry with nested variants and images — and gets queried mostly by its own ID or a handful of indexed fields, with no need for complex joins across entities.

---

### Redis

An in-memory key-value store almost never used as a system's primary source of truth, but everywhere as a cache, a session store, a rate limiter's counter, and a queue. Reads and writes in memory are orders of magnitude faster than anything that has to hit disk.

---

### Cassandra

Built for massive write throughput spread across many nodes with no single point of failure. The trade-off is a far more restrictive query model — you generally design tables around the exact queries you intend to run, rather than querying flexibly after the fact — a direct consequence of its wide-column, horizontally-partitioned design.

---

# Common Interview Questions

## When would you choose a relational database over a NoSQL one?

When the data has real relationships that need to stay consistent (foreign keys, referential integrity), when you need transactions across multiple entities (an order and its inventory decrement together), or when you can't fully predict your query patterns upfront and need genuine ad-hoc querying flexibility.

---

## When would you choose a document store over relational?

When your data is naturally hierarchical and mostly self-contained — read and written as one cohesive unit (a user profile with nested settings, a product with nested variants) — and you rarely need to join across separate top-level entities to answer a typical query.

---

## What actually happens between running a query and getting results back?

The query gets parsed for syntax, the planner picks an execution strategy (which indexes to use, if any), the execution engine runs that plan, and the storage engine pulls the data pages from disk or a memory cache. The planner's choice is why the same query can be fast or slow depending on what indexes and statistics exist — nothing about SQL execution is "just run the query as written."

---

## Why not just use NoSQL everywhere for "scale"?

Because scale isn't the only variable. Many NoSQL systems trade away strong consistency, joins, or multi-entity transactions to get it, and plenty of applications never hit a scale threshold where relational databases — which scale quite far themselves, see Replication and Sharding — become the bottleneck. Choosing NoSQL preemptively often means giving up real guarantees for a scale problem you don't have yet.

---

# Common Mistakes

❌ Picking a database technology based on trend rather than access pattern.

"NoSQL is web-scale" isn't a reason — the actual reason should be your data's shape and how you query it.

---

❌ Treating a document store like a relational database with manual joins in application code.

If you're constantly stitching together documents from multiple collections in your application layer, that's usually a sign the data was relational all along.

---

❌ Ignoring schema design early because "NoSQL is schemaless."

Schemaless storage doesn't mean the data has no shape — it just means the database won't enforce that shape for you. The discipline still has to exist somewhere, usually in your application code, which is a worse place for it to live.

---

❌ Assuming a query is fast because it "looks simple."

`SELECT * FROM orders WHERE user_id = 42` is either instant or a full table scan depending entirely on whether an index exists on `user_id` — nothing about the SQL syntax tells you which.

---

# Key Takeaways

- A database's real job is durability, safe concurrent access, enforced structure, and flexible querying — a filesystem gives you none of the last three.
- Relational databases enforce relationships and integrity as first-class guarantees; NoSQL variants each trade some of that away for a specific different strength (flexibility, raw speed, write scale, or graph traversal).
- The real database choice is about your access pattern, not a "SQL vs NoSQL" ideology — and defaulting to NoSQL for scale you don't have yet is one of the most common early-stage architecture mistakes.
- Every query passes through a parser, planner, execution engine, and storage engine — the planner's choice of execution strategy is why identical-looking queries can have wildly different performance.
- Data on disk is organized into pages, with indexes (typically B-trees) built to avoid scanning every page — this physical reality underlies every later discussion of indexing and query performance.
