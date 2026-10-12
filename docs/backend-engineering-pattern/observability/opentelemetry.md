# OpenTelemetry

# Why Does OpenTelemetry Exist?

Before OpenTelemetry, every observability vendor and open-source tool had its own separate instrumentation library — Prometheus's client libraries for metrics, Jaeger's client libraries for traces, and every commercial vendor's (Datadog, New Relic) own proprietary SDK for all three. An application choosing to instrument itself for observability was choosing, at the same time, to couple its actual application code tightly to one specific vendor's API.

```
Application code, instrumented directly against Vendor A's SDK

↓

Company later decides to switch to Vendor B (cost, features,
a merger, whatever the reason)

↓

Every single instrumentation call throughout the codebase —
scattered across potentially hundreds of services — needs to
be found and rewritten against Vendor B's completely different SDK
```

This is a real, expensive form of vendor lock-in, and it's specifically what OpenTelemetry (OTel) exists to eliminate — a single, vendor-neutral, standardized API and SDK for producing logs, metrics, and traces, decoupling **how you instrument your code** from **which backend you eventually send that data to**.

---

# One Standard, Three Signals

```
OpenTelemetry SDK/API:

Traces   →  the exact span/trace model from the Tracing chapter
Metrics  →  counters, gauges, histograms — the same types from the Metrics chapter
Logs     →  structured log records, correlated with trace context
```

Instrumenting an application with the OTel SDK produces all three signals through one consistent API, regardless of which backend they'll eventually be sent to — the application code itself never needs to know or care whether the data ends up in Prometheus, Jaeger, Datadog, or something else entirely.

---

# The Collector — Where Vendor Neutrality Actually Gets Delivered

The OTel Collector is a separate, standalone process that receives telemetry data from instrumented applications and can process, filter, and route it to any number of backends — this is the piece of the architecture that actually makes switching backends possible without touching application code at all.

```
Instrumented Application (OTel SDK)

↓  sends telemetry data via a standard protocol

OTel Collector

↓  the Collector decides where it goes:

    → Prometheus (metrics)
    → Jaeger (traces)
    → Datadog (everything)
    → any combination, or even multiple destinations at once
```

```
Switching observability vendors, WITHOUT the Collector:

Rewrite instrumentation code across every service

Switching observability vendors, WITH the Collector:

Reconfigure the Collector's output destination — application
code doesn't change at all
```

This is the actual, concrete payoff of the entire OpenTelemetry project — the Collector is what turns "vendor-neutral instrumentation" from a nice idea into something that genuinely removes the cost of switching backends later, since that decision lives entirely in Collector configuration, not scattered throughout application source code.

---

# Why This Matters Enough to Have Become an Industry Standard

```
Before OTel:  N different vendors, each with their OWN separate
              instrumentation SDK — application code coupled to
              whichever one was chosen first

With OTel:    ONE standard instrumentation layer, with the choice
              of backend(s) pushed entirely into Collector
              configuration — a decision that can change later
              with zero impact on application code
```

OpenTelemetry is now one of the most active projects under the Cloud Native Computing Foundation (CNCF) — the same foundation that hosts Kubernetes — reflecting just how broadly the industry converged on this as the standard way to instrument applications, specifically because the vendor-lock-in problem it solves was real and expensive for essentially every company operating at any meaningful scale.

---

# Real-World Examples

### OTel SDK + Prometheus + Jaeger

A very common, fully open-source combination — applications instrumented with the OTel SDK, with the Collector configured to export metrics to Prometheus and traces to Jaeger, giving a complete, standards-based observability stack with no single vendor's proprietary lock-in anywhere in the chain.

---

### Companies Migrating Observability Vendors

The direct, practical payoff this chapter describes — a company instrumented with OTel from the start can change its downstream observability vendor (for cost, features, or any other business reason) by reconfiguring the Collector, without a single line of application instrumentation code needing to change.

---

### CNCF's Broad Industry Backing

OpenTelemetry's status as one of the CNCF's most active projects is itself a real-world signal of just how widely the vendor-neutral instrumentation problem was felt across the industry — a strong, direct answer to "why does a standard like this matter" in an interview.

---

# Common Interview Questions

## Why does OpenTelemetry exist?

Because before it, every observability vendor and tool had its own separate, proprietary instrumentation SDK, coupling application code tightly to whichever vendor was chosen first. Switching vendors later meant finding and rewriting every instrumentation call throughout a codebase. OpenTelemetry provides one vendor-neutral standard for instrumenting logs, metrics, and traces, decoupling how code is instrumented from which backend ultimately receives the data.

---

## What does vendor lock-in in observability actually look like in practice?

An application's source code directly calling a specific vendor's SDK for logging, metrics, or tracing — meaning a decision to switch vendors requires finding and rewriting every one of those calls across potentially hundreds of services, a genuinely expensive migration cost that has nothing to do with the actual business reason for wanting to switch.

---

## What is the OTel Collector, and why does it matter?

A standalone process that receives telemetry data from instrumented applications and routes it to any configured backend (or multiple backends at once). It's what actually delivers on OpenTelemetry's vendor-neutrality promise in practice — changing where telemetry data goes becomes a Collector configuration change, not a rewrite of application instrumentation code.

---

## How does OpenTelemetry relate to Prometheus and Jaeger?

OpenTelemetry standardizes how applications produce telemetry data (metrics, traces, logs); Prometheus and Jaeger are backends that store and let you query/visualize that data once it's been collected. The OTel Collector can export metrics to Prometheus and traces to Jaeger (or many other backends) — OpenTelemetry doesn't replace these tools, it standardizes the layer that feeds them.

---

## Would you instrument a new service directly against Prometheus's client library, or use OpenTelemetry?

OpenTelemetry, in almost every case — instrumenting directly against a specific backend's own client library reintroduces the exact vendor-coupling problem OTel exists to solve, even if Prometheus happens to be the intended backend today; a future decision to add tracing, switch backends, or adopt a different metrics store becomes far more expensive without the OTel layer in between.

---

# Common Mistakes

❌ Instrumenting application code directly against a specific vendor's proprietary SDK when a vendor-neutral standard is available.

Reintroduces exactly the lock-in problem OpenTelemetry was built to eliminate, even if switching vendors isn't an immediate concern — the cost shows up later, when it becomes one.

---

❌ Hardcoding a specific backend destination directly in application instrumentation instead of routing through the Collector.

Removes the actual practical benefit of OpenTelemetry — the Collector is what makes changing backends a configuration change instead of a code change; skipping it reintroduces coupling at a different layer.

---

❌ Treating OpenTelemetry as a replacement for Prometheus, Jaeger, or Grafana.

OTel standardizes instrumentation and collection — it doesn't replace the storage, querying, or visualization tools those systems provide; they work together, not as substitutes for one another.

---

# Key Takeaways

- OpenTelemetry exists to eliminate vendor lock-in at the instrumentation layer — before it, every observability vendor had its own proprietary SDK, tightly coupling application code to whichever one was chosen first.
- One standard API/SDK produces all three telemetry signals — traces, metrics, and logs — regardless of which backend the data eventually ends up in.
- The OTel Collector is what actually delivers vendor neutrality in practice — routing telemetry data to any backend (or multiple at once) is a Collector configuration decision, not an application code change.
- OpenTelemetry's status as one of the CNCF's most active projects reflects how broadly the industry has converged on it as the standard instrumentation layer.
- OpenTelemetry doesn't replace tools like Prometheus, Jaeger, or Grafana — it standardizes how telemetry data is produced and collected before it reaches them.
