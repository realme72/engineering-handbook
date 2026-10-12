# Idempotency

# Why Does Idempotency Exist?

Networks fail. Not occasionally — constantly, in small ways, all day, in every production system you'll ever work on.

Here's the scenario that actually matters:

```
Client               Server

  │  POST /payments      │
  ├─────────────────────►│
  │                       │  charge card ₹500
  │                       │  save payment record
  │                       │
  │        ✕ ✕ ✕          │  response lost on the way back
  │  (timeout)            │
```

The client sent the request. The server processed it, charged the card, and tried to send back a `200 OK`. But the response never arrived — a network blip, a load balancer restart, the client's WiFi dropping for two seconds. It doesn't matter why.

From the client's point of view, it has no idea what happened. Did the request even reach the server? Did it fail before charging the card? Did it succeed and only the response got lost?

The only safe, honest answer is: **retry.**

```
Client retries POST /payments

↓

Server charges the card AGAIN

↓

Customer charged ₹500 twice
```

This is not a hypothetical. This is the single most common way payment systems double-charge customers, and it has nothing to do with buggy code — it's an inherent property of networks. You cannot fix it by "writing more careful code" on the client, because the client genuinely cannot know what happened.

Idempotency exists to make retries **safe by design**, so that "I don't know if that worked, let me just try again" is always a correct, harmless thing for a client to do — no matter what actually happened on the first attempt.

---

# What Problem It Actually Solves

Idempotency answers one question:

> **If this exact request is received more than once, does the system end up in the same state as if it were received once?**

If yes — the operation is idempotent, and retries are free lunch. If no — every retry is a gamble.

This shows up everywhere retries happen, which in a distributed system is *everywhere*:

