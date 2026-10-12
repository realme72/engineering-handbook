# Locks

# Why Do Locks Exist?

Isolation levels describe *what* a transaction is allowed to see of other transactions' work. Locks are one of the actual mechanisms databases use to *enforce* that — by making a transaction wait its turn before it's allowed to touch a piece of data another transaction is currently using.

```
T1:  reads stock = 10, plans to write 9

T2 (concurrently):  reads stock = 10, plans to write 9

Both transactions computed their new value from the SAME starting point.
Whichever writes second silently overwrites the first — one sale is lost.
```

Without any coordination mechanism, two transactions that both read-then-write the same data can produce exactly this kind of silent corruption — the lost update anomaly from the Isolation Levels chapter. A lock is the most direct fix: force the second transaction to wait until the first one has finished, instead of letting them both charge ahead based on the same stale read.

---

# What Problem It Actually Solves

- **Preventing lost updates** — the read-modify-write race above.
- **Preventing concurrent modification of the same row** in ways that would leave it in a state neither transaction intended.
- **Giving isolation levels their actual teeth** — an isolation level is a promise; locks (alongside MVCC, from the Isolation Levels chapter) are part of how the database keeps that promise.

---

# Shared Locks vs Exclusive Locks

```
Shared Lock (Read Lock)      →  many transactions can hold it simultaneously
                                 (many readers, no writer)

Exclusive Lock (Write Lock)  →  only ONE transaction can hold it
                                 (blocks every other reader and writer)
```

```sql
SELECT * FROM inventory WHERE product_id = 15 FOR SHARE;    -- shared lock
SELECT * FROM inventory WHERE product_id = 15 FOR UPDATE;   -- exclusive lock
```

`FOR SHARE` says "I'm reading this and I want to make sure nobody changes it while I'm still using it, but other readers are fine." `FOR UPDATE` says "I intend to modify this — nobody else, reader or writer, gets to touch it until I'm done." The compatibility rule is simple: any number of shared locks can coexist on the same row, but an exclusive lock excludes everyone else, readers included.

---

# Pessimistic Locking

Assume conflicts are likely, and prevent them upfront by locking before doing any work.

```sql
BEGIN;

SELECT stock FROM inventory WHERE product_id = 15 FOR UPDATE;  -- lock acquired here

-- any other transaction trying to read (FOR UPDATE) or write this row now BLOCKS

UPDATE inventory SET stock = stock - 1 WHERE product_id = 15;

COMMIT;   -- lock released
```

```python
def purchase_item(conn, product_id: int):
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT stock FROM inventory WHERE product_id = %s FOR UPDATE",
                (product_id,),
            )
            stock = cur.fetchone()[0]

            if stock <= 0:
                raise OutOfStockError()

            cur.execute(
                "UPDATE inventory SET stock = stock - 1 WHERE product_id = %s",
                (product_id,),
            )
    # lock released automatically when the transaction commits
```

A second, concurrent call to `purchase_item` for the same `product_id` simply blocks at the `SELECT ... FOR UPDATE` line until the first transaction commits — it physically cannot proceed with a stale read, because it can't even acquire the lock yet. This guarantees correctness by construction, at the cost of making every competing transaction wait in line.

**Best suited for:** high-contention resources where conflicts are frequent and expected — genuinely limited inventory, seat reservations, anything where "many people are racing for the same few units right now" is the normal case, not the exception.

---

# Optimistic Locking

Assume conflicts are rare, do the work without locking anything upfront, and only check for a conflict at the moment you try to write.

```sql
-- read (no lock)
SELECT stock, version FROM inventory WHERE product_id = 15;
-- → stock = 10, version = 7

-- ... application does some work, maybe validates the order, computes pricing ...

-- write, conditioned on nothing having changed since the read
UPDATE inventory
SET stock = stock - 1, version = version + 1
WHERE product_id = 15 AND version = 7;
```

```python
def purchase_item_optimistic(conn, product_id: int, max_retries: int = 3):
    for attempt in range(max_retries):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT stock, version FROM inventory WHERE product_id = %s",
                (product_id,),
            )
            stock, version = cur.fetchone()

            if stock <= 0:
                raise OutOfStockError()

            cur.execute(
                """UPDATE inventory SET stock = stock - 1, version = version + 1
                   WHERE product_id = %s AND version = %s""",
                (product_id, version),
            )
            conn.commit()

            if cur.rowcount == 1:
                return  # success — no one else modified this row in between
            # rowcount == 0 means someone else's write already bumped the version — retry

    raise ConflictError("too many concurrent conflicts, give up")
```

