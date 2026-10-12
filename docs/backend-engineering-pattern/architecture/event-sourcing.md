# Event Sourcing

# Why Does Event Sourcing Exist?

The Event-Driven Architecture chapter in the Message Queues section drew a specific distinction worth revisiting here in full: event-driven architecture is about how services *communicate*; event sourcing is about how a single service stores its **own internal state**. This chapter gives that idea its complete, dedicated treatment.

Traditional state storage keeps only the *current* value — an `UPDATE` overwrites whatever was there before, and the previous state is simply gone, unrecoverable.

```
Traditional storage:

accounts table:  { id: 42, balance: 800 }

↓

balance was 1000, then someone withdrew 200 — but the table only
ever shows 800. The fact that it WAS 1000, and that a withdrawal
of exactly 200 happened, is GONE the moment the UPDATE commits.
```

Event sourcing takes a fundamentally different position: instead of storing current state directly, store **every event that ever changed that state**, as an immutable, append-only log. Current state is *derived*, not stored directly — it's computed by replaying the full history of events.

```
Event-sourced storage:

Event Log:
  AccountOpened(id: 42, initial_balance: 1000)
  MoneyWithdrawn(id: 42, amount: 200)

↓

Current balance = REPLAY these events from the start:
  1000 (opened) → 1000 - 200 (withdrawn) = 800

↓

The event log itself IS the source of truth — not a derived,
cached "current balance" column
```

---

# What This Actually Buys You

## A Complete Audit Trail, for Free

```
"What happened to this account, exactly, in order?"

↓

Just READ the event log — every single state-changing event that
ever occurred is right there, in order, permanently — nothing was
ever overwritten or discarded
```

For financial systems, compliance-heavy domains, or anything where "what exactly happened, and when" genuinely matters as a first-class requirement (not an afterthought), this is an enormous, structural advantage — the audit trail isn't a separate, bolted-on logging system that might miss something; it's the actual, literal source of truth itself.

## Reconstructing State As of Any Point in the Past

```
"What was this account's balance on March 15th, before the
disputed withdrawal?"

↓

Replay only the events that occurred UP TO March 15th — the
answer is directly, precisely computable from the event log,
not something you'd need a separate historical snapshot system
to have anticipated capturing in advance
```

## Deriving New Views You Didn't Anticipate Needing

```
A new reporting requirement appears: "show total withdrawals
per account, per month, for the last two years"

↓

WITHOUT event sourcing:  if this specific aggregation wasn't
                          already being tracked, that historical
                          data may simply not exist anymore

↓

WITH event sourcing:      replay the EXISTING event log through a
                          brand new projection specifically built
                          for this new requirement — the raw
                          historical data was ALWAYS there, in the
                          events themselves, waiting to be
                          projected into whatever new shape is
                          needed later
```

---

# The Real Costs

## Replay Performance — Solved With Snapshots

```
An account that's had 500,000 events over its lifetime

↓

Replaying ALL 500,000 events every single time you need the
current balance is genuinely slow
```

```
Snapshot fix:

Periodically save the DERIVED current state at a point in time
(e.g. every 1,000 events)

↓

To get current state: load the LAST SNAPSHOT, then replay only
the events that happened AFTER it — not from the very beginning
every single time
```

Snapshots are the standard, necessary answer to replay performance — a deliberate optimization that doesn't compromise the event log's role as the actual source of truth (the snapshot is just a cached, derivable acceleration, always reconstructable from the events themselves if it were ever lost).

## Event Schema Evolution — A Genuinely Real Challenge

```
An event recorded 3 years ago:  MoneyWithdrawn(amount: 200)

↓

Today's schema for the SAME event type has evolved to include
a new required field:  MoneyWithdrawn(amount, currency, method)

↓

The OLD event, recorded years ago, doesn't have "currency" or
"method" at all — replaying it today needs a way to correctly
interpret this older-shaped event
```

This is directly analogous to the API Versioning chapter's additive-evolution discipline, applied specifically to events instead of API responses — old event shapes need to remain interpretable indefinitely (often via an "upcasting" step that transforms an old event's shape into the current one on read), which requires real, deliberate discipline from the very start, not an afterthought once the system has already accumulated years of historical events in an old format.

## Genuinely More Complex Than Simple CRUD

Event sourcing is not a default architecture to reach for reflexively — it's a deliberate trade of implementation complexity (replay logic, snapshots, schema evolution discipline) for specific benefits (audit trail, point-in-time reconstruction, flexible future projections) that a large share of ordinary CRUD-shaped domains simply don't need.

