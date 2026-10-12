# Domain-Driven Design (Bounded Contexts)

# Why Does Domain-Driven Design Exist?

The Microservices chapter closed with a question it deliberately left open: how do you actually decide where one service ends and another begins? Draw the boundaries badly — too fine-grained and entangled — and you get a distributed monolith. Draw them too coarse, and you get a handful of giant, unwieldy services that don't solve the original problem at all. Domain-Driven Design (DDD) exists to answer this precisely, by grounding service and module boundaries in the actual **business domain**, rather than arbitrary technical layers or guesswork.

```
Bad boundary-drawing:  split around technical layers
                        ("database service," "API service")
                        → everything still tightly coupled to
                          everything else

DDD's answer:           split around genuine BUSINESS CAPABILITIES
                         and the natural boundaries within the
                         actual domain the software serves
```

---

# Ubiquitous Language

The foundational DDD idea, and deceptively simple to state: use one shared, precise vocabulary — consistently, in code **and** in conversation — between engineers and business/domain experts.

```
Without ubiquitous language:

Engineers say:  "the user"
Business says:   "the customer" (in a sales context) or
                  "the member" (in a subscription context)

↓

Constant translation friction — every conversation between
engineering and the business risks subtle misunderstanding,
and the CODE ends up naming things differently than the
business actually talks about them
```

```
With ubiquitous language:

The exact term the business uses for a concept is the EXACT SAME
term used in code — variable names, class names, API endpoint
names all match how domain experts actually talk about the thing
```

This sounds like a minor naming convention, but it has real teeth — when code and business conversation share one precise vocabulary, misunderstandings between "what the business asked for" and "what got built" become far less likely, and the code itself becomes more directly readable as a reflection of the actual business domain, not a technical abstraction layered arbitrarily over it.

---

# Bounded Context — The Central Concept

This is the concept that directly answers the Microservices chapter's open question: a **bounded context** is a boundary within which a specific model, and its ubiquitous language, apply consistently — and outside of which, the same term might legitimately mean something entirely different.

```
"Product" in the CATALOG bounded context:

  { name, description, images, category, price }

"Product" in the SHIPPING bounded context:

  { weight, dimensions, fragile, warehouse_location }

"Product" in the SUPPORT bounded context:

  { warranty_info, known_issues, return_policy }
```

These are all legitimately "Product" — the same real-world business concept — but each bounded context needs a genuinely different model of it, because each context cares about entirely different attributes and business rules for that same concept. Trying to force **one single, unified "Product" model** across the entire system is often the actual root cause of an overly-tangled, painfully-coupled data model — a model trying to serve every context's needs at once ends up serving none of them well, and every unrelated change anywhere in the system risks breaking something in a completely different part of the business.

```
The key insight:  a bounded context is a strong CANDIDATE for a
                   microservice or module boundary — not a technical
                   layer, not an arbitrary split, but a genuine
                   seam that already exists in how the business
                   itself is organized
```

---

# Aggregates

Within a bounded context, an **aggregate** is a cluster of related objects treated as one consistency boundary — a group of things that must always change together, consistently, as a single unit.

```
Order Aggregate:

Order (the aggregate ROOT)
  ├── OrderLineItem
  ├── OrderLineItem
  └── ShippingAddress

↓

ALL changes to anything inside this aggregate go THROUGH the
Order root — you never modify an OrderLineItem directly,
independent of its parent Order
```

The root enforces the aggregate's **invariants** (business rules that must always hold) — for instance, "an order's total must always equal the sum of its line items" is a rule the Order root can enforce on every change, precisely because every change is forced to go through it. This makes an aggregate a natural, direct mapping onto both a transaction boundary (from the Transactions chapter — a single aggregate's changes typically commit together, in one transaction) and, very often, a natural service or module boundary too.

---

# How This Directly Informs Service Boundaries

```
Bounded Context  →  strong candidate for a MICROSERVICE or module boundary

Services communicating ACROSS bounded contexts do so via well-defined
APIs or events — NOT by sharing an internal model or a database table
directly
```

This is precisely the same principle the Microservices chapter's own guidance ("draw boundaries around business capabilities, not technical layers") was gesturing toward, now given a concrete, principled mechanism: identify the bounded contexts that already exist in the business domain, and let those become your service boundaries, rather than guessing at a split based on technical convenience.

---

# Context Mapping — Briefly

Real systems rarely have perfectly clean, isolated bounded contexts — they need to interact, and DDD includes explicit vocabulary for documenting *how* different contexts relate to and translate between each other.

