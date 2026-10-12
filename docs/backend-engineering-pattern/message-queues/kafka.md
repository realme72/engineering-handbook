# Kafka

# Why Does Kafka Exist?

LinkedIn built Kafka in 2011 because their existing messaging setup — traditional queues like ActiveMQ — couldn't keep up with one very specific problem: every user action on the site, a page view, a click, a profile update, generated an event, and LinkedIn needed to move that firehose to dozens of downstream systems (search indexing, recommendations, monitoring, analytics) reliably, at a volume those queues just weren't built for.

The deeper mismatch wasn't throughput — it was the model itself. A traditional queue's core assumption is that a message gets delivered, a consumer processes it, and it's gone.

```
Traditional Queue:

Message arrives → Consumer processes it → Message is REMOVED

↓

If a SECOND, independent system also needs that same message later,
too bad — it's already gone.
```

Fine if there's one consumer. LinkedIn had many independent systems that each needed the *same* stream of activity events, on their own schedule, sometimes wanting to reprocess history entirely — rebuilding a search index from scratch, backfilling a pipeline that didn't even exist when the original events happened.

Kafka's answer: stop treating messages as disposable, one-time-use items. Treat the whole stream as a durable, replayable log instead.

```
Kafka:

Message arrives → APPENDED to a durable log → stays for a configured
                                                retention period, REGARDLESS
                                                of who has or hasn't
                                                consumed it yet

↓

Any number of independent consumers can read through the same log,
at their own pace, including reading from the very beginning if needed
```

---

# The Core Abstraction: The Log

Everything about Kafka follows from one data structure: an append-only, ordered sequence of records.

```
Partition (a log):

[0] [1] [2] [3] [4] [5] [6] ...
 ↑                        ↑
first record          most recent record
(oldest)               (newest)
```

New records only ever get appended to the end — nothing inserted in the middle, nothing deleted on read. A consumer doesn't "remove" a message by reading it; it just tracks how far through the log it's gotten. That single detail is the most important thing in this chapter, and everything below builds on it.

---

# Topics and Partitions

A **topic** is a named stream of events (`order_events`, `page_views`). Underneath, it's split into multiple **partitions**, each its own independent, strictly-ordered log.

```
Topic: order_events

Partition 0: [msg][msg][msg][msg]
Partition 1: [msg][msg][msg]
Partition 2: [msg][msg][msg][msg][msg]
```

This is the "ordering scoped to a key" idea from Messaging Fundamentals, made concrete. Kafka guarantees strict ordering *within* a partition and makes no guarantee at all *across* partitions of the same topic.

```python
producer.send("order_events", key="order_42", value=event_data)
```

```
partition = hash(key) % num_partitions
```

A message's key decides its partition by default — every event for `order_42` lands on the same partition, in the order sent, so that one order stays strictly ordered. `order_43` might land on a different partition entirely and has no ordering relationship to `order_42` at all. That's fine — nothing needed it to.

---

# Consumer Groups — Combining Both Messaging Models at Once

Probably the single concept most likely to come up as a "walk me through this" interview question, because it quietly does two things at once: point-to-point and pub/sub, depending on which axis you look at.

```
Topic: order_events (3 partitions)

Consumer Group "email-service":     Consumer Group "analytics-service":
  Consumer A → Partition 0             Consumer X → Partition 0
  Consumer B → Partition 1             Consumer X → Partition 1
  Consumer C → Partition 2             Consumer X → Partition 2
```

```
WITHIN one consumer group:   each partition is read by exactly ONE consumer
                              in that group → this is competing consumers
                              (point-to-point) — work is DISTRIBUTED

ACROSS different consumer groups:  every group gets its OWN full copy
                                     of the entire topic, independently
                                     → this is pub/sub — the same events
                                     are BROADCAST to every group
```

The email service's group and the analytics service's group each read the *entire* topic independently, at their own pace, with their own tracked position — the same multiple-independent-subscribers pattern from the checkout example in Fundamentals. But inside the email service's own group, if it's running 3 consumers across 3 partitions, each message still only gets processed once by that group. That's competing consumers doing its job.

## What Happens When a Consumer Joins or Leaves a Group

```
Consumer Group "email-service" has 3 consumers, 3 partitions (1:1 mapping)

↓

A 4th consumer joins

↓

REBALANCE: partitions are reassigned among all 4 consumers
```

