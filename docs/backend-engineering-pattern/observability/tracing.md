# Distributed Tracing

# Why Does Distributed Tracing Exist?

Correlation IDs, from the Logging chapter, solve the problem of tying together log lines from the same request across multiple services — but they only give you scattered log entries to manually piece together. A single slow user request in a microservices system might touch a dozen different services, and the real question an engineer needs answered is much more specific than "which logs relate to this request": **exactly where, across that entire chain of service calls, did the time actually go?**

```
User request: 2.3 seconds total, feels slow

↓

Which of these ate up the time?

API Gateway → Order Service → Payment Service → Inventory Service
    ?              ?                 ?                 ?
```

Distributed tracing exists to answer exactly this — reconstructing the full, timed path of one request across every service it touched, so an engineer can see precisely which service (and which specific operation within it) was actually responsible for the slowness, instead of guessing from scattered, disconnected logs.

---

# Traces and Spans

```
A TRACE  =  the entire end-to-end journey of one request,
            across every service it touched

A SPAN   =  one unit of work WITHIN that journey — one specific
            service call, one specific database query, one
            specific operation with its own start and end time
```

```
Trace: "GET /checkout" (total: 2.3s)

├── Span: API Gateway routing        (10ms)
├── Span: Order Service - create order  (150ms)
│     └── Span: Database INSERT       (140ms)
├── Span: Payment Service - charge card  (1,900ms)  ← THE BOTTLENECK
│     └── Span: External payment API call  (1,880ms)
└── Span: Inventory Service - reserve stock  (200ms)
```

Spans form a parent-child tree — the whole request is the root, and every service call or sub-operation within it is a child span, nested as deeply as the actual call chain goes. Visualized as a **waterfall** (bars laid out over time, one per span), this immediately makes the bottleneck visually obvious — in the example above, 1.9 of the 2.3 total seconds is spent in one specific external API call inside the Payment Service, not spread evenly across every service.

---

# Context Propagation — How a Trace Actually Gets Reconstructed

Every span needs to know which trace it belongs to, and which span is its parent — this information has to travel *with* the request itself, across every service boundary it crosses.

```http
GET /orders/42 HTTP/1.1
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

The `traceparent` header (the W3C Trace Context standard) carries the trace ID and the current span ID along with the request. Each service that receives it:

```
1. Reads the incoming traceparent header

2. Creates its OWN new span, marking the incoming span as its PARENT

3. When it calls ANOTHER service, attaches an updated traceparent
   header (same trace ID, new parent span ID = its own span) to
   that outgoing call

4. Reports its completed span (with timing) to the tracing backend
```

This is exactly what stitches together spans generated independently by completely different services, running on different machines, into one coherent trace — every span, no matter which service generated it, carries enough information to know exactly where it fits in the overall tree.

---

# Real, Practical Uses Beyond "Where Was It Slow"

Tracing isn't only useful for diagnosing a single slow request — it can reveal structural problems in how services interact that would be very difficult to spot any other way.

```
A trace shows Service B calling Service C not once, but SEVEN times,
each attempt slightly slower than the last

↓

This is EXACTLY what retry amplification (from the Distributed
Systems section) looks like when you can actually SEE it — a trace
makes an otherwise invisible cascading retry pattern immediately
visible, rather than something inferred indirectly from aggregate
metrics alone
```

A trace can directly reveal a retry storm, an unexpectedly chatty service making far more downstream calls than expected, or a circuit breaker repeatedly tripping — problems that are genuinely hard to diagnose from metrics or logs alone, but become immediately, visually obvious once you can see the actual shape of one request's full call tree.

---

# Real-World Examples

### Jaeger

A widely used open-source distributed tracing backend — receives spans reported by instrumented services, stores them, and provides the waterfall-style visualization used throughout this chapter to explore a trace's full timing breakdown.

---

### Zipkin

An earlier, historically influential open-source tracing system, serving a similar purpose to Jaeger — one of the systems that helped establish distributed tracing as a standard practice before OpenTelemetry (its own chapter) unified how tracing data gets generated across different backends.

---

### Diagnosing a Slow Checkout Flow

The exact motivating scenario from this chapter's opening — a genuinely common, real production use case where a trace immediately reveals which specific service and which specific operation within it is actually responsible for a slow end-to-end user experience, rather than requiring guesswork across a dozen services' independent logs.

---

# Common Interview Questions

## What problem does distributed tracing solve that logs and metrics don't?

Logs give discrete, disconnected events per service, and metrics give aggregate numbers over time — neither reconstructs the specific, timed path of *one particular request* across every service it touched. Tracing does exactly that, making it possible to see precisely where time was spent across an entire multi-service call chain for a single request, rather than inferring it indirectly.

---

## What's the difference between a trace and a span?

A trace is the entire end-to-end journey of one request across every service it touched. A span is one specific unit of work within that journey — one service call, one database query — with its own start and end time. Spans form a parent-child tree that together make up the full trace.

---

## How does context propagation work across service boundaries?

A trace ID and the current span ID are carried along with the request itself, typically via an HTTP header (`traceparent`, per the W3C Trace Context standard). Each service that receives it creates its own span marked as a child of the incoming span, and attaches an updated header (same trace ID, its own span as the new parent) to any further calls it makes — this is what lets independently-generated spans from different services be correctly stitched together into one coherent trace.

---

## How would you use a trace to diagnose a slow request?

Look at the waterfall visualization of the request's full span tree — the span (or child spans) taking up the largest share of the total time is the actual bottleneck, which might be a specific service, a specific database query, or a specific external API call, rather than the slowness being evenly distributed across every service the request touched.

---

## What's a common gap in trace propagation that teams often miss?

Not propagating trace context across asynchronous boundaries — particularly message queues. If a service publishes an event without carrying the trace context forward, and the consuming service starts a brand-new, disconnected trace, the overall request's journey through the async portion of the flow becomes invisible, breaking the trace's continuity exactly at the point where async processing takes over.

---

# Common Mistakes

❌ Not propagating trace context across message queue boundaries.

Breaks trace continuity the moment a request's flow goes asynchronous — the resulting downstream processing shows up as an unrelated, disconnected trace instead of a continuation of the original request's journey.

---

❌ Sampling traces too aggressively.

If only a small, random percentage of traces are kept, the specific slow, unusual outlier requests you most need to diagnose can easily be the ones that get dropped — sampling strategy needs to account for keeping traces for anomalous or slow requests, not just a uniform random sample.

---

❌ Treating tracing as a replacement for logs and metrics rather than a complement.

Tracing answers "where did time go for this one request" — it doesn't replace metrics' aggregate trend visibility or logs' detailed, arbitrary event context; all three pillars serve different, complementary purposes.

---

# Key Takeaways

- Distributed tracing reconstructs the full, timed path of one request across every service it touched, answering "where did the time actually go" in a way neither logs nor metrics can on their own.
- A trace is the whole journey; a span is one unit of work within it — spans form a parent-child tree, visualized as a waterfall to make the actual bottleneck immediately visible.
- Context propagation (a trace ID and current span ID carried via a header like `traceparent`) is what lets independently-generated spans from many different services be stitched together into one coherent trace.
- Traces can reveal structural problems — like retry amplification or an unexpectedly chatty service — that are difficult to spot from aggregate metrics or scattered logs alone.
- Trace context needs to be explicitly propagated across asynchronous boundaries like message queues, or the trace's continuity breaks exactly where async processing takes over — a common, easy-to-miss gap.
