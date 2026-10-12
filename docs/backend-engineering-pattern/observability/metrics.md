# Metrics

# Why Do Metrics Exist?

Logs record discrete events — one specific request failed, one specific job started. But understanding a system's overall behavior over time — "is latency trending upward this hour," "how much memory are we using right now," "what fraction of requests are failing" — by scanning individual log lines is impractical at any real volume. Metrics exist to answer exactly this kind of question: numeric measurements, sampled or aggregated over time, that are dramatically cheaper to store and query at scale than full-detail logs of every individual event.

```
Logs:     "request 8821 failed at 10:15:32 with a 500 error"
           (one specific event, full detail)

Metrics:  "error rate: 2.3% over the last 5 minutes"
           (an aggregate number, computed from many events)
```

A metric trades away the specific detail of any single event in exchange for being able to track a trend or aggregate across millions of events cheaply — exactly what's needed for dashboards, alerting, and understanding a system's health at a glance.

---

# Metric Types

## Counter

```
A value that only ever goes UP (or resets to zero on restart) —
never decreases.

total_requests_served: 1,204,532
```

Used for anything that only accumulates — total requests handled, total errors encountered, total bytes sent. You never "decrement" a counter; you only ever increase it.

## Gauge

```
A value that can go up OR down, representing a current state.

current_memory_usage_mb: 512
active_connections: 47
```

Used for anything representing a current snapshot — memory usage, queue depth, the number of currently active connections — values that naturally fluctuate in both directions, unlike a counter.

## Histogram

```
Tracks the DISTRIBUTION of values across configured buckets,
not just a single number.

request_duration_seconds_bucket{le="0.1"}  8500
request_duration_seconds_bucket{le="0.5"}  9800
request_duration_seconds_bucket{le="1.0"}  9950
request_duration_seconds_bucket{le="+Inf"} 10000
```

A histogram counts how many observations fell at or below each bucket boundary — from this bucketed data, percentiles (covered next) can be computed after the fact, at query time, which is exactly what makes histograms so useful for latency measurement specifically.

## Summary

Similar in purpose to a histogram — tracking a distribution — but computes specific quantiles (percentiles) directly on the client side, before the data is even collected, rather than storing raw bucket counts for the aggregation system to compute quantiles from later. The trade-off: summaries are cheaper to query but can't be aggregated correctly across multiple instances the way histogram buckets can (you can't meaningfully average two different instances' pre-computed p99 values into a system-wide p99), which is a large part of why histograms are generally the more common and more useful choice for anything you need aggregated across many service instances.

---

# The Four Golden Signals