A rebalance briefly pauses consumption while partitions get reassigned. Worth taking seriously, not treating as an implementation footnote: a group with more consumers than partitions leaves some consumers sitting completely idle (only one consumer per group can actively read a given partition), and rebalances themselves cost real, measurable pause time — a genuine concern in high-throughput systems.

---

# Offsets — How Kafka Tracks "What's Been Read" Without Deleting Anything

Since nothing gets removed on consumption, Kafka needs a separate way to track where each consumer group has gotten to.

```
Partition 0:  [0] [1] [2] [3] [4] [5] [6] [7]
                              ↑
              email-service group's committed offset = 4
              (meaning: everything through index 4 has been processed)
```

```python
for message in consumer:
    process(message)
    consumer.commit()  # advances this group's tracked offset
```

This one mechanism is what makes replay possible — something a delete-on-consume queue simply can't offer. Reset a group's offset back to an earlier point, or all the way to the start, and it reprocesses history from there: useful for backfilling a brand-new downstream system, recovering from a bug that corrupted a window of processing, or rebuilding a derived data store from scratch.

```
Reset offset to 0  →  consumer group re-reads the ENTIRE topic from the start,
                       exactly as if it were the very first time
```

---

# Retention — Why Old Messages Don't Just Disappear

```
Topic configured with: retention.ms = 7 days   (or retention.bytes = some size cap)

↓

Messages stay available for up to 7 days, REGARDLESS of whether every
consumer group has read them yet
```

Deliberate design, not an oversight — retention is what makes replay meaningful in the first place. Delete a message the instant one group reads it, and the whole "many independent groups reading at their own pace" model falls apart. The trade-off is disk: a high-volume topic with a long retention window needs space proportional to volume times retention period, not just "however much is currently unread."

---

# Replication — Reusing the Replication Chapter's Concepts, Applied to Kafka

Each partition replicates across multiple brokers — one **leader** handling all reads and writes for that partition, and one or more **followers** replicating from it. Same primary-replica model from the Replication chapter, just applied per-partition.

```
Partition 0:  Leader (Broker 1)  →  replicates to  →  Follower (Broker 2), Follower (Broker 3)
```

```
ISR (In-Sync Replicas):  the set of followers that are currently
                          caught up closely enough with the leader
                          to be considered safe to promote if the
                          leader fails
```

If the leader broker dies, a new one gets elected from the ISR — the same failover idea from Replication, at the partition level. Which is also why a partition with no followers has zero redundancy: lose that one broker, and the data's gone until it comes back.

---

# Why Kafka Achieves Such High Throughput

```
Sequential disk writes    →  appending to the end of a log is a sequential
                              write, which is dramatically faster than the
                              random-access reads/writes a traditional
                              queue's "remove after read" model requires

Zero-copy transfer         →  Kafka can send data from disk to the network
                              socket without copying it through application
                              memory in between, reducing CPU overhead
                              significantly at high volume

Batching                    →  producers and consumers both batch multiple
                                messages into a single network round trip,
                                instead of one round trip per message
```

None of this is a special trick — it's just the natural consequence of an append-only log instead of a mutable queue that has to support random-access removal. That's the whole reason Kafka's throughput profile looks so different from a traditional broker's.

---

# Kafka's "Exactly-Once Semantics" (EOS)

From Messaging Fundamentals: true exactly-once delivery is hard, and what actually gets delivered in most systems is at-least-once plus idempotency. Kafka's EOS is a stricter version of the same idea, scoped to Kafka-to-Kafka pipelines — read from a topic, process, write to another topic.

```
Idempotent Producer:  each producer gets a unique ID and tags every message
                       with a sequence number — if a network issue causes
                       the producer to retry sending the SAME message,
                       the broker recognizes the duplicate sequence number
                       and discards it instead of writing it twice

Transactions:          a read-process-write cycle across multiple partitions
                        (or topics) can be committed as a single atomic unit —
                        either the consumed offset AND the produced output
                        both commit together, or neither does
```

This solves exactly-once for the case where both the input and the output stay inside Kafka. It doesn't — can't — extend to an arbitrary external side effect like charging a card or calling a third-party API. That's still the idempotent consumer's job, same as Messaging Fundamentals covers.

