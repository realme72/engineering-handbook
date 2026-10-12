# Transactions

# Why Do Transactions Exist?

Here's the example everyone reaches for, because it's exactly what goes wrong without transactions.

```
Transfer ₹500 from Alice to Bob

Step 1: UPDATE accounts SET balance = balance - 500 WHERE name = 'Alice';
Step 2: UPDATE accounts SET balance = balance + 500 WHERE name = 'Bob';
```

Now imagine the server crashes, the network drops, or the process gets killed **between** step 1 and step 2.

```
Step 1 executes  →  Alice's balance decreases by 500

↓  CRASH  ↓

Step 2 never runs  →  Bob's balance never increases

Result: ₹500 has vanished from the system entirely
```

Nobody stole the money. Nothing malicious happened. A perfectly ordinary two-statement operation got interrupted halfway through, and the database now holds a state that could never have existed if the operation had actually been treated as one indivisible unit.

A transaction exists to make a group of operations behave as a single, indivisible unit — either **all** of them apply, or **none** of them do. There is no in-between state a crash can leave you in.

```sql
BEGIN;
UPDATE accounts SET balance = balance - 500 WHERE name = 'Alice';
UPDATE accounts SET balance = balance + 500 WHERE name = 'Bob';
COMMIT;
```

If the crash happens before `COMMIT`, the database rolls the entire thing back on recovery — Alice's balance is exactly as if the transfer never started. There's no state where the money vanished, because the database never considers step 1 "real" until the whole transaction commits.

---

# What Problem It Actually Solves

- **Partial failure** — the crash-in-the-middle scenario above, which is not a rare edge case, it's a routine, expected event at any real scale (processes crash, networks drop, disks fail).
- **All-or-nothing multi-step operations** — anything that requires more than one write to stay logically consistent: debit + credit, order creation + inventory decrement, user signup + welcome email record.
- **A clean recovery story** — after a crash, the database doesn't need you to manually figure out which half-finished operations need cleanup; incomplete transactions are simply rolled back automatically on restart.

---

# The Basic Lifecycle

```sql
BEGIN;

-- do work
UPDATE inventory SET stock = stock - 1 WHERE product_id = 15;
INSERT INTO orders (product_id, user_id) VALUES (15, 42);

COMMIT;
```

```
BEGIN     →  start a new transaction

... work ...

COMMIT    →  make all changes permanent, visible to everyone
ROLLBACK  →  discard everything since BEGIN, as if it never happened
```

If anything goes wrong mid-transaction — a constraint violation, an application-level error, an explicit decision to abort — you `ROLLBACK` instead of `COMMIT`, and the database guarantees none of the intermediate writes ever become visible to any other connection.

---

# Python Implementation

```python
import psycopg2

conn = psycopg2.connect("dbname=shop")

try:
    with conn:  # psycopg2 commits on success, rolls back on exception, automatically
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE inventory SET stock = stock - 1 WHERE product_id = %s",
                (15,),
            )
            cur.execute(
                "INSERT INTO orders (product_id, user_id) VALUES (%s, %s)",
                (15, 42),
            )
except Exception:
    # the `with conn:` block already rolled back — nothing partially applied
    raise
```

Notice what happens if the `INSERT` fails for any reason — a foreign key violation, a dropped connection. The `UPDATE` that already ran doesn't stay applied. `conn` rolls back the whole block, because from the database's point of view, nothing inside `with conn:` was ever "real" until every statement in it succeeded and the block exited cleanly.

---

# Savepoints — Partial Rollback Within a Transaction

Sometimes you want to undo part of a transaction without throwing away everything.

```sql
BEGIN;

UPDATE accounts SET balance = balance - 500 WHERE name = 'Alice';

SAVEPOINT before_bonus;

UPDATE accounts SET balance = balance + 50 WHERE name = 'Alice';  -- a bonus credit

-- turns out the bonus was a mistake
ROLLBACK TO SAVEPOINT before_bonus;

UPDATE accounts SET balance = balance + 500 WHERE name = 'Bob';

COMMIT;
```

The bonus credit gets undone, but Alice's original debit and Bob's credit still commit normally. Savepoints are a checkpoint *within* a transaction — useful for complex multi-step operations where one specific sub-step might need to be retried or abandoned without restarting the whole transaction from scratch.

---

# Transactions Don't Automatically Span Services

This is the trap that catches people moving from a single monolithic database to microservices.

```
Monolith, one database:

BEGIN;
  UPDATE orders SET status = 'placed';
  UPDATE inventory SET stock = stock - 1;
COMMIT;                                        ← genuinely atomic
```

```
Microservices, two databases:

Orders Service  → its own database → COMMIT
Inventory Service → its own database → COMMIT   ← these are TWO separate transactions
```