- Client-side retry logic (mobile apps, frontend fetch wrappers)
- Load balancer / proxy retries on upstream timeout
- Message queue redelivery (a consumer crashes after processing but before acking)
- Client library auto-retry on 5xx (Stripe's own SDKs do this)
- A human refreshing the page after a slow response, thinking it failed

Idempotency isn't a nice-to-have for "critical" endpoints only — any operation that mutates state and can be retried needs an explicit answer to that question. Most of the time the honest answer, if you haven't designed for it, is "no, and we've been lucky so far."

---

# Idempotent by Nature vs Idempotent by Design

Some HTTP methods are idempotent just by following the spec correctly:

```
GET     → read-only, naturally idempotent
PUT     → replaces a resource with the exact same representation → same end state
DELETE  → resource is gone after the first call, still gone after the tenth
```

```http
DELETE /orders/101
```

Calling this once deletes order 101. Calling it five times still results in order 101 being deleted. The end state never changes — this is idempotency for free, as long as you don't do something silly like returning an error on the second `DELETE` because "it's already gone" (a genuinely common mistake — a repeated `DELETE` on an already-deleted resource should still return success, not a 404, precisely because the *goal state* — "resource does not exist" — was already achieved).

```
POST    → creates a new resource each time by design
PATCH   → depends entirely on what the patch expresses
```

```http
POST /payments
{ "amount": 500 }
```

Calling this twice creates two separate payments. There's nothing wrong with the method — POST is *supposed* to create a new thing on every call. The problem is that when the "thing" being created has a real-world side effect (money moved, an email sent, an SMS billed), "create a new one on every retry" is exactly the behavior you don't want.

This is the part that trips people up in interviews: **POST is not broken, and idempotency is not a flaw in HTTP.** POST and PATCH simply don't get idempotency for free from the method semantics — if you need it for a specific operation, you have to build it deliberately. That's what an idempotency key is for.

---

# Idempotency Keys

The pattern: the client generates a unique key for a logical operation (usually a UUID) and sends it alongside the request. The server uses that key to recognize "I've seen this exact operation before" and returns the original result instead of doing the work again.

```http
POST /payments
Idempotency-Key: 7d3f9c1a-88b2-4e2b-9c11-2b8f6b1a9a10
Content-Type: application/json

{
    "amount": 500,
    "currency": "INR"
}
```

```
First request  → Key: 7d3f...  → Payment created, charge processed, result stored against key
Retry (same)   → Key: 7d3f...  → Server finds existing result for key → returns it, does NOT charge again
```

Critically, the key belongs to **one logical attempt**, generated once by the client before the first try, and reused on every retry of that same attempt.

```
User clicks "Pay" once

↓

Client generates key: 7d3f...

↓

POST /payments  (Idempotency-Key: 7d3f...)   → times out

↓

Client retries automatically

↓

POST /payments  (Idempotency-Key: 7d3f...)   → SAME key → safe
```

If the client generated a *new* key on every retry, the whole mechanism is pointless — the server would treat each retry as a brand-new operation, which is exactly the bug you were trying to prevent. This is the single most common mistake teams make when they first adopt idempotency keys.

---

# How the Server Implements It

Conceptually, the server needs a fast key-value store (Redis is the usual choice) mapping `idempotency_key → result`.

```
Request arrives with Idempotency-Key: K

↓

Does K exist in the store?

  ├── Yes → is the original request still in-flight?
  │           ├── Yes → reject with 409 (avoid concurrent duplicate processing)
  │           └── No  → return the STORED response, do not re-run business logic
  │
  └── No  → mark K as "in-flight"
             ↓
             run business logic
             ↓
             store the result against K, with a TTL (e.g. 24 hours)
             ↓
             return the result
```

The "is it still in-flight" check matters more than people expect — without it, two near-simultaneous retries (common with aggressive client-side retry logic) can both see "key not found" and both start processing before either finishes, defeating the entire mechanism. This is why the check-and-mark step needs to be atomic (a single Redis `SET key value NX` — "set if not exists" — rather than a separate "check" then "set").

A subtlety worth knowing for interviews: the stored result should include the *original* request's parameters, so the server can detect a client reusing the same key with *different* parameters — which usually indicates a client-side bug and should be rejected outright rather than silently returning a stale, mismatched response.

```
Key: 7d3f...  originally used for  { "amount": 500 }

Same key reused with { "amount": 900 }

↓

422 — Idempotency key reused with a different request body
```

---

# Python Implementation

A simplified version of the pattern above, backed by Redis:

```python
import hashlib
import json
import redis

r = redis.Redis()
IDEMPOTENCY_TTL_SECONDS = 60 * 60 * 24  # 24 hours


def _fingerprint(payload: dict) -> str:
    # detect a key being replayed against a different request body
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def handle_payment(idempotency_key: str, payload: dict, process_fn):
    store_key = f"idem:{idempotency_key}"

    # atomic "claim" of this key — fails if another request already holds it
    claimed = r.set(
        store_key,
        json.dumps({"status": "in_progress", "fingerprint": _fingerprint(payload)}),
        nx=True,
        ex=IDEMPOTENCY_TTL_SECONDS,
    )

    if not claimed:
        existing = json.loads(r.get(store_key))

        if existing["fingerprint"] != _fingerprint(payload):
            raise ValueError("Idempotency key reused with a different request body")

        if existing["status"] == "in_progress":
            raise ConflictError("Request with this key is still being processed")

        return existing["result"]  # safe replay — return the original outcome

    # first time we've seen this key — actually do the work
    try:
        result = process_fn(payload)
        r.set(
            store_key,
            json.dumps({
                "status": "completed",
                "fingerprint": _fingerprint(payload),
                "result": result,
            }),
            ex=IDEMPOTENCY_TTL_SECONDS,
        )
        return result
    except Exception:
        r.delete(store_key)  # don't let a failed attempt block a legitimate retry
        raise
```

The two details that make this correct rather than just plausible-looking: `nx=True` makes the "claim" atomic (no race between two concurrent retries), and a failed attempt deletes the key instead of caching a failure — a retry after a genuine failure should be allowed to actually try again, not get stuck replaying an error forever.

---

# Idempotency at the Database Layer

Idempotency keys handle the API layer, but the same problem exists one level down — inside your own business logic and message consumers.

## Unique Constraints as a Safety Net

```sql
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    idempotency_key UUID UNIQUE NOT NULL,
    amount INT NOT NULL
);
```

```python
try:
    db.execute(
        "INSERT INTO payments (idempotency_key, amount) VALUES (%s, %s)",
        (idempotency_key, amount),
    )
except UniqueViolation:
    # a duplicate insert attempt — the row already exists, nothing to do
    existing = db.fetch_one(
        "SELECT * FROM payments WHERE idempotency_key = %s", (idempotency_key,)
    )
    return existing
```

Even if your application-layer Redis check somehow gets bypassed (a bug, a race, a server restart mid-request), the database itself refuses to create a duplicate row. This is the belt-and-suspenders approach real payment systems use — never trust a single layer to catch every duplicate.

## Idempotent Consumers in Message Queues

The exact same problem shows up in event-driven systems: a consumer processes a message, crashes before acknowledging it, and the broker redelivers the same message.

```
Consumer processes message → charges card → CRASHES before ack()

↓

Broker never received the ack

↓

Broker redelivers the same message

↓

Consumer processes it again → charges card a second time
```

The fix is structurally identical to the API-level idempotency key — track processed message IDs (most brokers provide one) in a store, and check-and-skip before reprocessing:

```python
def consume(message):
    if r.set(f"processed:{message.id}", 1, nx=True, ex=86400):
        process(message)  # first time seeing this message ID
    # else: already processed, ack and move on — do nothing
```

"At-least-once delivery" is the norm for message queues (Kafka, SQS, RabbitMQ) — exactly-once delivery at the broker level is either unavailable or prohibitively complex. Idempotent consumers are how real systems get exactly-once *processing* semantics on top of at-least-once *delivery*.

---

# Real-World Examples

### Stripe

```http
POST /v1/charges
Idempotency-Key: 7d3f9c1a-88b2-4e2b-9c11-2b8f6b1a9a10
```

Stripe's official SDKs generate an idempotency key automatically for you on every request and hold onto it across internal retries — most developers using the SDK get this for free without ever thinking about it. Stripe stores results for 24 hours and explicitly documents that reusing a key with a different request body returns an error rather than silently ignoring the mismatch.

---

### PayPal

PayPal requires a `PayPal-Request-Id` header on payment-creation calls, functionally identical to Stripe's idempotency key — same problem, same shape of solution, different header name. Whenever you see two competing payment platforms independently converge on the same pattern, that's usually a strong signal the pattern is solving a real, unavoidable problem rather than being one company's stylistic preference.

---

### Kafka Producers

```python
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    enable_idempotence=True,
)
```

Kafka has this concept built directly into the producer client — with `enable_idempotence=True`, the broker assigns each producer a unique ID and sequence number per partition, so a retried publish (e.g. after a network blip between producer and broker) doesn't create a duplicate message on the topic. This is idempotency solved at the infrastructure layer instead of the application layer.

---

# Common Interview Questions

## Is idempotency the same as caching?

No, though they're often confused because both involve "returning a stored result." Caching is about avoiding repeated *work* for performance (the underlying operation could safely run again — you just don't want to pay for it twice). Idempotency is about correctness — the operation genuinely must not run twice, because running it twice changes real-world state (money moved, an email sent). You can have idempotency without caching (a unique DB constraint) and caching without idempotency (caching a GET response).

