# Modular Monolith

# Why Does the Modular Monolith Exist?

The Monolith chapter's growing pains — a codebase that becomes tangled and hard to navigate as it grows — have an obvious-sounding fix: split it into microservices. But that fix comes with real, immediate costs: network calls where function calls used to be, distributed transactions instead of a single database transaction, and every coordination problem from the Distributed Systems section, all paid upfront, whether or not the system actually needs independent scaling or deployment of its different pieces yet.

The modular monolith exists as a genuine middle ground: keep the system as **one single deployable application** — still one process, still (typically) one database — but deliberately structure it internally into well-defined, loosely-coupled **modules**, each with clear boundaries and explicit interfaces between them, enforced with the same discipline a real service boundary would require.

```
Plain Monolith:          everything can reach into everything else's
                         internals — no enforced boundaries at all

Modular Monolith:         internally organized into distinct modules,
                          each with an explicit, enforced interface —
                          modules interact only through that interface,
                          never by reaching directly into each other's
                          internal data

Microservices:            the SAME discipline, but modules are also
                          SEPARATELY deployed, over the network
```

---

# What "Enforced Boundaries" Actually Means

```
Orders Module                    Inventory Module

public interface:                public interface:
  reserve_stock(order)             check_availability(product_id)
  release_stock(order)             update_stock(product_id, qty)

↓                                  ↓

Orders module can ONLY call Inventory through its public interface —
it CANNOT directly query Inventory's internal database tables, or
reach into its internal data structures directly, even though both
modules are running in the SAME process and could technically do so
```

This is a genuinely important, deliberate discipline — the modules are physically capable of reaching directly into each other (they're in the same process, same memory space), but the codebase's structure and conventions *prevent* it, exactly mirroring the discipline a real microservice boundary would enforce via the network, just without actually paying the network's cost.

---

# The Genuine "Best of Both Worlds" Payoff

```
Gets FROM microservices:  clear ownership, enforced boundaries
                          preventing "everything touches everything"
                          spaghetti, the ability to reason about
                          one module in isolation

Avoids FROM microservices:  network calls (and their latency/partial
                            failure) between modules, service discovery,
                            distributed transactions, separate
                            deployments and all the coordination
                            overhead that comes with them
```

For a genuinely large share of real systems — ones that need better internal organization as they grow, but don't actually need to scale or deploy different pieces independently yet — this is a legitimate, durable architecture choice, not merely a theoretical stepping stone toward "real" microservices eventually.

---

# A Natural Stepping Stone — If and When Extraction Is Actually Needed

If a specific module genuinely does need independent scaling or deployment later (say, the Inventory module needs to scale far more aggressively than the rest of the system, or a separate team wants to own and deploy it independently), the modular monolith's already-enforced boundary makes that extraction dramatically easier than pulling a boundary out of a tangled, undisciplined monolith.

```
Extracting a module into a real service:

From a MODULAR monolith:  the interface is already well-defined —
                           "extract" mostly means moving the module's
                           code to a new deployment and turning its
                           existing internal interface calls into
                           network calls instead

From a TANGLED monolith:   first need to DISCOVER where the actual
                           boundary should even be, untangle direct
                           references into the module's internals
                           scattered throughout the rest of the
                           codebase, THEN do the extraction
```

This is exactly the direct connection to the **Strangler Fig pattern** — gradually migrating pieces of a system to a new architecture by incrementally routing specific, well-bounded pieces of functionality to new services, one at a time, rather than a risky, all-at-once rewrite. A modular monolith's clean internal boundaries are precisely what make this kind of gradual, piece-by-piece extraction realistic rather than a much riskier, more disruptive big-bang rewrite.

---

# Real-World Examples

### Shopify

A widely cited, well-documented real case study — Shopify deliberately restructured its large monolithic Rails codebase into strictly-enforced internal modules (with tooling to actively detect and prevent boundary violations) specifically to get better organization and clearer ownership at scale, without taking on a full microservices migration.

---

### Many Pragmatic Production Systems

A genuinely common, if less publicly documented, real-world pattern — teams that recognize their monolith is becoming hard to navigate, and respond by imposing internal module discipline first, rather than immediately reaching for a microservices rewrite, precisely because the coordination costs of full microservices aren't yet justified by an actual independent-scaling or independent-deployment need.

---

### The Strangler Fig Migration Pattern

Directly enabled by a modular monolith's clean boundaries — a module can be incrementally extracted into its own service, with traffic gradually routed to the new service instead of the old module's code, allowing a full architectural migration to happen piece by piece over time rather than as one risky, all-at-once rewrite.

---

# Common Interview Questions

## What is a modular monolith, and what problem does it solve that a plain monolith doesn't?

A single deployable application, still one process and typically one database, but internally structured into well-defined modules with explicit, enforced interfaces between them — modules can't reach directly into each other's internal data, even though they're running in the same process. It solves the "everything is tangled together" problem a plain monolith develops as it grows, without paying microservices' network and distributed-systems coordination costs.

---

## How does a modular monolith make a future migration to microservices easier?

Because the module boundaries are already well-defined and enforced — extracting a module into a real, separately-deployed service mostly means moving its already-isolated code to a new deployment and converting its existing internal interface calls into network calls, rather than first needing to discover where a sensible boundary even is inside a tangled, undisciplined monolith.

---

## Why might a team choose a modular monolith over either a plain monolith or full microservices?

When better internal organization and clearer ownership are genuinely needed as the system grows, but there's no actual current need for independent scaling or independent deployment of different pieces — a modular monolith gets much of microservices' organizational benefit without its real network and coordination costs, making it the pragmatic middle ground for a large share of real systems.

---

## Is a modular monolith just a temporary stepping stone toward "real" microservices?

Not necessarily — for many systems, it's a legitimate, durable long-term architecture in its own right, not merely a phase to be outgrown. It only becomes a stepping stone if and when a specific module actually develops a genuine need for independent scaling or deployment that the rest of the system doesn't share.

---

# Common Mistakes

❌ Not actually enforcing module boundaries in practice.

If modules can still freely reach into each other's internal data "just this once," the discipline erodes over time, and the system becomes a regular tangled monolith with extra structure in name only, providing none of the real benefit.

---

❌ Assuming a modular monolith is only useful as a stepping stone, never a legitimate end state.

Plenty of real, successful systems (Shopify being a well-documented example) run as modular monoliths long-term, deliberately, without ever needing or wanting a full microservices migration.

---

❌ Confusing "having folders/packages" with actually enforcing module boundaries.

Directory structure alone doesn't prevent code in one module from directly importing and using another module's internals — genuine enforcement usually requires deliberate tooling or code review discipline to actually catch and prevent boundary violations.

---

# Key Takeaways

- A modular monolith keeps a system as one deployable application while enforcing well-defined, explicit boundaries between internal modules — getting much of microservices' organizational clarity without its network and coordination costs.
- The enforcement is deliberate and non-trivial — modules are physically capable of reaching into each other (same process, same memory) but are prevented from doing so by structure and convention, mirroring the discipline a real service boundary would require.
- It's a genuine, durable architecture in its own right for many systems, not merely a temporary stepping stone — Shopify's well-documented internal restructuring is a strong real-world example.
- When a module does eventually need independent scaling or deployment, a modular monolith's already-enforced boundaries make extraction (via the Strangler Fig pattern) dramatically easier than pulling a boundary out of a tangled, undisciplined monolith.
- The discipline only works if boundaries are genuinely enforced — a modular monolith with unenforced module boundaries degrades back into a regular, tangled monolith in practice.
