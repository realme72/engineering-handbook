# Hexagonal Architecture (Ports and Adapters)

# Why Does Hexagonal Architecture Exist?

Hexagonal Architecture (Alistair Cockburn) pursues essentially the same goal as Clean Architecture, covered in the previous chapter: isolate the application's core logic from external, volatile details — databases, UI, frameworks, third-party integrations. It's worth understanding as a genuinely earlier, independently-developed articulation of very similar ideas, using its own distinct vocabulary — and it's genuinely useful to be able to compare the two precisely, rather than treating them (as they're often mistakenly treated) as competing, incompatible approaches.

```
Same underlying goal as Clean Architecture:

Core application logic  →  isolated from  →  external, volatile details

↓ but described with DIFFERENT vocabulary:

"Ports and Adapters" instead of "layers and the Dependency Rule"
```

---

# The Core Metaphor

The application's core sits in the center — visualized as a **hexagon**, a shape chosen deliberately just to have multiple, visually equal-looking sides, specifically to avoid the "top vs bottom" hierarchy a traditional layered diagram's top-to-bottom arrangement implicitly suggests.

```
                    ┌─────────────┐
                    │   Adapter    │
                    └──────┬──────┘
                           │ Port
              ┌────────────┴────────────┐
              │                          │
    Adapter ──┤       APPLICATION        ├── Port ── Adapter
      │        │           CORE           │
      Port      │                          │
              └────────────┬────────────┘
                           │ Port
                    ┌──────┴──────┐
                    │   Adapter    │
                    └─────────────┘
```

The hexagon shape itself carries no special technical meaning beyond this — it's purely a deliberate visual choice to avoid implying that any one side is somehow more "top-level" than another, unlike a traditional layered stack diagram's built-in vertical hierarchy.

---

# Ports and Adapters

```
PORT:    an INTERFACE the application core defines — describing
         what it needs from, or offers to, the outside world,
         without knowing or caring how that's actually implemented

ADAPTER: a CONCRETE implementation that plugs into a port, translating
         between the outside world's specific technology and the
         core's own interface
```

```python
# A PORT — defined by the core, describing what it needs:
class PaymentGateway(Protocol):
    def charge(self, amount: float, card_token: str) -> bool: ...

# ADAPTERS — concrete implementations plugged in from outside:
class StripeAdapter:
    def charge(self, amount, card_token):
        # actual Stripe API calls here
        ...

class FakePaymentAdapter:  # for tests
    def charge(self, amount, card_token):
        return True  # always succeeds, no real API call at all
```

This is, mechanically, exactly the same pattern as Clean Architecture's interfaces defined by the core and implemented by outer layers — "port" and "adapter" are simply Hexagonal Architecture's own names for the same idea.

---

# Primary (Driving) Ports vs Secondary (Driven) Ports

A genuinely useful, precise distinction worth knowing by name, since it clarifies *direction* in a way that's easy to gloss over otherwise.

```
PRIMARY (Driving) Port:   how the OUTSIDE WORLD calls INTO the
                          application — a REST controller adapter
                          calling into a use case through this
                          kind of port

SECONDARY (Driven) Port:  how the APPLICATION calls OUT to the
                          outside world — a database adapter, an
                          email-sending adapter, a payment gateway
                          adapter, all reached through this kind
                          of port
```

```
User's HTTP request → REST Adapter → PRIMARY PORT → Application Core

Application Core → SECONDARY PORT → Database Adapter → actual database
```

Both are simply "ports" in the general vocabulary, but the *direction* of the call differs — being precise about which kind you're referring to (something calling *into* the core, versus the core calling *out* to something) avoids a common, subtle confusion when discussing this pattern.

---

# The Genuinely Practical Payoff — Same as Clean Architecture

```
Swap a REST adapter for a CLI adapter (a different way for the
outside world to drive the same application core)

↓

Swap a Postgres adapter for an in-memory test adapter (a different
way the core reaches a database)

↓

NEITHER swap requires touching the application core's own logic
at all — the core only ever depends on its OWN port interfaces,
never on any specific adapter's concrete implementation
```

This is exactly the same reward Clean Architecture provides — fast, isolated testing of the core logic (swap in fake adapters), and genuine flexibility to change infrastructure or entry points later without rewriting business logic.

---

# Comparing Hexagonal Architecture and Clean Architecture Directly

```
Hexagonal:  "ports and adapters," a hexagon diagram with the core
            at the center

Clean:       concentric layers (Entities → Use Cases → Interface
             Adapters → Frameworks/Drivers), the Dependency Rule
             stated explicitly as "dependencies point inward"
```

