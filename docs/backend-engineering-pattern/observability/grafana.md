# Grafana

# Why Does Grafana Exist?

Prometheus (and similar systems) collect and store metrics — but querying raw PromQL by hand, every time you want to check on a service, isn't how anyone actually wants to work day to day. Engineers need to *see* a service's behavior at a glance — a graph of latency over the last hour, an at-a-glance dashboard of error rates across every service, a heatmap of request volume. Grafana exists specifically to be that visualization layer, sitting on top of the data other systems have already collected.

```
Prometheus:  collects and stores the raw time series data

↓

Grafana:     queries that data and renders it as graphs, dashboards,
             and alerts — the layer humans actually look at
```

---

# Data-Source Agnostic — Grafana Doesn't Store Anything Itself

A frequently confused point worth being precise about: Grafana is not a database, and it doesn't collect metrics on its own. It's a visualization layer that queries **other** systems' already-collected data.

```
Grafana can query, and visualize data from, MANY different sources
simultaneously:

Prometheus   (metrics)
Loki         (logs — Grafana Labs' own log aggregation system)
Tempo        (traces — Grafana Labs' own tracing backend)
Elasticsearch, InfluxDB, CloudWatch, and many others
```

```
One Grafana dashboard, ONE screen, showing:

- A metrics graph, queried from Prometheus
- A log panel, queried from Loki
- A trace view, queried from Tempo

↓

A single "pane of glass" across multiple entirely separate
backend systems, without Grafana itself storing any of that
data — it's purely a query-and-render layer on top of whatever
data sources are configured
```

This is exactly why Grafana pairs so naturally with Prometheus specifically — Prometheus is extremely good at collection and storage with a powerful query language, but has comparatively minimal built-in visualization; Grafana fills exactly that gap without either system needing to do the other's job.

---

# Dashboards

A dashboard is a collection of panels — graphs, tables, heatmaps, single-value displays — each backed by its own query against a data source, arranged together to give an at-a-glance view of a service's health.

```
A typical service dashboard, built around the Four Golden Signals
(from the Metrics chapter):

┌─────────────────┬─────────────────┐
│  Request Rate    │  Error Rate      │
│  (traffic)        │  (errors)        │
├─────────────────┼─────────────────┤
│  p50/p95/p99      │  CPU/Memory      │
│  Latency          │  (saturation)    │
└─────────────────┴─────────────────┘
```

Dashboards are typically built once (often as code, via configuration files, so they're version-controlled and reproducible across environments) and reused across a team — the same dashboard checked during a normal day and pulled up first during an actual incident.

---

# Alerting — And How It Relates to Alertmanager

Grafana itself can evaluate alerting rules directly against its data sources and route notifications — but this overlaps with, and is often used alongside, Prometheus's own dedicated alerting component (Alertmanager, covered in the Alerting chapter). Worth distinguishing clearly: Prometheus/Alertmanager historically handled alert *evaluation and routing* specifically for Prometheus-sourced metrics, while Grafana's own alerting can evaluate rules against any of its configured data sources (not just Prometheus) and has increasingly become a unified alternative — teams need to make a deliberate choice (or clearly divide responsibility) about which system is the actual source of truth for a given alert, rather than accidentally running the same alert logic in both places.

---

# Real-World Examples

### Grafana + Prometheus

The single most common pairing in cloud-native observability stacks — Prometheus handles collection, storage, and querying via PromQL; Grafana handles visualization and dashboarding on top of it, each doing the part of the job it's actually built for.

---

### Grafana Loki and Grafana Tempo

Grafana Labs' own additions extending the "single pane of glass" idea across all three observability pillars — Loki for logs, Tempo for traces, alongside Prometheus for metrics — all queryable and visualizable from within the same Grafana instance, unifying what would otherwise be three separate tools' worth of dashboards into one.

---

### Incident Response Dashboards

A dashboard built specifically around the four golden signals is frequently the very first thing an on-call engineer pulls up the moment an alert fires — a direct, practical illustration of why a focused, well-designed dashboard (not a cluttered one, covered as a common mistake below) matters during a real, time-pressured incident.

---

# Common Interview Questions

## What role does Grafana play, and how is it different from Prometheus?

Prometheus collects, stores, and provides a query language (PromQL) for metrics data. Grafana is the visualization layer on top — it doesn't store or collect any data itself, it queries Prometheus (and potentially many other data sources) and renders that data as dashboards, graphs, and alerts. They serve different, complementary roles in the same observability stack rather than competing for the same job.

---

## Is Grafana a database?

No — it's a query-and-visualization layer that connects to other systems (Prometheus, Loki, Elasticsearch, and many others) which actually store the underlying data. Grafana's value is in querying and rendering data from potentially many different sources in one unified interface, not in storing anything itself.

---

## How do you decide what to put on a dashboard?

The four golden signals (latency, traffic, errors, saturation, from the Metrics chapter) are a strong, practical starting framework for any service's primary dashboard — giving an at-a-glance view of health without needing to hunt through dozens of panels. Additional, more specific panels can supplement this baseline for a particular service's unique concerns, but the core signals should be immediately visible without digging.

---

## How does Grafana's alerting relate to Prometheus's Alertmanager?

They can overlap in responsibility — Alertmanager has historically been the dedicated component for evaluating and routing alerts based on Prometheus metrics specifically, while Grafana's own alerting can evaluate rules against any of its configured data sources, not just Prometheus, and has increasingly become capable of serving as a unified alternative. Teams need to deliberately decide which system owns a given alert's evaluation and routing, rather than risk duplicating the same alert logic in both places unintentionally.

---

## Why does Grafana pair so naturally with Prometheus specifically?

Because Prometheus is strong at collection, storage, and powerful querying (PromQL) but has comparatively minimal built-in visualization, while Grafana is specifically built for visualization and doesn't do its own collection or storage — each system does the part of the job it's actually designed for, and together they cover the full path from raw data to a human-readable dashboard.

---

# Common Mistakes

❌ Confusing Grafana with Prometheus as if they perform the same function.

Grafana visualizes; Prometheus collects, stores, and queries — treating them as interchangeable, or assuming one replaces the need for the other, misunderstands how the two actually fit together in a typical stack.

---

❌ Building overly cluttered dashboards with dozens of panels instead of focusing on what actually matters.

Makes it harder, not easier, to quickly diagnose a real incident — a focused dashboard built around the golden signals is more useful under time pressure than one crammed with every metric that could conceivably be measured.

---

❌ Running duplicate, uncoordinated alerting logic in both Grafana and Alertmanager for the same underlying condition.

Creates confusion about which system is actually the source of truth for a given alert, and risks inconsistent thresholds or routing between the two — a deliberate choice about ownership avoids this.

---

# Key Takeaways

- Grafana is a visualization layer, not a data store — it queries other systems' already-collected data (Prometheus, Loki, Tempo, and many others) and renders it as dashboards, graphs, and alerts.
- It's data-source agnostic, letting a single dashboard combine metrics, logs, and traces from entirely different backend systems into one unified "pane of glass."
- Dashboards should be built around focused, meaningful signals (the four golden signals are a strong default) rather than cluttered with every possible metric, especially for anything meant to be useful during a real incident.
- Grafana's own alerting can overlap with Prometheus's Alertmanager — teams need to deliberately decide which system owns evaluation and routing for a given alert, rather than risk running duplicate logic in both.
- Grafana Loki and Tempo extend the same visualization philosophy to logs and traces, unifying all three observability pillars under one interface.
