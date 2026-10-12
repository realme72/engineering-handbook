# Event-Driven Architecture

# Why Does Event-Driven Architecture Exist?

Every other chapter in this section has covered a single queue or topic in isolation — how a message flows from one producer to one or more consumers. This chapter is about a broader architectural decision: what happens when you build an entire system's service-to-service communication around publishing and reacting to events, instead of services calling each other directly.

```
Direct (synchronous) service-to-service calls:

Order Service → calls → Payment Service → calls → Inventory Service → calls → Shipping Service

↓

Order Service now needs to KNOW about, and be available to call,
every single downstream service directly. If Shipping Service is
slow or down, does the whole chain fail?
```

```
Event-driven:

Order Service → publishes "OrderPlaced" event

↓                    ↓                    ↓

Payment Service    Inventory Service    Shipping Service
(reacts on its      (reacts on its       (reacts on its
 own schedule)       own schedule)        own schedule)
```

The Order Service doesn't call any of these services, doesn't know how many of them exist, and isn't blocked waiting on any of them. It states a fact — "an order was placed" — and every interested service reacts independently. This is the direct architectural generalization of the checkout example from Messaging Fundamentals, applied as a system-wide design philosophy rather than a single use case.

---

# What Problem It Actually Solves

- **Loose coupling between services** — a producer doesn't need to know which consumers exist, or how many, or whether they're currently healthy.
- **Independent scaling and failure isolation** — a struggling or down consumer doesn't block the producer or any other consumer; each reacts (or fails to react, temporarily) on its own.
- **Natural extensibility** — adding a new service that reacts to an existing event (a fraud-detection service that now also wants to see `OrderPlaced` events) requires zero changes to the producer or any existing consumer.
- **A built-in historical record** — a stream of events is, almost incidentally, an audit trail of everything that happened in the system over time.

---

# Choreography vs Orchestration

This is the central architectural choice within event-driven systems, and a very common interview topic in its own right.

## Choreography

```
No central coordinator. Each service independently reacts to events
and publishes new events as a result — the overall business process
EMERGES from the sum of these independent reactions.

OrderService: publishes OrderPlaced
    ↓
PaymentService: reacts, charges card, publishes PaymentCompleted
    ↓
InventoryService: reacts, decrements stock, publishes StockReserved
    ↓
ShippingService: reacts, schedules shipment, publishes ShipmentScheduled
```

Nobody explicitly wrote "step 1, then step 2, then step 3" anywhere — the sequence exists only implicitly, as a consequence of which service happens to listen for which event. This is maximally decoupled: no single service (or team) owns the whole flow, and any service can be added, removed, or changed without touching the others.

The real cost: **understanding the end-to-end business process requires piecing it together across every service's independent event handlers** — there's no single place to look and see "here's what happens when an order is placed." This is a genuine, common operational pain point, and it's exactly why distributed tracing (covered in the Observability section) becomes close to mandatory once a system leans heavily on choreography — without it, debugging a broken flow means manually tracing events across many independent services' logs.

## Orchestration

```
A central Orchestrator service explicitly calls/coordinates each step:

Orchestrator:
    1. call Payment Service → wait for result
    2. call Inventory Service → wait for result
    3. call Shipping Service → wait for result

    (or, in an event-driven variant: publish a command, wait for the
    corresponding response event, then explicitly trigger the next step)
```

The entire business process lives in one identifiable place — much easier to understand, trace, and modify the overall flow as a single unit. The cost is exactly the coupling choreography avoids: every service in the flow now has a dependency on the orchestrator, and the orchestrator itself becomes a central point that needs to know about every step, which can reintroduce some of the tight coupling event-driven architecture was meant to eliminate in the first place.

```
Choreography:   maximum decoupling, harder to trace the overall process
Orchestration:  easier to trace and reason about, more centralized coupling
```

