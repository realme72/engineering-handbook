# Consistency Models

# Why Do Consistency Models Exist?

CAP theorem establishes that during a partition, a system must sometimes sacrifice strict consistency for availability. But "sacrifice consistency" isn't a single, binary state — there's an entire spectrum between "every read sees the absolute latest write" and "reads can return arbitrarily stale data with zero guarantees." Consistency models exist to name specific, useful points on that spectrum, so a system (and the engineers building on it) can make a deliberate, precise choice instead of a vague one.

```
Strongest ─────────────────────────────────────────────► Weakest

Strong        Causal          Read-Your-Writes    Eventual
Consistency   Consistency      Consistency        Consistency
```

Choosing a consistency model is choosing exactly how much staleness or disagreement between nodes an application can tolerate, in exchange for exactly how much availability, latency, or throughput it gets back.

---

# Strong Consistency (Linearizability)

```
Every read reflects the most recent completed write, system-wide,
as if there were only ONE copy of the data — regardless of which
node actually answers the read.
```

```
Write X=5 completes at time T

↓

ANY read, on ANY node, after time T → returns 5, guaranteed, no exceptions
```

The strongest, most intuitive guarantee — and the most expensive to provide, since it generally requires coordinating with other replicas before answering a read (or write) to ensure nothing more recent exists elsewhere. This is exactly what consensus protocols (covered in the Consensus chapter) are built to provide reliably across multiple nodes.

---

# Eventual Consistency

```
If no NEW writes occur, all replicas will EVENTUALLY converge to the
same value — but there is no bound on how long "eventually" takes,
and reads in the meantime can return different, stale values from
different nodes.
```

```
Write X=5 → Node A

↓ (replication happening in the background, asynchronously)

Immediately after: read from Node B → might still return the OLD value

Some time later:   read from Node B → now returns 5
```

The weakest common model, and the cheapest to provide — no coordination required on the read or write path, which is exactly why it enables the highest availability and lowest latency. The trade-off is real and unbounded: "eventually" is a genuine, deliberate lack of a time guarantee, not a synonym for "quickly."

---

# Causal Consistency

A meaningful middle ground: operations that are **causally related** must be seen by everyone in the same order; operations with no causal relationship (**concurrent** operations) can be seen in different orders by different nodes without anyone caring.

```
Alice posts a comment: "Great trip!"
Bob replies to it: "Where did you go?"

↓

These two operations are CAUSALLY related — Bob's reply only makes
sense AFTER Alice's comment. Every node MUST show Alice's comment
before Bob's reply, never the reverse.
```

```
Meanwhile, Carol (unrelated) posts her own comment on a different post
at roughly the same time.

↓

Carol's comment has NO causal relationship to Alice/Bob's exchange —
different nodes can show it in a different relative order without
breaking anything anyone would notice or care about.
```

This is a genuinely useful, practical middle ground precisely because most real applications don't actually need strong consistency for every unrelated pair of operations in the system — they need it specifically for operations that depend on each other, which causal consistency captures without paying strong consistency's full coordination cost for everything.

---

# Read-Your-Writes Consistency

A narrower, specific, and extremely practical guarantee: a client is guaranteed to see its **own** writes reflected in its own subsequent reads, even if the underlying system is only eventually consistent overall for everyone else.

```
User updates their own profile picture

↓

That same user immediately reloads their profile page

↓

Read-your-writes guarantee:  THIS user sees their new picture,
                              even though OTHER users viewing the
                              profile might briefly still see the old
                              one via a lagging replica
```

This is exactly the practical fix for the read-your-own-writes problem introduced in the Replication chapter — sticky sessions, a consistency token/marker, or routing a user's own post-write reads to the primary are all ways of providing this specific, narrower guarantee without paying for full strong consistency system-wide.

---

# Session Consistency

A closely related, slightly broader guarantee: within one client's session, reads are guaranteed to be monotonic — a client never sees data go "backwards" in time relative to its own prior reads within that same session, even if the underlying replicas are only eventually consistent relative to each other.

```
Within Alice's session:

Read 1: sees comment count = 10
Read 2: MUST see comment count >= 10, never less — even if it's
        served by a different, slightly-behind replica
```

Without this guarantee, a client could read a fresher value from one replica, then get routed to a slightly-behind replica on its very next request and see an *older* value than it already saw — a confusing, backwards-feeling experience even though eventual consistency was technically never violated in the strict sense.

---

# Quorum-Based Tunable Consistency

Rather than committing to one fixed model, some systems let each individual read or write specify how many replicas must participate, directly trading off consistency against latency and availability per-operation.

```
N = total number of replicas
W = number of replicas that must acknowledge a WRITE before it's considered successful
R = number of replicas that must respond to a READ before returning a result

If W + R > N:   every read is guaranteed to overlap with at least
                 one replica that has the most recent write →
                 STRONG consistency

If W + R <= N:  reads and writes might not overlap on any single
                 replica → possible STALE reads, but lower latency
                 and higher availability
```

```
Example: N=3, W=2, R=2  → W+R=4 > N=3 → strongly consistent
Example: N=3, W=1, R=1  → W+R=2 <= N=3 → eventually consistent, faster
```

