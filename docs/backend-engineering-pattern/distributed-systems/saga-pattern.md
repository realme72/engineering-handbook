# Saga Pattern

# Why Does the Saga Pattern Exist?

The Transactions chapter established the gap this pattern fills: a `BEGIN`/`COMMIT` only covers one database connection's scope. The moment an operation spans multiple services — each with their own separate database — there's no native, atomic way to say "all of these steps succeed together, or none do." The Sharding chapter hit the identical problem across shards, and Event-Driven Architecture hit it again across a choreographed flow of services reacting to events.

```
Order Saga:

1. Order Service    creates the order
2. Payment Service  charges the customer's card
3. Inventory Service reserves stock
4. Shipping Service schedules the shipment

↓

Step 3 fails — the item is actually out of stock

↓

Step 2 already succeeded. The customer's card was ALREADY charged.

What happens now?
```

There's no single transaction to roll back — the charge happened in a completely separate service, with its own separate database, and it already committed. The Saga pattern is the answer: instead of one atomic transaction, structure the whole operation as a sequence of independent local transactions, each paired with an explicit **compensating transaction** that can semantically undo its effect if a later step in the sequence fails.

```
Step 1: create order          ↔  compensate: cancel order
Step 2: charge card            ↔  compensate: refund
Step 3: reserve stock          ↔  compensate: release stock
Step 4: schedule shipment      ↔  compensate: cancel shipment

↓

If step 3 fails:

↓

Run compensations for steps 2 and 1, IN REVERSE ORDER:

compensate step 2 (refund the customer)
compensate step 1 (cancel the order)
```

---

# Compensating Transactions Are Not a Rollback

This distinction matters, and it's a common point of confusion worth being precise about: a compensating transaction doesn't erase history the way a database `ROLLBACK` does. It's a **new**, forward-moving action that semantically counteracts a prior one.

```
A database ROLLBACK:  as if the original transaction never happened
                       at all — no trace remains

A compensating transaction ("refund"):  the charge DID happen, and
                                          still shows up in the
                                          customer's transaction
                                          history — the refund is a
                                          SEPARATE, subsequent
                                          transaction that reverses
                                          its financial effect
```

This is an important, practical nuance: a saga's compensations are themselves real, auditable operations, not an undo button — which means they need to be designed with the same care as any other transaction, including being idempotent in their own right (a compensation that's retried, itself, needs to be safe to run more than once — the exact same idempotency requirement covered throughout the Message Queues section, applying recursively to the failure-handling logic itself).

---

# Two Implementation Styles

## Choreography-Based Saga

Each service, upon completing its own local step, publishes an event; the next service in the sequence reacts to that event independently — the exact choreography model from the Event-Driven Architecture chapter, applied specifically to a saga's sequence of steps.

```
Order Service:    creates order → publishes OrderCreated

↓

Payment Service:  reacts to OrderCreated → charges card →
                   publishes PaymentCompleted (or PaymentFailed)

↓

Inventory Service: reacts to PaymentCompleted → reserves stock →
                    publishes StockReserved (or StockReservationFailed)

↓

If StockReservationFailed is published:

Payment Service: reacts to StockReservationFailed →
                  runs its OWN compensation (refund) →
                  publishes PaymentRefunded

Order Service:    reacts to PaymentRefunded →
                  runs its OWN compensation (cancel order)
```

No central coordinator — every service independently knows how to react both to the "happy path" event from the step before it, and to a "compensate" event indicating something downstream failed. This is maximally decoupled, exactly like choreography in general, at the same cost: understanding and debugging the full saga's behavior requires piecing it together across every service's independent event handlers, since there's no single place the entire sequence (or its failure/compensation logic) is defined.

## Orchestration-Based Saga

A central saga orchestrator explicitly calls each step in sequence and explicitly triggers compensations if a later step fails — the orchestration model from Event-Driven Architecture, applied here.

```
Saga Orchestrator:

1. call Order Service: create order          → success
2. call Payment Service: charge card          → success
3. call Inventory Service: reserve stock      → FAILS

↓

Orchestrator explicitly triggers, in reverse order:

4. call Payment Service: refund
5. call Order Service: cancel order
```

The entire saga's logic — the sequence, and exactly what compensates what — lives in one identifiable place, which makes it dramatically easier to understand, test, and modify as a whole. The trade-off is the same one orchestration always carries: every participating service now has a dependency on the orchestrator, and the orchestrator itself needs to know about every step, somewhat reintroducing the coupling a purely choreographed approach avoids.

```
Choreography:   maximally decoupled, harder to trace the full saga
Orchestration:  the full saga logic lives in one place, more centralized coupling
```

Real production systems commonly use orchestration engines (Temporal, Camunda, AWS Step Functions) specifically because they provide built-in visibility into exactly where a given saga instance is in its sequence and what's already been compensated — a genuine, practical answer to choreography's biggest weakness.

---

# Sagas Provide Eventual Consistency, Not Isolation

This is worth stating explicitly, because it's a real, meaningful trade-off compared to a genuine ACID transaction, not a minor footnote.

```
A real ACID transaction:  isolated — no other observer can see
                           partial, intermediate state while the
                           transaction is in progress

A saga:                    NOT isolated — intermediate states ARE
                            visible to other parts of the system
                            while the saga is still in progress
```

```
Saga in progress:

Order created (status: "pending")
Payment charged
Inventory NOT yet reserved

↓

A completely separate part of the system queries the order right
now → sees "pending", with the card ALREADY charged but stock NOT
YET reserved — a state that will either resolve forward (stock
reserved successfully) or backward (compensations run) a moment
later, but is genuinely, visibly inconsistent RIGHT NOW
```

