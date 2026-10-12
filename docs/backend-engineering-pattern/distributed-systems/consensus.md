# Consensus

# Why Does Consensus Exist?

Strong consistency, from the Consistency Models chapter, requires the ability to establish one agreed-upon truth across multiple, independent machines — "who is the current leader," "what's the next entry in the replicated log," "did this transaction commit." Consensus is the underlying problem of getting a group of nodes to agree on a single value or decision, even when some nodes might crash, restart, or have messages delayed or lost between them — and doing so in a way that guarantees every node that does decide, decides on the **same** value.

```
5 nodes need to agree on: "who is the leader?"

Node A: crashes partway through
Node B: message to it is delayed
Node C, D, E: functioning normally

↓

Can the remaining nodes still reach agreement, safely, without
risking two different nodes both believing they're the leader?
```

Without a formal answer to this problem, distributed systems have no reliable way to coordinate anything that requires exactly one authoritative decision — which turns out to be the foundation underneath leader election, distributed locks, and reliably replicated logs, all covered in their own chapters, all fundamentally *applications* of consensus.

---

# Why This Is a Genuinely Hard Problem

It's tempting to think "just have everyone vote and go with the majority" solves this trivially — the actual difficulty is doing that safely when nodes can crash and messages can be delayed or lost, without ever risking two different groups of nodes disagreeing about the outcome.

```
A classic failure scenario:

Node A proposes: "I should be leader"
Node A sends this to B, C, D, E

Message to D is delayed (not lost, just slow)
Node A receives votes from B, C only

↓

Does A have a majority? With 5 nodes, a majority is 3 —
A only has 2 confirmed votes (B, C) plus itself = 3.
Is that safe to act on, given D and E's actual votes are unknown?
```

There's a foundational theoretical result (the FLP impossibility result) proving that in a fully asynchronous network — one with no bound at all on message delay — no algorithm can *guarantee* consensus in bounded time if even one node might fail. Real systems work around this not by defying the theorem, but by making a practical assumption the theorem doesn't allow: using **timeouts**. If a node hasn't heard back within some reasonable time, assume it's failed or unreachable and proceed without it — this converts an unbounded theoretical wait into a practical, bounded decision, at the small risk of occasionally guessing wrong about a node that was merely slow, not actually dead.

---

# The Core Idea: Majority Quorums

Every practical consensus algorithm is built around the same foundational trick: a decision is considered final once a **majority** of nodes agree to it — not all of them, just more than half.

```
5 nodes total → majority = 3 (any 3 nodes agreeing is enough)

Why majority, specifically?

Any two majorities, out of the same set of nodes, MUST overlap
by at least one node (with 5 nodes, any two groups of 3 share
at least 1 node in common).

↓

This overlap is what prevents two CONFLICTING decisions from
both being finalized — any node that helped finalize decision A
would have to also be part of any group finalizing a conflicting
decision B, and it wouldn't agree to both.
```

This is exactly why consensus clusters are typically run with an **odd** number of nodes (3, 5, 7) — an odd count gives the cleanest majority threshold and the best fault tolerance per node added. A 5-node cluster tolerates 2 node failures and still has a majority (3) available; a 6-node cluster also only tolerates 2 failures (needing 4 for a majority) while spending an entire extra node to get no additional fault tolerance at all.

---

# Paxos — The Original, Foundational Algorithm

Paxos (Leslie Lamport, 1989/1998) is the original rigorous solution to this problem, built around two roles: **proposers**, who suggest a value, and **acceptors**, who vote on proposals.

```
Proposer suggests a value  →  sends to all Acceptors

↓

Acceptors respond with a promise (or reject, if they've already
promised something with a higher proposal number)

↓

Once a Proposer collects promises from a MAJORITY of Acceptors,
it can finalize ("commit") that value — and every future proposal
is guaranteed, by the protocol's rules, to also converge on that
same already-decided value
```

Paxos is famously correct, and famously difficult to actually understand and implement correctly — its formal description doesn't map cleanly onto a straightforward, step-by-step implementation, which is precisely the gap Raft was designed to close.

---

# Raft — Designed Specifically to Be Understandable

Raft (2014) provides the same safety guarantees as Paxos, deliberately decomposed into three separate, more intuitively graspable sub-problems: leader election, log replication, and safety.

```
1. Leader Election:   nodes elect ONE leader via majority vote for
                        a given "term" (covered in full in the
                        Leader Election chapter)

2. Log Replication:   ALL writes go through the leader, which
                        replicates each entry to followers

3. Safety:            an entry is only considered "committed" once
                        a MAJORITY of nodes have it in their log —
                        guaranteeing it survives even if the leader
                        immediately crashes afterward
```

```
Leader receives a write

↓

Appends it to its own local log

↓

Sends it to all followers

↓

Once a MAJORITY of followers have acknowledged receiving it →
the entry is COMMITTED (guaranteed durable, safe to apply)

↓

Leader notifies followers the entry is committed
```

The specific insight that makes Raft dramatically easier to reason about than Paxos: by decomposing consensus into "elect exactly one leader" plus "the leader linearly replicates a log, entry by entry, to followers," most of the hard coordination problem collapses into a much simpler structure — there's no need to reason about arbitrary competing proposals the way raw Paxos requires, because only the elected leader is ever allowed to propose new entries during its term.