---

# The Natural Pairing With CQRS

Event sourcing and CQRS (covered in full in its own chapter) are frequently used together, though neither requires the other. The event log serves naturally as the **write side** in a CQRS architecture — every write is simply a new event appended to the log — while one or more separately-maintained, read-optimized projections are built by replaying (or continuously consuming) those same events. This pairing is natural specifically because event sourcing already produces exactly the kind of durable, replayable stream that CQRS's read-model projections need to be built from.

---

# Real-World Examples

### Banking and Ledger Systems

The most intuitive, natural real-world case — a financial ledger is *inherently* event-sourced in spirit even in traditional accounting practice: you never "edit" a past transaction directly; you record a new, correcting entry. Event sourcing simply formalizes this exact, already-familiar accounting principle as a software architecture.

---

### Git as a Mental Model

A genuinely useful, intuitive analogy — a Git repository's current state (the files you see when you check out a branch) is literally derived by replaying a sequence of immutable commits from the beginning. Nobody edits history directly; every change is a new, appended commit, and "current state" is always just a computed, derived view of that commit history — precisely the event sourcing mental model, in a tool most engineers already understand deeply.

---

### EventStoreDB

A database purpose-built specifically for event sourcing — providing native support for append-only event streams, snapshotting, and projections, rather than adapting a general-purpose relational or document database to this specific access pattern.

---

# Common Interview Questions

## What is event sourcing, and how does it differ from traditional state storage?

Traditional storage keeps only the current state, overwriting previous values on every update — history is lost. Event sourcing stores every state-changing event as an immutable, append-only log, and derives current state by replaying that history — the event log itself is the source of truth, not a cached, derived "current state" table.

---

## What are snapshots, and why are they necessary?

A periodically saved copy of the derived current state at a point in time, so replaying doesn't need to start from the very beginning of an event log every single time — only from the last snapshot forward. They're necessary because replaying a very long event history from scratch on every read would otherwise become genuinely, unacceptably slow as the log grows.

---

## How do you handle event schema evolution over time?

With the same additive-evolution discipline covered in the API Versioning chapter, applied to events — old event shapes need to remain correctly interpretable indefinitely, often via an "upcasting" step that transforms an older event's shape into the current one when it's read and replayed, planned for deliberately from the start rather than discovered as a problem years later.

---

## When would you NOT use event sourcing?

For a genuinely simple, CRUD-shaped domain that doesn't actually need a complete audit trail, point-in-time historical reconstruction, or the flexibility to derive new projections from historical data later. The added implementation complexity — replay logic, snapshotting, schema evolution discipline — isn't worth paying for a domain that doesn't need those specific benefits.

---

## How does event sourcing relate to CQRS — are they the same thing?

No, and neither requires the other — but they pair naturally. Event sourcing's append-only event log serves as a ready-made write side, and separate, read-optimized projections (CQRS's read models) can be built by replaying or continuously consuming those same events, which is exactly why the two are so frequently seen together in practice, even though each can exist entirely independently of the other.

---

# Common Mistakes

❌ Adopting event sourcing for a domain that doesn't actually need an audit trail or historical replay, purely for its own sake.

Adds real implementation complexity (replay logic, snapshotting, schema evolution) without a genuine corresponding benefit for a domain that would be perfectly well served by simple, direct state storage.

---

❌ Not planning for event schema evolution from the very start.

Leads to an inability to correctly interpret old events once the schema inevitably changes years later, a much harder problem to retrofit after years of events have already accumulated in the old format.

---

❌ Not implementing snapshots.

Causes replay time to grow unboundedly as event history accumulates, eventually making even a simple "get current state" read genuinely, unacceptably slow.

---

# Key Takeaways

- Event sourcing stores every state-changing event as an immutable, append-only log, deriving current state by replaying that history — the event log itself is the source of truth, not a cached "current state" table.
- It provides a complete audit trail for free, the ability to reconstruct state as of any past point in time, and the flexibility to derive entirely new projections from existing historical events later, without needing to have anticipated that need in advance.
- Snapshots solve the real performance cost of replaying a very long event history, letting replay start from the last snapshot forward rather than from the beginning every time.
- Event schema evolution requires the same additive-evolution discipline as API versioning, applied to events — planned for from the start, since old events need to remain interpretable indefinitely.
- Event sourcing and CQRS pair naturally (the event log as the write side, projections as read models) but are genuinely independent concepts — neither requires the other.
