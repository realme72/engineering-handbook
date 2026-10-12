# Rate Limiting

# Why Does Rate Limiting Exist?

Imagine you ship a public API with no limits on it.

```http
POST /login
```

Nothing stops a client from calling it once.

Nothing stops a script from calling it 50,000 times a second either.

```
Attacker Script

↓

50,000 login attempts/sec

↓

Database connection pool exhausted

↓

Every real user's request now queues behind the attack

↓

Site is effectively down
```

Notice something important — nobody had to "hack" anything.

The API did exactly what it was built to do. It just did it too many times, too fast, from one source.

Rate limiting exists to answer one question before any business logic even runs:

> **Has this client made too many requests in too little time?**

If yes, reject early and cheaply, before it ever touches your database, your business logic, or your downstream services.

This is the part people miss when they're new to this: rate limiting isn't primarily a security feature. It's a **stability** feature. It protects your system from any client — malicious, buggy, or just a legitimate customer's retry loop gone wrong — that would otherwise take down the service for everyone else.

I've seen production incidents caused by our *own* mobile app retrying failed requests in a tight loop with no backoff — no attacker involved at all. Rate limiting is what turned that from an outage into a blip.

---

# What Problems It Actually Solves

- **Abuse and scraping** — someone hammering `GET /products` to scrape your entire catalog.
- **Brute-force attacks** — repeated `POST /login` attempts trying to guess a password.
- **Runaway clients** — a bug in a client's retry logic, hammering an endpoint with no backoff.
- **Noisy-neighbor problems** — on a shared/multi-tenant API, one customer's traffic spike shouldn't degrade service for every other customer.
- **Cost control** — every request against a paid third-party API (Twilio, OpenAI, a cloud provider) costs money; limits cap the blast radius of a bug that loops.
- **Fair usage on tiered plans** — free-tier users capped at 100 req/min, enterprise customers at 10,000 req/min, using the exact same infrastructure.

---

# Where Rate Limiting Happens

```
Client

↓

Request

↓

API Gateway / Load Balancer  ──→  Rate Limit Check  ──→  429 Too Many Requests

↓ (if allowed)

Application Server

↓

Business Logic
```

The earlier you reject an over-limit request, the cheaper it is. Rejecting at the API gateway/edge costs almost nothing. Rejecting after the request has already hit your database is the worst possible place to enforce this — by then the damage (a slow query, a connection held open) is already done.

In practice, rate limiting often exists at multiple layers simultaneously:

- **CDN/edge** (Cloudflare, AWS WAF) — blunt, high-volume protection against obvious abuse.
- **API Gateway** (Kong, AWS API Gateway, NGINX) — per-client, per-API-key limits.
- **Application layer** — fine-grained limits tied to business rules (e.g. "3 password reset emails per hour per account").

---

# Common Algorithms

## Fixed Window

Count requests in a fixed time bucket (e.g. per minute), reset the counter when the window rolls over.

```
Window: 12:00:00 – 12:00:59   →  Limit: 100 requests
```

```
Request 1  → count = 1
Request 2  → count = 2
...
Request 100 → count = 100
Request 101 → REJECTED (429)
```

At 12:01:00, the counter resets to zero.

**The problem** — the boundary. A client can send 100 requests at 12:00:59 and another 100 at 12:01:00 — 200 requests in a two-second window, while technically staying "within limit" every single window.

```
12:00:59  →  100 requests (fills window 1)
12:01:00  →  100 requests (fills window 2)

→ 200 requests in ~1 second, both windows "compliant"
```

This is the classic gotcha interviewers look for — fixed window is simple to implement but leaks at the edges.

**Python Implementation**

```python
import time

class FixedWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self.counters = {}  # client_id -> (window_start, count)

    def allow(self, client_id: str) -> bool:
        now = time.time()
        window_start, count = self.counters.get(client_id, (now, 0))

        # current window has expired — start a fresh one
        if now - window_start >= self.window_seconds:
            window_start, count = now, 0

        if count >= self.limit:
            return False

        self.counters[client_id] = (window_start, count + 1)
        return True


limiter = FixedWindowRateLimiter(limit=100, window_seconds=60)
limiter.allow("client_42")  # True until the 100th call in that window
```

