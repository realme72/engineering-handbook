# Distributed Cache

# Why Does a Distributed Cache Exist?

A single Redis or Memcached instance is still just one machine, and one machine has the same two structural limits every single-machine system eventually hits:

```
Problem 1: Memory ceiling.
           One machine's RAM caps how much can ever be cached at once,
           no matter how much you'd benefit from caching more.

Problem 2: Single point of failure.
           That one instance goes down → every application server
           depending on it suddenly loses its entire cache simultaneously,
           and every one of them falls back to the database at once
           (a cache stampede at the scale of your ENTIRE cache, not just one key).
```

A distributed cache spreads cached data across multiple machines — the exact same motivation as Sharding a database, applied to a cache instead. More total memory to work with, and no single machine's failure taking down the entire cached layer at once.

```
Single cache instance:              Distributed cache:

App Servers → ONE Redis instance     App Servers → Cache Node 1
                                                  → Cache Node 2
                                                  → Cache Node 3
```

---

# What Problem It Actually Solves

- **More total cache capacity** than any single machine's memory allows.
- **No single point of failure** for the cache layer as a whole — one node's failure only affects the slice of data it held, not everything.
- **Higher aggregate throughput** — spreading requests across multiple nodes instead of funneling every cache operation through one machine.

---

# Client-Side Sharding

The application itself decides which cache node holds a given key, using a hashing scheme, without any coordinating server in between.

```python
def get_cache_node(key: str, nodes: list):
    index = hash(key) % len(nodes)
    return nodes[index]

node = get_cache_node("product:15", ["cache-1", "cache-2", "cache-3"])
```

Simple, and avoids adding an extra network hop through a coordinating proxy — the client goes directly to the right node. The direct downside is the exact same one covered in the Sharding chapter: plain `hash(key) % N` reassigns nearly every key's node the moment `N` changes, meaning adding or removing a single cache node can invalidate almost the entire cache all at once — a self-inflicted cache stampede at the worst possible moment (right when you're trying to scale the cache layer up).

## Consistent Hashing, Again

```
Cache nodes and keys both mapped onto a fixed hash ring
(the exact same technique from the Sharding chapter)

Adding a new cache node only reassigns the small slice of keys
immediately adjacent to it on the ring — every other key's node
assignment is completely unaffected
```

This is the same consistent hashing solution covered in depth for database sharding, applied here for exactly the same reason — a distributed cache's node topology needs to change (scaling up, replacing a failed node) without a naive hashing scheme forcing a near-total cache wipe every time it does.

---

# Server-Side Sharding (Cluster Mode)

Instead of the application computing which node to talk to, a cluster-aware protocol or a coordinating layer handles routing internally.

```
Redis Cluster:  16,384 fixed hash slots, distributed among however many
                nodes are currently in the cluster

Client sends a command → cluster redirects to whichever node currently
                          owns that key's slot, if the client didn't
                          already know
```

This moves the routing complexity out of every individual application's client code and into the cache infrastructure itself — a genuine operational simplification once you have many application services all needing to talk to the same distributed cache correctly.

---

# Cache Replication for Availability

Sharding spreads *different* data across nodes; replication keeps *copies* of the same data on multiple nodes — the same distinction as Sharding vs Replication for databases, applied here.

```
Primary cache node for key "user:42"  →  Replica node (keeps a copy)

If the primary fails → replica can be promoted, data isn't gone
```

Without replication, losing a single shard's cache node doesn't just lose that node's worth of cache capacity — it means every key that lived on it now misses simultaneously, which can itself trigger a stampede back to the database for that entire slice of data at once. Replication trades additional memory cost for exactly the durability and failover story the Replication chapter covers for databases, applied to cache infrastructure.

---

# Multi-Tier Caching: Local (L1) + Distributed (L2)

A pattern common enough in high-traffic systems to be worth calling out directly: keeping a small, fast, in-process cache on each application server *in addition to* a shared distributed cache.

```
Application Server

↓ check LOCAL in-process cache first (nanoseconds, no network hop at all)
    ├── HIT  → return immediately
    └── MISS ↓

  check DISTRIBUTED cache (Redis) — still fast, but a real network round trip
      ├── HIT  → return, ALSO populate the local cache for next time
      └── MISS → fetch from database, populate both cache layers
```

For an extremely hot key — read by every single request on every server — even a fast Redis round trip is unnecessary overhead compared to reading directly from the requesting server's own memory. This tiered approach captures both: a distributed cache's shared, larger capacity, and a local cache's near-zero latency for the smallest set of truly hottest keys.

## The Cost: Local Cache Invalidation Gets Genuinely Harder

```
User updates their profile

↓

Distributed cache (Redis): invalidated — one DELETE, done

↓

Local cache on Server A: still has the OLD value
Local cache on Server B: still has the OLD value
Local cache on Server C: still has the OLD value
```

Invalidating one shared Redis key is a single operation. Invalidating the *same* data cached locally in-process on every single application server means reaching all of them — which requires a broadcast mechanism, commonly implemented via Redis's own pub/sub: publish an "invalidate this key" message, and every application server subscribes and clears its own local copy on receipt.