A widely cited, practical framework (from Google's SRE book) for what to actually monitor for any given service, when the question "what should we measure?" would otherwise be paralyzing in its breadth.

```
Latency:      how long requests take (and specifically, the
              DISTRIBUTION of that time — see percentiles below)

Traffic:      how much demand the system is currently receiving
              (requests per second, for instance)

Errors:       the rate of requests failing

Saturation:   how "full" the system is — how close to its
              capacity limits (CPU, memory, connection pool usage)
```

These four signals, tracked for any service, give a strong, practical baseline understanding of its health — a large share of real production dashboards are, in essence, a direct implementation of exactly these four categories, service by service.

---

# Why Average Latency Is a Misleading Metric

This is one of the most commonly tested, genuinely important ideas in this entire chapter — a classic interview question precisely because the mistake is so easy to make without thinking about it carefully.

```
100 requests:

99 requests complete in 50ms
1 request takes 5,000ms (5 seconds)

↓

Average latency = (99 × 50 + 5000) / 100 ≈ 99.5ms

↓

The average LOOKS totally fine — under 100ms!

↓

But 1% of your users just had a genuinely terrible, 5-second experience,
and the average completely HID it
```

This is exactly why percentiles (**p50**, **p95**, **p99**) matter far more than a single average for understanding real user experience — p99 latency tells you "the slowest 1% of requests took at least this long," which surfaces exactly the tail-latency problem an average silently absorbs and hides. A system with a great average but a terrible p99 is a system where a meaningful fraction of real users are having a bad time, invisible to anyone only watching the average.

```
p50 (median):  half of requests were faster than this
p95:           95% of requests were faster than this (5% were slower)
p99:           99% of requests were faster than this (1% were slower)
```

At real traffic volume, even a "small" 1% tail can represent thousands of genuinely bad experiences per day — which is exactly why serious SLOs (covered in their own chapter) are almost always defined in terms of a percentile, not an average.

---

# Cardinality

A genuinely important, often-overlooked concept: every unique combination of a metric's label values creates a separate, independently-tracked time series underneath. Adding a label with too many possible distinct values can cause a real, serious operational problem.

```
http_requests_total{method="GET", status="200", user_id="42"}
http_requests_total{method="GET", status="200", user_id="43"}
http_requests_total{method="GET", status="200", user_id="44"}
...
```

```
Reasonable labels (a small, bounded set of possible values):
  method (GET, POST, ...), status (200, 404, 500, ...)
  → a manageable, small number of distinct time series

High-cardinality label (an unbounded, huge set of possible values):
  user_id, request_id, a raw email address
  → potentially MILLIONS of distinct time series, one per unique value ever seen
```

This is called a **cardinality explosion**, and it's a real, common production incident cause — a metrics system that's perfectly healthy tracking a few thousand time series can become catastrophically slow, or run out of memory entirely, the moment someone adds a high-cardinality label like `user_id` to a metric that's incremented on every request. The fix is straightforward once understood: only use labels with a small, bounded, genuinely limited set of possible values on metrics — anything with unbounded cardinality (a user ID, a raw request ID) belongs in logs or traces, not as a metric label.

---

# Real-World Examples

### Prometheus's Metric Format

The de facto standard exposition format for metrics in the cloud-native world — services expose their current counters, gauges, and histograms via a simple `/metrics` HTTP endpoint, in exactly the plain-text format shown throughout this chapter, covered in full depth in the Prometheus chapter.

---

### StatsD

An older, simpler, push-based alternative for collecting counters, gauges, and timers — historically influential, though largely superseded by Prometheus's pull-based model (covered in the Prometheus chapter) in most modern cloud-native stacks.

---

### Latency SLOs Defined in Percentiles

Nearly every serious production SLO for latency is defined as a percentile threshold ("p99 latency under 300ms"), not an average — a direct, practical consequence of the average-hides-the-tail problem described above, and a strong signal in an interview that you understand why.

---

# Common Interview Questions

## What's the difference between a counter, a gauge, and a histogram?

A counter only ever increases (total requests served); a gauge can go up or down, representing a current value (current memory usage); a histogram tracks the distribution of observed values across buckets, letting percentiles be computed from it after the fact — essential for something like latency, where the distribution's shape matters far more than a single aggregate number.

---

## Why is p99 latency more useful than average latency?

Because an average can look perfectly healthy while hiding a real, meaningful tail of bad experiences — a small percentage of very slow requests can be mathematically absorbed into an otherwise-good average without visibly affecting it. p99 specifically surfaces "how bad is the experience for the slowest 1% of requests," which is exactly the information an average discards.

---

## What are the four golden signals?

Latency (how long requests take), traffic (how much demand the system is receiving), errors (the rate of failures), and saturation (how close to capacity the system is) — a widely cited, practical framework from Google's SRE practice for what to monitor for any given service.

---

## What is cardinality, and why does high cardinality cause real problems?

Cardinality refers to the number of unique label-value combinations a metric can have — each unique combination creates a separate, independently-tracked time series. A label with an unbounded or very large set of possible values (like a raw user ID) can explode the number of time series a metrics system has to track, potentially into the millions, causing serious performance degradation or outright failure of the metrics system itself — this is why high-cardinality data belongs in logs or traces, not metric labels.

---

## When would you use a histogram instead of a summary?

A histogram, since it stores raw bucket counts, can be correctly aggregated across many service instances (computing a genuine system-wide percentile from many instances' bucket data). A summary computes its quantiles client-side, before aggregation, which means those pre-computed percentiles can't be meaningfully combined across instances — histograms are generally the better default whenever metrics need to be aggregated across multiple sources.

---

# Common Mistakes

❌ Using average latency as the primary metric for understanding user experience or defining an SLO.

Averages can hide a meaningful tail of bad experiences entirely — percentiles (p95, p99) are what actually surface this.

---

❌ Adding a high-cardinality label (user ID, raw request ID) to a metric.

Risks a cardinality explosion — an unbounded number of unique time series that can seriously degrade or crash the metrics system, when the same data would have been perfectly appropriate as a log field or trace attribute instead.

---

❌ Using a counter for a value that can decrease.

Counters are only meaningful as strictly non-decreasing values — using one for something like "current active connections" (which needs to go down as well as up) is a fundamental type mismatch; that's what a gauge is for.

---

❌ Relying on a summary's pre-computed percentiles when metrics need to be aggregated across multiple service instances.

A summary's client-computed quantiles can't be correctly combined across instances into a genuine system-wide percentile — a histogram's raw bucket data is what makes that aggregation actually valid.

---

# Key Takeaways

- Metrics are numeric measurements, aggregated over time, that trade away individual-event detail for being dramatically cheaper to store and query at scale than full logs — ideal for trends, dashboards, and alerting.
- Counters (only increase), gauges (go up or down), and histograms (track a distribution, enabling percentile computation) are the core metric types, each suited to a different kind of measurement.
- The four golden signals — latency, traffic, errors, saturation — are a practical, widely used baseline framework for what to monitor about any service.
- Average latency can hide a meaningful tail of bad experiences; percentiles (p95, p99) surface exactly what an average discards, which is why serious SLOs are defined in percentiles, not averages.
- Cardinality — the number of unique label-value combinations — needs to stay bounded; high-cardinality labels like user IDs belong in logs or traces, not metrics, or they risk a cardinality explosion that can seriously degrade the metrics system itself.
