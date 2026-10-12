# Monolith

# Why Does the Monolithic Architecture Exist?

Every system has to start somewhere, and the simplest possible starting point is putting all of an application's logic — every module, every feature — into one single codebase, deployed and run as one single unit. A monolith isn't a mistake or a phase to be embarrassed about; it's the architecture with the fewest moving parts, and for a large share of real systems, that simplicity is genuinely the right trade-off, not just a beginner's compromise.

```
Monolith:

One codebase
One deployment
One running process (or many identical copies of it)
One database (typically)

↓

Internal calls between "modules" are just ORDINARY FUNCTION CALLS —
not network calls, not a separate service to coordinate with
```

---

# Why It's Genuinely Attractive, Not Just the Easy Default

```
Simplicity:              no network calls between internal
                          components — everything is a direct
                          function call, easy to trace and reason
                          about end to end

No distributed systems problems: none of the coordination costs
                          from the Distributed Systems section apply
                          at all — no service discovery, no partial
                          failure across services, no distributed
                          transactions (a single database transaction,
                          from the Transactions chapter, covers the
                          whole operation natively)

Fast early development:   one team, one codebase, no need to
                          coordinate API contracts or deployment
                          schedules across multiple separate teams
                          or services
```

For an early-stage product, a small team, or a system that genuinely doesn't need to scale different pieces independently, a monolith removes an enormous amount of complexity that a microservices architecture would otherwise force onto the team from day one, for a scaling problem that may not exist yet at all.

---

# Where It Genuinely Breaks Down as It Grows

## All-or-Nothing Scaling

```
The checkout flow is the actual bottleneck under load

↓

In a monolith, you can't scale JUST the checkout logic — scaling
means running MORE COPIES OF THE ENTIRE APPLICATION, even the 95%
of it that isn't actually under load
```

This is a direct callback to the Horizontal Scaling chapter — a monolith can absolutely scale horizontally (many identical copies behind a load balancer), but only as one indivisible unit; it can't scale one specific, actually-bottlenecked piece independently of the rest.

## No Fault Isolation

```
A bug or resource leak in ONE module (say, the reporting feature)

↓

Can bring down the ENTIRE process — including checkout, login,
everything — since it's all running in the same process, sharing
the same memory and resources
```

A microservices architecture's fault isolation (a crash in one service doesn't necessarily take down others) simply doesn't exist here by construction — everything shares fate, for better (simplicity) and worse (blast radius).

## Growing Pains at Scale

```
Codebase grows large  →  harder for new engineers to navigate and
                          understand the full system

Build/test suite grows →  CI/CD gets slower as the codebase and
                           test suite both grow, since everything
                           builds and tests together as one unit

Technology lock-in       →  the entire application is one language/
                            framework — adopting something new for
                            just one piece means either rewriting
                            that piece in isolation (awkward within
                            one codebase) or the whole thing
```

None of these are fatal on their own, but they compound as both the codebase and the team working on it grow — which is exactly the pressure that eventually pushes some systems toward a Modular Monolith or full Microservices, covered in their own chapters.

---

# The "Distributed Monolith" Warning, Previewed

Worth flagging here, and covered in full depth in the Microservices chapter: splitting a monolith into separately-deployed services *without* actually decoupling them (a shared database, synchronous call chains that must all succeed together, deploys that have to happen in lockstep) doesn't escape the monolith's problems — it adds network calls and operational complexity on top of them, with none of microservices' actual benefits gained in return. A poorly-executed split can genuinely be worse than staying a well-organized monolith.

---

# Real-World Examples

### Shopify

Ran (and for a long time continued to run) as a large, successful monolith at massive scale — a well-documented, often-cited real-world counterexample to the assumption that "real scale requires microservices."

---

### Basecamp / DHH's "Majestic Monolith"

David Heinemeier Hansson (creator of Ruby on Rails) has publicly and prominently advocated for staying monolithic as a deliberate, long-term architectural choice — not a phase to outgrow — for a large share of real, successful products, directly pushing back against the industry-wide assumption that microservices are the inevitable "mature" endpoint.

---

### Stack Overflow

Historically ran on a remarkably small number of servers running a monolithic architecture, serving enormous traffic — a strong, concrete illustration that a well-optimized monolith (see the Vertical Scaling chapter) can handle far more load than its reputation as "the simple, unscalable choice" suggests.

---

# Common Interview Questions

## What are the advantages of a monolith compared to jumping straight to microservices?

Simplicity — no network calls between internal components, no distributed systems coordination costs (service discovery, partial failure, distributed transactions), and faster early development since one team can work in one codebase without coordinating API contracts or deployment schedules across separate services.

---

## What specifically breaks down as a monolith and its team grow large?

Scaling becomes all-or-nothing — you can't scale just the actual bottlenecked piece independently, only the whole application as one unit. Fault isolation disappears — a bug in one module can bring down the entire process. And the codebase, build times, and test suite all grow together, making the system progressively harder to navigate and slower to iterate on as both the code and the team scale up.

---

## What is a "distributed monolith," and why is it worse than either a clean monolith or real microservices?

Splitting a system into separately-deployed services without actually decoupling them — a shared database, synchronous call chains requiring all services to succeed together, deploys that must happen in lockstep. This pays every real cost of microservices (network calls, operational complexity, distributed failure modes) while gaining none of the actual benefits (independent scaling, independent deployment), since the underlying coupling was never actually removed.

---

## Can a monolith scale at all, or does scaling require microservices?

A monolith can absolutely scale horizontally — running many identical copies of the entire application behind a load balancer — and vertically, by simply running on a bigger machine. What it can't do is scale one specific, bottlenecked piece independently of the rest; the whole application scales as one indivisible unit, which is the actual limitation, not an inability to scale at all.

---

# Common Mistakes

❌ Assuming a monolith fundamentally can't handle real production scale.

Real, large-scale companies (Shopify, Stack Overflow) have run successfully as monoliths — the actual limitation is that a monolith can't scale individual pieces independently, not that it's incapable of scale at all.

---

❌ Prematurely splitting into microservices before actually needing independent scaling or deployment of different pieces.

Pays real, ongoing coordination costs (the entire Distributed Systems section) for a scaling or organizational problem the team may not actually have yet — the same premature-complexity mistake covered in the Horizontal Scaling chapter, applied here specifically to architectural choice.

---

❌ Letting a monolith's internal modules become tangled with no enforced boundaries at all.

This is exactly the problem the Modular Monolith chapter addresses — a monolith doesn't have to mean "no internal structure," and a genuinely tangled monolith is much harder to eventually split (if that's ever needed) than one with clean, enforced internal module boundaries.

---

# Key Takeaways

- A monolith — one codebase, one deployment, internal calls as ordinary function calls — is the architecture with the fewest moving parts, and a genuinely correct choice for many real systems, not just a beginner's compromise.
- Its core weaknesses are all-or-nothing scaling (can't scale one bottlenecked piece independently) and lack of fault isolation (one module's failure can take down everything) — both of which compound as the codebase and team grow.
- Real, large-scale companies (Shopify, Stack Overflow, Basecamp) have run successfully as monoliths, directly challenging the assumption that microservices are an inevitable, mature endpoint every system must eventually reach.
- A "distributed monolith" — services split without actually decoupling their database, deploys, or call patterns — pays every real cost of microservices while gaining none of the actual benefits, and is worth naming precisely as a distinct, common failure mode.
- Prematurely abandoning a monolith for microservices' coordination costs, before an actual need for independent scaling or deployment exists, is a common and expensive mistake.
