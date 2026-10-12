# ACID

# Why Does ACID Exist?

ACID isn't a feature someone bolted onto databases. It's a name Andreas Reuter and Theo Härder coined in the 1980s for guarantees database researchers — Jim Gray chief among them — had already been building toward through the 1970s for banking and airline reservation systems. Those systems needed a precise answer to one question: **exactly what does a database promise you when you run a transaction?**

Without that answer, every team was left guessing which failure modes they had to guard against in application code, and which ones the database already covered. ACID is that answer: four guarantees, each closing off a specific way data can silently go wrong.

```
A — Atomicity     "all of it, or none of it"
C — Consistency   "never leaves the data in a state that violates its own rules"
I — Isolation     "concurrent transactions don't corrupt each other's view of the data"
D — Durability    "once committed, it survives a crash, permanently"
```

Each letter is really answering a different, specific failure that databases needed to rule out.

---

# Atomicity

**Guards against:** partial execution of a multi-step operation.

```sql
BEGIN;
UPDATE accounts SET balance = balance - 500 WHERE name = 'Alice';
UPDATE accounts SET balance = balance + 500 WHERE name = 'Bob';
COMMIT;
```

If the process crashes between the two `UPDATE` statements, atomicity guarantees that on recovery, neither statement is considered to have happened — Alice's balance is exactly as if the transaction never started. This is covered in full depth in the Transactions chapter; the short version here is: atomicity is what makes "all or nothing" actually true, not just a design intention.

---

# Consistency

**Guards against:** a committed transaction leaving the database in a state that violates its own declared rules.

```sql
ALTER TABLE accounts ADD CONSTRAINT positive_balance CHECK (balance >= 0);
```

```sql
BEGIN;
UPDATE accounts SET balance = balance - 1000 WHERE name = 'Alice';  -- Alice only has 500
COMMIT;   -- REJECTED — violates the CHECK constraint
```

Consistency here means the database enforces its own integrity rules — constraints, foreign keys, uniqueness — so a transaction that would violate one of them simply never commits. This is a genuinely important, and genuinely confusing, letter to get right in an interview, covered specifically below.

---

# Isolation

**Guards against:** concurrent transactions seeing or corrupting each other's in-progress work.

```
Transaction A:  reads Alice's balance → 500

Transaction B (concurrently):  updates Alice's balance to 400, but hasn't committed yet

Transaction A:  should it see 500, or 400, or something else entirely?
```

Isolation defines exactly what a transaction is allowed to see of other transactions' concurrent, uncommitted work. This is the single deepest and most nuanced letter in ACID — deep enough that it has its own dedicated chapter (Isolation Levels), because "isolated" is not one fixed guarantee; it's a spectrum, and different databases default to different points on that spectrum.

---

# Durability

**Guards against:** a crash immediately after commit losing data that was supposedly already saved.

```
COMMIT succeeds  →  application receives confirmation

↓  power failure one millisecond later  ↓

On restart: is that committed data still there?
```

Durability says yes — once a `COMMIT` returns successfully, that data is guaranteed to survive, even a total power loss the instant after.

## How Durability Is Actually Implemented: The Write-Ahead Log (WAL)

Writing every change directly to its final location on disk, synchronously, on every single transaction, would be far too slow. Instead, databases use a **write-ahead log**: before a transaction is allowed to report success, its intended changes are first appended to a sequential log file and forced to disk (`fsync`) — only *then* does the database consider the transaction durable, even though the actual data pages in the main table files might still get updated later, lazily, in the background.

```
COMMIT requested

↓

Write the transaction's changes to the WAL (sequential, fast, fsync'd to disk)

↓

Report success to the application    ← durability guarantee starts here

↓  (can happen later, lazily)  ↓

Actual table data pages get updated on disk from the WAL
```

If the database crashes after the WAL write but before the main table pages are updated, recovery simply **replays the WAL** from the last checkpoint — reapplying every committed transaction's changes in order, which is how a database can promise "committed means committed" without needing every single write to hit the final, scattered-across-disk table pages synchronously.

---

# The Classic Interview Trap: ACID's "C" vs CAP's "C"

Both ACID and the CAP theorem use the word **consistency**, and they mean genuinely different things — this single fact trips up more engineers in interviews than any other detail in this chapter.

```
ACID Consistency:   a committed transaction never violates the database's
                     own integrity rules (constraints, foreign keys, uniqueness)

CAP Consistency:    every node in a distributed system returns the same,
                     most-recent data for a given read, regardless of which
                     node answers the request
```

ACID consistency is about **rule enforcement within a single database**. CAP consistency is about **agreement across multiple replicas/nodes in a distributed system**. A single-node database can be perfectly ACID-consistent and the question of CAP consistency doesn't even apply to it, because CAP is fundamentally about what happens when a network partition separates multiple nodes — a scenario that doesn't exist on a single machine.

The full CAP theorem itself belongs to the Distributed Systems chapter — the point to take from ACID is narrower and more specific: **don't let the shared word "consistency" convince you they're the same guarantee measured at different scales. They are answering entirely different questions.**

---

# ACID vs BASE

NoSQL databases that intentionally relax some ACID guarantees for scale and availability are often described with the (deliberately punny) counter-acronym **BASE**:

```
BASE — Basically Available, Soft state, Eventual consistency

Basically Available   →  the system prioritizes staying up and responding,
                          even under partial failure

Soft state             →  the stored state may change over time even
                          without new input, as replicas converge

Eventual consistency   →  given enough time with no new writes, all
                          replicas will eventually agree — but not
                          necessarily immediately
```

