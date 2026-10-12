# Transactional Outbox Pattern

# Why Does This Pattern Exist?

A service handling an order needs to do two things: save the order to its own database, and publish an `OrderCreated` event so other services (payment, inventory) find out about it. These are two entirely separate operations against two entirely separate systems — a database and a message broker — and there's no native way to wrap both in one atomic transaction.

```
def create_order(order_data):
    db.save(order_data)                    # operation 1: the database
    broker.publish("OrderCreated", order_data)  # operation 2: the message broker

↓

What if the process crashes between these two lines?
```

```
Crash AFTER db.save() but BEFORE broker.publish():

↓

The order EXISTS in the database.
The event was NEVER published.

↓

Every downstream service (payment, inventory) that should have
reacted to this order NEVER FINDS OUT IT EXISTS.
```

```
Crash AFTER broker.publish() but BEFORE db.save() commits
(or the DB write itself fails for an unrelated reason):

↓

Downstream services react to an order that DOESN'T ACTUALLY EXIST
in the source-of-truth database.
```

This is the **dual-write problem** — writing to two independent systems that can't share a single atomic transaction, with no way to guarantee both succeed or both fail together. It's exactly the same underlying gap the Transactions and Saga Pattern chapters describe, applied specifically to the extremely common case of "update my database and publish an event about it."

---

# The Solution: Write the Event Into the Same Database Transaction

Instead of publishing directly to the broker as a separate operation, write the event as a row in an **outbox table** — inside the exact same local database transaction as the actual business data change.

```sql
BEGIN;

INSERT INTO orders (id, customer_id, status) VALUES (42, 7, 'created');

INSERT INTO outbox (id, event_type, payload, published)
VALUES (gen_random_uuid(), 'OrderCreated', '{"order_id": 42, ...}', false);

COMMIT;
```

Both inserts are now part of one ordinary database transaction — the exact atomicity guarantee from the Transactions chapter applies directly: either both rows are committed together, or neither is. There's no longer any window where the order exists without a corresponding outbox record, or vice versa, because they're not two separate operations against two separate systems anymore — they're two rows in the same local transaction.

```
Business Table              Outbox Table

orders                        outbox
├── id: 42                   ├── id: ...
├── customer_id: 7           ├── event_type: OrderCreated
└── status: created          ├── payload: {...}
                              └── published: false

    ↑ BOTH committed together, atomically, or neither is ↑
```

---

# The Message Relay — Getting the Event From the Outbox to the Broker

Writing the event into the outbox table doesn't publish it anywhere yet — a separate process (the **relay**) is responsible for reading unpublished outbox rows and actually sending them to the message broker.

## Polling Publisher

```python
def relay_loop():
    while True:
        unpublished = db.query(
            "SELECT * FROM outbox WHERE published = false ORDER BY id LIMIT 100"
        )
        for row in unpublished:
            broker.publish(row.event_type, row.payload)
            db.execute("UPDATE outbox SET published = true WHERE id = %s", (row.id,))
        time.sleep(1)
```

A background job periodically checks for new, unpublished outbox rows and sends them, marking each as published only *after* a confirmed successful publish — the same "process, then mark, atomically committed correctly" ordering principle from the Idempotent Consumers chapter, applied here on the sending side instead of the consuming side.

## Change Data Capture (CDC)

Rather than a hand-written polling loop, a CDC tool reads the database's own replication log directly — the exact WAL/binlog mechanism from the Replication chapter, and the same mechanism Facebook's approach to cache invalidation relies on.

```
Database's replication log (WAL / binlog)

↓

CDC tool (e.g. Debezium) reads the log directly, notices a new row
was inserted into the `outbox` table

↓

Automatically publishes it to Kafka — no application polling code
needed at all
```

This is a meaningfully more elegant version of the same idea: the database was already producing a durable, ordered log of every change for its own replication purposes; CDC just taps into that existing log instead of requiring the application to implement its own separate polling mechanism, and it naturally captures every committed outbox row with no risk of a polling loop missing one due to a bug or timing gap.

---

# The Guarantee: At-Least-Once, Not Exactly-Once

Worth stating precisely, tying directly back to Messaging Fundamentals: the outbox pattern guarantees the event will **eventually** be published if the local transaction committed — but it doesn't guarantee it's published exactly once.

```
Relay publishes the event successfully

↓

Relay CRASHES before marking the outbox row as published

↓

Relay restarts, sees the row is still marked "unpublished"

↓

Publishes it AGAIN — a duplicate
```

This means every consumer of an outbox-originated event still needs to be an **idempotent consumer**, exactly as covered in that chapter — the outbox pattern solves the dual-write atomicity problem on the *producing* side, but it doesn't eliminate the need for idempotency on the *consuming* side. These two patterns are complementary, not substitutes for each other.