This is single-process, in-memory — fine for a demo, not for a fleet of servers behind a load balancer. In production, the same logic runs against Redis (`INCR key` + `EXPIRE key window_seconds` on first increment) so every server shares one counter.

## Production Implementation (Redis)

The in-memory implementation above works only for a single application instance. In production, applications are usually deployed across multiple servers behind a load balancer, so each instance must share the same rate-limit state.

A common approach is to use **Redis** as a centralized counter store.

### How it works

Each client has a Redis key for the current time window.

```text
rate_limit:{client_id}:{window}
```

where

```python
window = current_timestamp // window_seconds
```

For every request:

1. Increment the counter using **`INCR`**.
2. If this is the first request (`INCR == 1`), set a TTL using **`EXPIRE`**.
3. Reject the request if the counter exceeds the configured limit.

Since Redis executes `INCR` atomically, the counter remains correct even when multiple application servers receive requests simultaneously.

### Redis Example (FastAPI)

```python
import time
from fastapi import FastAPI, HTTPException, Request
from redis import Redis

app = FastAPI()

redis = Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
)

LIMIT = 100
WINDOW = 60  # seconds


def check_rate_limit(client_id: str):
    now = int(time.time())

    # Fixed window identifier
    current_window = now // WINDOW

    key = f"rate_limit:{client_id}:{current_window}"

    # Atomically increment the counter
    current = redis.incr(key)

    # First request in this window
    if current == 1:
        redis.expire(key, WINDOW)

    if current > LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
        )


@app.get("/users")
def get_users(request: Request):
    client_id = request.client.host

    check_rate_limit(client_id)

    return {"message": "Success"}
```

### Why Redis?

- Shared state across all application servers.
- `INCR` is atomic, preventing race conditions.
- `EXPIRE` automatically removes old counters.
- O(1) time complexity per request.
- No background cleanup jobs are required.

### Even Better: Redis Lua Script

The implementation above performs two Redis commands (`INCR` and `EXPIRE`). While this is sufficient for many systems, production systems often combine them into a **Lua script**, ensuring both operations execute atomically in a single network round trip.

```lua
local current = redis.call("INCR", KEYS[1])

if current == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end

return current
```

Python:

```python
RATE_LIMIT_SCRIPT = """
local current = redis.call("INCR", KEYS[1])

if current == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end

return current
"""

script = redis.register_script(RATE_LIMIT_SCRIPT)

count = script(
    keys=[key],
    args=[WINDOW],
)

if int(count) > LIMIT:
    raise HTTPException(status_code=429)
```

This guarantees that incrementing the counter and setting the expiration happen as a single atomic operation, eliminating edge cases where a process might crash after incrementing the counter but before setting the TTL.

---

## Sliding Window Log

Keep a timestamp for every request in the last window, and count how many fall inside the trailing window at any given moment.

```
Now: 12:00:45
Window: last 60 seconds → 11:59:45 to 12:00:45

Count timestamps in that range → compare to limit
```

This is accurate — no boundary leak — but expensive. Storing every timestamp per client and scanning them on every request doesn't scale well under high traffic.

**Python Implementation**

```python
import time
from collections import deque

class SlidingWindowLogRateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self.logs = {}  # client_id -> deque of request timestamps

    def allow(self, client_id: str) -> bool:
        now = time.time()
        log = self.logs.setdefault(client_id, deque())

        # drop timestamps that have fallen outside the trailing window
        while log and now - log[0] > self.window_seconds:
            log.popleft()

        if len(log) >= self.limit:
            return False

        log.append(now)
        return True


limiter = SlidingWindowLogRateLimiter(limit=100, window_seconds=60)
limiter.allow("client_42")
```

Notice the memory cost: this keeps up to `limit` timestamps *per client*, forever recomputed on every request. That's the trade-off — perfectly accurate, but it doesn't scale to millions of clients the way a single integer counter does.

