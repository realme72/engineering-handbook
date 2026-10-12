# Redis

# Why Does Redis Exist?

Memcached, Redis's older sibling, proved that an in-memory key-value store could dramatically speed up read-heavy applications — but it was deliberately minimal: strings in, strings out, nothing else. Real applications kept running into the same wall: they needed a *little* more structure than a flat key-value string store gives them — a sorted set for a leaderboard, a list for a simple queue, atomic increment for a counter — and reached for a full relational database just to get it, paying disk-backed latency for what was fundamentally still a simple, fast-access problem.

Redis's actual pitch is narrower and more useful than "a faster Memcached": it's an in-memory data structure store, not just a key-value cache. The same server that caches a rendered HTML fragment can also maintain a sorted leaderboard, a rate-limiting counter, and a simple job queue — because it natively understands more than just "a string."

```
Memcached:  key → string, that's it

Redis:      key → string
                → hash (a nested object)
                → list
                → set
                → sorted set (score-ordered)
                → stream (an append-only log)
```

---

# What Problem It Actually Solves

- **Sub-millisecond access to hot data** — everything lives in memory, avoiding disk I/O entirely for reads and writes.
- **Native data structures beyond a flat key-value string** — a sorted set is a leaderboard for free; a list is a simple queue for free; you don't have to serialize a JSON blob and reimplement structure-specific operations in application code.
- **Atomic operations without your own locking** — `INCR`, `SETNX`, and Lua scripting let you do check-and-update logic atomically, inside Redis itself, instead of racing multiple clients against each other in application code.
- **More than "just a cache"** — session storage, rate limiting counters (exactly the token bucket implementation from the Rate Limiting chapter), simple pub/sub messaging, and lightweight job queues all commonly run directly on Redis, not a separate specialized system.

---

# Why Redis Is Fast: The Single-Threaded Event Loop

This is a genuinely counterintuitive design choice that surprises people the first time they learn it: Redis's core command processing is single-threaded, and that's a deliberate design decision, not a limitation someone hasn't gotten around to fixing.

```
Multi-threaded approach:  many threads, locks around shared data structures,
                          context-switching overhead, coordination complexity

Redis's approach:         ONE thread processes commands, one at a time,
                          no locks needed at all, since nothing runs concurrently
```

Because only one command executes at any instant, there's no possibility of two operations racing on the same data structure — every command is inherently atomic relative to every other command, with zero locking overhead. Combined with everything living in memory (no disk-wait to hide latency behind), a single thread turns out to be plenty fast — Redis can handle well over 100,000 operations per second on modest hardware precisely because it never pays for lock contention or context switching in the first place.

## The Catch: One Slow Command Blocks Everything

```
KEYS *          →  scans every single key in the entire keyspace, O(n)

↓

While this runs, EVERY other client's command waits — the single thread
is busy, and there's no other thread to pick up the slack
```

This is the direct, unavoidable cost of the single-threaded design — a genuinely slow command doesn't just run slowly, it blocks the entire server for every other connected client during that time. This is exactly why `KEYS *` is considered dangerous in production Redis (use `SCAN`, which walks the keyspace incrementally without blocking, instead) and why understanding a command's actual time complexity before running it against a large dataset matters far more in Redis than it might in a system where one slow operation only affects the thread running it.

---

# Core Data Structures, With Real Use Cases

## Strings — The Simplest Cache Entry

```python
r.setex("product:15:name", 300, "Wireless Mouse")
```

## Hashes — A Structured Object Without Serializing JSON Yourself

```python
r.hset("user:42", mapping={"name": "Alice", "email": "alice@example.com"})
r.hget("user:42", "email")
```

## Sorted Sets — A Leaderboard, For Free

```python
r.zadd("leaderboard", {"alice": 1500, "bob": 1200, "carol": 1800})

r.zrevrange("leaderboard", 0, 2, withscores=True)
# [("carol", 1800), ("alice", 1500), ("bob", 1200)]  — top 3, already sorted
```

