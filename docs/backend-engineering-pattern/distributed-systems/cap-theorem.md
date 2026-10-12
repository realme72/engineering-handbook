# CAP Theorem

# Why Does CAP Theorem Exist?

As a system scales, one database on one machine stops being enough, so the data gets spread across many machines. You use techniques like sharding and partitioning to decide which machine owns which slice of data, and a request for a particular piece of data gets routed to the specific machine that holds it. That solves the storage problem. But it quietly creates a new one: those machines now have to talk to each other over a network, and networks fail — a switch dies, a cable gets cut, a data center loses connectivity to another region for thirty seconds. That failure is called a **network partition**, and CAP theorem is really just a formal answer to one question: when a partition happens, what can your system still honestly promise?

Here's the situation before anything breaks:

```
Node A ──→ Node B ──→ Node C

A client sends a write to Node A.
The write flows through A, B, and C, and an
acknowledgment goes back to the client once
it's replicated.
```

And here's the moment a partition hits:

```
Node A ──✕── [network partition] ──✕── Node B ──→ Node C

A client still sends a write to Node A.

Node A now has a decision to make:

(a) Accept the write, even though it has no way
    to confirm Node B (or C) has the same data.

(b) Refuse the write, and refuse reads too, until
    the partition heals — to avoid the risk of
    nodes disagreeing with each other.
```

There's no third option that quietly avoids this. At the exact moment the network between nodes is broken, you cannot both guarantee that every node has the absolute latest data *and* guarantee that every request gets a successful response. Something has to give, at least for as long as the partition lasts.

---

# The Three Properties

```
C — Consistency:          every read gets back the most recent write,
                           agreed on by every node, as if there were
                           only one copy of the data

A — Availability:         every request gets a response, even if
                           that response can't guarantee it's the
                           most recent data

P — Partition Tolerance:  the system keeps operating even when
                           messages between nodes are being dropped
                           or delayed
```

## What CAP Actually Says

**When a network partition occurs, you have to choose between Consistency and Availability. You cannot have both at that exact moment.**

```
Partition happens between Node A and Node B

Choose CONSISTENCY:  refuse requests on the side that can't
                      confirm it has the latest data (or refuse
                      on both sides) until the partition heals —
                      you're trading away availability so you
                      never hand back stale or conflicting data

Choose AVAILABILITY: keep answering requests on both sides, and
                      accept that A and B might now silently
                      disagree until the partition heals and
                      they reconcile — you're trading away strict
                      consistency for uptime
```

---

# "Pick Any 2 of 3" Is a Bad Way to Say This

I still hear "pick any two of the three" get repeated in interviews like it's the whole theorem, and it's one of those things that sounds right until you've actually run a distributed system in production and realized it isn't.

Here's the issue with it: partition tolerance was never really a choice you get to make. It's not a feature you can decide to skip, the way you might decide to skip caching or skip multi-region deployment. Networks fail on their own schedule, not yours — a switch dies, a cable gets cut, some region loses connectivity for no reason anyone can explain until the postmortem. You don't get a vote. So when someone describes a system as "CA" — consistent and available, no partition tolerance — what they usually mean, whether they realize it or not, is "a system we haven't seen partition yet." The first time it does, it still has to answer the C-vs-A question, and it'll answer it whether or not anyone ever sat down and designed for that moment.

So I'd push back on the "pick 2 of 3" framing every time I hear it. The honest version is: partitions are coming, that part was decided for you the moment you went distributed. The only real decision left is what your system does in the seconds a partition is actually happening — does it lean toward C, or toward A? That's not a checkbox you tick once in an architecture doc. It's a behavior your system exhibits during one specific, unavoidable kind of failure, and if you haven't tested what it actually does, you don't really know the answer yet.

---

# A Concrete Example

```
Two-node system, replicating a user's account balance

Node A: balance = 1000
Node B: balance = 1000

↓ network partition between A and B

Client sends "withdraw 200" → routed to Node A
```

