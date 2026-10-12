# Throughput

# Why Does Throughput Matter, and How Is It Different From Latency?

Latency answers "how long does one request take?" Throughput answers a different question: "how much total work can the system get done per unit time?" They're related, but not the same axis — you can improve one while making the other worse.

```
Latency:     time for ONE request, start to finish

Throughput:  total requests (or transactions, or bytes) COMPLETED
             per unit time, across the whole system
```

```
A system could have:

- LOW latency per request, but LOW throughput (can't handle many
  requests AT ONCE, even though each individual one is fast)

- HIGHER latency per request, but HIGH throughput (batching many
  items together adds a bit of latency to each individual item,
  but processes far more total items per second overall)
```

A batch job processing 10,000 records in one 2-second pass has dramatically higher throughput than handling each record individually at 1ms — even though any single record arguably waits longer in the batching version, since it has to sit until the whole batch is ready. Confusing these two axes is one of the more common mix-ups in performance discussions.

---

# Little's Law

A classic result from queueing theory, and genuinely useful for capacity planning, not just trivia.

```
L = λ × W

L = average number of requests currently IN the system
λ = average arrival rate (requests per unit time)
W = average time each request spends in the system (latency)
```

```
Example: if requests arrive at 100/second (λ), and each takes an
average of 200ms = 0.2 seconds to complete (W):

L = 100 × 0.2 = 20

→ on average, 20 requests are "in flight" in the system at any
  given moment
```

This is directly actionable. Know your target throughput and your typical latency, and you know how much concurrent capacity — connections, threads, workers — you need to sustain that throughput without requests backing up and latency spiraling.

---

# Batching as a Throughput Optimization

The same idea covered in the Kafka chapter's discussion of batching, worth restating here as a general principle rather than something Kafka-specific.

```
Without batching:  100 individual network round trips, each with
                    its own fixed overhead (connection setup,
                    protocol overhead) — overhead is paid 100 TIMES

With batching:      1 round trip carrying all 100 items — fixed
                    overhead paid ONCE, amortized across all 100
```

The trade-off is real: an item now waits for the batch to fill (or a timeout) before it's sent at all. But the aggregate throughput gain from amortizing fixed overhead across many items instead of paying it repeatedly is often dramatic — which is exactly why bulk inserts, Kafka producer batching, and request batching are all standard, deliberate optimizations, accepted at the cost of individual-item latency.

---

# Finding the Bottleneck

A system's overall throughput can never exceed what its single most constrained resource can sustain. Optimizing everything else doesn't help if one piece is the actual limit.

```
Request pipeline:

Load Balancer → App Servers → Database Connection Pool → Database

↓

If the DATABASE can only sustain 500 queries/second, no matter how
many app servers you add, or how fast the load balancer is, the
SYSTEM'S overall throughput is capped at 500 queries/second —
the database is the bottleneck
```

```
Adding more app servers WITHOUT addressing the actual database
bottleneck:

↓

More app servers just means MORE requests queuing up, waiting on
the same constrained database — doesn't increase overall system
throughput at all, just moves where the queueing happens
```

Identifying the actual bottleneck, instead of reflexively adding more of everything, is the real skill. Profiling (its own chapter) finds where a single service's own ceiling comes from at the code level; Horizontal/Vertical Scaling is how you act on the answer once you have it.

---

# Real-World Examples

### Kafka's Batching

Producers and consumers both batch multiple messages into fewer round trips to maximize throughput, at the cost of a little added per-message latency while the batch fills — covered directly in the Kafka chapter.

---

### Database Connection Pool Sizing

Ties into the Connection Pooling chapter — a pool sized without regard to the database's actual processing capacity can become the bottleneck itself, or hide the fact that the database underneath it already is one.

---

### Horizontal Scaling to Increase Throughput

Once you've correctly identified the bottleneck (and it isn't something like a single shared database), adding more instances of whatever's constrained is the most direct throughput fix — covered in full in the Horizontal Scaling chapter.

---

# Common Interview Questions

## What's the difference between latency and throughput? Give a concrete example where they trade off.

Latency is how long one request takes; throughput is how much total work the system completes per unit time. Batching is the cleanest trade-off — waiting to batch 100 items adds latency to any individual item, but dramatically increases aggregate throughput by amortizing fixed overhead across all of them instead of paying it 100 times.

---

## Explain Little's Law and why it's useful.

`L = λ × W` — the average number of requests in a system equals arrival rate times average time each spends in the system. Know your target throughput and typical latency, and you can calculate exactly how much concurrent capacity you need to sustain it without requests backing up.

---

## How does batching improve throughput, and what's the cost?

It amortizes fixed per-request overhead across many items instead of paying it for each one individually. The cost is added latency — any single item now waits for the batch to fill (or a timeout) before it's sent.

---

## How do you find the bottleneck limiting a system's overall throughput?

Identify the single most constrained resource in the pipeline — the one whose capacity actually caps throughput no matter what else you optimize. That usually means profiling and measuring each stage's real sustained capacity, not guessing.

---

## Does lower latency always mean higher throughput?

No. They're independent axes. A system can have low per-request latency but low throughput if it can't handle much concurrency, or slightly higher latency (via batching) with much higher throughput. Treating them as the same thing is a common source of confused performance conversations.

---

# Common Mistakes

❌ Assuming lower latency automatically implies higher throughput.

They're different axes — batching is the clearest counterexample, deliberately trading latency for throughput.

---

❌ Adding more capacity to a part of the system that isn't actually the bottleneck.

Doesn't increase overall throughput if a different, unaddressed resource is the real limit — it just moves where requests queue.

---

❌ Not using Little's Law (or equivalent reasoning) to size capacity deliberately.

Leads to guessing at how many connections or workers you actually need instead of calculating it from known arrival rate and latency.

---

# Key Takeaways

- Throughput (total work per unit time) and latency (time for one request) are related but independent — optimizing one doesn't automatically help the other.
- Little's Law (`L = λ × W`) relates concurrency, arrival rate, and latency, and gives a concrete way to size capacity for a target throughput.
- Batching improves throughput by amortizing fixed overhead across many items, at the cost of added latency per item.
- A system's throughput is capped by its single most constrained resource — everything else is optimizing in the wrong place until that bottleneck is found.
- Finding the real bottleneck, rather than adding more of everything, is the practical skill here — it connects directly to Profiling and to Horizontal/Vertical Scaling.
