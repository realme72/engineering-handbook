# Retry Strategies

# Why Do Retry Strategies Exist?

Most failures in a distributed system are transient: a brief network blip, a connection pool momentarily exhausted, a downstream service overloaded for a few seconds before recovering on its own. Giving up on the first failure wastes work that would have succeeded a moment later if you'd just tried again.

But how you retry matters as much as whether you do. A naive retry strategy can turn a small, passing problem into a much bigger one you caused yourself.

```
Downstream service is briefly overloaded, failing 10% of requests

↓

Every failing client immediately retries

↓

Retries ADD to the load on a system that was ALREADY overloaded

↓

More requests fail → more immediate retries → even more load

↓

A brief blip has become a sustained outage, caused entirely by the retries
```

That's a **retry storm** — the retry logic itself becomes the cause of the outage instead of the fix for it. Getting retry strategy right means avoiding this while still recovering from problems that really are transient.

---

# Naive (Immediate) Retry

```python
for attempt in range(5):
    try:
        return call_downstream_service()
    except TransientError:
        continue  # retry immediately, no delay at all
```

The simplest approach, and the most dangerous one at scale. If the downstream system is overloaded, retrying instantly adds load right back at the worst possible moment, with zero time to recover. This is exactly how retry storms start.

---

# Fixed Delay Retry

```python
for attempt in range(5):
    try:
        return call_downstream_service()
    except TransientError:
        time.sleep(2)  # wait 2 seconds between every attempt
```

Better than nothing — it gives the downstream system some breathing room — but it has its own flaw. If many clients failed at roughly the same moment, they all wait the same fixed delay and then all retry at the same instant again. That just moves the thundering herd two seconds down the road instead of solving it.

---

# Exponential Backoff

Instead of a fixed wait, each retry waits progressively longer, giving the downstream system more time to recover the longer the failure persists.

```python
import time

def call_with_backoff(fn, max_retries=5, base_delay=1):
    for attempt in range(max_retries):
        try:
            return fn()
        except TransientError:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s, 8s, 16s
            time.sleep(delay)
```

```
Attempt 1 fails → wait 1s
Attempt 2 fails → wait 2s
Attempt 3 fails → wait 4s
Attempt 4 fails → wait 8s
Attempt 5 fails → give up (or dead-letter — see Dead Letter Queues)
```

This is the direct fix for naive retry — load on the struggling system decreases over successive attempts instead of staying constant, giving it a real chance to recover.

---

# Jitter — Why Backoff Alone Isn't Enough

Exponential backoff still has a version of the fixed-delay problem, just spread across a few points in time instead of one. If 1,000 clients fail at the same moment, they all wait exactly 1 second, retry at exactly the same instant, wait exactly 2 seconds if that fails too, and retry together again.

```
Without jitter:  every failing client retries at EXACTLY the same
                 moments: t=1s, t=3s, t=7s, t=15s, ...
                 → synchronized bursts of retries, just spaced further apart

With jitter:     each client adds a random amount of variance to its delay
                 → retries are SPREAD OUT over time instead of
                   arriving in synchronized bursts
```

```python
import random

def call_with_backoff_and_jitter(fn, max_retries=5, base_delay=1, cap=30):
    for attempt in range(max_retries):
        try:
            return fn()
        except TransientError:
            if attempt == max_retries - 1:
                raise
            exp_delay = min(cap, base_delay * (2 ** attempt))
            jittered_delay = random.uniform(0, exp_delay)  # "full jitter"
            time.sleep(jittered_delay)
```

This is the "full jitter" strategy AWS's engineering blog popularized after their own systems kept hitting synchronized retry storms despite already using exponential backoff. Jitter is what actually breaks the synchronization — backoff alone just reduces average load over time; jitter stops the retries from re-converging into new bursts.

---

# Retryable vs Non-Retryable Failures

Not every failure deserves a retry. Retrying only helps if the next attempt has a real chance of succeeding.

```
Retryable (transient):        Non-Retryable (permanent):

- Network timeout             - 400 Bad Request (the request itself is malformed)
- 503 Service Unavailable     - 401 Unauthorized (retrying with the same
- Connection reset               credentials will fail identically every time)
- Database deadlock           - 404 Not Found (the resource genuinely doesn't exist)
```

```python
def call_with_backoff(fn, max_retries=5):
    for attempt in range(max_retries):
        try:
            return fn()
        except (TimeoutError, ConnectionError, ServiceUnavailable):
            # transient — worth retrying
            ...
        except (BadRequestError, AuthenticationError):
            raise  # permanent — retrying is pointless, fail immediately
```

Retrying a permanent failure just burns time chasing an outcome that will never change, and delays surfacing the actual problem — bad input, an expired credential — that needs fixing, not waiting out.

---

# A Retry Needs a Ceiling, and a Plan for What Happens After