---

# Real-World Examples

### LinkedIn (Origin)

Kafka's original use case — moving a continuous stream of user activity to dozens of independent downstream consumers (search, recommendations, monitoring), each needing its own pace and, sometimes, the ability to replay history.

---

### Uber's Trip Event Pipeline

The exact scenario from Messaging Fundamentals — trip events (`requested`, `driver_assigned`, `trip_completed`) partitioned by `trip_id`, so any one trip's lifecycle stays strictly ordered while different trips process fully in parallel, consumed independently by pricing, the rider app, the driver app, and analytics as separate consumer groups.

---

### Netflix

Runs Kafka as the backbone of its real-time monitoring and event pipeline infrastructure, at a volume a traditional delete-on-consume queue would genuinely struggle to sustain.

---

# Common Interview Questions

## Why does Kafka use partitions, and what's the ordering guarantee?

Partitions are Kafka's mechanism for parallelism — a topic split into multiple independent, strictly-ordered logs. Ordering holds within a partition, never across partitions of the same topic. Messages are typically routed by key, so events for the same logical entity land on the same partition and stay ordered relative to each other.

---

## Explain how a consumer group works.

Within one group, each partition is consumed by exactly one consumer at a time — competing consumers, work distribution. Different groups each get their own independent, full copy of the topic — pub/sub, broadcast. One topic can serve many independent groups this way, each reading at its own pace with its own tracked offset.

---

## How does Kafka know what a consumer has already processed, if messages aren't deleted on read?

Each consumer group tracks a committed offset per partition — a marker for how far through that partition's log it's read. Completely separate from the messages themselves, which stick around per the topic's retention policy no matter who's read them. That separation is exactly what makes replay — resetting a group's offset backward — possible.

---

## Why does Kafka achieve such high throughput compared to a traditional message queue?

Its core structure is an append-only log, which gets you sequential (not random-access) disk writes, zero-copy transfer from disk to network, and batching of many messages per round trip — all direct consequences of not needing to support removing an arbitrary message after consumption, which a traditional queue's model requires.

---

## What does Kafka's "exactly-once semantics" actually guarantee?

An idempotent producer (deduplicating retried sends via sequence number) plus transactional commits tying together offset consumption and output production, scoped to Kafka-to-Kafka pipelines. It doesn't extend to an arbitrary external side effect outside Kafka — for that you still need an idempotent consumer, same idea as Messaging Fundamentals, just not something Kafka gives you automatically.

---

# Common Mistakes

❌ Assuming Kafka guarantees ordering across an entire topic.

Ordering only holds within a single partition — messages across different partitions of the same topic have no ordering relationship at all.

---

❌ Choosing a partition key that creates a hot partition.

The same hot-shard problem from the Sharding chapter, just applied to Kafka. If one key's traffic dwarfs the others, that single partition (and its one consumer per group) becomes a bottleneck no amount of adding consumers can fix, since only one consumer per group can ever read a given partition at a time.

---

❌ Under-provisioning the number of partitions upfront.

Partition count is a hard ceiling on how many consumers within one group can ever work in parallel — 3 partitions means never more than 3 actively-consuming instances per group, no matter how many you add.

---

❌ Treating Kafka's exactly-once semantics as covering arbitrary external side effects.

EOS solves exactly-once for Kafka-to-Kafka read-process-write pipelines specifically — a database write or an API call outside Kafka still needs its own idempotency handling.

---

# Key Takeaways

- Kafka's core design choice — treating messages as a durable, replayable log instead of a disposable, delete-on-consume queue — is what lets multiple independent consumer groups each read the same stream at their own pace, replay included.
- Partitions are Kafka's unit of both parallelism and ordering: strict order within a partition, none across partitions, with a message's key typically deciding which partition it lands on.
- Consumer groups run both messaging models from Fundamentals at once — competing consumers within a group, pub/sub across groups.
- Offsets, not deletion, are how Kafka tracks a group's progress through a partition — exactly what makes replay possible.
- High throughput comes straight from the log's append-only structure: sequential writes, zero-copy transfer, batching — advantages a random-access queue model can't offer as naturally.
- Kafka's exactly-once semantics (idempotent producer + transactions) solve exactly-once for Kafka-to-Kafka pipelines specifically — external side effects still need an idempotent consumer.
