# Isolation Levels

# Why Do Isolation Levels Exist?

The "I" in ACID says concurrent transactions shouldn't corrupt each other's view of the data. What it doesn't say is *exactly* how much one transaction can see of another's in-progress, uncommitted work — and that turns out to be a spectrum, not a single fixed rule.

The strictest answer — transactions behave as if they ran one at a time, in some order, with zero overlap, called **Serializable** — is also the most expensive to enforce. The database has to detect and prevent every possible way two concurrent transactions could interfere with each other.

```
Perfect isolation (Serializable)  →  maximum correctness, meaningfully slower under contention

Relaxed isolation                →  higher throughput, but specific, well-known anomalies become possible
```

Isolation levels exist because real systems need to choose a point on that spectrum deliberately, based on what anomalies they can actually tolerate for a given workload — not because databases are being sloppy by offering anything less than full serializability by default.

---

# The Anomalies

Before the levels make sense, you need to know exactly what they're protecting against.

## Dirty Read

Reading another transaction's uncommitted changes — changes that might still get rolled back.

```
T1:  UPDATE accounts SET balance = 1000 WHERE id = 1;   -- not committed yet

T2:  SELECT balance FROM accounts WHERE id = 1;         -- reads 1000

T1:  ROLLBACK;   -- balance reverts to original value

T2's read of 1000 was never real — it read data that turned out to have never happened.
```

## Non-Repeatable Read

Reading the same row twice within one transaction and getting two different values, because another transaction committed a change in between.

```
T1:  SELECT balance FROM accounts WHERE id = 1;   -- reads 500

T2:  UPDATE accounts SET balance = 300 WHERE id = 1;
T2:  COMMIT;

T1:  SELECT balance FROM accounts WHERE id = 1;   -- reads 300 — different value, same transaction
```

## Phantom Read

Re-running the same *filtering* query within one transaction and getting a different set of rows, because another transaction committed an insert or delete that changed which rows match the filter.

```
T1:  SELECT * FROM orders WHERE status = 'pending';   -- returns 5 rows

T2:  INSERT INTO orders (status) VALUES ('pending');
T2:  COMMIT;

T1:  SELECT * FROM orders WHERE status = 'pending';   -- returns 6 rows — a new "phantom" row appeared
```

The distinction from non-repeatable read matters: non-repeatable read is about an existing row's *value* changing; phantom read is about the *set of rows* matching a condition changing.

## Lost Update

Two transactions read the same value, both compute a new value based on what they read, and one transaction's write silently overwrites the other's — as if it never happened.

```
T1:  reads stock = 10
T2:  reads stock = 10

T1:  writes stock = 9    (10 - 1, one unit sold)
T2:  writes stock = 9    (10 - 1, one unit sold)

Two units were actually sold. The final stock should be 8. It's 9.
One of the two decrements was silently lost.
```

---

# The Four Standard Isolation Levels

| Level | Dirty Read | Non-Repeatable Read | Phantom Read |
|---|---|---|---|
| Read Uncommitted | Possible | Possible | Possible |
| Read Committed | Prevented | Possible | Possible |
| Repeatable Read | Prevented | Prevented | Possible* |
| Serializable | Prevented | Prevented | Prevented |

*Postgres and MySQL InnoDB's implementations of Repeatable Read actually also prevent phantom reads in practice — more on this below, because it's a genuinely common point of confusion between the SQL standard's baseline definition and specific database implementations.

## Read Uncommitted

```sql
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
```

The weakest level — transactions can see other transactions' uncommitted changes. Almost never used in practice; the risk of reading data that might be rolled back a moment later usually isn't worth whatever marginal performance gain it offers. Some databases (Postgres) don't even truly implement this level distinctly — it behaves the same as Read Committed.

## Read Committed

```sql
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

The default in PostgreSQL and Oracle. A transaction only ever sees data that's been committed by other transactions — no dirty reads — but if it reads the same row twice, and another transaction committed a change in between, it will see the new value the second time (a non-repeatable read is still possible).

## Repeatable Read

```sql
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
```

The default in MySQL's InnoDB engine. A transaction takes a consistent snapshot at its start, and every read within that transaction sees data as of that snapshot, regardless of what other transactions commit in the meantime — non-repeatable reads are prevented, because a re-read of the same row within the transaction always returns what that transaction's own snapshot saw.

## Serializable

```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

The strictest level — the database guarantees the outcome is equivalent to running every concurrent transaction one after another, in some order, with zero overlap. No anomaly from the table above is possible. The cost: significantly more contention and, in many implementations, transactions that fail with a serialization error and need to be retried by the application when a genuine conflict is detected.

---

# MVCC — How Modern Databases Implement Isolation Without Blocking Every Reader

