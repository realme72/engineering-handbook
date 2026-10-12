# Replication

# Why Does Replication Exist?

A single database running on a single machine has two structural problems, regardless of how well-tuned it is.

```
Problem 1: The machine dies.
           Disk failure, hardware fault, data center incident.
           → Every bit of data on it is gone or unreachable.

Problem 2: The machine is overwhelmed.
           One server, however powerful, has a ceiling on how many
           concurrent reads it can serve.
```

Replication solves both by keeping continuously-updated copies of the data on multiple machines.

```
Primary (Writes)

↓  (changes stream continuously)

Replica 1        Replica 2        Replica 3
```

If the primary dies, a replica already has (nearly) all the data and can be promoted to take over. And since replicas are kept up to date with the same data, they can independently serve read traffic — spreading read load across several machines instead of concentrating every single read and write on one.

---

# What Problem It Actually Solves

- **Durability against total machine loss** — a copy of the data survives even if the primary is destroyed entirely.
- **Read scalability** — read-heavy workloads (which most applications are) can be spread across many replicas instead of bottlenecking on one machine.
- **Availability during failover** — a replica can be promoted to primary, keeping the system operational (after some disruption) instead of being down until the original machine is repaired.
- **Geographic distribution** — replicas placed closer to users in different regions can serve reads with lower latency than always crossing the globe to a single primary.

What replication does **not** solve on its own: write scalability. Every write still has to go through the primary (in a standard primary-replica setup) — replicating those writes out to replicas afterward doesn't let you accept more writes per second than one primary can handle. That specific problem is what Sharding exists for.

---

# Primary-Replica Replication

```
Client writes  →  Primary  →  streams changes  →  Replica A
                                                →  Replica B
                                                →  Replica C

Client reads   →  can be served by ANY of the above
```

The primary is the single source of truth for writes. Every replica continuously applies the same stream of changes the primary already committed, keeping itself as close to the primary's state as its replication method allows.

Under the hood, this is usually implemented by shipping the primary's **write-ahead log** (the same WAL from the ACID chapter, used there for crash recovery) to each replica, which replays it to reconstruct the same sequence of changes locally — replication and crash recovery are, mechanically, close cousins of the same underlying idea: a durable, ordered log of changes that can be replayed.

---

# Synchronous vs Asynchronous Replication

This is the actual trade-off decision, and it's a direct instance of the classic latency-vs-durability tension that shows up everywhere in distributed systems.

## Asynchronous Replication

```
Client writes  →  Primary commits  →  returns success to client

↓  (happens afterward, independently)

Replica eventually receives and applies the change
```

The primary doesn't wait for any replica to confirm before telling the client the write succeeded. Fast — the client isn't delayed by network round trips to replicas — but if the primary crashes in the gap between committing and the replica catching up, that write can be lost entirely, even though the client was already told it succeeded.

## Synchronous Replication

```
Client writes  →  Primary writes  →  waits for replica to confirm  →  THEN returns success
```

The primary waits for at least one replica to confirm it has the change before reporting success to the client — meaning a client-visible "success" is genuinely guaranteed to survive the primary's failure, since a replica already has it too. The cost is latency: every write now waits on a network round trip to another machine, and if that replica is slow or unreachable, writes stall.

## Semi-Synchronous (A Common Middle Ground)

```
Primary confirms with the CLOSEST/FASTEST replica only,
while other replicas still catch up asynchronously in the background
```

Gets a durability guarantee from at least one additional copy without paying the full latency cost of waiting on every replica — a pragmatic compromise many production systems land on rather than choosing a pure extreme.

---

# Replication Lag

Because most production systems use asynchronous replication for performance reasons, replicas are very often slightly behind the primary — this gap is called **replication lag**, and it causes a genuinely common, easy-to-miss class of bug.

