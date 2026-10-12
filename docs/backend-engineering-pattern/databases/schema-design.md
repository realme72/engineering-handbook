# Schema Design

# Why Does Schema Design Matter So Much?

Indexing, isolation levels, sharding — all of it assumes a schema already exists and just asks how to make it fast, safe, or scalable. Schema design is the decision that comes before any of that: what should the tables actually look like in the first place?

It's also uniquely hard to undo. A bad index gets dropped and recreated in a minute. A bad isolation level is a config change. But a bad schema — wrong keys, wrong relationships, data modeled around how it looked on day one instead of how it's actually queried a year later — tends to calcify. By the time it's obviously wrong, there's production data, application code, and reports all built on top of the assumption.

It's also one of the most common things asked directly in senior interviews — "design a schema for a ride-sharing app," "design a schema for a URL shortener" — because it shows pretty quickly whether someone thinks about data structurally or just reaches for tables without a real model underneath.

---

# Normalization

Normalization is the discipline of structuring tables so each fact is stored exactly once, avoiding the specific anomalies that come from storing the same information redundantly.

## The Unnormalized Starting Point

```
orders

| order_id | customer_name | customer_email    | product_name | product_price |
|----------|---------------|--------------------|--------------|--------------|
| 1        | Alice         | alice@example.com | Laptop       | 1200         |
| 2        | Alice         | alice@example.com | Mouse        | 25           |
```

This looks harmless until you notice the actual problems:

```
Update Anomaly:   Alice changes her email → you have to update it in
                   EVERY row where she appears, or the data disagrees
                   with itself

Insert Anomaly:   You can't add a new customer until they place an
                   order, because customer data only exists attached
                   to an order row

Delete Anomaly:   Delete Alice's only order → you've also silently
                   deleted the only record that she exists as a customer
```

## Splitting Into Normal Form

```sql
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT,
    price NUMERIC
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    product_id INT REFERENCES products(id)
);
```

Now Alice's email exists in exactly one place. Changing it means updating one row, not hunting down every order she's ever placed. That's the actual point of normalization — not a theoretical purity exercise, but eliminating the specific anomalies redundant data creates.

## The Normal Forms, Practically

```
1NF  →  every column holds a single, atomic value (no comma-separated lists in a cell)
2NF  →  every non-key column depends on the WHOLE primary key, not just part of it
3NF  →  every non-key column depends ONLY on the key, not on another non-key column
```

Almost nobody in industry formally verifies "is this table in 3NF" against the textbook definition. What matters practically: **if updating one real-world fact requires touching more than one row, something is probably under-normalized.**

---

# Denormalization — Deliberately Breaking the Rules

Normalization optimizes for update integrity. It doesn't optimize for read speed — a fully normalized schema often means more joins to answer a common question.

```sql
-- Fully normalized: every request for an order's total needs a join and a SUM
SELECT SUM(oi.price * oi.quantity)
FROM order_items oi
WHERE oi.order_id = 101;
```

```sql
-- Denormalized: the total is computed once and stored directly on the order
ALTER TABLE orders ADD COLUMN total_amount NUMERIC;
```

Now reading an order's total is a single column read, no join or aggregation needed — at the cost of that `total_amount` column being able to drift out of sync with the underlying line items if it isn't updated carefully every time they change.

```
Normalization    →  optimizes for write integrity, at some cost to read speed
Denormalization  →  optimizes for read speed, at some cost to write complexity
                     and the risk of data drifting out of sync
```

This is a deliberate trade-off, not a mistake junior schemas fall into by accident. A social app storing a denormalized `like_count` on a post — instead of running `COUNT(*)` on a likes table for every view — is the textbook case: recomputing that count on every page load at scale costs far more than occasionally reconciling a slightly-stale counter.

---

# Modeling Relationships

## One-to-Many

```sql
CREATE TABLE authors (id SERIAL PRIMARY KEY, name TEXT);
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    author_id INT REFERENCES authors(id),
    title TEXT
);
```

The foreign key lives on the "many" side — a book knows its one author; an author doesn't need a list column of book IDs.

## Many-to-Many

```sql
CREATE TABLE students (id SERIAL PRIMARY KEY, name TEXT);
CREATE TABLE courses (id SERIAL PRIMARY KEY, title TEXT);

CREATE TABLE enrollments (
    student_id INT REFERENCES students(id),
    course_id INT REFERENCES courses(id),
    enrolled_at TIMESTAMP,
    PRIMARY KEY (student_id, course_id)
);
```

Neither table can hold the other's key directly, since either side can relate to many of the other — a join table (`enrollments`) sits between them. Notice it's also a natural place to store facts *about* the relationship itself (`enrolled_at`), not just the two foreign keys.

## One-to-One

```sql
CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT);
CREATE TABLE user_profiles (
    user_id INT PRIMARY KEY REFERENCES users(id),
    bio TEXT,
    avatar_url TEXT
);
```

