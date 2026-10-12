# Two-Phase Commit (2PC)

# Why Does Two-Phase Commit Exist?

The Transactions chapter's gap — no native atomic transaction spans multiple independent databases — has two fundamentally different answers, and this chapter covers the other one. The Saga pattern accepts eventual consistency and visible intermediate states in exchange for never blocking. Two-Phase Commit takes the opposite position: it tries to provide genuine, strong atomicity across multiple participants — all commit, or all abort, with no visible in-between state — at the direct cost of participants having to wait, blocked, for a coordinator's final decision.

```
Coordinator needs Database A and Database B to EITHER both commit
a transaction, or both abort it — never one committed and the other not
```

---

# The Two Phases

## Phase 1: Prepare (Voting)

```
Coordinator → Database A: "Can you commit this transaction?"
Coordinator → Database B: "Can you commit this transaction?"

↓

Database A: locks the relevant rows, writes the change to its own
             log (but does NOT actually commit yet) → replies "YES"

Database B: same → replies "YES"

(if EITHER replies "NO" — a constraint violation, a lock conflict —
 the coordinator will abort the whole transaction in Phase 2)
```

Each participant does everything necessary to *guarantee* it can commit if told to — writing the change durably to its own log, holding locks on the affected rows — without actually making it visible yet. This is the crucial property: once a participant votes "yes," it must be able to commit later, no matter what, even across its own crash and restart.

## Phase 2: Commit (or Abort)

```
Coordinator received YES from every participant

↓

Coordinator → Database A: "COMMIT"
Coordinator → Database B: "COMMIT"

↓

Both databases make the change visible, release their locks
```

```
If ANY participant had voted NO:

Coordinator → every participant: "ABORT"

↓

Every participant discards its prepared change, releases locks
```

Only after every single participant has confirmed it *can* commit does the coordinator instruct everyone to actually do so — this is what gives 2PC its strong, all-or-nothing guarantee, unlike a Saga's sequence of already-committed local transactions with compensations layered on top.

---

# The Blocking Problem

This is 2PC's most significant, most commonly cited weakness, and the reason it's rarely used in modern microservices architectures at real scale.

```
Coordinator sends Prepare → both participants vote YES

↓

Coordinator CRASHES before sending the final Commit/Abort decision

↓

Database A and Database B are now STUCK — they've voted yes, locked
their rows, and are waiting for a final instruction that will never
come until the coordinator recovers

↓

Neither participant can safely decide on its own whether to commit
or abort — committing without confirmation risks the OTHER participant
having independently aborted (or never having existed), and vice versa
```

Every row locked as part of the prepared transaction stays locked — blocking any other transaction that needs those same rows — for however long the coordinator takes to recover. This is fundamentally different from a Saga's failure mode: a Saga's already-completed local transactions have already committed and released their locks; a stuck 2PC transaction holds locks indefinitely across a coordinator outage.

## Why This Matters for CAP

2PC is inherently CP-leaning, and for the same structural reason as Consensus: it requires every participant to be reachable and to wait for agreement before proceeding — during a coordinator failure or network partition, the system doesn't gracefully degrade, it blocks.

---

# 2PC vs Saga — The Direct Comparison

| | Two-Phase Commit | Saga |
|---|---|---|
| Consistency | Strong — no visible intermediate state | Eventual — intermediate states ARE visible |
| Failure behavior | Blocks (locks held) until coordinator recovers | Compensates forward, never blocks indefinitely |
| Coupling | Tight — every participant must be available and wait | Loose — each step commits independently |
| Undo mechanism | Abort (nothing was ever truly committed) | Compensating transaction (undoes an already-committed effect) |
| Scale/microservices fit | Poor — locks held across services is expensive and fragile | Common default for cross-service business processes |