Every member is kept in score-sorted order automatically — no separate `ORDER BY` query, no re-sorting in application code. This single data structure is why "how would you implement a leaderboard" so often gets answered with "a Redis sorted set" rather than a hand-rolled solution.

## Atomic Counters — Rate Limiting, Revisited

```python
count = r.incr("rate_limit:user_42")
if count == 1:
    r.expire("rate_limit:user_42", 60)

if count > 100:
    raise TooManyRequests()
```

This is the exact token/fixed-window counter mechanic from the Rate Limiting chapter — `INCR` is atomic in Redis, meaning two concurrent requests incrementing the same counter can never race and silently lose an increment, without the application needing to implement any locking of its own.

## Distributed Locks — `SET NX EX`

```python
lock_acquired = r.set("lock:order_15", "1", nx=True, ex=10)
```

`SETNX` (or the modern combined form, `SET key value NX EX seconds`) atomically sets a key only if it doesn't already exist, with an expiration — the exact building block used for the cache stampede lock in the previous chapter, and a common way to implement a simple distributed mutex across multiple application servers that don't share memory.

---

# Persistence: RDB vs AOF

Redis is in-memory, but "in-memory" doesn't have to mean "gone forever on restart" — it supports two, combinable, persistence mechanisms.

## RDB (Snapshotting)

```
Periodically (e.g. every 5 minutes, or after N writes):
    fork the process → write the ENTIRE in-memory dataset to a single file
```

Compact and fast to restore from, but a crash between snapshots loses every write since the last one — potentially several minutes of data.

## AOF (Append-Only File)

```
Every write command is appended to a log file, in order, as it happens
```

Conceptually the same idea as a database's write-ahead log (from the ACID chapter) — replaying the log on restart reconstructs the exact sequence of writes. Far more durable (configurable down to "fsync on every single write," minimizing loss to essentially nothing), at the cost of a larger file and slower restart, since recovery means replaying potentially a very long command history rather than loading one compact snapshot.

```
RDB   →  faster restarts, smaller files, larger potential data loss window
AOF   →  minimal data loss, slower restarts, larger files

Many production deployments run BOTH, using RDB for fast bulk backups
and AOF for a tighter durability guarantee in between snapshots.
```

For a pure cache — data that can be safely, correctly reconstructed from a database if lost — persistence might not matter much at all. For Redis used as a primary store for something (a job queue, session data with no other backing store), persistence configuration becomes a genuinely important durability decision, not an afterthought.

---

# High Availability: Sentinel and Cluster

```
Redis Sentinel   →  monitors a primary/replica setup, automatically promotes
                     a replica if the primary fails (conceptually the same
                     failover problem covered in the Replication chapter)

Redis Cluster    →  shards data across multiple nodes using hash slots
                     (16,384 fixed slots, distributed among however many
                     nodes are in the cluster) — the same underlying
                     problem and motivation as the Sharding chapter,
                     applied specifically to Redis
```

Both exist because a single Redis instance, however fast, is still one machine — a single point of failure for anything depending on it, and eventually a ceiling on how much data or throughput one instance can hold. The concepts here aren't new; they're the same replication and sharding ideas from the Databases section, applied to an in-memory data store instead of a disk-backed relational one.

---

# Real-World Examples

### Rate Limiting (Twitter, Stripe, most API gateways)

The `INCR` + `EXPIRE` pattern above is close to the industry-standard way to implement a simple, effective rate limiter — atomic, fast, and requiring no application-level locking, directly reusing the token bucket / fixed window concepts from the Rate Limiting chapter.

---

### Sidekiq (Ruby background job processing)

Uses Redis lists and sorted sets directly as the backing store for job queues — a job is pushed onto a list, workers pop jobs off it, and scheduled/delayed jobs use a sorted set keyed by their execution time, all without needing a separate dedicated message queue system for a large share of real-world background job workloads.

---

### Twitter Timeline Caching