There's no `BEGIN`/`COMMIT` that spans both databases here. If the Orders Service commits and the Inventory Service's call then fails, you're left with an order marked "placed" and no corresponding inventory decrement — the same partial-failure problem transactions were built to solve, except transactions alone can't fix it, because the two operations live in genuinely separate databases with no shared boundary.

The **Saga Pattern** (covered in Distributed Systems) is what actually solves this — all-or-nothing behavior across separate databases, achieved through compensating actions instead of a single transaction. Distributed two-phase commit (2PC) is the theoretically cleaner answer, but it's rarely used at real scale, because it requires every participant to stay locked and available until the whole thing resolves. One slow or down participant blocks everyone.

---

# Real-World Examples

### Banking Transfers

The motivating example throughout this chapter — every real banking system wraps a transfer in a transaction specifically because "money debited but never credited" is not an acceptable failure mode under any circumstances, including a server crashing mid-operation.

---

### E-Commerce Checkout

```sql
BEGIN;
  INSERT INTO orders (...) VALUES (...);
  UPDATE inventory SET stock = stock - 1 WHERE product_id = 15;
  INSERT INTO payments (...) VALUES (...);
COMMIT;
```

A checkout flow that creates an order, decrements stock, and records a payment needs all three to succeed together — an order placed with no inventory decrement means overselling; a decrement with no order means lost stock for nothing.

---

### PostgreSQL / MySQL (InnoDB)

Both provide full transaction support as a core feature, not an add-on — `BEGIN`/`COMMIT`/`ROLLBACK`, savepoints, and configurable isolation levels (the next chapter) are baseline capabilities of any serious relational database engine.

---

# Common Interview Questions

## Why not just perform the two writes separately and check for errors in application code?

Because a crash between the two writes — the server process dying, the connection dropping, the machine losing power — leaves the system in a state that could never happen if the operation were treated as one unit. Application-level error checking can catch a thrown exception; it cannot catch the process being killed mid-operation. A transaction's guarantee comes from the database itself, not from your application successfully running cleanup code after the fact.

---

## What happens if the application crashes after BEGIN but before COMMIT?

On recovery, the database treats that transaction as if it never happened — none of its writes are visible or applied. This is exactly the guarantee that makes transactions useful: an interrupted transaction leaves zero trace, rather than a half-applied mess.

---

## What's a savepoint, and when would you use one?

A checkpoint within an open transaction that lets you roll back part of the work without discarding the entire transaction. Useful in complex multi-step transactions where one specific sub-step is allowed to fail and be abandoned while the rest of the transaction still proceeds normally.

---

## Can a transaction span two different microservices, each with their own database?

Not natively — a `BEGIN`/`COMMIT` only covers one database connection's scope. Two services with separate databases each commit independently; there's no shared atomic boundary connecting them. This is exactly the problem the Saga Pattern solves, using a sequence of local transactions plus compensating actions to undo prior steps if a later one fails, instead of relying on a single cross-service transaction.

---

## Why don't more systems use two-phase commit (2PC) for cross-service transactions?

Because 2PC requires every participant to hold its locks and stay available until the entire distributed transaction resolves — if one participant is slow, crashed, or unreachable, every other participant is stuck blocked, holding locks, unable to proceed. At real distributed-systems scale, that fragility is usually judged worse than the added complexity of an eventually-consistent Saga-based approach.

---

# Common Mistakes

❌ Holding a transaction open across a slow external call (an API request, an email send).

Every lock the transaction holds stays held for the entire duration — turning a slow third-party API call into something that blocks every other transaction waiting on the same rows.

---

❌ Assuming `try/except` in application code replaces a database transaction.

Catches exceptions your own code throws; does nothing for a crash, a killed process, or a dropped connection mid-operation — the exact failure modes transactions exist to protect against.

---

❌ Assuming a transaction automatically spans multiple services or databases.

Each database connection's transaction boundary is local to that database. Cross-service atomicity needs an explicit pattern like Saga, not an assumption that "everything happens in one big transaction somewhere."

---

❌ Forgetting to roll back on error paths in manually-managed transaction code.

If you're not using a context-manager style API (`with conn:` in Python, or equivalent), a caught exception that doesn't explicitly call `ROLLBACK` can leave a transaction hanging open, holding locks indefinitely.

---

# Key Takeaways

- Transactions exist because partial failure — a crash between two related writes — is a routine, expected event, not a rare edge case, and it can leave a system in a state that should be impossible.
- `BEGIN`/`COMMIT`/`ROLLBACK` make a group of operations atomic: either all of them apply, or none do, with no visible in-between state.
- Savepoints allow partial rollback within an otherwise-still-committing transaction.
- A transaction's boundary is local to one database connection — it does not automatically span multiple services or databases, which is exactly the gap the Saga Pattern is built to fill.
- Two-phase commit is the theoretically "complete" answer for distributed atomicity, but its requirement that every participant stay locked and available until resolution makes it fragile at real scale — most distributed systems favor Sagas instead.