Applications built around sagas need to explicitly tolerate this — either by designing the visible state machine so intermediate states make reasonable sense to observers (an order showing "processing" rather than something misleadingly definitive), or by accepting that some queries run during an in-progress saga will see a transient, resolving-itself state. This is the direct, concrete cost of trading a single ACID transaction's strong isolation guarantee for the ability to coordinate an operation across independent services at all.

---

# Handling a Compensation That Itself Fails

A genuinely important edge case: what happens if the *compensation* fails?

```
Step 3 fails → trigger compensation for step 2 (refund)

↓

The refund call ALSO fails (payment gateway is temporarily down)

↓

Now what?
```

Compensations are generally designed to be retried aggressively (with the retry and backoff strategies from earlier chapters) since they're the last line of defense against a genuinely inconsistent end state — and, precisely because retries are involved, compensations need to be idempotent themselves, or a retried compensation could double-refund a customer, trading one inconsistency for another. If a compensation exhausts its retries and still fails, the standard escalation is the same one covered in Dead Letter Queues — surface it for manual/alerted intervention rather than silently giving up, since an un-compensated step left in a bad state is a real, uncorrected business problem that needs a human, not just a background process quietly failing forever.

---

# Real-World Examples

### E-Commerce Order Fulfillment

The textbook example used throughout this chapter, and genuinely how most real order-processing systems handle the fact that "charge the card," "reserve inventory," and "schedule shipping" are usually three (or more) entirely separate services with separate databases, needing coordinated all-or-nothing behavior they can't get from a single transaction.

---

### Uber's Trip Booking Flow

Revisited once more from the Event-Driven Architecture chapter — if a driver assignment step fails after a rider's payment method has already been pre-authorized, the pre-authorization needs an explicit compensating action (releasing the hold) rather than leaving a customer with a mysterious pending charge and no assigned driver.

---

### Temporal / Camunda / AWS Step Functions (Orchestration Engines)

Purpose-built for implementing orchestration-based sagas in production — providing durable execution (the orchestrator's own state survives a crash and resumes exactly where it left off), built-in visibility into a given saga instance's current step, and structured support for defining compensating actions alongside the forward steps they correspond to.

---

# Common Interview Questions

## What problem does the Saga pattern solve?

Coordinating an operation that spans multiple services, each with its own separate database, where no single native transaction can span all of them — a saga breaks the operation into a sequence of local transactions, each paired with an explicit compensating action that can semantically undo its effect if a later step in the sequence fails.

---

## What's the difference between a compensating transaction and a rollback?

A rollback erases a transaction as if it never happened, with no trace remaining. A compensating transaction is a new, forward-moving action that semantically reverses a prior step's effect — the original action (a charge) still happened and is still visible in history; the compensation (a refund) is a separate, subsequent transaction that counteracts it.

---

## Choreography-based vs orchestration-based sagas — what's the trade-off?

Choreography has each service react independently to events, maximizing decoupling at the cost of the overall saga's logic being implicit and hard to trace across many services' independent handlers. Orchestration centralizes the entire sequence — including compensation logic — in one identifiable coordinator, making it easier to understand and debug, at the cost of every participating service depending on that orchestrator.

---

## Does a saga provide the same isolation guarantee as a real ACID transaction?

No — a saga's intermediate states are genuinely visible to other observers while it's still in progress, unlike an ACID transaction's isolation guarantee that hides partial work until commit. Applications built around sagas need to explicitly tolerate this, either by designing visible intermediate states to make sense on their own, or accepting that some queries will observe a transient, still-resolving state.

---

## What happens if a compensating transaction itself fails?

It's generally retried aggressively, since compensations are the last line of defense against a genuinely inconsistent end state — and because retries are involved, compensations need to be idempotent themselves, or a retried compensation risks a new inconsistency (like double-refunding). If retries are exhausted, the standard escalation is surfacing it for manual/alerted intervention, the same escalation pattern as a message that's exhausted its retries in the Dead Letter Queues chapter.

---

# Common Mistakes

❌ Assuming a saga provides the same isolation as an ACID transaction.

Intermediate, partially-completed states are genuinely visible to other observers while a saga is in progress — applications need to be explicitly designed to tolerate this, not assume it away.

---

❌ Designing compensations that aren't idempotent.

A compensation can itself need to be retried after a failure — if it isn't idempotent, a retried compensation can cause a new inconsistency (a double refund) instead of correctly resolving the original one.

---

❌ Running compensations in the wrong order.

Compensations need to run in reverse order relative to the original steps — undoing the most recent step first, working backward, to correctly unwind a partially-completed sequence.

---

❌ Treating a failed compensation as something to silently give up on.

An un-compensated step left in a bad state is a real, uncorrected business problem — a failed compensation, after exhausting reasonable retries, needs to escalate to a human, not fail silently.

---

# Key Takeaways

- The Saga pattern coordinates an operation across multiple services' separate databases by breaking it into a sequence of local transactions, each paired with an explicit compensating action to undo its effect if a later step fails — since no native transaction can span multiple independent services.
- Compensating transactions are new, forward-moving actions that semantically reverse an effect, not a rollback that erases history — a refund is a separate transaction, not an undo of the original charge.
- Choreography-based sagas maximize decoupling but make the overall sequence and its failure handling implicit and hard to trace; orchestration-based sagas centralize the sequence and compensation logic in one place, easier to reason about at the cost of centralized coupling.
- Sagas provide eventual consistency, not the isolation guarantee of a real ACID transaction — intermediate, partially-completed states are genuinely visible to other observers while a saga is still resolving.
- Compensations need to be idempotent and aggressively retried, since they're the last line of defense against an inconsistent end state — a compensation that exhausts its retries should escalate for manual intervention, not fail silently.