---

# Real-World Examples

### Debezium

The most widely used open-source CDC tool for implementing this pattern in production — it reads MySQL's binlog or Postgres's WAL directly and turns captured row changes (including inserts into an outbox table) into Kafka events automatically, without requiring any custom polling code in the application itself.

---

### Microservices Order/Payment Flows

The exact motivating scenario throughout this chapter — an Order Service needing to atomically record an order and notify Payment and Inventory services about it is one of the most common, practical reasons the outbox pattern gets adopted in real microservices architectures, since the alternative (a direct, unguarded dual-write) is a routine source of silent data-loss bugs.

---

### Event Sourcing–Adjacent Systems

Systems that already treat "what happened" as a first-class, durable record (closely related to, but distinct from, full event sourcing, as noted in the Event-Driven Architecture chapter) often use an outbox-like table as the natural place that record lives, with the relay/CDC layer simply being the mechanism that projects it outward to other services.

---

# Common Interview Questions

## What is the dual-write problem, and why can't you just write to the database and publish to the broker in sequence?

Writing to a database and publishing to a message broker are two independent operations against two independent systems, with no shared transaction spanning both. A crash or failure between the two operations leaves them out of sync — the database write succeeded with no corresponding event ever published, or an event published for a database write that never actually committed.

---

## How does the transactional outbox pattern solve the dual-write problem?

By writing the event as a row in an outbox table inside the same local database transaction as the actual business data change — since both are now part of one ordinary database transaction, they commit or roll back together atomically. A separate relay process (polling, or CDC reading the database's replication log) is then responsible for actually publishing outbox rows to the broker afterward.

---

## Polling publisher vs CDC — what's the trade-off?

A polling publisher is simpler to implement (a background job querying for unpublished rows) but requires custom application code and a polling interval that trades latency against database load. CDC (reading the database's own replication log directly) requires additional infrastructure (Debezium and its connection to the database) but needs no custom polling code and naturally captures every committed change with no risk of a polling bug missing a row.

---

## Does the transactional outbox pattern guarantee exactly-once event delivery?

No — it guarantees at-least-once delivery. The relay can crash after successfully publishing an event but before marking the outbox row as published, causing it to republish the same event on restart. Consumers of outbox-originated events still need to be idempotent, exactly as described in the Idempotent Consumers chapter — the outbox pattern solves atomicity on the producing side, not deduplication on the consuming side.

---

## Why is CDC often considered a more elegant relay mechanism than polling?

Because the database is already producing a durable, ordered log of every committed change for its own replication purposes — CDC taps directly into that existing mechanism instead of requiring a separately-implemented, separately-maintained polling loop, and naturally avoids any risk of a polling bug or timing gap missing a committed outbox row.

---

# Common Mistakes

❌ Writing directly to a message broker in the same code path as a database write, with no shared transaction.

This is the dual-write problem itself — a crash between the two operations leaves the database and the message stream out of sync, with no way to recover automatically.

---

❌ Assuming the outbox pattern eliminates the need for idempotent consumers.

The relay's own publish-then-mark-as-sent sequence can itself produce duplicate publishes on a crash — the outbox pattern guarantees at-least-once delivery, not exactly-once, so consumers still need to handle duplicates.

---

❌ Letting the outbox table grow unbounded with no cleanup of already-published rows.

Published rows serve no further purpose once confirmed sent — a real production outbox implementation needs a retention/cleanup strategy, the same underlying concern as any table accumulating rows indefinitely.

---

❌ Using a polling interval that's too slow for the application's latency requirements.

A polling-based relay introduces real latency between the local transaction committing and the event actually reaching the broker — CDC-based relay largely avoids this, since it reacts to the replication log directly rather than waiting for the next poll cycle.

---

# Key Takeaways

- The dual-write problem — writing to a database and publishing to a message broker as two independent, non-atomic operations — is a routine source of silent data-loss bugs, not a rare edge case.
- The transactional outbox pattern solves this by writing the event as a row in the same local database transaction as the actual business data change, giving genuine atomicity via the database's own transaction guarantee.
- A separate relay process — either a polling publisher or a CDC tool reading the database's replication log directly — is responsible for actually delivering outbox rows to the message broker afterward.
- The pattern guarantees at-least-once event delivery, not exactly-once — consumers of outbox-originated events still need to be idempotent, exactly as covered in the Idempotent Consumers chapter.
- CDC (Debezium reading a database's WAL or binlog directly) is generally the more elegant relay mechanism, avoiding custom polling code and the risk of a polling loop missing a committed change.
