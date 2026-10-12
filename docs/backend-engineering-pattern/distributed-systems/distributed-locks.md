# Distributed Locks

# Why Do Distributed Locks Exist?

The Locks chapter covered mutual exclusion within a single database — multiple transactions competing for the same row, coordinated via the database's own internal locking mechanism. Distributed locks solve the same fundamental problem — ensuring only one process touches a shared resource at a time — but for processes running on **entirely separate machines**, with no shared memory and no single database transaction connecting them.

```
Two independent application servers, both trying to process
the SAME scheduled job at the same time (e.g. "send the daily report")

Server A: picks up the job
Server B: ALSO picks up the same job, independently, at nearly the same moment

↓

Without coordination: the report gets sent TWICE
```

A distributed lock is a shared coordination mechanism — typically backed by Redis, Zookeeper, or etcd — that lets processes across different machines agree on "who currently holds the right to proceed" the same way a database's row lock does for transactions within one database.

---

# The Basic Mechanism

```python
lock_acquired = redis_client.set("lock:daily_report", "server_A_id", nx=True, ex=30)

if lock_acquired:
    try:
        send_daily_report()
    finally:
        redis_client.delete("lock:daily_report")
else:
    pass  # another server already holds the lock — skip this run
```

`SET key value NX EX seconds` (the exact mechanism from the Redis chapter) atomically acquires the lock only if no other process currently holds it, with an expiration so the lock is automatically released even if the holder crashes before explicitly releasing it. This looks simple, and mostly works — but has a specific, subtle, and genuinely famous flaw.

---

# The Fencing Token Problem

This is the single most important, most commonly cited gotcha about distributed locks, popularized by Martin Kleppmann's widely-referenced critique of naive Redis-based locking.

```
Server A acquires the lock (TTL = 30 seconds)

↓

Server A experiences a long pause — a garbage collection stop-the-world
pause, a slow disk write, a network delay — lasting 40 seconds

↓

Meanwhile, the lock's TTL EXPIRES after 30 seconds (Server A is still
paused, unaware time has passed)

↓

Server B successfully acquires the SAME lock (it's expired, so this
is entirely correct behavior from the lock service's point of view)

↓

Server B begins doing the protected work

↓

Server A FINALLY wakes up from its pause — still believing it holds
the lock (it never found out the TTL expired) — and ALSO proceeds
to do the same protected work

↓

Both Server A and Server B are now doing the work SIMULTANEOUSLY,
even though the lock was supposed to guarantee only one of them could
```

The lock's expiration is doing exactly what it's designed to do (preventing an unbounded hang if a holder genuinely crashes) — the problem is that a long pause is indistinguishable, from the lock service's perspective, from a genuine crash, and the paused process has no way of knowing time has passed once it resumes. **A TTL-based lock alone does not guarantee mutual exclusion for the actual protected work** — it only guarantees exclusive *possession of the lock key* for a bounded time, which is a subtly, importantly weaker guarantee.

---

# The Fix: Fencing Tokens

```
Each time the lock is acquired, the lock service issues a MONOTONICALLY
INCREASING number (a fencing token) along with it.

Server A acquires lock → gets token 33
Server B acquires lock (after A's TTL expired) → gets token 34
```

```
Server A wakes up from its pause, still believing it holds the lock,
and tries to write to the protected resource — presenting token 33

↓

The resource itself (not the lock service) checks: "have I already
seen a token higher than 33?" → YES, it already saw token 34 from
Server B → REJECTS Server A's write, even though Server A still
thinks it holds the lock
```

```python
def write_to_resource(token, data):
    if token < resource.last_seen_token:
        raise StaleTokenError("A newer lock holder has already acted")
    resource.last_seen_token = token
    resource.data = data
```

This is the actual, complete fix — the protected resource itself becomes the final arbiter, rejecting any write carrying an outdated token, regardless of what the writer believes about its own lock status. Fencing moves the safety guarantee from "trust that only one process believes it holds the lock" (which a long pause can break) to "the resource itself refuses stale writes" (which holds regardless of what any client mistakenly believes).

---

# Redlock — And Why It's Controversial

Redis's own proposed algorithm for a more robust distributed lock (Redlock) acquires the lock across multiple independent Redis instances, requiring a majority to agree, specifically to be more resilient to a single Redis node failing.

```
Redlock: acquire the same lock key across 5 independent Redis nodes

↓

Considered "acquired" if a MAJORITY (3 of 5) confirm it within a
time budget
```

This looks like a reasonable application of the majority-quorum idea from the Consensus chapter — but Kleppmann's critique specifically argues Redlock doesn't actually provide the safety guarantee it claims to under certain realistic failure scenarios (clock jumps or significant drift on any of the participating nodes, or the same long-pause scenario described above, can still allow two clients to both believe they hold the lock simultaneously). This is a genuinely famous, real industry disagreement — worth knowing about specifically because it demonstrates that "add more nodes and require a majority" isn't automatically equivalent to the rigorous safety guarantees a proper consensus algorithm (Raft, Paxos) provides; Redlock, as originally proposed, doesn't have the same formal safety proof behind it.