Historically used Redis-backed caching heavily for assembling and serving user timelines — read-heavy, latency-sensitive data that benefits enormously from in-memory access, with sorted sets being a natural fit for maintaining a timeline's chronological or ranked order.

---

# Common Interview Questions

## Why is Redis fast despite being single-threaded?

Because it avoids the overhead multi-threading would otherwise require — no locks around shared data structures, no context-switching between threads — since only one command executes at any instant, every command is inherently atomic relative to every other. Combined with everything living in memory rather than on disk, a single thread turns out to be sufficient for very high throughput, since there's no I/O wait to hide behind extra threads in the first place.

---

## What's a real risk of Redis's single-threaded design?

A slow command (like `KEYS *`, which scans the entire keyspace) blocks every other client's command for its entire duration, since there's no second thread to pick up the slack. This is why understanding a command's time complexity before running it in production matters more in Redis than in many multi-threaded systems, and why `SCAN` (which walks the keyspace incrementally without blocking) is preferred over `KEYS *`.

---

## RDB vs AOF — what's the trade-off?

RDB takes periodic full snapshots — fast to restore, smaller files, but can lose everything written since the last snapshot on a crash. AOF logs every write command as it happens — much smaller data-loss window (configurable down to nearly zero), but slower to restore and a larger file, since recovery means replaying the write history rather than loading one compact snapshot. Many production setups combine both.

---

## How would you implement a leaderboard using Redis?

A sorted set (`ZADD`), keyed by user with score as their leaderboard value — Redis maintains score-sorted order automatically, so retrieving the top N (`ZREVRANGE`) or a specific user's rank (`ZREVRANK`) is a direct, efficient operation with no separate sorting step needed in application code.

---

## How would you implement a simple distributed lock with Redis?

`SET key value NX EX seconds` — atomically sets the key only if it doesn't already exist, with an expiration so the lock is automatically released even if the holder crashes before explicitly releasing it. This is the same mechanism used to prevent cache stampedes in the previous chapter, applied more generally as a distributed mutex across multiple application servers.

---

# Common Mistakes

❌ Running `KEYS *` against a large production keyspace.

Blocks every other client for the entire scan duration, since Redis is single-threaded — use `SCAN` instead, which walks the keyspace incrementally without blocking.

---

❌ Treating Redis as durable by default without configuring persistence appropriately.

If Redis is being used for more than a disposable cache — session data, a job queue with no other backing store — the default persistence settings need to be deliberately reviewed, not assumed.

---

❌ Not setting a `maxmemory-policy`.

Without an eviction policy configured, Redis can either run out of memory and start rejecting writes (`noeviction`, the default) or behave unpredictably under memory pressure — this should be a deliberate choice (see the Cache Eviction Policies chapter), not left to the default.

---

❌ Storing very large values in a single key.

A single very large hash, list, or string can cause noticeable latency spikes on the operations that touch it, precisely because of the single-threaded design — a slow operation on one big key blocks every other client's fast operations on entirely unrelated keys during that time.

---

# Key Takeaways

- Redis is an in-memory data structure store, not just a key-value cache — sorted sets, hashes, and lists solve real problems (leaderboards, structured objects, queues) natively, without hand-rolled serialization.
- Its single-threaded design is what makes it fast, not despite being single-threaded — no locking overhead, since only one command ever executes at a time — but it also means one slow command blocks every other client simultaneously.
- `INCR` and `SET NX EX` provide atomic operations Redis makes trivial and application code would otherwise have to implement its own locking for — directly reused in both rate limiting and cache stampede prevention.
- RDB (periodic snapshots) and AOF (append-only write log) are Redis's two persistence mechanisms, trading restore speed and file size against how much data could be lost in a crash — many production systems run both together.
- Redis Sentinel (failover) and Redis Cluster (sharding via hash slots) apply the same replication and sharding concepts from the Databases section specifically to an in-memory store, for the same underlying reasons — durability, availability, and scaling past one machine's limits.