```
1. Client writes a new profile update to the Primary.  →  succeeds

2. Client immediately reads their own profile.

3. That read gets routed to a Replica.

4. The Replica hasn't received the update yet (lag = 200ms).

5. Client sees their OWN write... as if it never happened.
```

This is the **read-your-own-writes** problem — from the user's perspective, they just saved something and it's gone, which is a confusing and trust-eroding bug even though the data is, technically, safe and correctly saved on the primary.

## Common Fixes

```
Sticky Session       →  route a user's reads to the primary (or the specific
                          replica they just wrote to) for a short window after a write

Read-Your-Writes      →  track a "last written" marker (e.g. a timestamp or LSN)
Consistency Token        and only serve reads from a replica that has caught up
                          past that marker

Always Read Primary    →  for specifically sensitive post-write reads
for Critical Paths        (checkout confirmation, account settings), skip
                           replicas entirely and read from the primary
```

None of these are automatic — an application has to explicitly decide, for each read, whether replication lag is an acceptable risk for that specific use case (a public product listing can tolerate a few hundred milliseconds of staleness; a user's own just-submitted payment confirmation usually can't).

---

# Failover

When the primary genuinely goes down, a replica needs to be promoted to become the new primary.

```
Primary  →  CRASHES

↓

Monitoring detects the primary is unreachable

↓

A replica (usually the most up-to-date one) is promoted to Primary

↓

Remaining replicas are reconfigured to replicate from the NEW primary

↓

Clients are redirected to the new primary for writes
```

Tools like **Patroni** (for Postgres) or built-in mechanisms in managed services (AWS RDS/Aurora) automate this detection-and-promotion sequence, because doing it manually under the pressure of an actual outage is slow and error-prone.

## Split-Brain: The Failure Mode Within a Failure

The genuinely dangerous scenario: a network partition makes the primary *look* unreachable to the monitoring system, so a replica gets promoted to primary — but the original primary is actually still running and still accepting writes from clients that haven't yet learned about the failover.

```
"Old" Primary  →  still accepting writes (network partition, not actually dead)

"New" Primary  →  also accepting writes (promoted because it looked unreachable)

Two primaries, both accepting writes independently, with no coordination
→ diverging, conflicting data neither side knows about
```

This is why serious failover systems require a **quorum** or **fencing** mechanism — a way to guarantee the old primary is definitively stopped (fenced off from accepting further writes) before a new one is trusted, rather than just assuming "unreachable" means "dead." Getting this wrong is one of the more subtle and dangerous failure modes in distributed database operations.

---

# Multi-Leader (Multi-Master) Replication

```
Region A: Primary A  ←→  Region B: Primary B

Both accept writes independently, and replicate changes to each other
```

Instead of one primary, multiple nodes each accept writes and propagate them to each other — commonly used for multi-region setups where writes need to be accepted locally in each region for latency reasons, rather than every write in Asia routing all the way to a single primary in the US.

The unavoidable cost: **conflicts**. If the same record is modified in two regions at nearly the same time, before either write has propagated to the other region, you get two divergent versions of the same data with no natural ordering between them — resolved either with a deterministic rule (last-write-wins by timestamp, accepting the risk of silently discarding one write) or application-specific merge logic. This is a fundamentally harder problem than single-primary replication, which is exactly why most systems default to single-primary unless multi-region write latency specifically demands otherwise.

---

# Real-World Examples

### PostgreSQL Streaming Replication

Ships the primary's write-ahead log to replicas, which continuously replay it — the same WAL mechanism from the ACID chapter, reused here for a second purpose beyond crash recovery. Supports both asynchronous (default) and synchronous replication, configurable per use case.

---

### MySQL Binlog Replication

Uses a binary log of every change on the primary, which replicas consume and apply — conceptually similar to Postgres's WAL-based approach, historically MySQL's older statement-based replication had subtle correctness pitfalls (non-deterministic statements, like ones using `NOW()` or random functions, could produce different results on replicas) which is part of why row-based binlog replication became the safer modern default.