The practical industry answer: 2PC works reasonably well within a single, tightly-coupled system (a database's own internal distributed transaction coordinator across its own shards, for instance) where participants are trusted and highly available to each other. It becomes a liability across independently-owned, independently-scaled microservices — the blocking behavior means one service's slow coordinator or crash can hold another service's rows locked, reintroducing exactly the tight coupling microservices architectures are usually trying to avoid, which is precisely why Sagas dominate that specific use case instead.

---

# Real-World Examples

### XA Transactions

The classic, standardized implementation of 2PC across heterogeneous resources (a relational database and a JMS message queue, for instance, committed together as one XA transaction) — historically used in enterprise Java systems, but its blocking behavior and tight coordination requirements are exactly why it's fallen out of favor as systems have moved toward independently-deployed microservices.

---

### Distributed Databases' Internal Cross-Shard Transactions

Some distributed databases (CockroachDB, Spanner) use 2PC-like protocols internally to commit a transaction spanning multiple shards it owns and controls directly — a meaningfully different situation than 2PC across independently-owned microservices, since the database itself controls all participants' behavior and availability, mitigating (though not eliminating) the blocking concern.

---

### Why Microservices Architectures Favor Sagas Instead

The direct, practical reason this pattern appears repeatedly throughout this handbook (Transactions, Sharding, Event-Driven Architecture, Saga Pattern) — 2PC's requirement that every participant stay available and block until a coordinator's final decision is exactly the kind of tight coupling a microservices architecture is usually designed to avoid in the first place.

---

# Common Interview Questions

## Explain how Two-Phase Commit works.

In the Prepare phase, a coordinator asks every participant if it can commit; each participant locks the relevant resources, durably records the pending change, and votes yes or no, without actually committing yet. In the Commit phase, if every participant voted yes, the coordinator instructs all of them to commit; if any voted no, it instructs all of them to abort — giving a genuine all-or-nothing guarantee across every participant.

---

## What is the blocking problem in 2PC, and why is it considered a serious weakness?

If the coordinator crashes after participants have voted yes but before sending the final commit or abort instruction, every participant is stuck holding its locks indefinitely, unable to safely decide on its own whether to proceed — committing without confirmation risks disagreeing with participants that independently aborted, and there's no safe default. This can block unrelated transactions needing the same locked resources for however long the coordinator takes to recover.

---

## 2PC vs Saga — when would you choose each?

2PC when you need genuine, strong atomicity with no visible intermediate state, and participants are tightly coupled, trusted, and highly available to each other (often within a single system's own internal cross-shard coordination). Saga when coordinating across independently-owned, independently-scaled microservices, where 2PC's blocking behavior and tight coupling requirements would reintroduce exactly the coupling a service-oriented architecture is trying to avoid — accepting eventual consistency and visible intermediate states in exchange for never blocking indefinitely.

---

## Why isn't 2PC popular in modern microservices architectures?

Because it requires every participant to remain available and to hold locks while waiting for the coordinator's final decision — a single slow or crashed coordinator can block every participant's resources indefinitely. This tight coordination requirement runs directly against the loose coupling and independent availability microservices architectures are typically designed around, which is why Sagas are the far more common choice for cross-service business processes at that scale.

---

# Common Mistakes

❌ Assuming 2PC works well at internet/microservices scale.

Its blocking behavior under coordinator failure reintroduces tight coupling between services that are supposed to be independently deployable and available — a structural mismatch with typical microservices architecture goals, not just a minor performance concern.

---

❌ Not recognizing coordinator failure as 2PC's central weakness.

The Prepare/Commit phases themselves work correctly — the actual risk is entirely in what happens if the coordinator disappears between phases, leaving every participant blocked with no safe way to proceed independently.

---

❌ Treating "strong consistency" as an unconditionally better choice than a Saga's eventual consistency.

2PC's stronger guarantee comes with real costs (blocking, tight coupling) that a Saga's eventual consistency and compensating transactions specifically avoid — the right choice depends on whether the participants are tightly or loosely coupled, not on which guarantee sounds theoretically stronger.

---

# Key Takeaways

- Two-Phase Commit provides genuine, strong atomicity across multiple participants — a Prepare phase where every participant votes, followed by a Commit or Abort phase applied uniformly — with no visible intermediate state, unlike a Saga.
- Its central weakness is the blocking problem: if the coordinator crashes after participants vote yes but before the final decision, every participant is stuck holding locks indefinitely, unable to safely proceed on its own.
- 2PC is inherently CP-leaning, requiring every participant to be reachable and to wait for agreement — it doesn't gracefully degrade during a coordinator failure or partition, it blocks.
- 2PC suits tightly-coupled, trusted participants under one system's control (a database's own internal cross-shard transactions); Sagas suit independently-owned, independently-scaled microservices, which is exactly why Sagas dominate that use case in practice.
- The choice between 2PC and Saga is a real trade-off between strong consistency with blocking risk, and eventual consistency with visible intermediate states — not a question of which is unconditionally better.