---

## Sliding Window Counter

A practical middle ground: keep fixed-window counters, but weight the previous window's count by how much of it overlaps with the current sliding window.

```
Previous window count: 80    (weight: 25% still "in view")
Current window count:  40

Estimated count = 40 + (80 × 0.25) = 60
```

Cheap like fixed window, smooth like sliding log, at the cost of being an approximation rather than an exact count. This is what most production systems (including a lot of what Cloudflare and API gateways implement) actually use, because "approximately correct and fast" beats "perfectly correct and slow" for this problem.

**Python Implementation**

```python
import time

class SlidingWindowCounterRateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        # client_id -> {"window_start": ts, "curr": count, "prev": count}
        self.state = {}

    def allow(self, client_id: str) -> bool:
        now = time.time()
        s = self.state.setdefault(
            client_id, {"window_start": now, "curr": 0, "prev": 0}
        )

        elapsed = now - s["window_start"]

        if elapsed >= self.window_seconds:
            # roll over: how many full windows have we skipped?
            windows_passed = int(elapsed // self.window_seconds)
            s["prev"] = s["curr"] if windows_passed == 1 else 0
            s["curr"] = 0
            s["window_start"] += windows_passed * self.window_seconds
            elapsed = now - s["window_start"]

        # weight = how much of the previous window still "counts"
        weight = max(0.0, (self.window_seconds - elapsed) / self.window_seconds)
        estimated = s["curr"] + s["prev"] * weight

        if estimated >= self.limit:
            return False

        s["curr"] += 1
        return True


limiter = SlidingWindowCounterRateLimiter(limit=100, window_seconds=60)
limiter.allow("client_42")
```

This is the shape of what Redis-backed gateways implement, just with the two counters (`curr`/`prev`) living as two Redis keys with a TTL instead of a Python dict.

## Production Implementation (Redis)

The in-memory implementation stores the counters inside a Python dictionary, which only works for a single application instance. In production, the counters are typically stored in **Redis**, allowing every application server to share the same rate-limit state.

Instead of storing every request timestamp, Redis maintains **two counters** for each client:

- Current window counter
- Previous window counter

The estimated request count is then calculated as:

```text
estimated =
    current_window_count +
    previous_window_count × overlap_percentage
```

For example:

```text
Window Size = 60 seconds

Current Time = 12:00:45

Current Window
12:00:00 ─────────────────────── 12:00:59
                ▲
              Now

Previous Window
11:59:00 ─────────────────────── 11:59:59

Elapsed = 45 seconds

Weight = (60 - 45) / 60
       = 0.25

Estimated Requests

= current + previous × 0.25
```

### Redis Key Design

```text
rate_limit:{client_id}:{window}
```

where

```python
window = current_timestamp // window_seconds
```

For every request:

1. Read the current window counter.
2. Read the previous window counter.
3. Calculate the weighted estimate.
4. Reject if the estimate exceeds the configured limit.
5. Otherwise increment the current window counter.

### FastAPI Example

```python
import math
import time

from fastapi import FastAPI, HTTPException, Request
from redis import Redis

app = FastAPI()

redis = Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
)

LIMIT = 100
WINDOW = 60


def check_rate_limit(client_id: str):
    now = time.time()

    current_window = int(now // WINDOW)
    previous_window = current_window - 1

    current_key = f"rate_limit:{client_id}:{current_window}"
    previous_key = f"rate_limit:{client_id}:{previous_window}"

    # Fetch both counters in one network round-trip
    pipe = redis.pipeline()
    pipe.get(current_key)
    pipe.get(previous_key)
    current_count, previous_count = pipe.execute()

    current_count = int(current_count or 0)
    previous_count = int(previous_count or 0)

    elapsed = now % WINDOW
    weight = (WINDOW - elapsed) / WINDOW

    estimated = current_count + previous_count * weight

    if estimated >= LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
        )

    # Increment current window
    current_count = redis.incr(current_key)

    # First request in this window
    if current_count == 1:
        redis.expire(current_key, WINDOW * 2)

    return True


@app.get("/users")
def get_users(request: Request):

    client_id = request.client.host

    check_rate_limit(client_id)

    return {"message": "Success"}
```

