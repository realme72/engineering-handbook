# Sharding

# Why Does Sharding Exist?

Replication solves durability and read scaling by copying the *same* data onto multiple machines — but every write still funnels through one primary. Eventually, for a large enough system, that single primary hits a wall no amount of tuning fixes:

```
One primary machine has a ceiling:

CPU cores       →  finite
RAM             →  finite
Disk I/O        →  finite
Single-machine write throughput  →  finite, no matter how good the hardware
```

You can make that one machine bigger — more CPU, more RAM, faster disks — and this works for a while (that's **vertical scaling**), but it has a hard ceiling, and the biggest machine money can buy is still one machine handling every single write.

Sharding takes the opposite approach: instead of one machine holding *all* the data, split the data itself across multiple independent machines, each responsible for its own slice.

```
Without sharding:                    With sharding:

One database                         Shard 1: users 1–1,000,000
holding ALL users                    Shard 2: users 1,000,001–2,000,000
                                      Shard 3: users 2,000,001–3,000,000
```

Now there isn't one primary absorbing every write in the system — each shard only handles writes for its own slice of the data, and you can add more shards as the data and write volume grow, in a way that adding RAM to one machine simply cannot match.

---

# What Problem It Actually Solves

- **Write scalability past a single machine's ceiling** — this is the specific gap replication leaves open.
- **Storage beyond one machine's disk capacity** — a dataset that's outgrown what fits (performantly) on one machine's storage.
- **Isolating load** — a spike in traffic for one shard's data doesn't necessarily degrade every other shard's performance, the way it would on one shared machine.

The cost, and it's a real one: your data is no longer all in one place, which breaks a lot of things a single relational database gives you for free — covered in detail below.

---

# Choosing a Shard Key

This is the single most consequential decision in the entire sharding design, and it's very hard to change after the fact.

```sql
-- Which column determines which shard a row lives on?
shard_key = user_id
```

```
user_id = 42     →  hash(42) % 4 shards  →  Shard 2
user_id = 43     →  hash(43) % 4 shards  →  Shard 0
```

Every query that includes the shard key can be routed directly to the one shard that holds the answer. Every query that *doesn't* include it has to be broadcast to every shard and the results merged — which defeats much of the point of sharding in the first place, and is exactly why the shard key has to match how the application actually queries its data, not just how the data is conceptually organized.

---

# Sharding Strategies

## Range-Based Sharding

```
Shard 1:  user_id 1        – 1,000,000
Shard 2:  user_id 1,000,001 – 2,000,000
Shard 3:  user_id 2,000,001 – 3,000,000
```

Simple to reason about, and range queries (`WHERE user_id BETWEEN 500 AND 1500`) can often be satisfied by a small number of shards. The failure mode: **hot shards**. If IDs are assigned sequentially and most active traffic comes from your newest users, the newest shard absorbs a disproportionate share of load while older shards sit comparatively idle.

## Hash-Based Sharding

```
shard = hash(user_id) % num_shards
```

Distributes rows roughly evenly across shards regardless of the key's natural ordering, directly solving range sharding's hot-shard problem for sequentially-assigned IDs. The cost: range queries (`WHERE user_id BETWEEN ...`) can no longer target a small contiguous set of shards — the hash scatters what used to be a contiguous range across every shard.

## Directory-Based Sharding

```
Lookup Service:  user_id → shard mapping

user_id=42   →  Shard 2
user_id=9001 →  Shard 1
```

A separate lookup service explicitly tracks which shard holds which key, instead of computing it from a formula. More flexible — you can move individual keys between shards without a system-wide rehash — at the cost of an extra lookup hop and a new single point of failure (the lookup service itself) that has to be made highly available.

---

# What Breaks When You Shard

## Cross-Shard Joins

```sql
-- If users and orders are sharded by DIFFERENT keys, or independently,
-- this join might need to reach across every shard
SELECT * FROM orders JOIN users ON orders.user_id = users.id;
```

A join that used to be one query against one database engine now potentially means querying multiple shards and merging results in application code — the database engine itself has no native way to join rows that live on physically separate, independent machines.

The mitigation most sharded systems converge on: shard related tables by the **same** key, so a user's data and that user's orders always land on the same shard together — keeping the join local to a single shard instead of spanning several.

## Cross-Shard Transactions

Sharding introduces the exact same problem microservices with separate databases introduce at the Transactions chapter — a `BEGIN`/`COMMIT` only covers one database connection's scope, and each shard is, for this purpose, effectively its own independent database. An operation that needs to atomically update rows on two different shards can't rely on a single native transaction the way a single, unsharded database could.

This is the same gap the **Saga Pattern** (Distributed Systems) exists to fill — a sequence of local transactions, one per shard, with compensating actions to undo prior steps if a later one fails, instead of one atomic cross-shard transaction.

## Resharding Is Genuinely Painful

```
4 shards  →  need to add a 5th shard for more capacity

hash(user_id) % 4   →   hash(user_id) % 5

Almost every key's shard assignment CHANGES when the modulus changes
```

Because a plain `hash(key) % N` recomputes a completely different result for almost every key the moment `N` changes, adding or removing a single shard can require moving the overwhelming majority of your data between machines — an enormous, risky operation on a system that's presumably already under real production load.

---

# Consistent Hashing — Making Resharding Less Catastrophic

Instead of `hash(key) % N`, map both shards and keys onto positions on a fixed conceptual ring, and assign each key to the next shard clockwise from its position.

```
                     Shard A (position 90°)
                    /
    Shard D (315°) ●                    ● Shard B (180°)
                    \                  /
                     Shard C (position 270°)

key "user_42" hashes to 100° → belongs to the next shard clockwise → Shard B
```

```
Adding a new shard E at position 200°:

Only keys that fall BETWEEN the previous shard and E's new position
move to E. Every other key's assignment is completely unaffected.
```

This is the entire point: adding or removing one shard only reshuffles the small slice of keys immediately adjacent to that change on the ring, instead of recomputing almost every key's assignment the way a plain modulus does. It's the same fundamental technique that lets distributed caches and databases (many NoSQL systems, CDN request routing) scale their node count without a catastrophic full-dataset reshuffle every time.

---

# Real-World Examples

### Instagram

Historically sharded Postgres by `user_id`, using logical shards (schemas) mapped onto physical database servers — deliberately choosing `user_id` because the overwhelming majority of Instagram's queries are naturally scoped to a single user's own data (their posts, their followers), making it a shard key that keeps most real queries local to one shard.

---

### Discord

Shards data by `guild_id` (server ID) — messages, members, and channels for a given Discord server all live together, because virtually every real query Discord runs (loading a server's messages, its member list) is naturally scoped to one guild, the same "shard key matches actual query pattern" principle as Instagram's choice.

---

### MongoDB (Built-in Sharding)

Provides sharding as a first-class, built-in cluster feature rather than something an application has to hand-roll — a `mongos` router process sits in front of the shards and transparently routes each query to the correct one(s) based on the configured shard key, abstracting away much of the manual routing logic a hand-rolled sharded relational setup would otherwise require in application code.

---

# Common Interview Questions

## What's the difference between sharding and replication?

Replication copies the *same* data onto multiple machines, primarily for durability and read scaling — every write still goes through one primary. Sharding splits the data itself into distinct, non-overlapping pieces across multiple machines, primarily to scale write throughput and storage past what one machine can handle. They solve different axes of the scaling problem and are commonly used together — each shard often has its own set of read replicas.

---

## How do you choose a shard key?

Based on your actual, dominant query pattern — the column that appears in the `WHERE` clause of the vast majority of real queries. A shard key that matches how you query keeps most requests local to a single shard; a mismatched shard key means most queries have to fan out to every shard and merge results, which erodes much of the benefit of sharding in the first place.

---

## What breaks when you shard a relational database?

Joins across differently-sharded (or unrelated) tables become expensive or impossible to do natively, since the database engine can't join rows living on physically separate machines. Transactions spanning multiple shards lose native atomicity, for the same reason a transaction can't natively span two independent microservice databases — solved with patterns like Saga rather than a single native transaction.

---

## Why is resharding difficult with plain hash-based sharding, and how does consistent hashing help?

A plain `hash(key) % N` recomputes a completely different shard assignment for nearly every key the moment `N` (the number of shards) changes, forcing a massive data migration to add or remove even one shard. Consistent hashing maps shards and keys onto a fixed ring, so adding or removing a shard only reassigns the small slice of keys adjacent to that specific change, leaving every other key's assignment untouched.

---

## What is a hot shard, and how does it happen?

A shard that receives disproportionately more load than the others, usually because the shard key or sharding strategy doesn't actually distribute real traffic evenly — the classic case is range-based sharding by a sequentially-increasing ID, where the newest (and most active) users all land on the same, most recently created shard.

---

# Common Mistakes

❌ Choosing a shard key based on what feels like the "primary entity" rather than actual query patterns.

If most real queries don't naturally filter on the chosen key, most queries end up fanning out to every shard anyway, undermining the entire reason to shard.

---

❌ Range-sharding by a sequentially assigned ID without considering traffic distribution.

Creates a predictable hot shard — the newest range, holding the newest (often most active) data, absorbs disproportionate load while older shards sit comparatively idle.

---

❌ Needing constant cross-shard joins or transactions as a routine, everyday operation.

A strong signal the shard key doesn't actually match the application's real relationships — related data that's frequently queried or modified together should generally live on the same shard.

---

❌ Using plain `hash(key) % N` sharding and treating resharding as a rare afterthought.

Every shard count change becomes a massive, risky data migration under this scheme — worth adopting consistent hashing upfront if you expect to ever change the shard count, rather than discovering the pain the first time you actually need to add capacity.

---

# Key Takeaways

- Sharding splits the data itself across multiple independent machines to scale write throughput and storage past a single primary's ceiling — a different problem than replication, which copies the same data for durability and read scaling.
- The shard key choice is the most consequential decision in the design, and should match the application's dominant, real query pattern — not just an intuitive sense of the "main entity."
- Sharding breaks native cross-shard joins and transactions, the same way splitting a database across separate microservices does — mitigated by co-locating related data on the same shard, and by patterns like Saga for genuinely cross-shard operations.
- Plain hash-based sharding (`hash(key) % N`) makes resharding painful, since changing `N` reassigns nearly every key — consistent hashing solves this by only reassigning the small slice of keys adjacent to an actual shard addition or removal.
- Real systems (Instagram, Discord) pick shard keys that match their actual dominant query pattern — `user_id` and `guild_id` respectively — precisely because that keeps the overwhelming majority of real queries local to a single shard.