For most practical purposes, these are **the same underlying idea**, expressed with different vocabulary and a different diagram shape — not two fundamentally different architectural approaches to be debated as rivals. A "port" is functionally the same thing as one of Clean Architecture's interfaces at a layer boundary; an "adapter" is functionally the same thing as a concrete implementation living in an outer layer. Real production systems described as either "hexagonal" or "clean architecture" are, on close inspection, very often doing essentially the same structural thing — the specific terminology a team uses often just reflects which book or blog post they happened to read first, not a genuinely different underlying decision.

---

# Real-World Examples

### Many Production Systems Labeled Either Way

Codebases described as "hexagonal" and codebases described as "clean architecture" frequently turn out, structurally, to be doing the same thing — core logic isolated behind interfaces, concrete implementations plugged in from outside — differing mainly in which specific terminology and diagram the team adopted, not in any deep architectural distinction.

---

### Swappable Payment Gateway Adapters

A common, concrete real-world illustration — an application's core defines a `PaymentGateway` port, with separate adapters for Stripe, PayPal, or a fake test implementation, letting the payment provider be changed (or a new one added alongside an existing one) without touching the core checkout logic at all.

---

### Testing With Fake Adapters Instead of Real External Services

An everyday, practical benefit shared with Clean Architecture — tests run against fast, in-memory or fake adapters (no real database, no real third-party API calls) while production code uses the real adapters, with the application core itself completely unaware of which one it's actually talking to.

---

# Common Interview Questions

## What is Hexagonal Architecture (Ports and Adapters)?

An architectural style that isolates an application's core logic from external details by having the core define "ports" (interfaces describing what it needs from or offers to the outside world) and having "adapters" (concrete implementations) plug into those ports from outside — the hexagon shape itself is just a deliberate visual choice to avoid implying a top-to-bottom hierarchy.

---

## What's the difference between a primary/driving port and a secondary/driven port?

A primary (driving) port is how the outside world calls into the application — like a REST controller driving a use case. A secondary (driven) port is how the application calls out to the outside world — like a database or payment gateway adapter. Both are "ports," but the direction of the call differs, and being precise about which one you mean avoids confusion.

---

## How does Hexagonal Architecture relate to (or differ from) Clean Architecture?

They pursue the same underlying goal — isolating core application logic from external, volatile details — using different vocabulary and diagram shapes. A "port" is functionally the same as one of Clean Architecture's interfaces at a layer boundary; an "adapter" is functionally the same as a concrete implementation in an outer layer. For most practical purposes, they're the same idea, not competing approaches.

---

## What's the practical payoff of designing a system this way?

The application core can be tested in complete isolation using fake adapters (no real database, no real third-party API calls needed), and infrastructure — a database, a payment provider, even the way the outside world drives the application (REST vs CLI) — can be swapped later without touching the core business logic at all, since it only ever depends on its own port interfaces.

---

## Should a team debate whether to adopt "Hexagonal" or "Clean" architecture as if choosing between two different approaches?

Not really — since they express essentially the same underlying idea with different vocabulary, the more useful conversation is about whether isolating core logic behind interfaces is worth its complexity for this specific system, not which of the two nearly-identical namings to formally adopt.

---

# Common Mistakes

❌ Treating Hexagonal Architecture and Clean Architecture as fundamentally different, competing approaches.

They express the same underlying idea — isolating core logic behind interfaces implemented by outer, swappable adapters — with different vocabulary and diagram shapes, not two genuinely different architectural philosophies.

---

❌ Confusing which side (primary vs secondary) a specific port or adapter is on.

A REST controller adapter is primary (driving the application from outside); a database adapter is secondary (the application driving out to it) — mixing these up muddles discussion of the pattern's actual direction of control.

---

❌ Assuming the hexagon shape itself carries technical meaning.

It's purely a deliberate visual choice to avoid implying a top-to-bottom hierarchy — the number of sides or their specific arrangement in a diagram has no architectural significance beyond that.

---

# Key Takeaways

- Hexagonal Architecture pursues the same goal as Clean Architecture — isolating core application logic from external, volatile details — using its own vocabulary: ports (interfaces the core defines) and adapters (concrete implementations plugged in from outside).
- Primary (driving) ports describe the outside world calling into the application; secondary (driven) ports describe the application calling out to the outside world — a useful, precise distinction for discussing direction of control.
- The practical payoff mirrors Clean Architecture exactly — fast, isolated testing via fake adapters, and the ability to swap real infrastructure later without touching core business logic.
- For most practical purposes, Hexagonal Architecture and Clean Architecture are the same underlying idea with different vocabulary and diagram shapes, not competing architectural philosophies to be debated as rivals.
- The hexagon shape itself carries no special technical meaning — it's a deliberate visual choice to avoid the implied hierarchy of a traditional top-to-bottom layered diagram.
