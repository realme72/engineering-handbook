# Amazon SQS

# Why Does SQS Exist?

Kafka and RabbitMQ are both systems you have to run: provision brokers, manage disk, handle replication and failover, patch and upgrade, plan capacity. That's a real, ongoing cost — and for a lot of real messaging needs ("reliably get this task from service A to service B"), it's more infrastructure than the problem actually calls for.

SQS is AWS's answer: a fully managed queue, no servers to run, no cluster to operate, scales automatically, and charges per message instead of per always-on broker. You call an API; AWS handles everything underneath.

```
Self-hosted (Kafka/RabbitMQ):   you manage brokers, disks, replication,
                                 scaling, patching, monitoring, failover

SQS:                             you call SendMessage / ReceiveMessage —
                                 AWS handles everything else
```

The trade-off for that simplicity is flexibility — no rich exchange-based routing like RabbitMQ, no native replay-a-log capability like Kafka. SQS solves a narrower problem, but solves it well: a durable, managed queue with at-least-once delivery (or, in FIFO mode, effectively-exactly-once).

---

# Standard Queue vs FIFO Queue

## Standard Queue

```
Delivery:    at-least-once  (a message might occasionally be delivered
                              more than once — the standard guarantee
                              from Messaging Fundamentals)

Ordering:    best-effort — NOT guaranteed. Messages are generally
             delivered in the order sent, but not reliably so.

Throughput:  effectively unlimited
```

The default, high-throughput option — right whenever strict ordering isn't a real requirement and the consumer is idempotent, which it should be anyway under at-least-once delivery.

## FIFO Queue

```
Delivery:    exactly-once PROCESSING (via deduplication — see below)

Ordering:    strict, WITHIN a message group

Throughput:  capped — 300 messages/sec by default (3,000/sec with
             batching), notably lower than a standard queue
```

```python
sqs.send_message(
    QueueUrl=queue_url,
    MessageBody=json.dumps(event),
    MessageGroupId="order_42",              # scopes ordering — same concept as Kafka's partition key
    MessageDeduplicationId="event_abc123",  # scopes deduplication
)
```

`MessageGroupId` is the same "ordering scoped to a key" idea as Kafka's partition key — order holds strictly within one group ID, different group IDs process independently with no relationship between them. It's the same fix for the ordering-vs-parallelism tension: full parallelism across groups, strict order within each.

---

# Visibility Timeout — SQS's Core Mechanism, and Its Answer to "What Counts as an Ack"

The single most important SQS-specific concept, and genuinely different from RabbitMQ's persistent-connection acknowledgment model.

SQS has no persistent connection between consumer and broker the way RabbitMQ does — consumers *poll* via an API call. So how does it know whether a message was actually processed, versus the consumer having crashed?

```
Consumer calls ReceiveMessage

↓

Message becomes INVISIBLE to every other consumer for the
visibility timeout duration (e.g. 30 seconds) — but is NOT deleted

↓

Consumer processes the message

↓

Consumer calls DeleteMessage  →  message is permanently removed

                                  ↓ (if DeleteMessage is NEVER called —
                                     the consumer crashed, or processing
                                     took longer than the timeout)

                              Visibility timeout expires

                              ↓

                              Message becomes VISIBLE again →
                              redelivered to another ReceiveMessage call
```

`DeleteMessage` is SQS's version of an acknowledgment — the explicit signal that processing genuinely finished. The visibility timeout is what makes redelivery happen on a crash automatically, with no persistent connection needed: if nobody confirms within the window, something went wrong, so make it available again.

## Getting the Timeout Wrong in Either Direction

```
Timeout TOO SHORT:   consumer is still legitimately processing when the
                      timeout expires → message becomes visible again →
                      a SECOND consumer picks it up and processes it too
                      → duplicate processing, even though the first
                      consumer was actually still working correctly

Timeout TOO LONG:     if a consumer genuinely crashes, the message sits
                      invisible and unprocessed for the entire timeout
                      duration before anyone else can pick it up —
                      a real, direct delay in recovering from failure
```

```python
# extend the visibility timeout if processing is taking longer than expected
sqs.change_message_visibility(
    QueueUrl=queue_url,
    ReceiptHandle=receipt_handle,
    VisibilityTimeout=60,  # buy more time without waiting for redelivery
)
```

This value needs deliberate tuning — based on realistic worst-case processing time, with `ChangeMessageVisibility` as an escape hatch for the occasional slow run — not a default left untouched.

---

# Long Polling vs Short Polling

```
Short Polling:   ReceiveMessage returns IMMEDIATELY, even if no message
                 is currently available — can also miss a message that's
                 present on a different backend partition SQS happened
                 to check, wasting API calls on empty responses

Long Polling:    ReceiveMessage WAITS (up to 20 seconds, WaitTimeSeconds)
                 for a message to become available before returning empty
```

```python
sqs.receive_message(
    QueueUrl=queue_url,
    WaitTimeSeconds=20,  # long polling — wait for a message instead of returning immediately
)
```

Long polling is close to a free upgrade for most real use cases — fewer wasted empty API calls (which matters, since SQS bills per request), and a better shot at actually finding a message on the first try. The cost is a consumer occasionally waiting up to the configured timeout when the queue is genuinely empty.

---

# Deduplication in FIFO Queues

