# Logging

# Why Does Logging Exist?

A production system runs unattended, most of the time, with no human watching each individual request as it happens. When something goes wrong — a request fails, a background job errors out — there's no way to go back in time and watch it happen again. Logging exists to leave a durable, after-the-fact record of discrete events, specifically so an engineer can reconstruct what actually happened, hours or days later, without having needed to be watching live.

```
Request comes in → something goes wrong → request fails

↓

Without logs:  no way to know WHY it failed, after the fact

↓

With logs:     a record of what the code was doing, what data it
                had, and where it failed — reconstructable long
                after the actual request completed
```

---

# Structured vs Unstructured Logging

## Unstructured (Plain Text)

```
2026-07-22 10:15:32 ERROR Failed to process order 42 for user 7: insufficient stock
```

Readable by a human scanning a file directly — but hard to query at scale. Finding "every failed order for user 7 in the last week" means grep-ing through text and hoping the message format stayed consistent.

## Structured (Typically JSON)

```json
{
    "timestamp": "2026-07-22T10:15:32Z",
    "level": "ERROR",
    "message": "Failed to process order",
    "order_id": 42,
    "user_id": 7,
    "reason": "insufficient_stock"
}
```

Every field is a real, queryable attribute — "show me every log where `reason = insufficient_stock` and `user_id = 7`" becomes a precise, structured query instead of a hopeful text search. At any real production scale — millions of log lines a day — structured logging is what makes logs actually searchable rather than just readable one file at a time.

---

# Log Levels

```
DEBUG  →  fine-grained detail, useful only while actively debugging
           a specific issue, usually disabled in production by default

INFO   →  normal, expected events worth recording (a request completed,
           a job started)

WARN   →  something unexpected happened, but the system recovered or
           continued anyway

ERROR  →  something failed, and it likely needs attention

FATAL  →  the application cannot continue running at all
```

Levels exist so verbosity can be controlled per environment and per moment — a production system typically runs at `INFO` or `WARN` by default (to avoid the cost and noise of `DEBUG`-level output at scale), with the ability to temporarily raise verbosity when actively investigating a specific problem.

---

# Correlation IDs — The Concept That Makes Logs Useful in a Distributed System

This is the single most important idea in this entire chapter for any system with more than one service, and it directly sets up the Tracing chapter.

```
One user request:  Client → API Gateway → Order Service → Payment Service

↓

Each service writes its OWN logs, independently, with no
inherent connection to the others
```

```json
// Order Service's log
{ "message": "Creating order", "order_id": 42 }

// Payment Service's log (a moment later)
{ "message": "Charging card", "amount": 500 }
```

Without anything tying these together, there's no way to know these two log lines came from the *same* originating request — if the payment failed, an engineer has no way to find the corresponding order-creation log line among millions of unrelated ones.

```json
// Order Service's log
{ "message": "Creating order", "order_id": 42, "correlation_id": "req-abc123" }

// Payment Service's log
{ "message": "Charging card", "amount": 500, "correlation_id": "req-abc123" }
```

A **correlation ID** — generated once at the edge (typically the API Gateway) and propagated through every subsequent service call (usually via an HTTP header) — gets attached to every log line related to that one request, across every service it touches. Now "find every log line for this one user's failed request" is a single query filtering on one ID, regardless of how many services were involved. This is the foundational idea that Distributed Tracing (its own chapter) formalizes and builds a much richer visualization on top of.

---

# Centralized Log Aggregation

In any system with more than a handful of servers — and especially with ephemeral, frequently-recreated containers — logs sitting on individual machines' local disks are effectively unusable. A container that crashed and got replaced takes its logs with it unless they were shipped somewhere durable first.

```
Individual servers/containers, each writing logs LOCALLY

↓

A log shipper (Fluentd, Logstash, a cloud-native agent) reads
each server's logs and forwards them to a CENTRAL, durable,
searchable store

↓

Engineers query ONE central system instead of needing to know
which of potentially hundreds of individual machines to SSH into
```

This is not optional infrastructure at any real scale — without centralization, debugging a distributed system means guessing which of many machines might have the relevant log, then manually connecting to check, one at a time, which becomes completely impractical past a handful of instances.

---

# Log Volume and Sampling at Scale

Logging everything, at full verbosity, for every single request, gets genuinely expensive at high traffic volumes — both in storage cost and in how slow searching becomes across an enormous volume of largely-redundant data.

```
Every request logs 5 lines × 100,000 requests/minute
= 500,000 log lines/minute, most of them "everything worked fine"
```