### Why is the TTL `WINDOW * 2`?

The current window eventually becomes the **previous** window during the next interval.

```
Current Window
│────────────│

After rollover

Previous Window
│────────────│
```

Therefore, Redis must retain the counter for **one additional window** so that it can still contribute to the weighted calculation.

After two windows, the counter is no longer needed and Redis automatically removes it.

### Why use a Redis Pipeline?

Every request needs both counters.

Without a pipeline:

```
GET current
GET previous
INCR current
EXPIRE current
```

With a pipeline, the two `GET` operations are sent together, reducing network latency.

### Complexity

| Operation | Complexity |
|-----------|-----------:|
| Read current counter | O(1) |
| Read previous counter | O(1) |
| Increment counter | O(1) |
| Memory per client | O(2) |

### Advantages

- Much smoother than Fixed Window.
- O(1) memory regardless of request volume.
- Shared across all application servers using Redis.
- No need to store individual request timestamps.
- Widely used by API gateways and reverse proxies because it offers an excellent balance between accuracy and performance.

### Limitation

The algorithm estimates the request count using a weighted average rather than tracking every request timestamp. Consequently, it may occasionally allow or reject a request near the limit that an exact Sliding Window Log implementation would handle differently. In practice, this small approximation is usually acceptable in exchange for significantly lower memory usage and higher throughput.

---

## Token Bucket

Each client has a bucket that holds tokens. Every request consumes one token. Tokens refill at a fixed rate, up to a max capacity.

```
Bucket capacity: 10 tokens
Refill rate: 1 token / second

Request arrives → bucket has tokens? → consume 1, allow
                                     → empty? → reject (429)
```

The key property: it allows **bursts**. If a client has been idle and the bucket is full, it can fire off 10 requests instantly, then it's throttled to the steady refill rate. This matches real traffic much better than a hard "N requests per minute, evenly spread" assumption — clients are naturally bursty (a user loading a dashboard fires 8 requests at once, then goes quiet).

This is the algorithm I reach for by default unless there's a specific reason not to — it's simple to reason about, cheap to implement with Redis (`INCR` + `EXPIRE`, or a Lua script for atomicity), and it matches how real traffic actually behaves.

**Python Implementation**

```python
import time

class TokenBucketRateLimiter:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity          # max tokens the bucket can hold
        self.refill_rate = refill_rate    # tokens added per second
        self.buckets = {}  # client_id -> (tokens, last_refill_ts)

    def allow(self, client_id: str) -> bool:
        now = time.time()
        tokens, last_refill = self.buckets.get(client_id, (self.capacity, now))

        # top up tokens earned since the last request, capped at capacity
        elapsed = now - last_refill
        tokens = min(self.capacity, tokens + elapsed * self.refill_rate)

        if tokens < 1:
            self.buckets[client_id] = (tokens, now)
            return False

        self.buckets[client_id] = (tokens - 1, now)
        return True


# 10-request burst capacity, refilling at 1 request/second
limiter = TokenBucketRateLimiter(capacity=10, refill_rate=1)
limiter.allow("client_42")
```

An idle client's bucket fills back up to `capacity`, so it can burst up to 10 requests instantly, then it's throttled to 1/second — exactly the bursty-but-bounded behavior described above.

---

## Leaky Bucket

Requests enter a queue (the "bucket") and are processed at a fixed, constant rate — like a bucket with a small hole leaking at a steady drip, regardless of how fast water is poured in.

```
Requests in  →  [ Queue ]  →  processed at fixed rate  →  Server
                    ↓
              overflow → rejected
```

Unlike token bucket, it smooths bursts out into a constant output rate instead of allowing them through. Useful when the downstream system genuinely can't handle bursts at all (e.g. a legacy system behind you that chokes on spiky load), but it adds latency for bursty legitimate traffic that token bucket would have just let through immediately.