Neither is universally "correct" — many real systems use choreography for straightforward, independent reactions (send a notification, update a cache) and orchestration for genuinely complex, multi-step business processes where the sequence and failure handling need to be explicit and centrally understood (a multi-step onboarding flow, a complex order fulfillment process with many possible failure branches).

---

# Event Notification vs Event-Carried State Transfer

The same "thin vs full payload" trade-off from the Webhooks chapter, generalized here as a deliberate architectural choice.

```
Event Notification (thin):

{ "event": "OrderPlaced", "order_id": 42 }

↓ consumer needing details must call BACK to the Order Service
```

```
Event-Carried State Transfer (fat):

{
    "event": "OrderPlaced",
    "order_id": 42,
    "customer_id": 7,
    "items": [ ... ],
    "total": 500
}

↓ consumer has everything it needs, no additional call required
```

Thin events keep the producer's internal data model private and avoid staleness (a consumer always fetches current data when it actually needs it), at the cost of an extra network round trip and a new runtime dependency — the consumer now needs the Order Service to be reachable and healthy at the moment it processes the event, which partially reintroduces the coupling event-driven architecture was meant to remove. Fat events avoid that extra dependency entirely, at the cost of larger payloads, and a real risk: the embedded data is a snapshot from the moment the event was published, and can drift out of sync with the producer's current state if the consumer processes it much later.

---

# Handling Transactions Across Multiple Services

An event-driven flow spanning several services runs into the exact same problem covered in the Transactions and Sharding chapters — there's no single database transaction spanning multiple independent services, so "all of these steps succeed together, or none do" can't be achieved with a native `BEGIN`/`COMMIT` the way it could within one service's own database.

```
OrderPlaced → PaymentService charges card successfully
            → InventoryService fails to reserve stock (out of stock)

↓

The charge already happened. Does it get refunded? Who's responsible
for noticing and fixing this?
```

This is precisely the problem the **Saga Pattern** exists to solve — a sequence of local transactions across services, with explicit compensating actions (like a refund) to undo prior steps if a later one fails, instead of relying on a single cross-service atomic transaction that doesn't exist. It's covered in full depth in the Distributed Systems section; the important thing to internalize here is that event-driven architectures don't get atomicity across services for free just because messaging is involved — a multi-step, cross-service event flow needs an explicit failure-handling strategy just as much as any other distributed transaction does.

---

# Related, But Distinct: Event Sourcing and CQRS

Two concepts commonly confused with event-driven architecture, worth distinguishing clearly rather than conflating.

```
Event-Driven Architecture:  services COMMUNICATE via events
                             (the focus of this chapter)

Event Sourcing:              a service's own internal STATE is stored
                              as a sequence of events, with current
                              state derived by replaying them, rather
                              than storing just the current state directly

CQRS:                        separating the model used for WRITES from
                              the model used for READS entirely
```