```python
def invalidate_everywhere(key: str):
    redis_client.delete(key)                          # distributed cache
    redis_client.publish("cache_invalidation", key)    # broadcast to all local caches

# each application server, in a background listener:
def on_invalidation_message(key: str):
    local_cache.pop(key, None)
```

This is a real, meaningful complexity cost, which is exactly why multi-tier local caching is reserved for genuinely hot keys where the latency win is worth the added invalidation coordination — not applied indiscriminately to everything just because a local cache is technically faster.

---

# Real-World Examples

### Memcached's Client-Side Consistent Hashing

One of the earliest and most widely cited real-world uses of consistent hashing specifically to solve this problem — Memcached itself has no built-in clustering, so client libraries implement consistent hashing to distribute keys across a pool of independent Memcached instances without a coordinating server in between.

---

### Redis Cluster's Hash Slots

A concrete, specific implementation of server-side sharding — 16,384 fixed slots divided among however many nodes exist, giving predictable, manageable rebalancing when nodes are added or removed (redistributing whole slots, not recomputing every individual key's placement from scratch).

---

### Caffeine (Local) + Redis (Distributed) — A Common Java/JVM Pattern

A widely used real-world instance of the multi-tier pattern — an in-process, extremely fast local cache (Caffeine) backed by a shared Redis layer, specifically for data hot enough that even a Redis round trip is worth avoiding on the absolute hottest read paths.

---

# Common Interview Questions

## Why would a single Redis/Memcached instance not be enough for a large system?

Two structural limits: total memory is capped by one machine's RAM, and that one instance is a single point of failure — if it goes down, every application server relying on it loses its entire cache simultaneously, potentially triggering a stampede back to the database at the scale of the whole cache, not just one key.

---

## Client-side vs server-side sharding for a distributed cache — what's the difference?

Client-side sharding has the application itself compute which node owns a key (via a hashing scheme) and talk to that node directly — simple, no extra hop, but every client needs consistent, correctly-configured hashing logic. Server-side sharding (like Redis Cluster) handles routing within the cache infrastructure itself, moving that complexity out of every individual application's code.

---

## Why does plain `hash(key) % N` cause problems when scaling a distributed cache?

Because changing `N` (adding or removing a node) reassigns nearly every key's target node at once — effectively invalidating almost the entire cache simultaneously right when you're trying to scale it, which can itself trigger a database-hammering stampede. Consistent hashing solves this the same way it does for database sharding — only reassigning the small slice of keys adjacent to the actual change.

---

## What's the benefit of a local (in-process) cache layer in addition to a distributed cache?

Avoiding even the fast network round trip to a distributed cache for the very hottest keys — a local, in-process read is nanoseconds versus a network hop that, while fast, is still meaningfully slower at very high request volume. The cost is a genuinely harder invalidation problem, since the same data now needs to be invalidated across every application server's own local copy, typically via a pub/sub broadcast mechanism.

---

## How do you invalidate a local cache that's duplicated across many application servers?

Since there's no single shared store to delete a key from, you need an explicit broadcast — commonly implemented with the distributed cache's own pub/sub capability (Redis `PUBLISH`/`SUBSCRIBE`): publish an invalidation message for the key, and have every application server's background listener clear its own local copy on receipt.

---

# Common Mistakes

❌ Using plain `hash(key) % N` sharding for a distributed cache without considering consistent hashing.

Makes scaling the cache layer itself a self-inflicted stampede — adding or removing one node reshuffles almost every key's location at once.

---

❌ No replication for cache nodes holding genuinely hot data.

A single node failure means every key it held misses simultaneously, which can spike the database hard enough to cause a real incident — replication trades memory cost for avoiding exactly this.

---

❌ Adding a local (L1) cache layer without a real invalidation strategy.

A stale local cache on even one application server can serve outdated data indefinitely if there's no broadcast mechanism to notify every server when the underlying data changes.

---

❌ Applying multi-tier local caching indiscriminately instead of reserving it for genuinely hot keys.

The added invalidation complexity is a real cost — worth paying only where the latency win (avoiding even a fast distributed-cache round trip) is actually significant for that specific data.

---

# Key Takeaways

- A distributed cache exists to scale past a single machine's memory ceiling and eliminate the cache layer as a single point of failure — the same underlying motivation as database sharding, applied to a cache.
- Client-side sharding puts routing logic in the application; server-side sharding (Redis Cluster) handles it within the cache infrastructure itself — both need consistent hashing to avoid a near-total cache invalidation every time a node is added or removed.
- Cache replication protects against a single node's failure causing every key it held to miss simultaneously, which can itself trigger a database-hammering stampede.
- Multi-tier caching (a fast local in-process cache backed by a shared distributed cache) captures both very low latency for the hottest keys and a distributed cache's shared capacity — at the real cost of needing a broadcast mechanism to invalidate local copies across every application server.
- Distributed caching reuses the same sharding, replication, and consistent hashing concepts from the Databases section — it's the same set of trade-offs, applied to an in-memory layer instead of a disk-backed one.
