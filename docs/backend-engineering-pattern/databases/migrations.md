# Database Migrations

# Why Does This Deserve Its Own Chapter?

Schema Design covers what the schema should look like. This chapter covers a problem that only exists because real systems are never down long enough to redesign the schema all at once: **how do you change a live schema, under a live database, while old and new application code are both running against it at the same time?**

That last part is the detail that makes this genuinely hard, and it's not hypothetical — it's what happens on every single rolling deploy.

```
You deploy a change that adds a required "phone_number" column.

↓

Rolling deploy: 10 application servers, updated one at a time

↓

Server 1: new code, expects phone_number to exist
Server 2: new code, expects phone_number to exist
Server 3-10: OLD code, has never heard of phone_number

↓

If the migration and the deploy aren't sequenced correctly,
either the old servers crash, or the new ones do.
```

For a few minutes — sometimes longer — two different versions of your application code are running simultaneously against the *same* database, during literally every deploy that touches a table those servers use. A migration strategy that only considers "before" and "after" and ignores this messy "during" window is the single most common cause of production incidents caused by schema changes.

---

# The Core Problem: Schema Changes Aren't Atomic With Deploys

```
Database schema change:   happens at one specific moment

Application deploy:        rolls out gradually, server by server,
                            often over several minutes
```

These two events are not the same event, and they don't happen atomically together, no matter how tightly you try to coordinate them. Any migration strategy has to explicitly answer: **what happens to the old code, still running, when it hits the new schema? And what happens to the new code if it runs before the schema change has fully applied?**

---

# The Expand-Contract Pattern (Parallel Change)

This is the standard answer to the problem above — instead of one atomic "old schema → new schema" jump, break the change into multiple, individually-safe steps, each of which is backward compatible with the version of the code that was running just before it.

```
1. EXPAND    →  add the new thing (nullable column, new table) —
                 old code ignores it completely, unaffected

2. MIGRATE   →  backfill existing data into the new shape,
                 update application code to write to (or read from) both

3. CONTRACT  →  once every application instance is running the new
                 code and all data is backfilled, remove the old thing
```

At every single step, both the currently-deployed old code and the currently-deployed new code can coexist safely against the schema as it exists *at that moment* — which is the entire property this pattern is designed to guarantee.

## Concrete Example: Renaming a Column

Renaming `orders.total` to `orders.total_amount` looks like a one-line change. Done naively, it breaks immediately:

```sql
-- naive, unsafe: instantly breaks any code still referencing the old name
ALTER TABLE orders RENAME COLUMN total TO total_amount;
```

```
Old code:  SELECT total FROM orders;        → column no longer exists → CRASH
```

The expand-contract version:

```sql
-- Step 1 (Expand): add the new column alongside the old one
ALTER TABLE orders ADD COLUMN total_amount NUMERIC;

-- Step 2 (Migrate): backfill existing rows
UPDATE orders SET total_amount = total WHERE total_amount IS NULL;

-- Application code, deployed during this window, writes to BOTH columns:
--   UPDATE orders SET total = %s, total_amount = %s WHERE id = %s
-- and reads from the new column, falling back to the old if needed

-- Step 3 (Contract): once every instance is on the new code and reads/writes
-- total_amount exclusively, drop the old column
ALTER TABLE orders DROP COLUMN total;
```

Three small, individually-safe migrations instead of one that requires every application server to update in perfect, instantaneous unison — which is not a real thing that happens in a live rolling deploy.

---

# Adding a NOT NULL Column to a Huge Table Without Downtime

This is one of the most commonly asked concrete "how would you actually do this" senior-engineer questions, precisely because the naive approach locks the table.

```sql
-- naive: on many databases, this locks the ENTIRE table while it rewrites
-- every existing row to include the new column's default value
ALTER TABLE orders ADD COLUMN priority TEXT NOT NULL DEFAULT 'normal';
```

On a table with 100 million rows, that lock can hold for minutes — during which every read and write against `orders` anywhere in your application queues up and waits. The safe sequence:

```sql
-- Step 1: add the column as NULLABLE — modern Postgres (11+) treats a
-- constant-default nullable column add as a fast, metadata-only operation,
-- no table rewrite required
ALTER TABLE orders ADD COLUMN priority TEXT;

-- Step 2: backfill in small batches, not one giant UPDATE
-- (see batching example below) — avoids holding a long-running lock
-- and generating an enormous burst of transaction log activity at once

-- Step 3: add the NOT NULL constraint WITHOUT validating existing rows yet
ALTER TABLE orders ALTER COLUMN priority SET DEFAULT 'normal';
ALTER TABLE orders ADD CONSTRAINT priority_not_null
    CHECK (priority IS NOT NULL) NOT VALID;

-- Step 4: validate the constraint separately — this DOES scan the table,
-- but critically, it only takes a brief lock, not a long one, since it's
-- just checking, not rewriting
ALTER TABLE orders VALIDATE CONSTRAINT priority_not_null;
```

The key insight: splitting "add the constraint" from "verify every existing row satisfies it" into two separate steps (`NOT VALID` then `VALIDATE CONSTRAINT`) is what avoids a single long table-wide lock — each individual step is fast, even though the overall change achieves the exact same end state as the naive one-liner.

---

# Backfilling in Batches

```python
BATCH_SIZE = 1000

def backfill_priority(conn):
    last_id = 0
    while True:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE orders SET priority = 'normal'
                    WHERE id > %s AND priority IS NULL
                    ORDER BY id
                    LIMIT %s
                    RETURNING id
                    """,
                    (last_id, BATCH_SIZE),
                )
                rows = cur.fetchall()

        if not rows:
            break  # backfill complete

        last_id = rows[-1][0]
        time.sleep(0.1)  # brief pause between batches — lets other queries through
```

A single `UPDATE orders SET priority = 'normal'` across 100 million rows holds a lock and generates a massive burst of write-ahead-log activity all at once. Breaking it into small batches, each its own short transaction, lets other queries interleave between batches instead of queuing behind one enormous operation — slower in total wall-clock time, but far gentler on a live, currently-serving-traffic database.

---

# Adding an Index Without Locking Writes

```sql
-- naive: locks the table against writes for the entire duration of the build
CREATE INDEX idx_orders_priority ON orders (priority);

-- safe: builds the index without blocking concurrent writes
CREATE INDEX CONCURRENTLY idx_orders_priority ON orders (priority);
```

`CONCURRENTLY` takes noticeably longer to complete and requires a bit more care (it can fail partway through and leave behind an invalid index that needs to be dropped and retried), but it avoids taking the kind of table-wide write lock that would otherwise stall every insert and update against a live, high-traffic table for however long the index build takes.

---

# Migration Tooling

Hand-writing raw SQL migration scripts and tracking which ones have run manually doesn't scale past a team of one. Real systems use version-controlled migration tools:

```python
# Alembic (Python) — auto-generates a migration script from model changes
def upgrade():
    op.add_column('orders', sa.Column('priority', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('orders', 'priority')
```

```
Flyway / Django Migrations / Alembic / Rails Migrations

- Each migration is a versioned, ordered, checked-into-source-control file
- A migrations table in the database tracks which have already run
- CI/CD can run migrations automatically as part of a deploy pipeline,
  in a known, repeatable order
```

The `downgrade()` function matters more than it looks like it should — a migration that can't be reversed turns any bad deploy into a much harder recovery than "roll back to the previous version," which is exactly the safety net a reversible migration is meant to preserve.

---

# Real-World Examples

### GitHub / Large-Scale Rails Shops

The Rails community's `strong_migrations` gem is a direct, tooling-level codification of this entire chapter — it statically analyzes migrations before they run and flags exactly the dangerous patterns discussed here (adding a column with a non-constant default that forces a table rewrite, adding a `NOT NULL` constraint without a safe two-step validate, an index creation missing `CONCURRENTLY`) automatically, before they ever reach production.

---

### Stripe