This is the mechanism question interviewers actually want, beyond just naming the four levels.

The naive approach: every reader takes a lock, blocking writers, and every writer takes a lock, blocking readers. Correct, but terrible for concurrency — reads and writes end up fighting each other constantly, even when they're not touching the same row at the same moment.

**Multi-Version Concurrency Control (MVCC)**, used by PostgreSQL, MySQL InnoDB, and Oracle, takes a different approach: instead of locking rows for reads, the database keeps **multiple versions** of a row simultaneously, and each transaction sees the version that was current as of its own snapshot.

```
Row (id=1, balance=500) — version created at T1

T2 starts, takes a snapshot as of "now"

T3:  UPDATE ... SET balance = 300 WHERE id = 1;
T3:  COMMIT;
     → a NEW version of the row is created (balance=300),
       the OLD version (balance=500) isn't deleted yet

T2:  SELECT balance ...   → still sees 500, its own snapshot's version

T4 starts AFTER T3 committed
T4:  SELECT balance ...   → sees 300, the current version
```

```
Row versions on disk (conceptually):

Version A: balance=500, created by T1, valid until T3
Version B: balance=300, created by T3, valid from T3 onward
```

Readers never block writers, and writers never block readers, because a reader simply looks at an older version of the row instead of waiting for a writer's lock to release. Old, no-longer-visible-to-anyone versions get cleaned up later by a background process (Postgres calls this **vacuum**).

This is precisely why Postgres and MySQL can offer meaningfully strong isolation (Repeatable Read, Read Committed) without the brutal contention that a naive locking-only approach would cause — MVCC is the mechanism, isolation levels are the guarantee it's used to deliver.

---

# The Detail That Trips People Up: MySQL InnoDB's Repeatable Read Actually Prevents Phantoms

The SQL standard's baseline definition of Repeatable Read explicitly still permits phantom reads. But InnoDB's specific implementation of Repeatable Read *also* prevents most phantom reads, using **next-key locking** — a locking strategy that locks not just existing matching rows, but the *gaps* between them, specifically to prevent new rows from being inserted into a range a transaction has already queried.

This is a genuinely common interview gotcha: the standard's definition of a named isolation level and a specific database's actual behavior at that same named level are not guaranteed to be identical. Always be ready to say "the standard says X, but [database] specifically implements it as Y" rather than reciting the standard table as if every engine matches it exactly.

---

# Write Skew — The Anomaly Serializable-Sounding Levels Don't Always Catch

A more advanced trap: some databases' "Serializable" isolation is actually implemented as **Snapshot Isolation**, which prevents everything in the anomaly table above but still permits a subtler anomaly called **write skew**.

```
Constraint: at least one doctor must be on call at all times.

Doctor A and Doctor B are both currently on call.

T1 (Doctor A): reads → both A and B are on call → "safe for me to go off call" → commits
T2 (Doctor B): reads → both A and B are on call → "safe for me to go off call" → commits

Both transactions individually saw a valid state and made a locally correct decision.
Result: NEITHER doctor is on call — the constraint is violated, and no single
transaction's read+write, viewed alone, was wrong.
```

Each transaction read a consistent snapshot and wrote based on it — no dirty read, no non-repeatable read, no phantom read occurred. But the combination of both transactions' decisions violates a real business constraint neither transaction alone could see coming, because each only looked at its own snapshot in isolation. True serializability (verifying no equivalent serial ordering of transactions could have produced this outcome) catches this; snapshot isolation alone does not — this is exactly why some databases' "Serializable" mode does genuinely more work than simply "the strictest snapshot isolation."

---

# Fixing a Lost Update

## Pessimistic: Lock the Row on Read

```sql
BEGIN;
SELECT stock FROM inventory WHERE product_id = 15 FOR UPDATE;  -- locks the row
UPDATE inventory SET stock = stock - 1 WHERE product_id = 15;
COMMIT;
```

`FOR UPDATE` forces any other transaction trying to read (for update) or write that same row to wait until this transaction commits — the second transaction physically cannot proceed with a stale value, because it can't even acquire the lock until the first is done.

## Optimistic: Detect the Conflict at Write Time

```sql
UPDATE inventory
SET stock = stock - 1, version = version + 1
WHERE product_id = 15 AND version = 7;   -- the version this transaction originally read
```

```python
rows_affected = cursor.rowcount
if rows_affected == 0:
    # someone else updated this row first — our read is stale, retry
    raise ConflictError("stock was modified concurrently, retry")
```

Instead of locking anything upfront, each transaction includes the version it originally read as part of its `WHERE` clause. If another transaction already changed that row (and its version number), this update simply matches zero rows, and the application detects that and retries — cheaper than locking under low contention, but requires the application to explicitly handle the retry path. The full trade-off between these two approaches is covered in depth in the Locks chapter.

