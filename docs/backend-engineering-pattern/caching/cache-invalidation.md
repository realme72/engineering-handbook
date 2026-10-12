# Cache Invalidation

# Why Is This "One of the Two Hard Things in Computer Science"?

The joke — "there are only two hard things in computer science: cache invalidation, naming things, and off-by-one errors" — is funny specifically because cache invalidation genuinely is harder than it sounds on first encounter.

The problem in its simplest form:

```
Database:  user.name = "Alice"

Cache:     user:42:name = "Alice"    (cached 10 minutes ago)

↓

Application updates the database:  user.name = "Alicia"

↓

Cache still says "Alice" — nobody told it anything changed
```

The core difficulty isn't storing a copy of data — that part is easy. It's reliably knowing the *exact moment* that copy becomes wrong, across every possible code path that might change the underlying data, without either serving stale data for too long or invalidating so aggressively that the cache stops providing any benefit at all.

---

# The Two Baseline Strategies

## TTL-Based Expiration

```python
redis_client.setex(f"user:{user_id}:name", 300, name)  # expires automatically after 5 minutes
```

The simplest possible answer: accept that data might be stale for up to some bounded window, and let it expire on its own. No code path needs to remember to invalidate anything — staleness is capped by the TTL, and that's the whole guarantee.

The trade-off is obvious once stated plainly: for those up-to-5-minutes, a genuinely changed value can still be served as if nothing happened. Whether that's acceptable depends entirely on the data — a product's display name being 5 minutes stale is fine; a user's account balance being 5 minutes stale after a withdrawal is not.

## Explicit Invalidation on Write

```python
def update_user_name(user_id: int, new_name: str):
    db.execute("UPDATE users SET name = %s WHERE id = %s", (new_name, user_id))
    redis_client.delete(f"user:{user_id}:name")   # invalidate immediately, on the write path
```

Every code path that changes the underlying data is also responsible for invalidating (or updating) the corresponding cache entry, immediately, as part of the same operation. This closes the TTL's staleness window almost entirely — but only as reliably as every single write path actually remembers to do it, which is precisely where this strategy tends to break down in a large, real codebase with many ways to modify the same underlying data.

---

# Why Delete, Not Update, on a Write

A subtle but important design decision: when invalidating on write, prefer **deleting** the cache key over directly writing the new value into it.

```python
# Riskier: writing the new value directly into the cache on write
def update_user_name_v1(user_id: int, new_name: str):
    db.execute("UPDATE users SET name = %s WHERE id = %s", (new_name, user_id))
    redis_client.set(f"user:{user_id}:name", new_name)

# Safer: delete the cache key, let the next READ repopulate it
def update_user_name_v2(user_id: int, new_name: str):
    db.execute("UPDATE users SET name = %s WHERE id = %s", (new_name, user_id))
    redis_client.delete(f"user:{user_id}:name")
```

Here's the race condition that "update on write" is exposed to, and "delete on write" avoids:

```
T1: reads OLD value from DB (in-flight, hasn't cached yet)

T2: writes NEW value to DB
T2: writes NEW value to cache

T1: (finishes its slow read) writes the OLD value into the cache

↓

Cache now holds the OLD value, permanently (or until TTL),
even though the database has the correct NEW value
```