Runs schema changes against enormous, constantly-written tables serving live payment traffic — exactly the environment where a naive `ALTER TABLE` locking the table for even a few seconds is unacceptable, which is why expand-contract-style migrations, careful backfilling, and non-blocking index builds aren't optional best practices there, they're baseline operational requirements.

---

### PostgreSQL 11+ Fast Column Addition

A concrete engine-level improvement directly relevant to this chapter — adding a nullable column with a constant default became a fast, metadata-only operation (no full table rewrite) starting in Postgres 11, specifically because this exact "adding a column to a huge live table" pain point was common enough across the ecosystem to justify a database engine change.

---

# Common Interview Questions

## How would you add a NOT NULL column to a table with hundreds of millions of rows, with zero downtime?

Add the column as nullable first (fast, metadata-only in modern Postgres), backfill existing rows in small batches rather than one giant update, then add the constraint as `NOT VALID` and validate it in a separate step — splitting the constraint's addition from checking every existing row against it avoids one single long table-wide lock.

---

## Why can't you just rename a column directly in production?

Because application code is deployed gradually, not atomically — during a rolling deploy, some servers are still running old code that references the old column name. Renaming it outright breaks those servers instantly. The expand-contract pattern handles this by adding the new column, dual-writing to both during a transition window, and only dropping the old column once every server is confirmed running the new code.

---

## What is the expand-contract (parallel change) pattern?

A strategy for making schema changes backward compatible with whatever code is currently deployed at every intermediate step: expand (add the new structure without touching the old), migrate (backfill data and have the application write to/read from both), then contract (remove the old structure only once nothing depends on it anymore). It exists specifically because a schema change and an application deploy are two separate events that don't happen atomically together.

---

## Why does creating an index sometimes lock a table, and how do you avoid it?

A standard `CREATE INDEX` takes a lock that blocks concurrent writes to the table for the entire duration of the index build. `CREATE INDEX CONCURRENTLY` (Postgres) builds the index without blocking writes, at the cost of taking longer and requiring a bit more care around potential partial failure.

---

## Why should migrations be reversible?

Because a bad deploy needs a fast, reliable rollback path — if the corresponding migration can't be cleanly reversed, rolling back the application code alone might leave the schema in a state the old code doesn't actually work with either, turning a routine rollback into a much harder, more manual recovery.

---

# Common Mistakes

❌ Adding a `NOT NULL` column directly, without a nullable-then-backfill-then-validate sequence.

Locks the entire table for however long it takes to rewrite every existing row with the default value — on a large table, this can mean minutes of blocked reads and writes.

---

❌ Backfilling a huge table with one giant `UPDATE` statement.

Holds a long-running lock and generates a massive burst of write-ahead-log activity all at once — batching the backfill avoids both problems at the cost of a longer total wall-clock time.

---

❌ Renaming or dropping a column that's still being read or written by currently-running application code.

Breaks any server still running the previous deploy the instant it touches that column — this is the exact failure mode the expand-contract pattern exists to prevent.

---

❌ Creating an index without `CONCURRENTLY` on a live, high-traffic table.

Blocks every write against that table for the entire duration of the index build, which can be a serious, user-visible outage on a large table.

---

❌ Writing a migration with no working rollback path.

Turns a bad deploy into a much harder recovery problem than "roll back to the previous version" — reversibility is a deliberate design property of a migration, not something to add only if convenient.

---

# Key Takeaways

- A schema migration and an application deploy are two separate events that never happen atomically together — any real migration strategy has to account for old and new application code running simultaneously against the database during the transition.
- The expand-contract pattern (add the new structure, migrate/backfill and dual-write, then remove the old structure) is the standard way to make every intermediate step backward compatible with whatever code happens to be deployed at that moment.
- Adding a `NOT NULL` column to a huge table safely means adding it nullable first, backfilling in small batches, and validating the constraint as a separate step — never one direct `ALTER TABLE ... NOT NULL` on a large live table.
- `CREATE INDEX CONCURRENTLY` avoids blocking writes during index creation, at the cost of a longer build time and a bit more operational care.
- Migrations should be version-controlled, tracked, and reversible — a migration with no rollback path turns an ordinary bad deploy into a much harder production incident.