---

# How This Relates to CAP

Consensus fundamentally requires a majority of nodes to be reachable and participating — which means a consensus-based system is inherently **CP**, not AP: during a partition where no side has a majority, the system makes **no progress at all**, by design, rather than risk an unsafe decision.

```
5-node cluster, partition splits it into a group of 2 and a group of 3

↓

Group of 3 (has a majority) → can still elect a leader, commit new entries

Group of 2 (no majority)    → CANNOT elect a leader or commit anything,
                                intentionally, to avoid two independent
                                "leaders" existing simultaneously
```

This is a deliberate, safety-preserving trade — refusing to make progress on the minority side is exactly what prevents the split-brain scenario covered in the Replication and Leader Election chapters, at the direct cost of availability on whichever side lacks a majority.

---

# Real-World Examples

### etcd (Raft)

Kubernetes's entire control plane relies on etcd, which uses Raft internally to maintain a consistent, replicated store of cluster state — every scheduling decision, every deployment update, ultimately depends on etcd's Raft-based consensus to ensure the whole cluster agrees on the current state.

---

### Zookeeper (ZAB — a Paxos-like protocol)

Historically the standard coordination service for distributed systems needing leader election and consistent configuration state — Kafka relied on Zookeeper for exactly this purpose for years, before eventually replacing it with a built-in Raft-based mechanism (KRaft) to remove the operational dependency on a separate Zookeeper cluster entirely.

---

### CockroachDB / TiDB (Raft, applied to data replication)

Both use Raft not just for leader election but to replicate actual data across nodes with strong consistency guarantees — a direct, concrete example of consensus as the mechanism underneath a database's own replication and consistency story, not just an abstract coordination tool.

---

# Common Interview Questions

## What problem does consensus actually solve?

Getting a group of nodes to agree on a single value or decision, even in the presence of crashes and delayed or lost messages, while guaranteeing that any node that does reach a decision reaches the *same* one every other deciding node reaches. It's the foundational problem underneath leader election, distributed locks, and reliably replicated logs.

---

## Why do consensus clusters typically use an odd number of nodes?

Because an odd count gives the most fault tolerance per node — a 5-node cluster tolerates 2 failures while still having a majority (3) available, whereas a 6-node cluster also only tolerates 2 failures (needing 4 for a majority) while spending an entire additional node for zero extra fault tolerance.

---

## Why does majority-based agreement prevent conflicting decisions?

Because any two majorities drawn from the same set of nodes are mathematically guaranteed to overlap by at least one node — a node that helped finalize one decision would have to also participate in finalizing any conflicting decision, and a correctly-implemented node won't agree to two conflicting proposals, which is exactly what prevents a split decision from ever being finalized twice.

---

## How does Raft differ from Paxos, and why was it created?

Raft provides the same fundamental safety guarantees as Paxos but decomposes the problem into three more intuitively separable pieces — leader election, log replication, and safety — specifically because Paxos, while provably correct, is notoriously difficult to understand and implement correctly from its formal description. Raft was designed explicitly for understandability as a first-class goal.

---

## Why is a consensus-based system inherently CP rather than AP?

Because reaching consensus fundamentally requires a majority of nodes to participate — during a partition where no side has a majority, the system deliberately makes no progress at all on that side, rather than risk two independently-operating "leaders" or conflicting decisions. This refusal to proceed without a majority is exactly what preserves safety, at the direct cost of availability for whichever side lacks one.

---

# Common Mistakes

❌ Assuming consensus can make progress without a majority of nodes reachable.

This is a deliberate design constraint, not a limitation to work around — proceeding without a majority is exactly what risks split-brain and conflicting decisions; a consensus-based system correctly refuses to make progress in that situation.

---

❌ Confusing consensus (agreeing on one value, once) with general distributed consistency (an ongoing property of every read and write).

Consensus is the specific mechanism often used to *implement* strong consistency guarantees (electing a leader, committing a log entry) — but consistency models describe a broader, ongoing spectrum of guarantees, not a single one-time agreement.

---

❌ Choosing an even number of nodes for a consensus cluster.

Spends an additional node's cost without any additional fault tolerance compared to using one fewer node — the majority threshold doesn't improve, since an even-sized cluster's majority requirement doesn't decrease.

---

# Key Takeaways

- Consensus solves the problem of getting multiple, potentially-failing nodes to agree on a single value or decision safely, and is the foundational mechanism underneath leader election, distributed locks, and replicated logs.
- Real consensus algorithms work around the theoretical impossibility of guaranteed bounded-time agreement in a fully asynchronous network by using timeouts — a practical assumption, not a violation of the underlying theory.
- Majority quorums are the core trick that makes consensus safe — any two majorities from the same node set are guaranteed to overlap, which is exactly what prevents two conflicting decisions from both being finalized.
- Raft provides the same guarantees as Paxos, deliberately decomposed into leader election, log replication, and safety specifically to be more understandable and implementable than Paxos's original formal description.
- Consensus-based systems are inherently CP — during a partition where no side has a majority, the system deliberately refuses to make progress on that side, preserving safety at the cost of availability.