A system can be event-driven (services communicate via events) without using event sourcing internally (each service might still just store its current state directly in a normal table) — and vice versa. They frequently show up together in practice because they share a natural affinity (an event-sourced service's internal event log is a very natural thing to also publish externally), but they solve different problems. Both are covered in full depth in the Architecture section — the distinction worth remembering here is simply that "our services talk to each other via events" and "our services store their own state as a sequence of events" are two separate architectural decisions, not the same one.

---

# Real-World Examples

### Amazon's Service-Oriented Shift

Amazon's well-documented internal move toward independently-deployable services communicating asynchronously (rather than one monolith with direct internal calls) is one of the most cited real-world case studies for why loose coupling between services — enabled heavily by event-driven communication — became foundational to scaling both the system and the organization building it.

---

### Uber's Trip Event Pipeline

Revisited once more, now at the architecture level — the same `requested` → `driver_assigned` → `trip_started` → `trip_completed` event sequence isn't just "a Kafka topic," it's choreography: pricing, the rider app, the driver app, and analytics all independently react to the same events with no central orchestrator dictating what each of them should do in response.

---

### Netflix

Uses event-driven patterns extensively for cross-service communication precisely because of the failure-isolation benefit — an event that a struggling or temporarily-down downstream service hasn't processed yet doesn't block the producer or any other, unrelated consumer of the same event.

---

# Common Interview Questions

## Choreography vs orchestration — how do you decide which to use for a given workflow?

Choreography for straightforward, independent reactions where no single service needs to own or understand the whole process — maximizes decoupling, at the cost of the overall flow being harder to trace end-to-end. Orchestration for complex, multi-step business processes where the sequence and failure handling genuinely need a centralized, explicit definition — easier to reason about and debug, at the cost of every step now depending on the orchestrator.

---

## Event notification vs event-carried state transfer — what's the trade-off?

Thin "notification" events keep the producer's data model private and avoid staleness, but require the consumer to call back to the producer for details, reintroducing a runtime dependency. Fat "state transfer" events avoid that extra call and dependency, but risk the embedded data becoming stale relative to the producer's current state, and couple consumers more tightly to the producer's event schema.

---

## How do you handle a business transaction spanning multiple services in an event-driven architecture?

There's no native cross-service atomic transaction, the same underlying gap covered in the Transactions and Sharding chapters — this is exactly what the Saga Pattern (covered in depth in the Distributed Systems section) solves: a sequence of local transactions with explicit compensating actions to undo prior steps if a later one fails, rather than assuming messaging alone provides atomicity across services.

---

## What's the difference between event-driven architecture and event sourcing?

Event-driven architecture is about how services *communicate* — via published events instead of direct calls. Event sourcing is about how a single service stores its *own internal state* — as a sequence of events replayed to derive current state, rather than storing current state directly. A system can adopt either without the other, though they're often used together in practice.

---

## What's the biggest practical downside of a heavily choreographed, event-driven system?

Tracing and understanding an end-to-end business process becomes genuinely difficult, since the overall flow is implicit — spread across many independent services' event handlers rather than defined in one place. This is exactly why distributed tracing becomes close to essential infrastructure once a system leans heavily on choreography, not an optional nice-to-have.

---

# Common Mistakes

❌ Adopting heavy choreography with no distributed tracing in place.

Makes debugging a broken end-to-end business process extremely difficult, since there's no single place the overall flow is defined — tracing has to be reconstructed manually across many independent services' logs.

---

❌ Changing an event's schema without any versioning discipline.

Silently breaks every downstream consumer relying on the old shape — event schemas need the same evolution discipline as the API Versioning chapter covers for REST/GraphQL contracts, not an assumption that "it's just an internal event, it doesn't matter."

---

❌ Assuming messaging alone provides atomicity across a multi-step, cross-service flow.

There's no native cross-service transaction just because the steps are connected by events — a failure partway through (a charge succeeding but a later step failing) needs an explicit compensating strategy like the Saga Pattern, not an assumption that it "probably works out."

---

❌ Applying event-driven architecture to every interaction, including ones that genuinely need a synchronous answer.

Some operations (validating a payment method before letting a user submit a form) need an immediate, synchronous response — forcing everything through asynchronous events even where a direct answer is required just adds unnecessary complexity and latency.

---

# Key Takeaways

- Event-driven architecture generalizes the producer/consumer relationship from a single queue into a system-wide design philosophy — services publish facts about what happened instead of calling each other directly, gaining loose coupling and independent scaling at the cost of a more implicit overall process.
- Choreography maximizes decoupling but makes the end-to-end business process harder to trace; orchestration centralizes and clarifies the flow at the cost of reintroducing coupling to the orchestrator.
- Event notification (thin) avoids staleness and keeps a producer's data model private but adds a callback dependency; event-carried state transfer (fat) avoids that dependency but risks staleness and tighter schema coupling.
- Event-driven communication does not provide cross-service transactional atomicity for free — a multi-step flow spanning services still needs an explicit strategy like the Saga Pattern for handling partial failure.
- Event-driven architecture, event sourcing, and CQRS are related but distinct decisions — a system can adopt any of them independently of the others, even though they're often paired together in practice.