**Python Implementation**

```python
import time
from collections import deque

class LeakyBucketRateLimiter:
    def __init__(self, capacity: int, leak_rate: float):
        self.capacity = capacity      # max queued requests
        self.leak_rate = leak_rate    # requests processed per second
        self.queues = {}  # client_id -> (deque, last_leak_ts)

    def allow(self, client_id: str) -> bool:
        now = time.time()
        queue, last_leak = self.queues.get(client_id, (deque(), now))

        # drain the queue at the fixed leak rate since we last checked
        leaked = int((now - last_leak) * self.leak_rate)
        for _ in range(min(leaked, len(queue))):
            queue.popleft()
        if leaked > 0:
            last_leak = now

        if len(queue) >= self.capacity:
            self.queues[client_id] = (queue, last_leak)
            return False  # bucket is full — request overflows and is rejected

        queue.append(now)
        self.queues[client_id] = (queue, last_leak)
        return True


# queue holds at most 20 requests, drained at a constant 5/second
limiter = LeakyBucketRateLimiter(capacity=20, leak_rate=5)
limiter.allow("client_42")
```

Here `allow()` returning `True` means "accepted into the queue," not "processed immediately" — a real implementation pairs this with a worker that dequeues and processes requests at exactly `leak_rate`, which is what turns a bursty arrival pattern into a constant, predictable output rate.

---

# Token Bucket vs Leaky Bucket vs Fixed Window — When to Use Which

| | Allows bursts | Smooths to constant rate | Simplicity | Typical use |
|---|---|---|---|---|
| Fixed Window | Yes (at boundaries — a flaw, not a feature) | No | Very simple | Quick and dirty, internal tools |
| Sliding Window Counter | Limited, smoothed | Mostly | Moderate | Production API gateways |
| Token Bucket | Yes, by design | No | Moderate | Public APIs, per-client limits (most common default) |
| Leaky Bucket | No | Yes | Moderate | Protecting a fragile downstream system |

---

# What Key Do You Rate Limit On?

The algorithm is only half the design. The other half is deciding *what identifies a client*.

```
By IP address       →  breaks for users behind shared NAT/corporate proxies
By API key          →  standard for public APIs (Stripe, Twilio)
By user/account ID  →  ties limits to a logical customer, not a network detail
By endpoint         →  /login might allow 5/min while /search allows 100/min
```

Real systems usually combine these — e.g. Stripe rate-limits per API key, but a login endpoint might *also* separately limit by IP to slow down credential-stuffing attacks regardless of API key.

---