Real production systems often apply **sampling** — logging full detail for only a subset of requests (or specifically for slow/failed ones, which matter most) rather than every single one — trading some completeness for a manageable volume and cost. This is a deliberate trade-off, not a compromise made reluctantly; the goal is having enough signal to debug real problems, not literally every byte of every request.

---

# Real-World Examples

### ELK / EFK Stack

Elasticsearch (storage and search), Logstash or Fluentd (log shipping and processing), and Kibana (visualization) — one of the most widely adopted open-source combinations for centralized log aggregation, giving teams a searchable, queryable interface over logs collected from potentially hundreds of individual services and machines.

---

### Datadog / CloudWatch Logs

Managed, cloud-native equivalents of the same idea — centralized ingestion, structured querying, and often direct integration with metrics and traces from the same vendor, avoiding the operational overhead of self-hosting an ELK stack.

---

### Correlation IDs in Practice

Nearly every serious microservices architecture propagates some form of request ID through every service call specifically to make cross-service debugging possible — this is one of the most universally adopted practices in this entire chapter, precisely because the alternative (no way to correlate logs across services) is close to unworkable at any real scale.

---

# Common Interview Questions

## Structured vs unstructured logging — what's the actual trade-off?

Unstructured, free-text logs are easy to read directly but hard to query precisely at scale — finding a specific pattern means text-searching and hoping the format is consistent. Structured logs (typically JSON) treat every field as a real, queryable attribute, making precise filtering and aggregation possible — essential once log volume is too large to search line by line manually.

---

## Why are correlation IDs essential in a microservices architecture?

Because each service logs independently, with no inherent connection between log lines from different services handling the same originating request. A correlation ID, generated once at the edge and propagated through every subsequent call, lets every related log line across every service be tied back to the same request — without it, reconstructing what happened to one specific request across multiple services is close to impossible.

---

## Why centralize logs instead of just checking individual servers directly?

Because at any real scale — many servers, especially ephemeral containers that get replaced frequently — there's no practical way to know which specific machine holds the relevant log, and a crashed or replaced container can take its local logs with it entirely. Centralizing logs into one durable, searchable store means engineers query one system instead of guessing which of potentially hundreds of machines to check.

---

## When would you use DEBUG vs INFO vs ERROR log levels?

DEBUG for fine-grained detail useful only while actively investigating a specific issue, typically disabled by default in production due to volume and cost. INFO for normal, expected events worth recording. ERROR for failures that likely need attention. Levels let verbosity be controlled per environment and per moment, rather than either drowning in noise constantly or having nothing to look at when something actually breaks.

---

## Why would a production system sample logs instead of logging everything in full detail?

Because logging every field for every single request at high traffic volume becomes genuinely expensive — both in storage and in how slow searching becomes across a mostly-redundant volume of "everything worked fine" entries. Sampling trades some completeness for a manageable, affordable volume, often specifically preserving full detail for slow or failed requests, which matter most for debugging.

---

# Common Mistakes

❌ Logging sensitive data (passwords, full credit card numbers, personal information) in plaintext.

A serious security and compliance risk — logs are often retained for a long time, replicated to multiple systems, and accessible to more people than the original request path ever was.

---

❌ Using unstructured, free-text logs at a scale where precise querying is actually needed.

Makes debugging a specific pattern across millions of log lines dramatically harder than it needs to be — structured logging exists specifically to solve this.

---

❌ Not propagating a correlation ID across service boundaries.

Makes it effectively impossible to reconstruct one request's full journey across multiple services, turning cross-service debugging into manual, time-consuming guesswork.

---

❌ Over-logging every possible detail, or under-logging so little that failures are undebuggable.

Both are real failure modes — too much volume becomes expensive and hard to search; too little leaves no trail to actually diagnose what went wrong when something fails.

---

# Key Takeaways

- Logging exists to leave a durable, after-the-fact record of discrete events, since production systems run unattended most of the time with nobody watching each request live.
- Structured logging (typically JSON) makes logs precisely queryable at scale, unlike unstructured free text, which only supports hopeful text-searching.
- Correlation IDs — propagated through every service a request touches — are the foundational idea that makes cross-service debugging possible at all, and directly set up the richer visualization Distributed Tracing provides.
- Centralized log aggregation is close to mandatory at any real scale, since individual servers' local logs (especially on ephemeral containers) are impractical to check manually one at a time.
- Sampling and level-based filtering are deliberate trade-offs for managing log volume and cost at scale, not compromises to avoid — the goal is enough signal to debug real problems, not logging literally everything.