**Choosing consistency (CP):** Node A says no. It can't reach B, so it has no way to confirm B will agree with the new balance, and it would rather hand the customer an error than risk two nodes silently disagreeing about how much money is in their account. The customer sees "service temporarily unavailable" — annoying, but nobody's balance is ever wrong.

**Choosing availability (AP):** Node A just does the withdrawal locally (`balance = 800`), tells the customer it worked, and figures out reconciliation with Node B later, once the partition heals. This is where it gets interesting — if Node B *also* accepted some conflicting write while it was cut off, you now have a genuine conflict on your hands after the fact, not a hypothetical one. That's the exact same problem I'd point to in the multi-leader replication conflicts discussion — CAP and replication aren't really separate topics, they're the same failure mode looked at from two angles.

I wouldn't call either choice "correct" in the abstract — it depends entirely on what's more expensive to get wrong. For a bank withdrawal, I'd go CP without much debate; a wrong balance is the kind of bug that ends up in a compliance review, and an error message is cheap by comparison. For something like a "like" button or "add to cart," I'd go AP — nobody's going to be upset that their cart briefly disagreed across two replicas, but plenty of people will be upset if the app just refuses to let them add an item because some node three hops away is unreachable.

---

# Beyond CAP: PACELC

CAP only tells you what happens **during a partition**. PACELC is the more complete version — it adds the trade-off that exists even when the network is perfectly healthy:

```
P.A.C.E.L.C

If Partitioned:      choose Availability or Consistency (this is CAP)

Else (no partition):  choose Latency or Consistency
```

This is the part I think gets skipped too often, because most people stop thinking about CAP the moment the network is healthy again — as if the trade-off only exists during the bad weather. It doesn't. Even on a perfectly quiet day, with every node reachable, you still have to decide: does a write wait for every replica to confirm before you tell the client it succeeded, or do you respond the moment one node has it and let the rest catch up? The first option is safer and slower. The second is faster and means, for a brief window, some replica somewhere is behind. That's just synchronous vs. asynchronous replication again, dressed up in theory language.

I'd bring up PACELC in an interview specifically because it signals you're not just reciting CAP from a slide — you understand that the interesting trade-off isn't confined to outages. Latency vs. consistency is a decision your system is making on every single write, all day, whether or not anything is broken.

---

# CAP's "C" vs. ACID's "C" — Revisited

I want to call this out directly, because I've watched people talk past each other in interviews over exactly this, and it's an easy trap if nobody's pointed it out to you before. ACID's Consistency is a single-database concern — it just means a committed transaction doesn't leave the data violating its own rules, foreign keys still pointing somewhere real, constraints still holding. It has nothing to say about other machines. CAP's Consistency is a completely different animal — it's about whether multiple nodes, potentially in different data centers, agree on the latest value of the same piece of data.

They landed on the same word by coincidence more than design, and if you use them interchangeably in an interview, it's usually a tell that you've memorized the acronym without having actually reasoned about either one. I'd keep them mentally filed under different names if it helps — ACID's C is "the database didn't lie to itself," CAP's C is "the nodes didn't lie to each other."

---

# Real-World Examples

### MongoDB

Leans CP by default. Reads and writes go through a single primary, so by default they reflect the most recently acknowledged write — the trade-off is that the primary can be briefly unavailable during a failover, rather than serving potentially stale data from a node that hasn't been elected yet.

---

### Cassandra

Leans AP, but makes the trade-off explicitly tunable per query — you can ask for consistency level `ONE`, `QUORUM`, or `ALL`, which controls how many replicas have to agree before a read or write counts as successful. Different queries in the same system can sit at different points on the C-vs-A spectrum depending on what that data actually needs.

---

### DynamoDB

Built around availability from the start — it's the system Amazon built specifically after its own well-known availability incidents during checkout. Reads are eventually consistent by default, with strongly-consistent reads available as an explicit, higher-cost opt-in when you actually need them.