It isn't worse than ACID — it's a different trade-off, deliberately accepting temporary inconsistency across replicas for availability and write scale that a strictly ACID system struggles to match across many distributed nodes.

The industry has actually drifted back toward ACID even in the NoSQL world. MongoDB added multi-document ACID transactions in version 4.0 (2018) — a quiet admission that plenty of real applications need atomicity guarantees "eventually consistent" alone doesn't give them, even in a document-store shape.

---

# Real-World Examples

### PostgreSQL / MySQL (InnoDB)

Fully ACID-compliant by default — atomicity and durability via WAL, consistency via enforced constraints, and isolation via MVCC (see Isolation Levels) — the baseline that most relational workloads take for granted, and the reason banking and payment systems build on top of them without a second thought.

---

### MongoDB

Historically only guaranteed atomicity at the single-document level (a single document's fields update atomically together, but not across multiple documents) — a deliberate design trade for scale and flexibility. Since version 4.0, it supports true multi-document ACID transactions, for the cases where an application genuinely needs cross-document atomicity, at some cost to performance relative to single-document operations.

---

### DynamoDB

Offers configurable read consistency (eventually consistent by default, strongly consistent as an opt-in per-read) and supports ACID transactions across multiple items — a concrete example of a NoSQL system deliberately offering both ends of the ACID/BASE spectrum and letting the application choose per-operation, rather than committing to one philosophy system-wide.

---

# Common Interview Questions

## Walk me through ACID with a concrete example.

Atomicity: a bank transfer's debit and credit either both happen or neither does, even across a crash mid-transaction. Consistency: a `CHECK (balance >= 0)` constraint prevents any committed transaction from leaving an account negative. Isolation: two concurrent transactions reading and updating the same row don't see each other's uncommitted, in-progress changes in a way that corrupts the result. Durability: once a transfer's commit returns success, it survives a crash the very next instant, via the write-ahead log.

---

## How is durability actually implemented under the hood?

Via a write-ahead log — before a transaction is reported as successfully committed, its changes are appended to a sequential log file and forced to disk. The actual data pages in the main table files can be updated later, lazily; if a crash happens in between, recovery replays the WAL to reconstruct every committed change, which is what makes "committed means committed" true without requiring every write to synchronously hit its final scattered location on disk.

---

## What's the difference between ACID's Consistency and CAP's Consistency?

ACID consistency means a committed transaction never violates the database's own integrity rules — constraints, foreign keys, uniqueness — within a single database. CAP consistency means every node in a distributed system agrees on the most recent value for a given read. They share a word but answer different questions at different scales — ACID's C is about single-database rule enforcement; CAP's C is about multi-node agreement during a network partition.

---

## What's the difference between ACID and BASE?

ACID prioritizes strict correctness guarantees (atomicity, enforced consistency, isolation, durability), typically within a single database or tightly-coordinated cluster. BASE (Basically Available, Soft state, Eventual consistency) deliberately relaxes immediate consistency in exchange for availability and horizontal scale across many distributed nodes — a trade-off, not an inferior alternative, chosen based on what a specific system actually needs.

---

## Can a NoSQL database be ACID-compliant?

Yes — ACID isn't exclusive to relational databases. MongoDB added multi-document ACID transactions in 4.0, and DynamoDB supports ACID transactions across multiple items. The historical association of "ACID = relational, BASE = NoSQL" is a useful simplification for a first-pass mental model, but the real industry has moved toward letting applications choose per-operation rather than picking one philosophy system-wide.

---

# Common Mistakes

❌ Confusing ACID's Consistency with CAP's Consistency in an interview.

The single most common ACID-related mix-up — they are genuinely different concepts sharing one overloaded word, not the same guarantee described twice.

---

❌ Assuming ACID guarantees good performance.

ACID guarantees correctness, not speed — strict isolation levels (Serializable) in particular can meaningfully reduce throughput under high concurrency, which is exactly why isolation levels exist as a tunable trade-off rather than a single fixed guarantee.

---

❌ Treating "NoSQL" and "not ACID" as synonyms.

Several major NoSQL systems (MongoDB, DynamoDB) now offer ACID transactions as an explicit, opt-in capability — the ACID/BASE split is a spectrum applications choose from, not a hard boundary between database categories.

---

❌ Assuming durability means data is instantly written to its final location on disk.

Durability is guaranteed via the write-ahead log the moment a commit succeeds — the actual table pages can be updated lazily afterward. Understanding this distinction is what makes WAL-based recovery make sense at all.

---

# Key Takeaways

- ACID names four specific guarantees a database transaction makes: Atomicity (all-or-nothing), Consistency (never violates its own integrity rules), Isolation (concurrent transactions don't corrupt each other's view), and Durability (a commit survives a crash, permanently).
- Durability is implemented via a write-ahead log — changes are logged sequentially and fsync'd before a commit is reported successful, with the actual table pages updated lazily afterward and reconstructed via WAL replay if a crash happens first.
- ACID's "Consistency" (single-database rule enforcement) and CAP's "Consistency" (multi-node agreement) are different concepts that happen to share a name — this distinction is one of the most common places engineers get tripped up.
- BASE (Basically Available, Soft state, Eventual consistency) is the deliberate counter-philosophy some NoSQL systems adopt, trading immediate consistency for availability and horizontal scale — not an inferior alternative, a different trade-off.
- The ACID/NoSQL boundary has blurred in practice — MongoDB and DynamoDB both offer ACID transactions as an explicit, opt-in capability rather than treating "NoSQL" and "eventually consistent only" as synonyms.
