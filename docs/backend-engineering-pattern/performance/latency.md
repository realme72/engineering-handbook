# Latency

# Why Does Latency Matter So Much?

Latency is the time a single request takes, end to end — from the moment it's sent to the moment the response arrives. It's the most user-visible performance metric there is: nobody experiences "throughput." They experience how long their click, search, or checkout took to respond.

```
User clicks "Buy Now"

↓

... 3,000 milliseconds later ...

↓

Response finally arrives

↓

That 3 seconds is exactly what the user experienced — and it's a
concrete, measured business cost, not just an abstract engineering metric
```

Amazon's own internal finding — every additional 100ms of latency cost them roughly 1% in sales — is why serious companies don't treat latency as a nice-to-have. It's tracked as a business metric with a real, quantified dollar cost attached.

---

# Where Latency Actually Comes From

A request's total latency is the sum of a lot of individual pieces, most invisible unless you go looking for them.

```
DNS resolution           (from the DNS chapter)
TCP handshake             (from the TCP chapter)
TLS handshake              (from the TLS chapter)
Network transit time       (physical distance — from the CDN chapter)
Server processing time      (business logic, database queries)
Queueing time                (waiting for an available thread/connection
                              — from the Connection Pooling chapter)
Serialization/deserialization (converting data to/from JSON, etc.)
```

DNS, TCP, and TLS all happen before a single line of your business logic runs, and they're completely invisible to application code. Reducing latency usually means looking at the whole request path (much of it covered across the Networking section), not just profiling your own handlers.

---

# Latency Should Be Measured in Percentiles, Not Averages

Covered in depth in the Metrics chapter, and worth repeating here because this is where the mistake shows up most: a good average can hide a genuinely bad experience for a real chunk of your users. Talk about latency in p50/p95/p99, not a single average number.

---

# Tail Latency Amplification

A deep, underappreciated idea from Google's "The Tail at Scale" paper — naming it correctly in an interview is a real signal.

```
A single user request fans out to 10 backend calls, run in PARALLEL,
and waits for ALL 10 to complete before responding

↓

Each individual backend has a perfectly reasonable p99 latency —
say, 1% of its calls take longer than 100ms

↓

What's the probability that AT LEAST ONE of the 10 parallel calls
hits ITS OWN tail latency?

↓

Even at just 1% per call, with 10 independent calls:
1 - (0.99)^10 ≈ 9.6% chance AT LEAST ONE of them is slow

↓

The OVERALL request's latency is bounded by the SLOWEST of the
10 calls — so nearly 1 in 10 overall requests now experiences
tail-level latency, even though each individual backend's OWN
tail latency rate was only 1%
```

Here's the counterintuitive part: fanning out to more parallel dependencies makes your overall tail latency *worse*, even if every individual dependency's own tail stays exactly the same. The odds that at least one of many parallel calls hits its tail just grow with the number of calls. A system built from many individually well-behaved microservices can still end up with a surprisingly ugly p99, purely from this compounding effect.

---

# Reducing Latency

```
Caching:              avoid the expensive work entirely on a
                       repeated request (the full Caching section)

Fewer round trips:     HTTP/2 multiplexing, connection reuse,
                        avoiding unnecessary sequential calls
                        (the Networking section)

CDN / edge placement:  serve data from physically closer to the
                        user, reducing network transit time itself
                        (the CDN chapter)

Parallelizing work:    do independent pieces of work simultaneously
                        rather than sequentially, where genuinely safe

Request hedging:       for a request to a resource with multiple
                        replicas, send a SECOND, duplicate request to
                        a different replica if the first hasn't
                        responded within some threshold, and use
                        whichever response arrives first — directly
                        addresses tail latency amplification by
                        giving a slow individual call a second chance
                        to actually complete on time
```

Hedging is the clever one here. Instead of accepting that one of many parallel calls will occasionally hit its tail, you give a slow call a second shot via a different replica — trading a bit of extra load (the duplicate request) for a noticeably better tail.

---

# Real-World Examples

### Amazon's 100ms Finding

Cited everywhere because it turns an abstract engineering concern into a concrete number with a dollar sign on it — a memorable reason latency work gets prioritized at serious scale.

---

### Google's "The Tail at Scale"

The paper that formalized tail latency amplification and proposed hedged requests as a fix. Worth reading directly if you want the full argument, since the effect isn't obvious from first principles.

---

### CDN Edge Placement

Reducing the physical distance data travels is one of the most reliable ways to cut latency for a geographically spread-out user base — and it works independent of anything you do at the application level.

---

# Common Interview Questions

## What contributes to a request's overall latency?

DNS resolution, TCP and TLS handshakes, network transit time, server-side processing, time spent queued waiting for a resource (a thread, a database connection), and serialization overhead. A lot of this happens before your application logic even runs, which is why reducing latency usually means looking at the whole request path, not just your own code.

---

## What is tail latency amplification, and why does fanning out to more services make it worse?

When a request waits on multiple parallel backend calls, its overall latency is bounded by the slowest one. The odds that at least one of those calls hits its own tail latency grow with the number of calls, even if each call's individual tail rate stays fixed. A system built from many well-behaved services can still end up with a much worse overall p99, purely from this compounding effect.

---

## How would you reduce latency in a system?

Caching to skip repeated expensive work, fewer round trips (connection reuse, HTTP/2 multiplexing), a CDN to shorten network transit, parallelizing independent work, and for tail latency specifically, hedged requests — send a duplicate to a second replica if the first is slow, use whichever comes back first.

---

## Why does latency matter as a business metric, not just an engineering one?

Because there's real data connecting it to revenue — Amazon's own ~1% sales impact per 100ms is the classic example. It's not an abstract technical concern; it has a measurable cost.

---

## What is a hedged request, and what problem does it solve?

A duplicate request sent to a different replica if the first hasn't responded within some threshold, using whichever comes back first. It's a direct fix for tail latency amplification — instead of hoping a slow call recovers, you give it a second path to succeed on time.

---

# Common Mistakes

❌ Only measuring and optimizing average latency.

Hides the tail experience that matters most for a real chunk of your users — look at p95/p99 alongside (or instead of) the average.

---

❌ Fanning out to many parallel backend dependencies without considering tail latency amplification.

Every dependency looking healthy on its own doesn't mean the combined request is healthy — the odds of hitting at least one tail grow with the number of parallel calls.

---

❌ Ignoring network/physical distance as a real source of latency.

For a geographically spread user base, distance to a single origin server can dominate total latency. No amount of application-level tuning fixes a user being physically far from their data — that's what CDN edge placement is for.

---

# Key Takeaways

- Latency is the most user-visible performance metric, and it has a real, quantifiable business cost — Amazon's ~1% sales impact per 100ms is the classic citation.
- Total latency accumulates across DNS, TCP/TLS handshakes, network transit, server processing, and queueing — much of it outside your own application code.
- Talk about latency in percentiles (p95, p99), not averages — an average can hide a real tail of bad experiences.
- Tail latency amplification means fanning out to more parallel calls worsens overall latency, even with each dependency's own tail unchanged, because the odds of hitting at least one grow with the number of calls.
- Caching, fewer round trips, CDN placement, parallelization, and hedged requests (for tail latency specifically) are the core levers.