If a write instead just *deletes* the cache key, the same race is far less damaging — the next read (whether it's T1 finishing its stale read or a brand new request) simply repopulates the cache from the database, which by then has the correct value. Deleting can't leave a *wrong* value sitting in the cache the way overwriting it with a stale value can; at worst, it causes an extra cache miss, never a wrong cache hit.

---

# Versioned Cache Keys (Cache-Busting)

Instead of invalidating an old value, make the old value permanently unreachable by changing the key itself.

```python
# Include a version number as part of the key
cache_key = f"user:{user_id}:v{user_version}:profile"
```

```
User's profile updated → bump user_version from 3 to 4

↓

Old key "user:42:v3:profile" is now simply never looked up again
(it eventually falls out of the cache naturally via its own TTL or eviction)

New reads use "user:42:v4:profile" — a guaranteed cache miss, correctly
recomputed from the current database state
```

This sidesteps the entire "did every write path remember to explicitly delete the right key" problem — there's nothing to explicitly delete, because the version bump alone makes the previous key unreachable. The cost: the stale, orphaned old-version entries linger in the cache until they naturally expire or get evicted, technically wasting some memory in the meantime.

---

# Multi-Layer Invalidation

Real systems often cache the same logical data at several layers simultaneously — an application-level Redis cache, a CDN edge cache, and the user's own browser cache. Invalidating just one layer doesn't help if a stale copy is still being served from another.

```
Source of Truth (Database)

↓

Application Cache (Redis)     — invalidated by application code on write

↓

CDN Edge Cache                 — invalidated by an explicit purge API call

↓

Browser Cache                  — controlled by Cache-Control headers,
                                   generally can't be actively "pushed" an
                                   invalidation at all, only expires on its own
```

This is exactly why a coordinated cache invalidation strategy for a real production system usually needs to reason about every layer explicitly (the CDN chapter covers the specific mechanics of edge cache purging), rather than assuming that invalidating the application-level cache is sufficient on its own.

---

# Real-World Examples

### Facebook — Invalidation via Database Change Streams

Rather than relying on every single application code path to remember to manually invalidate memcache on every write, Facebook's infrastructure listens directly to the MySQL replication stream (the same binlog mechanism covered in the Replication chapter) and uses it to automatically invalidate corresponding cache entries whenever the underlying row changes — moving the responsibility for correctness out of scattered application code and into one centralized, reliable mechanism.

---

### Instagram

Uses a similar pattern for feed and profile caches — deliberately favoring "delete on write, repopulate on next read" over "update on write," for exactly the race-condition-avoidance reason described above.

---

### Stripe API — Cache-Control on Read Endpoints

Read-heavy, rarely-changing endpoints (e.g. certain reference/configuration data) are given TTL-based caching headers with modest expiration windows, deliberately accepting a small amount of staleness in exchange for not needing perfect, comprehensive explicit invalidation coverage across every possible write path.

---

# Common Interview Questions

## Why is cache invalidation considered genuinely hard?

Because correctly invalidating a cache means correctly identifying every possible code path that could change the underlying data and ensuring each one properly notifies the cache — miss even one, in a large codebase with many ways to modify the same data, and that path silently serves stale data indefinitely (or until a TTL bails it out). It's a coverage problem across the whole codebase, not a single localized piece of logic.

---

## Why prefer deleting a cache key over updating it directly on a write?

Deleting avoids a specific race condition: a slow, in-flight read that started before the write can finish afterward and overwrite the cache with the old, now-incorrect value, if the cache was written to directly. Deleting instead just causes the next read to repopulate the cache from the database — which by then reflects the write — turning a potential permanent wrong-value bug into, at worst, one extra cache miss.

---

## How does TTL-based expiration relate to explicit invalidation — do you need both?

Yes, in most real systems. Explicit invalidation minimizes staleness for the common, well-covered write paths, but TTL acts as a safety net for anything that falls through the cracks — a write path someone forgot to add invalidation to, a direct database change outside the application (a manual fix, a batch job), or a bug in the invalidation logic itself. Relying on explicit invalidation alone, with no TTL fallback, means any single missed invalidation path can leave stale data cached indefinitely.

---

## What is a versioned cache key, and what problem does it solve?

Embedding a version number in the cache key itself, so bumping the version on a change makes the old key permanently unreachable without needing to explicitly find and delete it. It solves the "did every write path remember to invalidate the right key" reliability problem, at the cost of orphaned old-version entries lingering in the cache until they naturally expire or get evicted.

---

## Why is invalidating a CDN cache harder than invalidating an application-level cache?

Because a CDN cache is replicated across many geographically distributed edge locations, and purging a key generally means propagating that purge out to every one of them — which is neither instantaneous nor as simple as a single `DELETE` against one in-memory store. This is why CDN purges often have measurable propagation delay, unlike a local Redis `DEL`.

---

# Common Mistakes

❌ Writing the new value directly into the cache on a write, instead of deleting the key.

Exposes the system to a race condition where a slow, in-flight read can overwrite the cache with a stale value after the write already completed.

---

❌ Relying entirely on explicit invalidation, with no TTL as a fallback.

Any single write path someone forgot to add invalidation to — or any change made outside normal application code (a manual DB fix, a batch job) — can leave stale data cached indefinitely with no natural recovery.

---

❌ Invalidating only the application-level cache and forgetting about a CDN or browser layer caching the same data.

A stale response can still be served from a layer that was never told anything changed, even though the "real" cache was correctly invalidated.

---

❌ Setting a TTL so long that explicit invalidation gaps go unnoticed for a long time, or so short that the cache barely provides any benefit at all.

The TTL should be chosen deliberately based on how stale the specific data can tolerably be — not copy-pasted as a default value across every cache key regardless of what it actually holds.

---

# Key Takeaways

- Cache invalidation is hard because it requires correctly identifying and covering every code path that could change the underlying data — missing even one leaves a silent, hard-to-notice source of stale reads.
- TTL-based expiration and explicit invalidation solve different failure modes and are typically used together — TTL as a safety net, explicit invalidation to minimize staleness on well-known write paths.
- Deleting a cache key on write is safer than updating it directly, because it avoids a specific race condition where a slow, in-flight read could overwrite the cache with a stale value after a newer write already landed.
- Versioned cache keys sidestep the "did every write path remember to invalidate" reliability problem entirely, at the cost of some memory spent on orphaned old-version entries until they naturally expire.
- Real systems often cache the same data at multiple layers (application, CDN, browser) — a complete invalidation strategy has to account for every layer, not just the one closest to the application code.