---

## Why isn't POST idempotent by default, and is that a flaw in HTTP?

It's not a flaw — POST's whole job is "create a new thing," so calling it twice creating two things is the method behaving exactly as specified. The mismatch only appears when the "new thing" has an external side effect you don't want duplicated. HTTP never promised idempotency for POST; idempotency keys are an application-level pattern layered on top precisely because the spec doesn't provide it for free.

---

## What happens if the client crashes before it can retry?

Nothing — and that's fine. Idempotency keys solve the problem of *safe retries*, not the problem of *guaranteed delivery*. If the client never retries, the operation simply doesn't happen again, which is the correct behavior — the customer wasn't charged twice, but they also weren't charged at all if the first attempt genuinely failed. This distinction matters: idempotency doesn't guarantee an operation eventually succeeds, only that succeeding twice doesn't cause double effects.

---

## Should a repeated DELETE return 404 on the second call?

This is genuinely debated, but the more defensible answer: no. The client's *intent* — "this resource should not exist" — has already been achieved by the first call. Returning 404 on the retry (treating "already gone" as an error) punishes the client for something that isn't actually a problem. Many APIs return 204 on both the first and subsequent DELETE calls for exactly this reason.

---

## How would you design idempotent consumers for a message queue?

Track a per-message unique ID (most brokers, like Kafka and SQS, provide one) in a fast store, and check-and-skip before processing — atomically claim the ID before doing the work, same pattern as an API-level idempotency key. This is necessary because virtually every major message broker guarantees only *at-least-once* delivery, meaning redelivery of an already-processed message is an expected, normal event, not an edge case.

---

## Where should the idempotency check live — application code or the database?

Both, ideally. The application-layer check (Redis, an idempotency key) is what makes the *fast path* efficient — it avoids redoing expensive work like calling a third-party payment processor. A unique constraint at the database layer is the last line of defense, catching the case where the application-layer check is bypassed by a race, a bug, or a crash mid-request. Relying on only one of the two is how "we thought we handled this" incidents happen.

---

# Common Mistakes

❌ Generating a new idempotency key on every retry.

Defeats the entire mechanism — the server sees a "new" operation every time, exactly like having no idempotency key at all. The key must be generated once per logical attempt and reused across retries of that attempt.

---

❌ Treating the "check if key exists" and "mark key as in-progress" steps as two separate operations.

Creates a race window where two near-simultaneous retries both slip through before either finishes. This step must be atomic (`SET NX` in Redis, or an equivalent compare-and-set).

---

❌ Caching a failed result against the idempotency key.

If the first attempt genuinely fails (e.g. the downstream payment processor rejected the card), a retry should be allowed to actually try again — not get stuck replaying the same failure forever. Only cache successful, completed results.

---

❌ Assuming idempotency keys alone are enough, with no database-level constraint.

A single layer of protection is one bug away from a duplicate. Pair the application-layer key with a unique constraint at the database layer.

---

❌ Silently accepting a reused key with a different request body.

If a client sends the same key with a different payload, that's very likely a client bug — return an explicit error instead of guessing which version was "correct" and returning a mismatched response.

---

# Key Takeaways

- Idempotency exists because networks fail in ways that make it impossible for a client to know whether a request actually succeeded — retries are the only honest response, so they need to be safe.
- GET, PUT, and DELETE are idempotent by the nature of what they do; POST and PATCH are not, and that's not a flaw in HTTP — it's just something you have to design for explicitly when it matters.
- An idempotency key belongs to one logical attempt and must be reused across retries of that same attempt — generating a new key per retry defeats the whole point.
- The claim-and-store step on the server must be atomic, or two concurrent retries can both slip through before either completes.
- Never cache a failed result against an idempotency key — only successful, completed operations should be replayed instead of re-run.
- Idempotency at the API layer (keys) and idempotency at the database layer (unique constraints) solve the same problem at different layers — real systems use both, because no single layer is bulletproof on its own.
- The identical problem exists in message queues, where at-least-once delivery is the norm — idempotent consumers are how systems get effectively-once processing on top of that.
