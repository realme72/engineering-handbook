# Vertical Scaling

# Why Does Vertical Scaling Exist?

The simplest answer to "we need more capacity" is the obvious one: get a bigger machine. More CPU, more RAM, faster disks, same application untouched. Vertical scaling is that low-complexity first move, and for a lot of real systems it's the right one to make before reaching for horizontal scaling's coordination overhead at all.

```
Vertical scaling:  same application, same architecture,
                    JUST a bigger machine underneath it
```

---

# Why It's Genuinely Attractive, Not Just "The Lazy Option"

```
No architectural changes needed:  the application code doesn't
                                   need to know or care it's
                                   running on bigger hardware —
                                   nothing needs to be rewritten
                                   to be "multi-instance aware"

No new distributed-systems problems: none of the Horizontal
                                       Scaling chapter's coordination
                                       costs apply at all — no service
                                       discovery, no need to externalize
                                       state, no new consistency
                                       questions, since there's still
                                       only ONE machine
```

Worth internalizing: vertical scaling isn't the lesser cousin of "real" scaling. For a system that hasn't outgrown a single machine, it's the objectively lower-risk choice, and jumping past it early just means paying coordination costs you didn't need to pay yet.

---

# The Hard Ceiling

```
There EXISTS a maximum size of machine that's available and
economically sensible

↓

Vertical scaling means paying for that biggest available machine
100% of the time, even during periods when load is only occasionally
that high — there's no equivalent to horizontal scaling's auto-scaling
flexibility, since you can't dynamically resize a running machine's
actual physical hardware the way you can add or remove entire
instances
```

Once you're on the biggest practical machine and still need more, you're out of road — the point where this eventually forces a move to horizontal scaling, or for a database specifically, sharding.

---

# The Single Point of Failure Risk

A real, structural cost distinct from the ceiling above.

```
One giant, vertically-scaled machine

↓

If THAT machine fails — hardware fault, a bad deploy, anything —
EVERYTHING running on it goes down AT ONCE

↓

No redundancy at all, by construction — there's only one machine
```

Compare that to horizontal scaling's built-in redundancy — many instances behind a load balancer mean one dying doesn't take the system down. Vertical scaling trades that away for simplicity, and if high availability actually matters, you need a separate mitigation for it (a standby replica, typically — which starts pulling in some of horizontal scaling's coordination concerns anyway).

---

# When Vertical Scaling Is Genuinely the Right Choice

```
A primary database is the strong, common example — per the
Sharding chapter, sharding introduces real costs (broken
joins, harder cross-shard transactions, a genuinely significant
migration effort)

↓

Many real production databases get vertically scaled — bigger
instance, more RAM, faster disks — for YEARS, successfully handling
substantial real load, before a genuine, unavoidable need to shard
actually arises

↓

Reaching for sharding's complexity before actually needing it means
paying its real costs (broken joins, cross-shard transaction
complexity) for a scale problem the system doesn't actually have yet
```

The general lesson: don't reach for horizontal scaling or sharding until vertical scaling's ceiling is actually in sight — not because of a hypothetical future scale that may never show up.

---

# Real-World Examples

### A Single Large Postgres/MySQL Primary

Extremely common in practice — one well-provisioned relational database, vertically scaled as needed, serving as the entire system's primary store for years before sharding ever becomes necessary.

---

### AWS's Ever-Larger Instance Types

Cloud providers keep releasing bigger instance types precisely because vertical scaling remains a real, ongoing strategy at scale — not a stepping stone everyone rushes past.

---

### Databases Specifically, as the Textbook Case

The Sharding chapter frames it exactly this way — sharding as the answer once a primary's vertical ceiling is actually reached, not a default starting point, because vertical scaling is usually the better first move for this kind of stateful system.

---

# Common Interview Questions

## Vertical vs horizontal scaling — what's the actual trade-off?

Vertical scaling needs no architectural changes and none of horizontal scaling's coordination costs, but it has a hard ceiling and zero redundancy — one machine, one failure domain. Horizontal scaling has no inherent ceiling and built-in redundancy, at the cost of real, ongoing coordination complexity.

---

## Why might you choose to vertically scale a database rather than immediately sharding it?

Sharding brings real costs — broken cross-shard joins, harder distributed transactions, a genuinely difficult migration. Not worth paying until a well-provisioned primary's vertical ceiling is actually close. Plenty of production databases run for years on one vertically-scaled instance before sharding is ever necessary.

---

## What's the fundamental ceiling on vertical scaling?

There's a biggest machine that exists and is economically sensible at any given time. Once you're already on it and still need more, vertical scaling has nothing left to give.

---

## Why is a vertically-scaled single machine considered a single point of failure risk?

Because it's one machine — a hardware fault or bad deploy takes down everything running on it at once. Horizontal scaling's multiple instances give you redundancy a single machine structurally can't.

---

## Is vertical scaling always the "lesser" or less serious option compared to horizontal scaling?

No. For a system that hasn't outgrown a single machine, it's the lower-risk, lower-complexity choice. Jumping to horizontal scaling before it's needed just means paying its costs for a scale problem you don't have yet.

---

# Common Mistakes

❌ Prematurely reaching for horizontal scaling's complexity before exhausting the simpler vertical option.

Pays real, ongoing coordination costs for a scale problem the system may not have yet.

---

❌ Not recognizing that vertical scaling alone provides zero redundancy.

A single machine failing takes everything down with it — worth a separate mitigation (a standby replica) if high availability actually matters.

---

❌ Treating vertical scaling as a temporary stepping stone everyone inevitably outgrows.

Plenty of production systems, databases especially, run on one vertically-scaled instance for years. It's a legitimate long-term strategy, not just a placeholder.

---

# Key Takeaways

- Vertical scaling — a bigger machine, same application — avoids all of horizontal scaling's coordination costs, making it the simpler, lower-risk first move for a lot of systems, especially databases.
- Its ceiling is the biggest available, economically sensible machine — past that, there's no more room to give.
- It provides zero redundancy — one machine failing takes down everything on it, a structural risk separate from the capacity ceiling.
- Databases are the textbook case for staying vertical a long time, since sharding's costs (broken joins, harder transactions) aren't worth paying until genuinely necessary.
- It isn't a lesser option to outgrow as fast as possible — for many systems it's a legitimate, durable strategy, and jumping past it early means paying horizontal scaling's costs before you need to.