If another transaction already updated `product_id = 15` (and its `version`) between this transaction's read and write, the `UPDATE`'s `WHERE version = 7` simply matches nothing — `rowcount` is 0, and the application knows its read was stale and retries with a fresh read.

**Best suited for:** low-contention resources where conflicts are rare — most application data most of the time — because you avoid paying the cost of locking on every single operation, and only pay a (cheap) retry cost on the rare occasion a genuine conflict occurs.

---

# Pessimistic vs Optimistic — Head to Head

| | Pessimistic | Optimistic |
|---|---|---|
| Mechanism | Lock upfront, block competitors | No lock; detect conflict at write time |
| Best under | High contention | Low contention |
| Cost when no conflict | Pays lock overhead regardless | Nearly free — just a version check |
| Cost when conflict occurs | Competitor simply waits | Application must retry |
| Failure mode if misused | Long lock waits, deadlocks | Retry storms under high contention |

A practical rule of thumb: default to optimistic locking for most application data, and reach for pessimistic locking specifically when you know a resource is a genuine hotspot — a small number of rows that many concurrent transactions are realistically racing for at the same time (concert ticket inventory, a limited flash-sale item).

---

# Lock Granularity

```
Table-Level Lock   →  locks the ENTIRE table
                       simple, but blocks every unrelated row's readers/writers too

Row-Level Lock     →  locks only the specific row(s) actually touched
                       lets unrelated rows proceed completely unaffected
```

```sql
LOCK TABLE inventory IN EXCLUSIVE MODE;   -- table-level: blocks everything, everywhere in this table

SELECT * FROM inventory WHERE product_id = 15 FOR UPDATE;  -- row-level: only this one row
```

Modern relational databases (Postgres, MySQL InnoDB) default to row-level locking specifically because it allows far more real concurrency — two transactions updating two different, unrelated rows in the same table shouldn't have to wait on each other at all. Table-level locks still exist and get used deliberately for specific operations (certain schema changes, some bulk operations) where locking the whole table is actually the correct, intended behavior, not an accident of coarse-grained tooling.

---

# Deadlocks

A deadlock happens when two transactions each hold a lock the other one needs, and neither can proceed.

```
T1:  locks row A
T2:  locks row B

T1:  tries to lock row B  →  BLOCKS (T2 holds it)
T2:  tries to lock row A  →  BLOCKS (T1 holds it)

Neither transaction can ever proceed. Forever, unless something intervenes.
```

```sql
-- Transaction 1                          -- Transaction 2
BEGIN;                                    BEGIN;
UPDATE accounts SET balance = balance - 100
  WHERE id = 1;                           UPDATE accounts SET balance = balance - 50
                                             WHERE id = 2;
UPDATE accounts SET balance = balance + 100   UPDATE accounts SET balance = balance + 50
  WHERE id = 2;   -- waits on T2's lock       WHERE id = 1;   -- waits on T1's lock

                    ↑ DEADLOCK ↑
```