---

# Real-World Examples

### Zookeeper / etcd — Ephemeral Sequential Nodes

A common, more rigorously-grounded pattern: a client creates an ephemeral, sequentially-numbered node in Zookeeper representing its lock request; the client holding the *lowest*-numbered node holds the lock; if that client's session dies (detected via Zookeeper's own heartbeat mechanism), its ephemeral node is automatically removed, and the next-lowest-numbered client becomes the new lock holder. Because this is built directly on Zookeeper's own consensus mechanism (ZAB), it inherits the same rigor Raft-based systems provide, rather than relying on a looser, ad-hoc majority scheme layered on top of independent nodes.

---

### Chubby (Google)

Google's original internal distributed lock service, and the direct inspiration for Zookeeper's design — Chubby was built specifically because Google's own engineers kept independently reinventing (and getting subtly wrong) distributed locking, motivating a single, carefully-designed, consensus-backed service instead.

---

### Distributed Cron / Scheduled Job Deduplication

The exact motivating example from the top of this chapter — ensuring a scheduled job (a daily report, a batch cleanup task) only runs once across a fleet of servers, all capable of running it, is one of the most common practical uses of a distributed lock in real production systems.

---

# Common Interview Questions

## How would you implement a simple distributed lock?

Using a shared coordination store (Redis, Zookeeper, etcd) with an atomic "acquire only if not already held" operation and an expiration, so the lock is automatically released even if the holder crashes. `SET key value NX EX seconds` in Redis is the most common simple implementation.

---

## What is the fencing token problem, and why doesn't a simple TTL-based lock fully solve mutual exclusion?

A process can experience a long pause (GC, network delay) after acquiring a lock, during which the lock's TTL expires and a different process legitimately acquires it and starts working. When the first process resumes, it still believes it holds the lock and can proceed to do the same protected work simultaneously with the second process — the lock's expiration only guarantees exclusive possession of the lock *key* for a bounded time, not that the actual protected work is mutually exclusive.

---

## How do fencing tokens fix this?

Each lock acquisition is issued a monotonically increasing token. The protected resource itself — not the lock service — tracks the highest token it's seen and rejects any write carrying an older one. This moves the safety guarantee to the resource itself, which holds regardless of what a stale lock holder mistakenly believes about its own lock status.

---

## Why is Redlock considered controversial?

Because it claims to provide safety guarantees (only one client ever believes it holds the lock) under a majority-based scheme across independent Redis nodes, but Kleppmann's widely-cited critique argues this doesn't hold under realistic failure scenarios like clock drift or long process pauses — unlike Raft or Paxos, which have rigorous, formal safety proofs, Redlock's majority scheme wasn't built with the same formal rigor, despite superficially resembling a consensus algorithm.

---

## How does distributed locking differ from single-machine locking (from the Locks chapter)?

Single-machine locking relies on the database's own internal, tightly-coupled locking mechanism, operating within one process's or one transaction's memory and timing model. Distributed locking has to coordinate across independent machines with no shared memory, over an unreliable network, where a lock holder can experience an arbitrarily long pause and have no way of knowing whether its lock has since expired — which is exactly why the fencing token problem exists in the distributed case but has no equivalent in a single-machine lock.

---

# Common Mistakes

❌ Relying on lock TTL alone as a complete mutual-exclusion guarantee.

A long pause after acquiring the lock can let its TTL expire while the holder is still unaware, allowing a second process to also acquire it and proceed — TTL alone bounds how long a lock can be held, it doesn't guarantee only one process ever acts as if it holds it.

---

❌ Not verifying a fencing token at the point where the protected resource is actually modified.

Without this check, a stale lock holder that resumes after a long pause has no barrier stopping it from acting as if it still legitimately holds the lock.

---

❌ Assuming Redlock provides the same rigorous safety guarantees as a proper consensus algorithm.

Redlock's majority-based scheme across independent Redis nodes has been credibly argued to not hold under realistic failure conditions — a Zookeeper/etcd-based lock, built on an actual consensus protocol, offers stronger, more rigorously proven guarantees.

---

# Key Takeaways

- Distributed locks solve mutual exclusion across independent machines with no shared memory, using a shared coordination service (Redis, Zookeeper, etcd) instead of a database's own internal locking mechanism.
- A TTL-based lock alone doesn't fully guarantee mutual exclusion — a long pause after acquiring it can let the TTL expire while the holder is unaware, letting a second process acquire the same lock and proceed simultaneously.
- Fencing tokens fix this by having the protected resource itself reject any write carrying an outdated token, moving the safety guarantee from "trust the lock holder's own belief" to "the resource verifies independently."
- Redlock's majority-based approach across independent Redis nodes is a genuinely controversial, actively debated design — it doesn't carry the same formal safety guarantees as a proper consensus-backed lock built on Zookeeper or etcd.
- Distributed cron/scheduled job deduplication across a fleet of servers is one of the most common, practical real-world uses of a distributed lock.