```
Content-based deduplication:  SQS hashes the message body itself to
                               detect duplicates — no explicit ID needed

Explicit deduplication ID:    you provide MessageDeduplicationId directly,
                               useful when two messages could have
                               identical content but represent genuinely
                               different events
```

```
Two messages with the SAME deduplication ID, sent within a 5-minute window
→ the SECOND is treated as a duplicate and silently dropped, never delivered
```

This is what makes FIFO queues "exactly-once processing" instead of just at-least-once like standard queues. But notice the scope — deduplication happens at send time, within a bounded window. It won't retroactively fix a consumer that isn't idempotent for messages arriving further apart than that window. Treating FIFO's dedup as a substitute for consumer-side idempotency is still a mistake.

---

# Delay Queues

```python
sqs.send_message(
    QueueUrl=queue_url,
    MessageBody=json.dumps(event),
    DelaySeconds=300,  # message won't be visible to consumers for 5 minutes
)
```

A message can stay invisible to consumers for a delay period after sending — useful for scheduling work a fixed time in the future (a reminder, a timeout check) without a separate scheduling system.

---

# Real-World Examples

### S3 Event Notifications → SQS

An S3 bucket configured to publish an event straight to an SQS queue on every new upload — a downstream service consumes "a new file arrived" without polling S3 or building any custom notification infrastructure.

---

### Decoupling Microservices on AWS

The same checkout-style decoupling from Messaging Fundamentals, built with SQS specifically because it gives messaging's benefits without the cost of running Kafka or RabbitMQ yourself — the default choice for a lot of AWS-native architectures for exactly this reason.

---

### Order Processing Pipelines with Strict Per-Order Ordering

A natural fit for FIFO queues with `MessageGroupId` set to the order ID — an order's events (`created`, `paid`, `shipped`) always process in sequence, while different orders run fully in parallel with no ordering relationship between them.

---

# Common Interview Questions

## How does SQS know whether to redeliver a message, given it has no persistent connection to consumers?

The visibility timeout. When a message is received, it goes invisible to other consumers for a set duration, but isn't deleted. `DeleteMessage` within that window removes it for good. If it doesn't come — a crash, or processing running long — the message becomes visible again automatically once the timeout expires and gets redelivered. No persistent connection needed, just the passage of time without a delete.

---

## Standard vs FIFO queues — what's the actual trade-off?

Standard queues offer effectively unlimited throughput with at-least-once delivery and no ordering guarantee. FIFO queues guarantee strict per-group ordering and effectively-exactly-once processing via deduplication, at a meaningfully lower throughput ceiling. Reach for FIFO when ordering or duplicate avoidance is a hard requirement; default to standard otherwise.

---

## What happens if you set the visibility timeout too short?

A consumer still legitimately processing can have the message go visible again before it finishes, and a second consumer picks it up too — genuine duplicate processing, not because anything crashed, just because the timeout expired too early relative to actual processing time.

---

## Why is long polling generally preferred over short polling?

Fewer wasted empty API calls (a real cost consideration, since SQS bills per request), and better odds of actually retrieving a message on one call. The cost — occasionally waiting up to the configured timeout on an empty queue — is a trade that's almost always worth making.

---

## Does FIFO deduplication eliminate the need for an idempotent consumer?

Not entirely. Deduplication only covers messages sent within a bounded window (5 minutes) with matching IDs or content — it doesn't cover every duplicate scenario a consumer might see, like a message redelivered because the visibility timeout expired before processing finished. Consumer-side idempotency is still the more complete guarantee.

---

# Common Mistakes

❌ Setting the visibility timeout without considering realistic processing time.

Too short causes duplicate processing from premature redelivery; too long delays recovery when a consumer genuinely crashes — tune it deliberately, with `ChangeMessageVisibility` as an escape hatch for slow runs.

---

❌ Using short polling by default.

Wastes API calls (and money) on empty responses and can occasionally miss an available message — long polling is close to a free upgrade for most real use cases.

---

❌ Choosing a standard queue when strict ordering is a genuine requirement.

Standard queues make no ordering promise at all. If a workflow depends on processing events in order, that's a FIFO queue with the right message group ID, not a standard queue and hope.

---

❌ Treating FIFO deduplication as a complete substitute for an idempotent consumer.

It has real scope limits — a bounded window, specific ID matching — and reduces duplicate risk without eliminating every scenario a consumer could see the same event twice.

---

# Key Takeaways

- SQS trades RabbitMQ's routing flexibility and Kafka's replay capability for full operational simplicity — no brokers to run, automatic scaling, pay-per-message pricing.
- The visibility timeout is SQS's mechanism for at-least-once delivery without a persistent connection — invisible on receipt, permanently removed only by an explicit `DeleteMessage`, otherwise visible again for redelivery once the timeout expires.
- Standard queues give high throughput with at-least-once delivery and no ordering guarantee; FIFO queues give strict per-group ordering and effectively-exactly-once processing via deduplication, at a meaningfully lower throughput ceiling.
- `MessageGroupId` in FIFO queues is the same "ordering scoped to a key" idea as Kafka's partition key — strict order within a group, full parallelism across groups.
- Long polling cuts wasted empty API calls and improves retrieval odds over short polling — close to a default upgrade.
- FIFO deduplication reduces duplicate-processing risk but doesn't replace the need for an idempotent consumer — same underlying concept from Messaging Fundamentals.
