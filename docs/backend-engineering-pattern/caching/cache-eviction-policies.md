# Cache Eviction Policies

# Why Do Eviction Policies Exist?

A cache lives in memory, and memory is finite — much smaller than the total amount of data that could theoretically be cached. Eventually, the cache fills up, and a new item needs to go in.

```
Cache capacity: 1,000 items
Cache currently holds: 1,000 items

New item needs to be cached

↓

Something has to go
```

An eviction policy is simply the rule for deciding *what* gets removed to make room. This is a separate concept from TTL-based expiration — expiration is about **correctness** (this data is now considered too old to trust), while eviction is about **capacity pressure** (the cache is full and something has to leave, regardless of whether it's technically still "valid"). A cache can evict a perfectly fresh, non-expired item simply because it's the least likely to be needed again soon, and something more urgently needed just arrived.

---

# LRU — Least Recently Used

**Rule:** when the cache is full, evict whichever item hasn't been accessed for the longest time.

The intuition: data that was just used is more likely to be used again soon than data nobody has touched in a while (this pattern — "recently accessed data tends to be accessed again soon" — is called **temporal locality**, and it holds true for a surprising amount of real-world access patterns: a user's active session, a trending post, a hot product page).

## Implementation: O(1) Get and Put

This is one of the most commonly asked coding interview questions on its own, precisely because a naive implementation is easy to get working but hard to get efficient.

```
Naive approach: a plain list, scanned linearly to find/move the "most recent" item
                → O(n) per operation — too slow for a real cache

Correct approach: a doubly linked list (tracks recency order) + a hash map
                  (gives O(1) lookup by key) working together
                → O(1) per operation
```

```python
class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}  # key -> Node, for O(1) lookup

        # dummy head/tail sentinels simplify edge cases at the list boundaries
        self.head = Node(None, None)
        self.tail = Node(None, None)
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add_to_front(self, node):
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        node = self.cache[key]
        self._remove(node)
        self._add_to_front(node)   # accessing it makes it "most recently used"
        return node.value

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self._remove(self.cache[key])

        node = Node(key, value)
        self.cache[key] = node
        self._add_to_front(node)

        if len(self.cache) > self.capacity:
            lru = self.tail.prev          # least recently used = right before the tail sentinel
            self._remove(lru)
            del self.cache[lru.key]
```

Every `get` and `put` does a fixed, small number of pointer updates and one hash map operation — no scanning, regardless of how large the cache gets. The linked list maintains recency order (most recent at the front, least recent at the back, right before the tail); the hash map gives instant access to any node by key without walking the list to find it.

---

# LFU — Least Frequently Used

**Rule:** when the cache is full, evict whichever item has been accessed the *fewest* times overall — not the longest-untouched, but the least popular.

```
Item A: accessed 100 times, last accessed 5 minutes ago
Item B: accessed 2 times, last accessed 10 seconds ago

LRU would evict A (least recently touched)
LFU would evict B (least frequently touched, despite being more recent)
```

LFU is a better fit when true popularity, not recency, is what predicts future access — a reference dataset that's read constantly by many users, where a single very-recent-but-rare access shouldn't outweigh months of consistent, heavy use.

## The Cache Pollution Problem

LFU has a specific, well-known failure mode: an item that was extremely popular once, but is no longer relevant, can keep an artificially high frequency count forever, permanently crowding out genuinely current, popular items that just haven't accumulated as long a history yet.

```
"2023 Year in Review" post: accessed 1,000,000 times last year, essentially 0 today
"Today's Trending Post": accessed 5,000 times today, climbing fast

Plain LFU: keeps the stale 2023 post cached indefinitely (1,000,000 > 5,000),
           evicts genuinely relevant current data instead
```

The fix is **aging/decay** — periodically reducing every item's frequency count (or weighting recent accesses more heavily than old ones), so old popularity fades over time instead of being permanent. Real LFU implementations (including Redis's) build this decay in specifically to avoid the plain-count version's pollution problem.

---

# FIFO — First In, First Out

**Rule:** evict whichever item was inserted earliest, regardless of how often or recently it's been accessed.

```
Insert order: A, B, C, D  (cache full after D)

New item E arrives → evict A (oldest inserted), regardless of A's usage since insertion
```

The simplest policy to implement (just a queue), and the crudest — it can evict an extremely hot, constantly-accessed item purely because it happened to be inserted first, which is precisely the scenario LRU and LFU are both designed to avoid. Rarely the right default choice for a general-purpose cache, though its simplicity still makes it a reasonable choice for specific, low-stakes use cases.

---

# Random Eviction

**Rule:** evict a randomly chosen item when the cache is full.

This sounds like giving up, and in a sense it is — but it has a real, practical advantage: it requires no bookkeeping at all. No recency list to maintain, no frequency counters to update on every access, which means zero overhead on the hot read path. Under many real-world access distributions, its actual hit-rate performance ends up surprisingly close to LRU's, while being meaningfully cheaper to implement and maintain at scale — which is exactly why Redis offers it as a legitimate, real production option, not a placeholder.

---

# Comparison

| Policy | Tracks | Overhead | Weakness |
|---|---|---|---|
| LRU | Recency of access | Moderate (linked list + map) | Recently-touched-once items outrank genuinely popular ones |
| LFU | Frequency of access | Higher (counters, often decay logic) | Cache pollution without decay — old popularity never fades |
| FIFO | Insertion order only | Very low (a queue) | Can evict a hot item purely due to insertion timing |
| Random | Nothing | Effectively zero | No intelligence at all, but often "good enough" and cheapest to run |

---

# Real-World Examples

### Redis `maxmemory-policy`

Redis exposes eviction policy as a direct configuration choice, not a hardcoded behavior:

```
noeviction        →  reject new writes once memory limit is hit (errors instead of evicting)
allkeys-lru        →  evict least-recently-used key, across ALL keys
volatile-lru       →  evict least-recently-used key, but ONLY among keys with a TTL set
allkeys-lfu        →  evict least-frequently-used key, across all keys
volatile-lfu       →  least-frequently-used, only among keys with a TTL set
allkeys-random     →  evict a random key
volatile-ttl       →  evict the key with the nearest expiration time first
```

The `volatile-*` variants exist specifically so you can mark certain keys as "never evict this one due to memory pressure" (by simply not giving them a TTL) while still letting genuinely cacheable, expendable data be evicted freely — a practical, real distinction between "this is cached, expendable data" and "this happens to live in Redis but isn't really disposable."

---

### CPU Caches (L1/L2/L3)

Hardware caches inside a CPU use variants of LRU (often approximated, since true LRU bookkeeping is expensive to implement directly in silicon at that speed) for exactly the same underlying reason software caches do — recently-used data (instructions, memory addresses) is disproportionately likely to be reused again very soon.

---

### CDN Edge Caches

Often lean toward simpler or approximated eviction (rather than perfectly precise LRU/LFU) at extreme scale, because the overhead of perfectly precise bookkeeping across an enormous, constantly-churning set of cached objects can itself become a meaningful cost — a good illustration that "the theoretically best policy" isn't always the practically best choice once overhead is accounted for.

---

# Common Interview Questions

## Implement an LRU cache with O(1) get and put.

A doubly linked list to track recency order (most recent at the front) combined with a hash map from key to linked-list node for O(1) lookup — every access moves the accessed node to the front, and eviction removes whatever's at the back. Neither structure alone achieves O(1) for both operations; it's the combination that does.

---

## LRU vs LFU — how do you decide which to use?

LRU when recency predicts future access well — most general-purpose caching workloads. LFU when true popularity matters more than recency — a dataset where some items are consistently, heavily used by many callers over a long period, and a single recent-but-rare access shouldn't be able to evict something genuinely popular. LFU needs decay/aging to avoid permanently favoring old popularity over new (the cache pollution problem).

---

## What's the difference between eviction and expiration (TTL)?

Expiration is about correctness — this data is now considered too old or stale to serve, regardless of memory pressure. Eviction is about capacity — the cache is full and something has to be removed to make room, regardless of whether it's technically still valid. A perfectly fresh, non-expired item can still be evicted if the cache is full and something else is deemed more valuable to keep.

---

## Why would a production system ever use random eviction instead of LRU?

Because it requires zero bookkeeping overhead — no recency list or frequency counters to maintain and update on every single access — and its real-world hit-rate performance is often surprisingly close to LRU's under many access patterns. At extreme scale, that lower overhead can be a genuinely better trade than a small hit-rate improvement from a more "intelligent" policy.

---

# Common Mistakes

❌ Implementing LRU with a plain list, scanning it to find and move the most-recently-used item.

Turns every operation into an O(n) scan — the correct O(1) implementation requires a doubly linked list paired with a hash map, not a single simpler structure.

---

❌ Using plain LFU without any decay/aging mechanism.

Old, once-popular data can accumulate a frequency count high enough to never get evicted again, permanently crowding out genuinely current, relevant data — the cache pollution problem.

---

❌ Confusing eviction policy with TTL expiration.

They solve different problems — TTL is about data going stale; eviction is about memory pressure. A cache needs a sensible answer for both, not just one.

---

❌ Assuming the "smartest" policy is always the right choice.

LRU and LFU both carry real bookkeeping overhead. At sufficient scale, that overhead itself becomes a cost worth weighing against a simpler policy's slightly lower hit rate — there's no universal "best," only the right trade-off for the actual workload and scale.

---

# Key Takeaways

- Eviction policies decide what to remove when a full cache needs room for something new — a separate concern from TTL-based expiration, which is about data going stale rather than the cache being full.
- LRU evicts based on recency of access and is implemented efficiently with a doubly linked list plus a hash map, giving O(1) get and put — a genuinely common coding interview question in its own right.
- LFU evicts based on access frequency and better predicts true popularity, but needs decay/aging to avoid the cache pollution problem — old popularity permanently crowding out current, relevant data.
- FIFO and random eviction carry far less bookkeeping overhead than LRU/LFU, and random in particular performs surprisingly competitively in practice despite tracking nothing at all.
- Redis exposes eviction policy as direct, explicit configuration (`allkeys-lru`, `volatile-lfu`, etc.), letting real systems choose the right trade-off deliberately rather than accepting one hardcoded behavior.