Databases detect this automatically (typically via a wait-for graph — tracking who's waiting on whom, and spotting a cycle) and resolve it by forcibly rolling back one of the two transactions — usually whichever has done the least work — with an error the application is expected to catch and retry.

```python
try:
    execute_transfer(conn, from_id=1, to_id=2, amount=100)
except DeadlockDetected:
    # the database already rolled this transaction back completely — safe to retry
    execute_transfer(conn, from_id=1, to_id=2, amount=100)
```

## Preventing Deadlocks: Consistent Lock Ordering

The actual fix isn't retry logic — it's removing the *possibility* of the cycle in the first place, by always acquiring locks in the same order across every code path.

```python
def transfer(conn, from_id: int, to_id: int, amount: int):
    first_id, second_id = sorted([from_id, to_id])  # always lock the lower ID first

    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM accounts WHERE id = %s FOR UPDATE", (first_id,))
            cur.execute("SELECT * FROM accounts WHERE id = %s FOR UPDATE", (second_id,))

            cur.execute(
                "UPDATE accounts SET balance = balance - %s WHERE id = %s",
                (amount, from_id),
            )
            cur.execute(
                "UPDATE accounts SET balance = balance + %s WHERE id = %s",
                (amount, to_id),
            )
```

If every transaction that touches accounts 1 and 2 always locks account 1 before account 2 — regardless of which one is the "from" or "to" account in that particular call — the cyclic-wait scenario above can never occur, because there's no code path where a transaction holds the higher ID and waits on the lower one. This is the standard, deliberate fix for deadlocks that recur in a predictable pattern, rather than relying on the database's detection-and-retry safety net as the primary defense.

---

# Real-World Examples

### Ticket Booking Systems

The textbook pessimistic-locking use case — when a concert has 500 seats and 10,000 people are trying to book in the same 30 seconds, letting everyone read-then-write optimistically produces a storm of conflicting retries. Locking the seat row at read time (`FOR UPDATE`) so competing bookings genuinely queue up is usually the more predictable choice under that specific kind of extreme, momentary contention.

---

### E-Commerce Inventory

Most inventory systems default to optimistic locking (a `version` or `stock` check at write time) because most products, most of the time, aren't under heavy simultaneous contention — reserving a pessimistic lock on every single add-to-cart action would needlessly serialize traffic that was never actually going to conflict.

---

### Banking Transfers

The deadlock example above is not hypothetical — any system that locks multiple accounts as part of one transaction (transfers, batch settlements) needs a consistent lock-ordering discipline, or deadlocks under real concurrent load become a routine occurrence rather than a rare incident.

---

# Common Interview Questions

## Pessimistic vs optimistic locking — how do you decide which to use?

Pessimistic when contention is high and conflicts are expected and frequent (limited inventory, seat bookings) — locking upfront avoids wasted work from repeated failed attempts. Optimistic when contention is low and conflicts are rare — most application data most of the time — since it avoids the overhead of locking on every operation and only pays a retry cost on the occasional actual conflict.

---

## What causes a deadlock, and how does the database resolve one?

Two transactions each hold a lock the other needs, and neither can proceed — a genuine cycle in who's waiting on whom. Databases detect this via a wait-for graph and resolve it by forcibly rolling back one of the transactions (typically the one that's done the least work), returning an error the application must catch and retry.

---

## How do you actually prevent deadlocks, rather than just recovering from them?

Enforce a consistent lock-acquisition order across every code path that touches the same set of resources — e.g. always lock the lower ID first in a transfer between two accounts, regardless of which account is conceptually the source or destination in that specific call. If a cyclic wait can never form, a deadlock can never occur.

---

## What's the difference between a shared lock and an exclusive lock?

A shared lock allows multiple concurrent holders — many readers can hold it at once, none of them blocking each other, but it blocks any writer from acquiring an exclusive lock. An exclusive lock allows only one holder at a time and blocks everyone else, readers included, until it's released.

---

## What's the difference between row-level and table-level locking?

Row-level locking only blocks access to the specific row(s) actually touched, letting unrelated rows in the same table proceed with zero contention. Table-level locking blocks the entire table regardless of which specific rows are involved — much coarser, and used deliberately only for operations where locking the whole table really is the intended behavior.

---

# Common Mistakes

❌ Holding a lock across a slow external operation (an API call, an email send) inside the same transaction.

Every other transaction waiting on that lock is now blocked for however long that external call takes — turning a slow third-party dependency into a database-wide contention problem.

---

❌ Defaulting to pessimistic locking everywhere "to be safe."

Needlessly serializes traffic on resources that were never actually contended, hurting throughput for no real correctness benefit on the vast majority of low-contention data.

---

❌ Relying solely on deadlock detection and retry instead of fixing lock ordering.

Retry-on-deadlock is a safety net, not a design — if the same deadlock pattern recurs constantly under real load, the actual fix is enforcing consistent lock ordering so the cyclic wait can't form in the first place.

---

❌ Forgetting to handle the zero-rows-affected case in optimistic locking.

If the application doesn't check `rowcount` after an optimistic update and doesn't retry on a mismatch, a genuine conflict silently does nothing instead of either succeeding or raising a clear error — a subtle, hard-to-notice correctness bug.

---

# Key Takeaways

- Locks are one of the actual mechanisms (alongside MVCC) that give an isolation level its teeth — they prevent lost updates and other corruption from concurrent read-modify-write races.
- Shared locks allow many simultaneous readers; exclusive locks allow exactly one holder and block everyone else, readers included.
- Pessimistic locking (`FOR UPDATE`) suits high-contention resources where conflicts are frequent and expected; optimistic locking (a version check at write time, with application-level retry) suits the low-contention majority of typical application data.
- Row-level locking is the default in modern relational databases specifically because it allows far more real concurrency than table-level locking.
- A deadlock is a genuine cycle of transactions each waiting on a lock the other holds — databases detect and resolve it automatically by rolling back one participant, but the real fix is enforcing a consistent lock-acquisition order so the cycle can never form.
