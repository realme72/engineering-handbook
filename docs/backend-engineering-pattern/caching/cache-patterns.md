# Cache Patterns

# Why Does Caching Exist?

Some data is expensive to produce and cheap to reuse.

```
Query: SELECT * FROM products WHERE category = 'electronics' ORDER BY popularity;

↓

Joins across 3 tables, sorts 50,000 rows, runs on every single page view

↓

The exact same result, for the exact same category, for the next 10,000 requests
```

If a thousand people load the electronics category page in the next minute, and the underlying data hasn't changed, running that same expensive query a thousand times is pure waste — the database does the same work over and over to produce an answer that was already sitting there, computed, a second ago.

A cache is simply a fast, temporary store that holds the *result* of expensive work, so the next request that needs the same thing can skip redoing it.

```
Without a cache:  every request → hits the database → recomputes the result

With a cache:     first request  → computes it, stores the result
                  every request after → reads the stored result directly
```

The speed difference isn't incidental — reading from memory (Redis, an in-process cache) is routinely 10-100x faster than a database round trip involving disk I/O, query planning, and execution. That gap is the entire economic case for caching.

---

# What Problem It Actually Solves

- **Reduces load on the expensive source of truth** — a database, a slow computation, a third-party API with its own rate limits and costs.
- **Reduces latency for the caller** — reading from memory is dramatically faster than recomputing from scratch.
- **Absorbs traffic spikes** — a sudden burst of identical requests hits the cache, not the fragile system behind it.

What caching does **not** do: replace the source of truth. A cache is disposable — if it's wiped out entirely, the system should still work correctly (just slower, temporarily), by falling back to recomputing from the real source of truth. If losing the cache would lose data permanently, that's not a cache, it's an undocumented second database.

---

# Cache-Aside (Lazy Loading)

The most common pattern in practice — the application code explicitly manages the cache, checking it first and falling back to the source of truth on a miss.

```
Read:

Application → check cache
                ├── HIT  → return cached value
                └── MISS → read from database
                              ↓
                           store in cache
                              ↓
                           return value
```

```python
def get_product(product_id: int):
    cached = redis_client.get(f"product:{product_id}")
    if cached is not None:
        return json.loads(cached)  # cache hit

    product = db.query("SELECT * FROM products WHERE id = %s", (product_id,))
    redis_client.setex(f"product:{product_id}", 300, json.dumps(product))  # cache miss — populate, 5 min TTL
    return product
```

The cache only ever contains what's actually been requested — nothing is pre-loaded speculatively, which makes this pattern simple and memory-efficient, at the cost of every *first* request for a given key always paying the full, uncached latency (a "cold" cache miss).

---

# Read-Through

Conceptually similar to cache-aside, but the caching logic lives inside the caching layer itself, not the application — the application only ever talks to the cache, and the cache is responsible for fetching from the underlying store on a miss.

```
Application → Cache
                ├── HIT  → return cached value
                └── MISS → Cache itself fetches from the database,
                            stores it, THEN returns it to the application
```

The application code becomes simpler (`cache.get(key)` always "just works," never needs its own miss-handling branch), at the cost of needing a caching layer sophisticated enough to know how to reach the underlying data store itself — which is why this is more commonly seen as a feature of a dedicated caching framework or service than something hand-rolled directly against Redis.

---

# Write-Through

Every write goes to the cache and the database together, as part of the same operation, before the write is considered complete.

```
Application writes  →  Cache  →  Database
                        (both updated before returning success)
```

```python
def update_product_price(product_id: int, new_price: float):
    db.execute("UPDATE products SET price = %s WHERE id = %s", (new_price, product_id))
    redis_client.setex(f"product:{product_id}", 300, json.dumps({"id": product_id, "price": new_price}))
```

The cache is never stale relative to the database, because they're updated together — a strong consistency guarantee cache-aside doesn't provide by default. The cost: every write now pays the latency of writing to both systems, and if the cache write fails after the database write succeeds (or vice versa), the two can still drift apart — this needs its own handling, it isn't automatically solved just by calling it "write-through."

---

# Write-Behind (Write-Back)

Writes go to the cache immediately and are persisted to the database *later*, asynchronously, often batched.

```
Application writes  →  Cache  (fast, returns success immediately)

↓  (happens later, asynchronously, in the background)

Database  ←  batched writes flushed from the cache
```

This is significantly faster for the writer — no waiting on a database round trip — and can batch many writes into fewer, more efficient database operations. The real risk: if the cache crashes before those pending writes are flushed to the database, that data is genuinely lost, not just temporarily stale. This pattern is reserved for data where that risk is acceptable (view counts, non-critical analytics events) — never for anything where losing a write is unacceptable, like a financial transaction.

---

# Write-Around

