# Prometheus

# Why Does Prometheus Exist?

Understanding the metric types from the Metrics chapter — counters, gauges, histograms — still leaves a practical question unanswered: something actually needs to collect these values from every running service, store them over time, and let engineers query and aggregate them. Prometheus is the de facto standard open-source system for exactly this, especially in the Kubernetes and cloud-native world.

```
Many services, each with in-memory counters/gauges/histograms

↓

Something needs to: collect these values periodically, store them
                     as time series, and support querying/aggregating
                     them later

↓

Prometheus
```

---

# The Pull Model — Prometheus's Defining Design Choice

This is the single most distinguishing architectural decision behind Prometheus, and it's the opposite of what many people assume by default.

```
Push model (e.g. StatsD):  each application actively SENDS its
                            metrics to a central collector

Pull model (Prometheus):    Prometheus itself actively REACHES OUT
                             and SCRAPES metrics from each service,
                             on a schedule, via a simple HTTP endpoint
```

```python
from prometheus_client import Counter, start_http_server

requests_total = Counter("http_requests_total", "Total HTTP requests")

@app.route("/products")
def get_products():
    requests_total.inc()
    return jsonify(products)

start_http_server(8000)  # exposes current metric values at :8000/metrics
```

```
GET /metrics

# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total 1204532
```

The application does nothing more than expose its current metric values at a simple HTTP endpoint — Prometheus itself, on its own configured schedule (every 15 seconds, for instance), reaches out and scrapes that endpoint.

## Why Pull Instead of Push

```
If a service's scrape FAILS (connection refused, timeout):

↓

Prometheus KNOWS something is wrong — the target is unreachable,
which is itself meaningful, actionable information
```

```
With a PUSH model, if a service simply stops sending data:

↓

Is that because nothing happened (no requests to report)?
Or because the service CRASHED and can no longer push anything?

↓

A push-based collector genuinely can't tell the difference —
"no data" is ambiguous
```

A pull-based system gets a specific, meaningful signal — "the scrape itself failed" — that a push-based system's mere absence of incoming data can't provide on its own. Pull also centralizes *what to scrape and how often* into Prometheus's own configuration, rather than needing every individual service to be separately configured with where to push its data.

---

# PromQL

Prometheus's own query language for aggregating and analyzing collected time series data.

```promql
rate(http_requests_total[5m])
```

```
Computes the PER-SECOND rate of increase of a counter, averaged
over the trailing 5-minute window — turning a raw, ever-increasing
counter value into a meaningful "requests per second" figure
```

```promql
histogram_quantile(0.99, rate(request_duration_seconds_bucket[5m]))
```

```
Computes the p99 latency directly from a histogram's bucket data —
exactly the percentile computation the Metrics chapter described,
expressed as a genuine, ready-to-use query
```

PromQL is what turns raw collected time series into the actual dashboards, alerts, and answers engineers need — "what's our current error rate," "what's our p99 latency over the last hour" are both direct, expressible PromQL queries against the raw data Prometheus has already scraped and stored.

---

# Local Storage Limitations and Long-Term/HA Setups

A single Prometheus instance stores its data locally, on its own disk — which works well for a bounded retention window (weeks, not years) and a single instance's own scale, but has real limits worth knowing about.

```
Single Prometheus instance:  local disk storage, limited retention,
                              a single point of failure for that
                              instance's own data

Thanos / Cortex / Mimir:      systems built specifically to extend
                               Prometheus with long-term, durable,
                               horizontally-scalable remote storage,
                               and to unify queries across MULTIPLE
                               Prometheus instances
```

Teams running Prometheus at real production scale commonly pair it with one of these — not because Prometheus itself is flawed, but because a single instance's local storage was never designed to be the long-term, highly-available, multi-year retention story on its own; these companion projects fill exactly that gap.

---

# Real-World Examples

### The Standard Metrics Backend in Cloud-Native Stacks

Prometheus is close to the default choice for metrics collection across Kubernetes-based and broader cloud-native architectures — its pull-based, service-discovery-aware scraping model fits naturally with Kubernetes's own dynamic, constantly-changing set of pods and services.