Usually modeled as two tables sharing the same primary key, typically split out specifically when one side of the data is much larger, much less frequently accessed, or has fundamentally different access patterns than the other (a `users` table read on every request vs. a `user_profiles` table with a large rarely-changed bio field).

---

# Choosing a Primary Key

```
Natural Key   →  a real-world value that's already unique (an email, a national ID)
Surrogate Key →  a synthetic value with no real-world meaning (an auto-increment
                  integer, a UUID), generated solely to identify the row
```

Surrogate keys are the overwhelming default in practice, because natural keys have an uncomfortable habit of turning out not to be as unique or as permanent as they seemed — emails change, national ID formats vary by country, two "unique" business identifiers turn out to collide during a merger.

## Auto-Increment Integer vs UUID

```sql
id SERIAL PRIMARY KEY          -- 1, 2, 3, 4, ...
id UUID PRIMARY KEY DEFAULT gen_random_uuid()   -- a1b2c3d4-...
```

```
Sequential Integer:
  + Small, fast to index, naturally ordered (helps range queries, clustered storage)
  - Reveals row count / growth rate to anyone who sees an ID
  - Awkward to generate independently across multiple database instances
    (two separate services can't safely generate the "next" integer without coordination)

UUID:
  + Can be generated anywhere, independently, with no coordination or central authority
    (critical for sharded systems and offline-first clients)
  + Doesn't leak business information through sequential ordering
  - Larger (16 bytes vs 4-8), which matters at scale for index size and cache efficiency
  - Random UUIDs (v4) don't sort in insertion order, which can hurt clustered-index
    locality — this is exactly why time-ordered UUID variants (UUIDv7) exist, combining
    a UUID's decentralized generation with a sequential integer's index-friendly ordering
```

Default to a sequential integer for a single-database system with no need for uncoordinated ID generation. Reach for UUIDs once IDs need to be generated client-side, across multiple services, or across shards without a shared sequence.

---

# Soft Deletes vs Hard Deletes

```sql
-- Hard delete: the row is genuinely gone
DELETE FROM orders WHERE id = 101;

-- Soft delete: the row stays, marked as deleted
UPDATE orders SET deleted_at = NOW() WHERE id = 101;
```

Soft deletes preserve history (useful for audit trails, "undo" features, and analytics that need to count things that were later removed) at a real cost: every single query in the application now has to remember to add `WHERE deleted_at IS NULL`, forever, or risk silently including "deleted" rows. Unique constraints get trickier too — if emails must be unique but a user can be soft-deleted and a new user can sign up with that same email later, a plain `UNIQUE` constraint on `email` alone will incorrectly reject the new signup.

```sql
-- A partial unique index only enforces uniqueness among non-deleted rows
CREATE UNIQUE INDEX idx_active_email ON users (email) WHERE deleted_at IS NULL;
```

---

# JSON Columns and the EAV Anti-Pattern