---

# Common Interview Questions

## Walk me through CAP theorem with a real example.

I'd start with the partition, not the acronym — that's what actually forces the trade-off. Say a write hits Node A right as the network between A and B breaks. Node A has two options: reject the write until it can confirm B agrees, which keeps things consistent but makes the system unavailable in that moment, or accept the write locally and reconcile with B later, which keeps the system available but means A and B can disagree for a while. A bank withdrawal usually wants the first behavior; a "like" button usually wants the second. That's the whole theorem — everything else is vocabulary on top of that one decision.

## Why do people say "pick any 2 of 3" is wrong?

Because it implies partition tolerance is something you can opt out of, and in a real networked system it isn't — networks partition whether you want them to or not. The only choice you actually get to make is between consistency and availability, and only in the window where a partition is actually happening. I'd rather say it as: partitions are inevitable, so the real question is what your system does when one hits, not which two of three properties you "chose" at design time.

## How is CAP's Consistency different from ACID's Consistency?

They just share a word. ACID's C is about a single database not violating its own constraints — foreign keys, uniqueness, that sort of thing. CAP's C is about multiple nodes agreeing on the latest value of the same piece of data. One is a single-node integrity guarantee, the other is a multi-node agreement problem, and conflating them is a pretty common mix-up I'd flag if I heard it in an interview.

## What does PACELC give you that CAP doesn't?

CAP stops at "what happens during a partition." PACELC adds the part CAP is silent on — what happens the rest of the time, when there's no partition at all. Even then, you're still choosing between latency and consistency: wait for replicas to confirm a write (safer, slower) or respond as soon as one node has it (faster, and other replicas catch up shortly after). It's the same idea as sync vs. async replication, just framed as a permanent, ongoing trade-off instead of one that only shows up during failures.

## Would you go CP or AP for a shopping cart's "add to cart" button, and why?

AP, almost every time. If a customer taps "add to cart" during a brief partition, I want that to succeed — losing the add because two replicas couldn't confirm each other in time is a worse outcome than the cart being briefly out of sync and reconciling a moment later. Compare that to a bank balance, where showing a wrong number, even briefly, is worse than making the customer wait — that's where I'd flip to CP.

---

# Common Mistakes

❌ Treating CAP as "pick 2 of 3, permanently, at design time."

Partition tolerance isn't actually something you can decline in a real system. The genuine, forced choice is only between C and A, and it only exists while a partition is actually in progress.

---

❌ Mixing up CAP's Consistency with ACID's Consistency.

One is about a database enforcing its own rules on a single node; the other is about multiple nodes agreeing during a partition. Related in name only.

---

❌ Assuming a system's CAP behavior is fixed and identical for every operation.

Real systems like Cassandra and DynamoDB make this tunable per query — the same system can lean AP for one kind of read and CP for another, depending on what that specific data actually needs.

---

❌ Forgetting the latency-vs-consistency trade-off that exists with no partition at all.

CAP alone doesn't cover this — PACELC's addition is a trade-off you're making constantly in production, not a theoretical edge case you only think about during an outage.

---

# Key Takeaways

- CAP theorem describes a forced choice that only becomes real during an actual network partition: sacrifice availability (reject requests until you can guarantee consistency) or sacrifice consistency (keep answering requests, accepting that nodes may briefly disagree).
- "Pick any 2 of 3" undersells it — partition tolerance isn't optional in a real networked system, so the real choice is only between C and A, and only while a partition is happening.
- CAP's Consistency and ACID's Consistency are different concepts that happen to share a word — one is multi-node agreement, the other is single-database rule enforcement.
- PACELC extends CAP by naming the latency-vs-consistency trade-off that exists even without a partition — the same underlying idea as synchronous vs. asynchronous replication.
- Real systems usually make the CAP trade-off tunable per operation instead of fixed system-wide — Cassandra and DynamoDB both let different queries land at different points on the consistency-availability spectrum.