---

### OpenTelemetry Integration

The OTel Collector can export metrics directly in Prometheus's format, or Prometheus itself can scrape an OTel-instrumented service's metrics endpoint — a direct, practical example of the vendor-neutral instrumentation layer (OpenTelemetry) and a specific storage/query backend (Prometheus) working together.

---

### Kubernetes' Own Metrics Server and Ecosystem

Much of the broader Kubernetes observability ecosystem (kube-state-metrics, node-exporter) is built specifically to expose cluster and node-level metrics in Prometheus's own scrape format, reflecting how deeply Prometheus's conventions have become the shared standard across the ecosystem.

---

# Common Interview Questions

## Pull vs push for metrics collection — what's the actual trade-off?

A pull-based system (Prometheus) gets a meaningful, actionable signal when a scrape fails — the target is genuinely unreachable. A push-based system can't distinguish "nothing happened" from "the service crashed and stopped pushing entirely," since both look identical: an absence of incoming data. Pull also centralizes scrape configuration (what to collect, how often) in one place rather than requiring every service to be separately configured with a push destination.

---

## How does Prometheus know if a service is down?

Because it actively scrapes each target on a schedule — if a scrape attempt fails (connection refused, timeout), Prometheus directly knows the target is unreachable, which is itself a meaningful, alertable signal, distinct from the target simply having no new data to report.

---

## What is PromQL used for?

Prometheus's query language for aggregating and analyzing the time series data it's collected — computing a counter's rate of increase over time, calculating percentiles from histogram bucket data, or building the underlying queries that power dashboards and alerting rules.

---

## Why might you pair Prometheus with Thanos, Cortex, or Mimir?

Because a single Prometheus instance's local disk storage has real limits on retention and scale, and represents a single point of failure for that instance's own data. These companion projects extend Prometheus with durable, horizontally-scalable long-term storage and let queries span multiple Prometheus instances, addressing exactly the gap a single instance's local storage wasn't designed to fill on its own.

---

## Why does Prometheus's pull model fit naturally with Kubernetes?

Because Kubernetes environments have a constantly changing set of pods and services — Prometheus can use Kubernetes's own service discovery to know what currently exists and needs to be scraped, rather than requiring every dynamically-created pod to separately know where to push its own metrics.

---

# Common Mistakes

❌ Assuming a single Prometheus instance scales indefinitely for long-term storage without any additional architecture.

Local disk storage has real retention and scale limits — production setups needing long-term retention or high availability typically pair Prometheus with Thanos, Cortex, or Mimir rather than relying on one instance alone.

---

❌ Exposing high-cardinality labels on a service's `/metrics` endpoint.

The exact cardinality explosion problem from the Metrics chapter, applied concretely here — a label like `user_id` on a frequently-scraped metric can overwhelm Prometheus with an unbounded number of distinct time series.

---

❌ Treating a push-based system's silence as equivalent to a pull-based system's failed scrape.

They carry genuinely different meaning — a pull-based scrape failure is a direct, actionable "this target is unreachable" signal; a push-based system's absence of data is ambiguous and requires additional heuristics to interpret correctly.

---

# Key Takeaways

- Prometheus collects metrics via a pull model — actively scraping each service's `/metrics` endpoint on a schedule — rather than services pushing data to it.
- Pull gives Prometheus a direct, meaningful signal when a target is unreachable (the scrape itself fails), which a push-based system's mere absence of data cannot distinguish from "nothing happened."
- PromQL is the query language that turns raw collected time series into the rates, percentiles, and aggregations that power real dashboards and alerts.
- A single Prometheus instance's local storage has real retention and scale limits, which is why production systems at real scale commonly pair it with Thanos, Cortex, or Mimir for durable, long-term, multi-instance storage.
- Prometheus's pull-based, service-discovery-aware scraping model is a natural fit for Kubernetes's constantly changing set of pods and services, which is a large part of why it's become the de facto standard in that ecosystem.