Modern relational databases (Postgres's `JSONB`) let you store semi-structured data directly in a column — genuinely useful for data that's legitimately variable in shape (a product's category-specific attributes, where a "laptop" and a "t-shirt" have completely different relevant fields).

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT,
    attributes JSONB   -- { "ram_gb": 16, "cpu": "M3" } or { "size": "L", "color": "blue" }
);
```

The trap is reaching for this as a default escape hatch instead of a deliberate choice — using a JSON blob (or its older, uglier ancestor, the **Entity-Attribute-Value** pattern: a generic `attribute_name`/`attribute_value` table meant to store "any field on anything") for data that actually *does* have a fixed, known shape, just because it feels more flexible upfront.

```sql
-- EAV anti-pattern — technically flexible, practically miserable to query
CREATE TABLE entity_attributes (
    entity_id INT,
    attribute_name TEXT,
    attribute_value TEXT
);
```

It looks maximally flexible and turns out to be the opposite in practice: every query that used to be a simple `WHERE` clause on a real column becomes a self-join per attribute, type safety disappears (`attribute_value` is always text, whether it's actually a number, date, or boolean), and the database can no longer enforce any constraint on the data. Use JSON/JSONB for data that's genuinely variable in shape. Use real columns for anything with a known shape, even one that changes occasionally — that's what migrations are for.

---

# Design for Query Patterns, Not Just Entities

The single most important mental shift senior engineers bring to schema design: don't just model "what entities exist" — model "how will this actually be queried, at the volume we expect."

```
Entity-first thinking:    "We have Users, Posts, and Comments" → three tables, done

Query-pattern thinking:   "We'll load a user's feed 1000x more often than we'll
                          load a single comment thread — what does THAT query
                          need to be fast?"
```

That's the same thinking behind deliberate denormalization — a cached `comment_count` on a post, since displaying it happens constantly and `COUNT(*)` on every page view doesn't scale — and behind deciding which foreign keys need an index. Any column regularly used in a `WHERE` or `JOIN` needs one; an unindexed foreign key is one of the most common accidental sources of a slow lookup, since most databases don't index foreign keys automatically just because they reference another table.

---

# Real-World Example: A Compact E-Commerce Schema

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price NUMERIC NOT NULL,
    attributes JSONB   -- category-specific variable fields
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'pending',
    total_amount NUMERIC,        -- denormalized for fast reads
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_items (
    order_id INT REFERENCES orders(id),
    product_id INT REFERENCES products(id),
    quantity INT NOT NULL,
    unit_price NUMERIC NOT NULL,  -- snapshot of price AT TIME OF ORDER, not a live join
    PRIMARY KEY (order_id, product_id)
);

CREATE INDEX idx_orders_user_id ON orders (user_id);
```

Two decisions worth calling out: `total_amount` is denormalized directly onto `orders` for fast reads, and `unit_price` is stored on `order_items` as a snapshot rather than joined live from `products`. A product's price changing next month shouldn't retroactively change what last month's receipt says the customer paid. That's a deliberate schema decision, not a bug — some data needs to be a point-in-time copy, not a live reference.

---

# Common Interview Questions

## Walk me through designing a schema for [some system] — where do you start?

Identify the core entities, then — before writing any SQL — identify the actual, dominant *access patterns*: which queries will run constantly, at high volume, versus which are rare. Model relationships (one-to-many, many-to-many) based on the real cardinality between entities. Normalize by default to avoid update anomalies, then deliberately denormalize specific fields where a known, high-volume read pattern would otherwise require an expensive join or aggregation on every request.

---

## When would you deliberately denormalize a schema?

When a specific piece of derived data (a total, a count, a computed status) is read far more often than the underlying data changes, and recomputing it live on every read would be more expensive than accepting the small risk and complexity of keeping a stored copy in sync. A `like_count` on a post is the classic example — reading it should never require aggregating an entire likes table on every single page view.

---

## Sequential integer IDs vs UUIDs — how do you decide?

Sequential integers by default — smaller, faster to index, naturally ordered for clustered storage. UUIDs specifically when IDs need to be generated independently, without central coordination — client-side generation, multiple services, or a sharded architecture where a single shared auto-increment sequence isn't available.

---

## What's wrong with the Entity-Attribute-Value pattern?

It trades away everything a real schema gives you — type safety, the ability to add real constraints, and simple `WHERE`/`JOIN` queries — in exchange for flexibility you often don't actually need, since the "attributes" being modeled usually do have a known, fixed shape. It turns simple queries into repeated self-joins and pushes all type-checking into application code instead of the database. JSON/JSONB columns solve the genuine "variable shape" use case far better when it's truly needed.

---

## How does soft-deleting affect schema design elsewhere?

Every query touching that table now needs an explicit `WHERE deleted_at IS NULL` (easy to forget, and a real source of subtle bugs when it is), and any `UNIQUE` constraint needs to become a partial index scoped to non-deleted rows, or a soft-deleted user's freed-up email can't be reused by a new signup.

---

# Common Mistakes

❌ Modeling only the entities, never the actual query patterns.

Leads to a schema that looks clean on a whiteboard and requires expensive joins or aggregations for the queries that actually run constantly in production.

---

❌ Reaching for a JSON column or EAV pattern for data that has a known, fixed shape.

Trades away type safety, constraints, and simple queries for flexibility the data doesn't actually need — reserve this for genuinely variable-shaped data.

---

❌ Forgetting to index foreign key columns.

Many databases don't automatically index a foreign key just because it references another table — an unindexed foreign key used constantly in `JOIN`s or `WHERE` clauses is a common, easy-to-miss source of a slow query.

---

❌ Adding a soft-delete column without updating unique constraints to match.

A plain `UNIQUE` constraint on an email column will block a legitimate new signup if a previous user with that same email was only soft-deleted, not actually removed.

---

❌ Treating "3NF" as a box to check rather than a tool for avoiding real anomalies.

The goal is avoiding update/insert/delete anomalies in practice, not reciting which normal form a table technically satisfies — and deliberately denormalizing for a real, known read pattern is a legitimate senior-level decision, not a violation of some rule.

---

# Key Takeaways

- Schema design decisions are the hardest in this entire section to walk back later, which is exactly why it's one of the most common things probed directly in senior interviews.
- Normalization eliminates specific update/insert/delete anomalies caused by redundant data; denormalization is a deliberate, informed trade of some of that integrity for read speed on a known, high-volume access pattern.
- Model relationships (one-to-many, many-to-many, one-to-one) based on real cardinality, and design with actual query patterns in mind, not just a list of entities.
- Default to surrogate keys (usually sequential integers) unless IDs genuinely need to be generated independently across services or shards, in which case UUIDs (or time-ordered variants like UUIDv7) are the better fit.
- Reserve JSON/JSONB columns for genuinely variable-shaped data — using them (or the EAV pattern) as a default escape hatch for data with a known, fixed shape trades away type safety and simple queries for flexibility you don't actually need.