```
Anti-Corruption Layer:  a translation layer specifically isolating
                        your bounded context from a LEGACY system's
                        (or an external third-party's) different,
                        possibly messy model — so your own clean
                        domain model isn't contaminated by
                        another system's incompatible concepts
```

This is worth knowing exists — a genuinely practical pattern for the extremely common real-world case of integrating with a legacy system or an external API whose own model doesn't cleanly match your bounded context's model at all.

---

# Real-World Examples

### Eric Evans' Original "Domain-Driven Design" (2003)

The foundational source of this entire vocabulary — bounded contexts, aggregates, ubiquitous language all originate from this single, still-widely-referenced book, and it remains the standard reference point whenever these terms come up in a real architecture discussion.

---

### Netflix/Amazon-Style Microservice Boundaries

In practice, very often bounded-context-shaped, even at organizations that don't explicitly invoke DDD terminology — a "Payments" service, an "Inventory" service, a "Recommendations" service each typically represent a genuine bounded context with its own model and rules, arrived at independently by teams solving the same underlying boundary problem DDD names explicitly.

---

### An Anti-Corruption Layer Around a Legacy Billing System

A common, concrete real-world case — a modern service needing to integrate with an old, awkwardly-modeled legacy billing system builds a translation layer specifically so its own clean domain model never has to directly represent the legacy system's incompatible concepts.

---

# Common Interview Questions

## What is a bounded context, and why does it matter for service boundaries?

A boundary within which a specific model and its associated vocabulary apply consistently — outside of it, the same term can legitimately mean something different. It matters because it's a principled, business-grounded candidate for a microservice or module boundary, directly answering "where should this service end and another begin" based on genuine seams in the business domain, rather than arbitrary technical splits.

---

## Why might the "same" business entity, like Product, legitimately have different models in different parts of a system?

Because different parts of the business genuinely care about different attributes and rules for that same real-world concept — a catalog context cares about description and images, a shipping context cares about weight and warehouse location. Forcing one single, unified model to serve every context at once tends to produce an overly-coupled, painfully-compromised data model that serves no single context well.

---

## What is ubiquitous language, and what problem does it solve?

A shared, precise vocabulary used consistently by both engineers and business/domain experts, in code and in conversation. It solves the constant translation friction and misunderstanding that arises when engineers and the business use different terms for the same concept — aligning code's naming directly with how the business actually talks about its own domain.

---

## What is an aggregate, and how does it relate to a transaction boundary?

A cluster of related objects treated as one consistency boundary, with a root entity through which all changes must go, enforcing the aggregate's business invariants consistently. An aggregate typically maps directly onto a transaction boundary — its internal changes are committed together, as one unit, in a single database transaction, and very often maps onto a natural service or module boundary as well.

---

## How would you use DDD to decide where to split a monolith into microservices?

Identify the bounded contexts that already exist within the business domain — the natural seams where a distinct model, vocabulary, and set of business rules already apply — and let those become the service boundaries, rather than splitting along technical layers or guessing. Services that need to interact across bounded contexts should communicate via well-defined APIs or events, never by directly sharing an internal model or database.

---

# Common Mistakes

❌ Trying to build one single, unified data model for a concept that actually means different things in different parts of the business.

The frequent root cause of a painfully over-coupled "master" data model that serves no single part of the business well and makes unrelated changes risky everywhere.

---

❌ Drawing microservice boundaries around technical layers instead of bounded contexts.

A "database service" or "API service" split along purely technical lines tends to produce services that remain tightly, constantly coupled to each other — exactly the boundary-drawing mistake DDD exists to prevent.

---

❌ Not maintaining a consistent ubiquitous language between engineering and the business.

Causes ongoing, low-grade translation friction and misunderstanding between what the business actually means and what gets built, compounding over time as the vocabulary drifts further apart.

---

# Key Takeaways

- Domain-Driven Design exists to give a principled, business-grounded answer to where microservice or module boundaries should actually go — a question the Microservices chapter deliberately left open.
- Ubiquitous language — one shared, precise vocabulary used consistently by engineers and business experts alike, in code and conversation — reduces translation friction and keeps code aligned with how the business actually thinks about its own domain.
- A bounded context is a boundary within which a specific model and vocabulary apply consistently — the same real-world concept can and often should have different models in different bounded contexts, rather than being forced into one unified model everywhere.
- Aggregates are a cluster of related objects treated as one consistency boundary, enforced through a root entity — naturally mapping onto both a transaction boundary and often a service/module boundary too.
- Bounded contexts are strong, principled candidates for microservice or module boundaries — services communicate across contexts via well-defined APIs or events, never by sharing an internal model or database directly.