---

# Real-World Examples

### PostgreSQL

Defaults to Read Committed, offers Repeatable Read and a true Serializable mode (using Serializable Snapshot Isolation, which specifically does detect write skew, unlike plain snapshot isolation) as opt-in, all implemented via MVCC.

---

### MySQL (InnoDB)

Defaults to Repeatable Read, and its specific implementation additionally prevents most phantom reads via next-key locking — stricter in practice than the SQL standard's baseline definition of the same-named level.

---

### Oracle

Defaults to Read Committed, and notably calls its strictest available level "Serializable" while actually implementing snapshot isolation underneath — meaning it is genuinely susceptible to write skew, despite the name suggesting full serializability. Knowing this specific naming trap is a strong signal of real depth in an interview.

---

# Common Interview Questions

## What's the difference between a non-repeatable read and a phantom read?

A non-repeatable read is re-reading the *same row* and getting a different value, because another transaction updated it and committed in between. A phantom read is re-running the *same filtering query* and getting a different *set* of rows, because another transaction inserted or deleted a row matching that filter and committed in between. One is about a value changing; the other is about which rows exist changing.

---

## What is MVCC, and why do Postgres and MySQL use it?

Multi-Version Concurrency Control — instead of locking rows for every read, the database keeps multiple versions of each row, and each transaction sees the version consistent with its own snapshot. This lets readers and writers proceed without blocking each other, which is what makes strong isolation levels (Read Committed, Repeatable Read) practical at real concurrency without the contention a pure locking-based approach would cause.

---

## What's the default isolation level in Postgres vs MySQL, and why does that matter?

Postgres defaults to Read Committed; MySQL's InnoDB defaults to Repeatable Read. This matters because code written and tested against one database's default behavior around repeatable reads or phantom reads can behave subtly differently if ported to the other without adjusting the isolation level explicitly.

---

## What is write skew, and why doesn't standard Serializable-sounding isolation always prevent it?

Write skew happens when two transactions each read a consistent snapshot, each make a locally valid decision based on it, but the combination of both transactions' writes violates a constraint neither transaction alone could see. Snapshot isolation (which some databases label "Serializable," notably Oracle) prevents the four classic anomalies but not write skew — true serializability requires actually verifying no valid serial ordering of the transactions could have produced the result, which is stricter and more expensive than snapshot isolation alone.

---

## How would you fix a lost update?

Either pessimistically — lock the row at read time (`SELECT ... FOR UPDATE`) so a competing transaction can't even start its own conflicting update until the first commits — or optimistically — include a version number in the update's `WHERE` clause and have the application detect and retry when zero rows are affected, meaning someone else updated it first.

---

# Common Mistakes

❌ Assuming "Serializable" always means true serializability across every database.

Some databases (Oracle) use that name for snapshot isolation, which is still vulnerable to write skew. Always verify what a specific engine's named level actually guarantees rather than trusting the label.

---

❌ Assuming Repeatable Read behaves identically across databases.

MySQL InnoDB's Repeatable Read additionally prevents most phantom reads via next-key locking; the SQL standard's baseline definition of the same name does not require this.

---

❌ Defaulting to Serializable everywhere "to be safe."

Serializable isolation meaningfully increases contention and, in many databases, requires the application to handle serialization-failure retries. Most workloads don't need it — understanding what anomalies your specific workload can tolerate is the actual engineering decision, not reflexively choosing the strictest option.

---

❌ Using naive read-then-write logic without locking or versioning under real concurrency.

This is exactly how lost updates happen — two transactions both read the same value, both compute independently, and one write silently overwrites the other with no error or warning at all.

---

# Key Takeaways

- Isolation levels exist because perfect isolation (Serializable) is expensive, and real workloads deliberately choose a point on the correctness/performance spectrum based on which anomalies they can actually tolerate.
- The four anomalies — dirty read, non-repeatable read, phantom read, lost update — are what the four standard levels are defined against; know the anomaly before trying to memorize the level.
- MVCC is the mechanism (multiple row versions, no reader/writer blocking) that makes strong isolation levels practical without brutal lock contention — Postgres, MySQL, and Oracle all use it.
- A named isolation level's guarantee can differ meaningfully between databases — MySQL's Repeatable Read prevents more than the standard requires; Oracle's "Serializable" is actually snapshot isolation and remains vulnerable to write skew.
- Write skew is a subtler anomaly that snapshot isolation alone doesn't catch — each transaction's individual read-then-write looks locally valid, but the combination violates a constraint neither transaction could see on its own.
- Lost updates are fixed either pessimistically (lock the row upfront with `FOR UPDATE`) or optimistically (a version check at write time, with the application retrying on conflict) — the right choice depends on how much contention you actually expect.