This is exactly how Cassandra and DynamoDB implement the "tunable" consistency mentioned in the CAP Theorem chapter — a single system, with a single replication topology, letting different queries independently choose a different point on the consistency-latency-availability spectrum based on what that specific read or write actually needs.

---

# Real-World Examples

### Google Spanner — Aiming for Global Strong Consistency

Spanner is a rare, notable case of a system built specifically to provide strong (linearizable) consistency across globally-distributed replicas, using highly synchronized clocks (TrueTime) to establish a reliable global ordering of events — a direct, deliberate rejection of the "strong consistency is too expensive at global scale" assumption most other systems accept, at the cost of specialized infrastructure most companies don't have access to.

---

### DynamoDB and Cassandra — Tunable Per-Query Consistency

Both let a client specify the desired consistency level per request (`ONE`, `QUORUM`, `ALL` in Cassandra; eventually-consistent vs strongly-consistent reads in DynamoDB) — a direct, practical implementation of the quorum-based model above, letting different parts of the same application make different trade-offs.

---

### Social Media Comment Threads

The canonical real-world example of causal consistency mattering in practice — a reply must never be visible before the comment it replies to, even in a system that's only eventually consistent overall for unrelated content across the platform.

---

# Common Interview Questions

## What's the difference between strong and eventual consistency, and what does each cost?

Strong consistency guarantees every read reflects the most recent write, system-wide, at the cost of coordination overhead (and therefore latency and reduced availability during a partition). Eventual consistency guarantees replicas will converge given enough time with no new writes, with no bound on how long that takes, but requires no coordination on the read or write path — much cheaper, much more available, at the cost of readers occasionally seeing stale data.

---

## What is causal consistency, and why is it a useful middle ground?

A guarantee that causally related operations (a reply and the comment it responds to) are seen by everyone in the same order, while unrelated, concurrent operations can be seen in different orders on different nodes without issue. It's useful because most real applications don't actually need strong consistency for every unrelated pair of operations — only for the ones that genuinely depend on each other — so causal consistency captures the guarantee that actually matters without paying for full global coordination.

---

## How do you achieve read-your-writes consistency in an otherwise eventually consistent system?

By giving a specific user's own subsequent reads a way to guarantee they see their own prior writes — routing their post-write reads to the primary, using a consistency token/marker to ensure a replica has caught up past a known point, or sticky-routing a session to the same replica it wrote to. This is a narrower, cheaper guarantee than full strong consistency, since it only needs to hold for a user's own writes relative to their own reads, not for every user relative to every other user's writes.

---

## Explain quorum-based consistency — what does W + R > N actually guarantee?

With N total replicas, requiring W replicas to acknowledge a write and R replicas to respond to a read, W + R > N guarantees that any read quorum and any write quorum must overlap on at least one replica — meaning any read is guaranteed to see the most recent acknowledged write. If W + R ≤ N, no such overlap is guaranteed, and a read can miss the most recent write, trading consistency for lower latency and higher availability.

---

## Why would a single system offer multiple consistency levels instead of picking just one?

Because different operations within the same application genuinely need different points on the trade-off — a financial balance check might need strong consistency, while a "view count" display doesn't. Systems like Cassandra and DynamoDB expose consistency as a per-request choice specifically so an application can make this trade-off deliberately, operation by operation, instead of the whole system being locked into one fixed guarantee for everything.

---

# Common Mistakes

❌ Assuming "eventual consistency" means "eventually, quickly."

There is no bound on how long convergence takes in the general case — treating it as a near-instant guarantee is a common and risky misunderstanding.

---

❌ Reaching for strong consistency everywhere by default, "to be safe."

Strong consistency's coordination cost is real — applying it uniformly, including to data that would tolerate eventual consistency perfectly well, needlessly sacrifices latency and availability for a guarantee much of the system doesn't actually need.

---

❌ Confusing read-your-writes consistency with full strong consistency.

Read-your-writes is a narrower, cheaper, per-user guarantee — it says nothing about what other users see, or how quickly the rest of the system converges.

---

❌ Not distinguishing causally related operations from merely concurrent ones when reasoning about ordering requirements.

Applying strict ordering to genuinely unrelated, concurrent operations wastes coordination effort on a guarantee nobody actually needs — causal consistency exists specifically to avoid this by scoping the ordering requirement to operations that are truly dependent.

---

# Key Takeaways

- Consistency models name specific, deliberate points on the spectrum between strong consistency (every read sees the latest write, expensive) and eventual consistency (replicas converge eventually, with no time bound, but cheap and highly available).
- Causal consistency captures ordering only for operations that are genuinely dependent on each other, letting unrelated concurrent operations be seen in different orders on different nodes without issue — a practical middle ground most real applications actually need.
- Read-your-writes and session consistency are narrower, cheaper, per-client guarantees — solving the specific "did I just see my own write" and "did I just see time go backwards" problems without requiring full system-wide strong consistency.
- Quorum-based tunable consistency (W + R > N for strong, W + R ≤ N for eventual) lets a single system offer different consistency levels per operation, which is exactly how Cassandra and DynamoDB let applications choose the right trade-off per query instead of being locked into one fixed guarantee.
- Choosing a consistency model is choosing exactly how much staleness an application can tolerate in exchange for exactly how much latency and availability it gets back — there's no universally correct choice, only the right one for a given piece of data's actual requirements.
