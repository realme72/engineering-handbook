# Circuit Breaker

# Why Does the Circuit Breaker Pattern Exist?

Retrying a failed request (covered in the Retry & Backoff chapter) makes sense when a failure is transient — a momentary blip that's likely to succeed on the next attempt. But what happens when a downstream service isn't having a momentary blip — it's genuinely, sustainedly down, for the next ten minutes?

```
Payment Service is completely down

↓

Order Service keeps calling it, on every single incoming request

↓

Each call waits for a full timeout (say, 5 seconds) before failing

↓

Every one of Order Service's own threads/connections is now tied up
waiting on calls that are GUARANTEED to fail

↓

Order Service itself starts timing out and becoming unresponsive
to ITS OWN callers — the failure has now CASCADED upstream
```

This is the exact mechanism behind a **cascading failure** — one struggling service's outage spreading to every service that calls it, purely because those callers keep patiently waiting on calls that have no chance of succeeding. The circuit breaker pattern exists to stop this: once a downstream dependency is confirmed to be failing persistently, **stop calling it entirely** for a while, fail immediately instead, and only cautiously try again later.

---

# The Three States

This is a direct electrical-circuit metaphor, and it's worth holding onto because the state names map cleanly onto the actual behavior.

```
CLOSED  →  normal operation. Requests flow through to the real
           downstream service. Failures are counted.

           ↓ (failure rate crosses a threshold)

OPEN    →  requests FAIL IMMEDIATELY, without even attempting
           the real call, for a cooldown period.

           ↓ (cooldown period elapses)

HALF-OPEN → a LIMITED number of test requests are allowed through.

              ↓ success        ↓ failure
           back to CLOSED    back to OPEN
```

```
CLOSED ──(failure threshold exceeded)──► OPEN
   ▲                                        │
   │                                (cooldown timer elapses)
   │                                        ▼
   └──(test requests succeed)──── HALF-OPEN ──(test requests fail)──► OPEN
```

## Closed — Normal Operation

```python
failure_count = 0
FAILURE_THRESHOLD = 5

def call_payment_service():
    global failure_count
    try:
        result = actual_http_call()
        failure_count = 0  # reset on any success
        return result
    except ServiceError:
        failure_count += 1
        if failure_count >= FAILURE_THRESHOLD:
            open_circuit()
        raise
```

Requests pass through normally, with failures tracked. Crossing the configured threshold is what triggers the transition to Open.

## Open — Fail Fast

```python
def call_payment_service():
    if circuit_state == "OPEN":
        if time.time() < open_until:
            raise CircuitOpenError("Payment service is currently unavailable")  # instant, no real call attempted
        else:
            circuit_state = "HALF_OPEN"
    # ... proceed with the real call in HALF_OPEN or CLOSED state
```

While open, calls fail **instantly**, without ever attempting the real network call — this is the entire point. An instant, cheap failure preserves the caller's own threads, connections, and latency budget, instead of every request patiently waiting out a full timeout on a call that was never going to succeed anyway.

## Half-Open — Cautious Recovery Testing

```python
if circuit_state == "HALF_OPEN":
    try:
        result = actual_http_call()  # ONE test request
        circuit_state = "CLOSED"      # success → fully recovered, resume normal operation
        failure_count = 0
        return result
    except ServiceError:
        circuit_state = "OPEN"        # still failing → reopen, wait another cooldown period
        open_until = time.time() + COOLDOWN_SECONDS
        raise
```

Rather than immediately slamming a possibly-still-recovering service with the full volume of traffic the moment the cooldown timer expires, Half-Open allows only a small number of test requests through. If they succeed, the circuit fully closes and normal traffic resumes; if they fail, it reopens for another cooldown period — protecting a genuinely still-fragile, recovering service from being immediately overwhelmed again the instant it shows the first signs of life.

---

# Why Failing Fast Is the Actual Point

```
Without a circuit breaker:  every request, during an outage, waits
                             out a full timeout before failing —
                             tying up the CALLER's resources
                             (threads, connections) the entire time

With a circuit breaker:      requests fail in microseconds once the
                             circuit is open — the caller's resources
                             are immediately freed for other work
```

The circuit breaker doesn't make the downstream service recover any faster — it protects the **caller** from being dragged down by a dependency that's already failing, which is precisely what prevents one service's outage from cascading into every service that depends on it.

---

# How Circuit Breaker Interacts With Retry

This is a genuinely important, commonly-tested distinction: circuit breaker and retry solve related but different problems, and they need to be layered correctly, not applied independently of each other.

```
WRONG: retry logic runs independently of circuit breaker state

Circuit is OPEN (service is known to be down)

↓

Retry logic STILL attempts 3 retries per request, each one
immediately failing against the open circuit

↓

Wasted effort — the circuit breaker's fail-fast benefit is
partially undone by retrying against a circuit that's already open
```

