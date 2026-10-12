# Cache Stampede

# Why Does This Problem Exist?

A cache key has a TTL. Eventually, it expires — that's the entire point of a TTL, ensuring data doesn't stay stale forever. But expiration has a specific, nasty edge case when the key being expired is genuinely popular.

```
Cache key "homepage:featured_products" — TTL just expired

↓

10,000 requests arrive in the next 100 milliseconds, all needing this same data

↓

ALL 10,000 see a cache miss AT THE SAME TIME

↓

ALL 10,000 independently query the database to recompute the exact same result

↓

The database, which was handling this load just fine when the cache was warm,
suddenly receives 10,000x its expected load for this one query, simultaneously
```

Nothing exotic happened here — a single TTL simply expired at a bad moment, on a key popular enough that "everyone who needs this data" translates to a genuinely enormous number of simultaneous requests. This is a **cache stampede** (also called a **thundering herd**), and it's one of the more common ways a perfectly reasonable caching setup causes a real production outage — the cache did exactly what it was configured to do, and that was the problem.

---

# What Problem It Actually Solves (By Preventing It)

- **Protects the source of truth from a synchronized spike** — the database (or whatever expensive system sits behind the cache) shouldn't ever see traffic that looks like "every cached request all landed on it at once."
- **Avoids wasted, duplicate work** — 10,000 requests all recomputing the identical result is 9,999 redundant computations that provide zero additional value over doing it once.
- **Keeps latency predictable during the recompute window** — without protection, every one of those 10,000 requests waits on a suddenly-overloaded database; with protection, most of them get a fast answer while exactly one request does the real work.

---

# Fix 1: Locking (Mutex on Recompute)

The first request that sees a miss acquires a lock and does the actual recompute. Every other concurrent request, seeing the lock already held, waits briefly instead of independently hammering the database too.

```python
import redis
import time

r = redis.Redis()

def get_featured_products():
    cached = r.get("homepage:featured_products")
    if cached:
        return json.loads(cached)

    lock_acquired = r.set("lock:featured_products", "1", nx=True, ex=10)

    if lock_acquired:
        try:
            data = db.query_featured_products()  # the ONE expensive recompute
            r.setex("homepage:featured_products", 300, json.dumps(data))
            return data
        finally:
            r.delete("lock:featured_products")
    else:
        # someone else is already recomputing — wait briefly and retry the cache
        time.sleep(0.05)
        return get_featured_products()
```

Only one request per key ever actually reaches the database during the recompute window; every other concurrent request politely waits for that single result instead of duplicating the work. The lock's own TTL (`ex=10` above) matters — if the process holding the lock crashes before releasing it, the lock still expires on its own, rather than permanently blocking every future request for that key.

---

# Fix 2: Request Coalescing (Single-Flight)

A closer variant, usually implemented within a single application process: if multiple concurrent calls ask for the same key at the same moment, they all share the result of one single in-flight computation instead of each triggering a separate one.

```python
import threading

_in_flight = {}
_lock = threading.Lock()

def get_with_coalescing(key, compute_fn):
    with _lock:
        if key in _in_flight:
            future = _in_flight[key]
        else:
            future = _in_flight[key] = SingleFlightFuture(compute_fn, key)

    return future.wait_for_result()  # all callers for this key share ONE computation
```

This is the same idea as the distributed lock above, but scoped to one process's in-memory concurrent requests rather than coordinating across multiple servers via Redis — Go's standard library even ships this exact pattern as `singleflight`, precisely because the problem is common enough to warrant a first-class library solution.

---

# Fix 3: Probabilistic Early Expiration

Instead of every request treating the TTL as a hard, synchronized cliff edge, have requests *near* expiration randomly decide to recompute slightly early — spreading the recompute load out over a small window instead of concentrating it all in the exact instant the TTL hits zero.

```python
import random
import math
import time

def get_with_early_recompute(key, ttl, beta=1.0):
    cached, computed_at, delta = get_cache_with_metadata(key)  # delta = time the last compute took

    now = time.time()
    expiry = computed_at + ttl

    # XFetch-style: probability of early recompute increases as expiry approaches
    if cached is not None and now - delta * beta * math.log(random.random()) < expiry:
        return cached

    # either truly expired, or this particular request "lost the coin flip" and recomputes early
    fresh = expensive_compute()
    store_cache_with_metadata(key, fresh, ttl)
    return fresh
```

This is the core idea behind the **XFetch** algorithm (used in production caching systems, notably described in engineering work from Facebook and others) — rather than one single moment where every request simultaneously discovers a miss, a small, randomized fraction of requests recompute slightly ahead of the actual deadline, so by the time true expiration arrives, the cache has likely already been refreshed by one of those early, low-probability recomputes.

---

# Fix 4: Stale-While-Revalidate

Instead of blocking a request on a miss, serve the *stale* (expired) value immediately, while kicking off a background refresh that updates the cache for the next request.

```python
def get_with_stale_while_revalidate(key):
    cached, is_stale = get_cache_allowing_stale(key)

    if cached is not None:
        if is_stale:
            enqueue_background_refresh(key)   # fire-and-forget, doesn't block this request
        return cached   # return immediately — stale, but immediately available

    return synchronous_compute_and_cache(key)  # only a genuinely empty cache blocks
```