```
max_retries = 5

↓

After the 5th failed attempt, what happens?

Option A:  give up entirely, return an error to the caller
Option B:  route the failed operation to a Dead Letter Queue for
           later investigation (see the Dead Letter Queues chapter)
```

Retry with no upper bound is exactly how a poison pill turns into an infinite resource drain. A retry strategy isn't complete without an answer for "and then what, once we've actually given up."

---

# The Idempotency Requirement

The thread running through this whole chapter: retrying an operation is only safe if it's idempotent — calling it twice has to produce the same effect as calling it once.

```
Retrying a GET request:            always safe — reads have no side effect

Retrying "charge the customer":    only safe if the operation is idempotent
                                    (e.g. via an idempotency key) — otherwise
                                    a retry after a lost response can mean
                                    a customer gets charged twice
```

This is why the next chapter, Idempotent Consumers, isn't really a separate topic — it's the precondition that makes everything here safe to use for anything with a real side effect. A retry strategy on top of a non-idempotent operation isn't a solution; it's a strategy for how often to risk duplicating that side effect.

---

# When the Failing System Tells You How Long to Wait

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 30
```

The same `Retry-After` header from the Rate Limiting chapter — when a downstream system tells you exactly how long to wait, that's better information than a blind backoff guess, and a well-behaved client should just honor it instead of computing its own delay from scratch.

---

# Real-World Examples

### AWS SDKs

Every official AWS SDK ships exponential backoff with jitter by default for retryable errors — a direct acknowledgment, from AWS's own engineering experience, that naive retries reliably cause storms at their scale, and that jitter specifically, not backoff alone, is what stops them.

---

### Stripe's Client Libraries

Stripe's SDKs retry with exponential backoff and pair it with idempotency keys on the retried request — a real-world instance of this chapter's whole point: retries and idempotency get solved together, not separately.

---

### Database Connection Retry Logic

A very common, practical case — a connection pool briefly exhausted or a transient network blip to the database is exactly the failure exponential backoff with jitter is built for, unlike a permanent failure like an invalid query, which no amount of retrying will fix.

---

# Common Interview Questions

## Why is immediate, naive retry dangerous at scale?

If the original failure came from the downstream system being overloaded, immediate retries add load right back at the worst possible moment, with no time to recover — a brief blip turns into a sustained, self-inflicted outage.

---

## What does exponential backoff actually solve, and what does it not solve on its own?

It reduces average load on a struggling system by waiting progressively longer between attempts, giving it real time to recover. What it doesn't solve alone: many clients that failed together still retry in synchronized lockstep at the same subsequent moments. That's jitter's job.

---

## Why is jitter necessary in addition to exponential backoff?

Because backoff alone still produces synchronized bursts — every client that failed together waits the same calculated delay and retries at the same instant. Jitter randomizes each client's actual wait, spreading retries out instead of letting them re-converge.

---

## How do you decide whether a failure should be retried at all?

Whether it's transient (a timeout, a 503, a connection reset — worth retrying) or permanent (malformed input, a failed auth check, a resource that doesn't exist — retrying is pointless). Retrying every failure blindly wastes resources on ones that will never succeed no matter how many attempts you throw at them.

---

## Why does a retry strategy depend on the operation being idempotent?

Because retrying means the operation might run more than once. If it isn't idempotent, a retry after a lost response — even though the original attempt actually succeeded — can cause a real duplicated side effect, like charging a customer twice. Retry strategy only holds up when paired with an idempotent operation underneath it.

---

# Common Mistakes

❌ Retrying immediately with no delay at all.

Risks turning a downstream system's transient overload into a sustained, retry-caused outage.

---

❌ Using exponential backoff without jitter.

Still produces synchronized bursts among clients that failed together — backoff reduces average load, but doesn't stop retries from re-converging at each subsequent interval.

---

❌ Retrying with no upper bound on attempts.

Turns a permanently failing operation into an unbounded resource drain — every retry strategy needs a ceiling and a defined answer for what happens once it's reached.

---

❌ Retrying non-idempotent operations without any duplicate-safety mechanism.

A retry after a lost response can cause a real duplicated side effect, even though the original attempt actually succeeded — retries are only safe on genuinely idempotent operations.

---

❌ Retrying permanent failures (malformed requests, authentication errors) as if they were transient.

Wastes time chasing an outcome that will never change, and delays fixing the real problem.

---

# Key Takeaways

- Retry strategies exist because most real failures are transient, but a poorly designed one can become the cause of a sustained outage — a retry storm.
- Exponential backoff reduces average load on a struggling system over successive attempts; jitter is the separate mechanism that stops synchronized retries from re-converging.
- Only transient failures are worth retrying — permanent ones (malformed requests, auth errors) should fail immediately.
- Every retry strategy needs an upper bound and a defined outcome once it's reached — typically a Dead Letter Queue instead of retrying forever.
- Retrying is only safe when the underlying operation is idempotent — retry strategy and idempotency are two halves of one solution, not separate concerns.