---

### AWS Aurora

Decouples storage from compute in a way that makes replica promotion and read-scaling largely managed and near-instant compared to a hand-rolled Postgres/MySQL replication setup — a concrete example of a managed service absorbing most of the operational complexity described in this chapter, at the cost of vendor lock-in and less low-level control.

---

# Common Interview Questions

## Synchronous vs asynchronous replication — what's the actual trade-off?

Synchronous guarantees a client-visible "success" survives the primary's failure (since a replica already has it), at the cost of added write latency waiting on a replica's confirmation. Asynchronous is faster for writes but risks losing the most recent write(s) if the primary crashes before replicas catch up. Semi-synchronous is a common middle ground — waiting on just one fast replica while others catch up asynchronously.

---

## What is replication lag, and why does it cause bugs?

The delay between a write committing on the primary and a replica actually reflecting it. If an application reads from a replica shortly after writing to the primary, it can see stale data — including, confusingly, failing to see its own just-completed write (the "read-your-own-writes" problem) — even though the data is safely committed on the primary.

---

## How does automatic failover work, and what can go wrong?

Monitoring detects the primary is unreachable, promotes the most up-to-date replica to primary, and reconfigures remaining replicas and clients around the new primary. The dangerous failure mode is split-brain — the old primary wasn't actually dead, just network-partitioned, and continues accepting writes while a new primary is simultaneously promoted, producing two independently-writable primaries with diverging data. Serious failover systems use quorum or fencing mechanisms specifically to prevent this.

---

## Does replication solve write scalability?

No — in a standard primary-replica setup, every write still goes through the single primary; replicas only help with read scaling and durability/availability. Scaling write throughput beyond what one primary can handle requires a fundamentally different approach — sharding, which splits the data itself (not just copies of it) across multiple independently-writable machines.

---

## When would you use multi-leader replication instead of single-primary?

When writes need to be accepted locally in multiple regions for latency reasons, rather than every write traveling to one single, possibly distant, primary. The trade-off is having to handle write conflicts between regions — two writes to the same record in different regions before either propagates to the other — which single-primary replication never has to deal with at all.

---

# Common Mistakes

❌ Reading a user's own just-written data from a replica without accounting for lag.

Produces the confusing "I just saved this and it's gone" bug — route immediately-post-write reads to the primary, or track a consistency marker, for anything where this matters to the user.

---

❌ Assuming asynchronous replication means zero risk of data loss.

If the primary crashes before a replica catches up, the most recent asynchronously-replicated write(s) can be lost even though the client was already told the write succeeded.

---

❌ Trusting "unreachable" to mean "dead" during failover.

This is exactly the setup for split-brain — a network partition can make a perfectly healthy primary look unreachable, and promoting a new primary without properly fencing off the old one risks two simultaneously-writable primaries.

---

❌ Assuming replication solves the problem of scaling writes.

Replicas help with reads and durability; every write in a standard setup still funnels through one primary — a fundamentally different problem, solved by sharding, not replication.

---

# Key Takeaways

- Replication exists to survive total machine loss and to scale read traffic across multiple machines — it does not, by itself, scale write throughput.
- Synchronous replication trades write latency for a durability guarantee; asynchronous trades a small risk of data loss on primary failure for faster writes — semi-synchronous is a common practical middle ground.
- Replication lag is a real, everyday phenomenon in asynchronous setups, and the read-your-own-writes problem is its most common user-visible symptom — solved with sticky routing, consistency tokens, or reading critical paths from the primary directly.
- Failover promotes a replica to primary when the original fails, but the real danger is split-brain — a network partition making a healthy primary look dead, risking two simultaneously-writable primaries unless a proper quorum/fencing mechanism prevents it.
- Multi-leader replication accepts writes in multiple locations for latency reasons, at the cost of having to resolve genuine write conflicts between leaders — a fundamentally harder problem than single-primary replication.