Writes go directly to the database, bypassing the cache entirely. The cache only gets populated later, lazily, the next time that data happens to be read (falling back to cache-aside's read path).

```
Application writes  →  Database only

↓ (cache is NOT updated)

Next read for this data  →  cache MISS (stale/absent)  →  reads from DB  →  populates cache
```

Useful specifically for data that's written often but read rarely — avoiding the wasted work of caching something on every write when most of those cached writes will expire, unread, before anyone ever asks for them. The trade-off: a read immediately after a write is guaranteed to be a cache miss, paying full latency, since the cache was never updated by the write itself.

---

# Choosing a Pattern

| Pattern | Consistency | Write Latency | Best For |
|---|---|---|---|
| Cache-Aside | Eventual (until TTL/invalidation) | Normal (writes untouched) | General-purpose, most common default |
| Read-Through | Eventual | Normal | Same as cache-aside, logic lives in the cache layer |
| Write-Through | Strong (cache always fresh) | Higher (writes both systems) | Read-heavy data that must never be stale |
| Write-Behind | Strong from the reader's view, but risky | Very low | High write volume, tolerant of rare data loss |
| Write-Around | N/A for cache | Low (cache untouched on write) | Write-heavy, rarely-read data |

Cache-aside is the default the overwhelming majority of real applications reach for, precisely because it's simple, cache-agnostic (the cache can be wiped entirely and the system just gets slower, never wrong), and doesn't require coupling writes to cache updates at all.

---

# Real-World Examples

### Facebook / Memcached ("Scaling Memcache at Facebook")

Facebook's widely-cited engineering paper on their memcache deployment describes, at enormous scale, essentially cache-aside as the dominant pattern — application servers read from memcache, fall back to MySQL on a miss, and populate the cache themselves — precisely because it decouples the cache's health from the correctness of the system entirely.

---

### Stripe API Response Caching

Read-heavy, rarely-changing reference data (a merchant's own configuration, product catalog data) is a natural fit for cache-aside with a modest TTL — the cost of an occasional few-seconds-stale read is far lower than the cost of hitting the primary database for every single request.

---

### View Counters / Analytics Events

A classic write-behind use case — incrementing a "views" counter on every page load doesn't need to hit the database synchronously on every single view; batching those increments and flushing periodically dramatically reduces write load, and losing a few increments during a rare crash is an acceptable trade nobody will notice.

---

# Common Interview Questions

## Cache-aside vs read-through — what's the actual difference?

Both fall back to the source of truth on a miss and populate the cache afterward — the difference is *where* that logic lives. In cache-aside, the application code explicitly checks the cache and handles the miss. In read-through, the caching layer itself is responsible for fetching from the underlying store on a miss, so the application only ever talks to the cache.

---

## Why would you choose write-through over cache-aside?

When the cache must never serve stale data relative to the database — write-through updates both together as part of the same operation, giving a stronger consistency guarantee than cache-aside's "eventually correct after the next read populates it" behavior. The cost is higher write latency, since every write now touches two systems instead of one.

---

## What's the risk with write-behind caching, and when is it acceptable?

If the cache crashes before pending writes are flushed to the database, that data is genuinely, permanently lost — not just temporarily stale. It's acceptable for data where losing a small amount is tolerable (view counters, non-critical analytics) and never acceptable for data where every write must be durable (financial transactions, order records).

---

## When would you use write-around instead of write-through?

When data is written far more often than it's read — caching on every write would waste memory and effort on data that expires unread before anyone asks for it. The trade-off is that a read immediately following a write is guaranteed to miss the cache, since the write never touched it.

---

# Common Mistakes

❌ Treating the cache as the system's source of truth.

If wiping the cache would lose real data, it isn't a cache — a cache should always be safely reconstructable from the actual source of truth.

---

❌ Using write-behind for data that can't tolerate loss.

The performance win isn't worth it if a crash before the next flush means a lost financial transaction or order record.

---

❌ Populating the cache on every write with write-around-style data.

Wastes cache memory and effort on data that will expire, unread, long before anyone queries it — write-around exists specifically to avoid this for write-heavy, rarely-read data.

---

❌ Assuming write-through guarantees the cache and database can never drift apart.

If the cache write succeeds but the database write fails (or the reverse), the two are now inconsistent — write-through reduces this risk compared to cache-aside, but doesn't eliminate the need to handle partial failure explicitly.

---

# Key Takeaways

- Caching exists because some data is expensive to compute and cheap to reuse — a cache stores the result once and serves it repeatedly instead of recomputing it for every request.
- A cache should always be disposable — safely reconstructable from the real source of truth — never itself the only copy of important data.
- Cache-aside (application checks cache, falls back to source on miss, populates cache) is the most common default, precisely because it's simple and decouples the cache's health from system correctness.
- Write-through trades write latency for strong cache/database consistency; write-behind trades durability risk for very low write latency; write-around avoids caching write-heavy, rarely-read data at all.
- The right pattern depends on your actual read/write ratio and how much staleness or risk your specific data can tolerate — there's no universally "best" pattern, only the right trade-off for a given access pattern.