This directly trades a small amount of staleness for eliminating the stampede almost entirely — no request has to wait on a synchronous recompute except the very first one that ever populates the key. This is exactly the `stale-while-revalidate` directive in the HTTP `Cache-Control` header (covered in the CDN chapter) — the same idea, standardized at the HTTP layer instead of hand-rolled in application code.

---

# Comparing the Fixes

| Approach | Blocks the requester? | Complexity | Best for |
|---|---|---|---|
| Locking | Yes, briefly | Low | Simple, most common general-purpose fix |
| Request Coalescing | Yes, briefly (in-process) | Low-Moderate | High concurrency within one process/server |
| Probabilistic Early Expiration | No | Moderate | Very hot keys, smoothing load proactively |
| Stale-While-Revalidate | No | Moderate | User-facing latency-sensitive endpoints, tolerant of brief staleness |

Locking is the simplest, most broadly applicable fix and a reasonable default. Stale-while-revalidate is the strongest choice specifically when a slightly stale response is clearly preferable to any request ever waiting on a synchronous recompute — which is true for a large share of real-world read-heavy, latency-sensitive endpoints.

---

# Real-World Examples

### Facebook / Memcached Leases

Facebook's memcache infrastructure introduced "leases" specifically to solve this problem at enormous scale — a request that misses gets a lease token, and only the holder of a valid lease is allowed to write the recomputed value back to the cache; other concurrent misses for the same key are told to wait briefly rather than all independently querying the backing store.

---

### Varnish / HTTP Reverse Proxies

Many HTTP caching proxies implement request coalescing natively — if multiple requests for the same not-yet-cached URL arrive concurrently, only one is actually forwarded to the origin server; the others wait and receive the same response once it arrives, rather than each independently hitting the origin.

---

### CDNs and `stale-while-revalidate`

Modern CDNs (Cloudflare, Fastly) support the `stale-while-revalidate` `Cache-Control` directive directly — serving a slightly stale cached response immediately while refreshing it in the background, which is precisely this pattern applied at the HTTP layer rather than inside application code.

---

# Common Interview Questions

## What is a cache stampede, and why does it happen?

When a popular cache key expires (or the cache is cold on startup), a burst of concurrent requests all miss the cache simultaneously and independently recompute the same expensive result at once — overwhelming the system behind the cache with load it never sees while the cache is warm. It happens because expiration is a synchronized event affecting every concurrent reader of that key at the same moment.

---

## How would you prevent a cache stampede on a very hot key?

Several valid approaches: a lock/mutex so only one request recomputes while others wait briefly; request coalescing so concurrent identical requests within a process share one in-flight computation; probabilistic early expiration so a small random fraction of requests refresh the key slightly before its actual deadline, smoothing the recompute out over time; or stale-while-revalidate, serving the expired value immediately while refreshing it in the background.

---

## What's the trade-off with stale-while-revalidate?

It eliminates blocking almost entirely — only the very first request to populate a key ever waits synchronously — at the cost of occasionally serving data that's slightly out of date during the background refresh window. It's the right trade for most latency-sensitive, read-heavy endpoints where a moment of staleness is far preferable to added latency or a stampede.

---

## Why does a lock-based fix need its own expiration/timeout?

If the process holding the recompute lock crashes before releasing it, an unbounded lock would permanently block every future request for that key. Giving the lock itself a short TTL ensures it's eventually released even if the holder never explicitly does so, at the cost of a small window where two requests could theoretically both attempt the recompute if the timing is unlucky — an acceptable trade against permanently blocking a key.

---

# Common Mistakes

❌ Having no stampede protection at all on hot keys.

Every TTL expiration on a genuinely popular key becomes a synchronized spike of duplicate work against whatever's behind the cache — not a rare edge case, but a routine, foreseeable event for any sufficiently popular data.

---

❌ Using one single global lock for all cache keys instead of a per-key lock.

Serializes recomputation across completely unrelated keys, needlessly blocking requests for key B while key A's unrelated recompute is in progress.

---

❌ A recompute lock with no timeout.

If the process holding it crashes mid-recompute, every future request for that key can be permanently blocked waiting on a lock that will never be released.

---

❌ Assuming a low request volume means stampedes "don't apply to us."

A stampede is about concurrency at the moment of expiration, not overall traffic volume — a key read by only 50 concurrent requests can still meaningfully spike a database that wasn't sized for 50 simultaneous identical queries landing at once.

---

# Key Takeaways

- A cache stampede happens when a popular key's expiration causes many concurrent requests to miss simultaneously and independently recompute the same expensive result at once, overwhelming whatever sits behind the cache.
- Locking (one request recomputes, others wait briefly) is the simplest, most broadly applicable fix, and a reasonable default.
- Request coalescing shares one in-flight computation among concurrent callers within a process — the same idea as locking, scoped locally instead of across servers.
- Probabilistic early expiration spreads recompute load out over time by having a small random fraction of requests refresh a key slightly before its real deadline, instead of everyone hitting the same instant.
- Stale-while-revalidate serves a slightly stale value immediately while refreshing in the background, eliminating blocking almost entirely at the cost of brief staleness — the same idea exists as a standard HTTP `Cache-Control` directive at the CDN layer.