```
RIGHT: circuit breaker sits ABOVE retry logic

Check circuit state FIRST

↓ OPEN → fail immediately, skip retry logic entirely

↓ CLOSED/HALF-OPEN → proceed, and retry logic (with backoff) only
                      applies to the individual attempt(s) made
                      while the circuit is closed
```

The correct layering: the circuit breaker is checked first, and retries only ever happen against a circuit that's currently closed (or cautiously half-open) — once the circuit is open, there's no reason to retry at all, since the whole point of opening it was recognizing further attempts are pointless for now.

---

# Real-World Examples

### Netflix Hystrix

The library that originated and popularized this pattern in mainstream backend engineering — built specifically because Netflix's own microservices architecture kept experiencing cascading failures from one struggling dependency dragging down callers that kept patiently retrying and waiting on it. Hystrix's design (and Netflix's own public writing about why they built it) is the direct reason "circuit breaker" became a standard term in resilience engineering vocabulary.

---

### Resilience4j

A modern Java library commonly used as Hystrix's successor (Hystrix itself is now in maintenance mode) — implementing the same three-state model, often combined directly with retry and rate-limiting logic in one configurable resilience layer.

---

### Istio / Envoy (Service Mesh Level)

Circuit breaking implemented at the infrastructure layer rather than in application code — a service mesh can apply circuit-breaking policy uniformly across every service-to-service call passing through its proxies, without each individual service needing its own circuit breaker library or implementation.

---

# Common Interview Questions

## Explain the three circuit breaker states and how they transition.

Closed is normal operation — requests flow through, and failures are counted. Once failures cross a configured threshold, the circuit transitions to Open, where requests fail immediately without attempting the real call, for a cooldown period. After the cooldown elapses, the circuit moves to Half-Open, allowing a limited number of test requests through — success transitions back to Closed, failure sends it back to Open for another cooldown.

---

## Why is failing fast better than retrying every request during a real, sustained outage?

Because retrying (or even just attempting) a call against a service that's confirmed to be down ties up the caller's own resources — threads, connections — waiting out timeouts on calls that have no chance of succeeding. Failing instantly, once the circuit is open, frees those resources immediately, which is exactly what prevents the downstream outage from cascading into the caller's own availability.

---

## How should circuit breaker and retry logic interact?

The circuit breaker should sit above retry logic — check circuit state first, and skip retries entirely once the circuit is open, since further attempts are already known to be pointless. Retry logic (with backoff) should only apply to individual attempts made while the circuit is closed or cautiously half-open; retrying against an already-open circuit wastes the fail-fast benefit the circuit breaker exists to provide.

---

## Why does Half-Open only allow a limited number of test requests, instead of immediately resuming full traffic?

Because the downstream service might still be fragile even after the cooldown period — immediately slamming it with full traffic volume the instant the timer expires risks overwhelming a service that's only just starting to recover. A small number of test requests verifies actual recovery before committing to full traffic resumption.

---

## What causes cascading failure, and how does a circuit breaker prevent it?

A struggling downstream service causes every caller waiting on full timeouts to also become slow or resource-exhausted, which in turn makes those callers unreliable to whatever calls *them* — the failure spreads outward through the call graph. A circuit breaker prevents this by failing fast once a dependency is confirmed unhealthy, protecting the caller's own resources instead of letting them be consumed waiting on doomed calls.

---

# Common Mistakes

❌ Setting the failure threshold too sensitive.

Opens the circuit on rare, genuinely transient blips, unnecessarily failing requests that would have succeeded with a normal retry, rather than reserving the circuit breaker for sustained, confirmed outages.

---

❌ Setting the failure threshold too lax, or the cooldown period too short.

Takes too long to actually open the circuit during a real outage (continuing to tie up caller resources on doomed calls far longer than necessary), or reopens and closes too rapidly, thrashing between states.

---

❌ Retrying every request even while the circuit is open.

Wastes the fail-fast benefit the circuit breaker exists to provide — retries should be skipped entirely once the circuit is confirmed open, not applied independently of circuit state.

---

❌ Resuming full traffic immediately once the cooldown period expires, with no half-open testing phase.

Risks overwhelming a service that's only just starting to recover, potentially reopening the circuit immediately and repeating the cycle rather than allowing a cautious, gradual verification of actual recovery.

---

# Key Takeaways

- The circuit breaker pattern exists to stop cascading failure — a downstream service's sustained outage spreading upstream because callers keep waiting out full timeouts on calls that have no chance of succeeding.
- The three states — Closed (normal operation, failures counted), Open (fail fast, no real call attempted), Half-Open (limited test requests to verify recovery) — model a deliberate, cautious response to sustained failure rather than either naive optimism or permanent avoidance.
- Failing fast protects the *caller's* own resources (threads, connections, latency budget), which is what actually prevents a struggling dependency's failure from cascading to everything that depends on it.
- Circuit breaker logic should sit above retry logic — retries only make sense against a closed or half-open circuit; retrying against an open circuit wastes the entire benefit the pattern provides.
- Half-Open's limited test-request approach protects a still-fragile, recovering service from being immediately overwhelmed the instant its cooldown period expires.