# HTTP Semantics

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 30
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1721568000
```

`429` is the correct status code — not `403` (that implies a permissions problem, not a rate problem) and not `503` (that implies the server itself is unhealthy).

The `X-RateLimit-*` headers aren't formally standardized, but they've become a de facto convention (GitHub, Stripe, Twitter all use some variant) — well-behaved clients read `X-RateLimit-Remaining` and slow down *before* hitting the wall, instead of hammering the API until they get a 429.

`Retry-After` tells the client exactly how long to back off, which removes the guesswork that otherwise leads to clients hammering retries even harder right after being throttled.

---

# Real-World Examples

### GitHub

```http
GET /user
```

```http
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4999
X-RateLimit-Reset: 1721568000
```

GitHub's REST API allows 5,000 requests/hour for authenticated users, a much lower number for unauthenticated ones, and separate, tighter limits for search endpoints specifically — because search is far more expensive to compute per request than a simple resource fetch. Not every endpoint deserves the same limit.

---

### Stripe

Stripe rate-limits per API key, using a token-bucket-style approach, and explicitly documents that read requests and write requests are limited separately — write operations (charges, refunds) get a tighter cap than reads, because the blast radius of a runaway write loop is financial, not just computational.

---

### Cloudflare / API Gateways

Most CDNs and API gateways rate-limit at the edge, before traffic even reaches origin servers, using approximate sliding-window counters, because at that scale (millions of requests/sec) exact counting is too expensive — an approximation that's "close enough" and cheap wins over perfect accuracy that doesn't scale.

---

# Common Interview Questions

## Why is 429 the correct status code, not 403?

403 means "you don't have permission" — a permanent-ish state. 429 means "you're currently sending too many requests" — a temporary, time-based condition the client can recover from just by waiting, which is exactly what `Retry-After` communicates.

---

## What's the flaw in fixed-window rate limiting?

The boundary problem — a client can send a full window's worth of requests right at the end of one window and another full window's worth right at the start of the next, doubling the effective limit for a brief moment around the boundary.

---

## Why does token bucket allow bursts, and why is that actually desirable?

Because tokens accumulate while a client is idle, up to the bucket's capacity. This matches real traffic — a dashboard loading 8 resources at once isn't abuse, it's just how a normal page load behaves. A rate limiter that can't tell the difference between "one burst from a normal user" and "sustained abuse" ends up punishing real users.

---

## How would you rate-limit a distributed system with multiple servers?

You can't keep the counter in each server's local memory — server A wouldn't know what server B has already counted for the same client. You need a shared, fast store (Redis is the standard choice) that every server checks against, typically via an atomic `INCR`+`EXPIRE` or a Lua script to avoid race conditions between the read and the increment.

---

## Should you rate-limit by IP or by API key/user ID?

Depends what you're protecting against. IP-based limiting is a blunt instrument — it breaks down for users behind a shared corporate NAT (one office = one IP = everyone throttled together) and does nothing against an attacker rotating IPs. API-key or account-based limiting ties the limit to an actual identity. Production systems commonly use both — API key/account for general fairness, plus an IP-based layer specifically on sensitive endpoints like login, to slow down credential stuffing regardless of account.

---

## How do you communicate rate limits to well-behaved clients?

Standard headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`) so clients can self-throttle before hitting a 429, plus `Retry-After` on the 429 response itself so a client knows exactly how long to wait instead of guessing and retrying too soon.

---

# Common Mistakes

❌ Rate limiting only at the application layer, after the request already hit the database.

By the time you reject it, the expensive part of the work is already done. Reject as early as possible — ideally at the gateway/edge.

---

❌ Using a single global limit for every endpoint.

A `GET /products` call and a `POST /checkout` call don't cost the same, and don't carry the same abuse risk. Login and password-reset endpoints in particular deserve much tighter limits than general reads.

---

❌ Rate limiting by IP alone on a public API.

Breaks legitimate users behind shared NAT/proxies, and does nothing to stop an attacker who simply rotates IP addresses.

---

❌ Returning 403 or 500 instead of 429.

Misleads clients about what actually happened and whether retrying is appropriate.

---

❌ Not sending `Retry-After`.

Without it, clients (especially poorly-written ones) often retry immediately, which is exactly the behavior you were trying to prevent.

---

❌ Keeping rate-limit counters in local server memory in a multi-server deployment.

Each server only sees its own slice of traffic, so the effective limit becomes (per-server limit × number of servers) — far looser than intended. Use a shared store like Redis.

---

# Key Takeaways

- Rate limiting is fundamentally a stability mechanism, not just a security one — it protects the system from any source of excessive load, malicious or not.
- Reject over-limit requests as early as possible (ideally at the edge/gateway) — the cost of enforcement should always be cheaper than the cost of the request it's blocking.
- Fixed window is simple but leaks at window boundaries; token bucket is the common default because it allows natural bursts while still enforcing a steady-state limit; leaky bucket smooths traffic into a constant rate for fragile downstream systems.
- Rate limiting needs a shared, fast store (like Redis) in any multi-server deployment — local in-memory counters silently multiply the effective limit.
- Choose the identifying key deliberately (IP, API key, account ID) based on what you're actually protecting against — most real systems layer more than one.
- Always return 429 with `Retry-After` and expose `X-RateLimit-*` headers so well-behaved clients can self-throttle instead of hammering the wall.
