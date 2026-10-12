# Horizontal Scaling

# Why Does Horizontal Scaling Exist?

Vertical scaling — making one machine bigger — runs into a wall eventually. There's a biggest machine you can buy, and even that has a traffic ceiling. Horizontal scaling breaks past it by adding more machines instead of a bigger one, and spreading load across all of them.

```
Vertical scaling:    1 machine → a BIGGER machine
                     (hard ceiling at the largest available machine)

Horizontal scaling:  1 machine → many machines, working together
                     (no inherent ceiling — add more machines as needed)
```

This is the motivation behind most of the Databases, Distributed Systems, and Networking sections. Replication, sharding, consensus, load balancing — all of it exists because a system chose to scale out instead of staying on one ever-bigger box.

---

# The Prerequisite: Statelessness

The single most important requirement for this to work cleanly, and a direct callback to the REST chapter.

```
If a server holds state LOCALLY that only IT knows about
(a session stored in its own memory, a local file it wrote):

↓

A request MUST go back to that SPECIFIC server to work correctly

↓

You can't freely route a request to ANY instance — which
directly breaks the whole point of having multiple, interchangeable
instances in the first place
```

```
If servers are STATELESS (any session/shared state lives in an
external store — Redis, a shared database):

↓

ANY instance can handle ANY request

↓

Adding, removing, or replacing instances becomes trivial — the
load balancer (from its own chapter) can route anywhere, freely
```

This is why the Sessions/Cookies chapters push so hard on externalizing state, and why Load Balancing discourages sticky sessions. Neither is a random best practice — both are prerequisites for horizontal scaling working at all.

---

# Auto-Scaling

Instead of provisioning a fixed instance count and manually nudging it, auto-scaling adds or removes instances based on real-time demand. It's what makes horizontal scaling economically sane, not just architecturally possible.

```
Metric-based scaling rule:

IF average CPU usage > 70% for 5 minutes  →  ADD an instance
IF average CPU usage < 30% for 15 minutes →  REMOVE an instance
```

```
Daily traffic pattern:

Low traffic overnight  → fewer instances running → lower cost
Peak traffic at noon    → auto-scaling adds instances → handles the spike
Traffic drops in evening → auto-scaling removes instances → cost drops back down
```

Without it, you're stuck choosing: provision for average load and fall over during real spikes, or provision for peak and pay for idle capacity most of the day. Auto-scaling just matches capacity to actual demand instead.

---

# The Coordination Cost of Scaling Out

None of this is free. You're trading a single machine's simplicity for a set of coordination problems that simply don't exist when there's only one server.

```
Single server:            no coordination needed — everything
                          lives in one place, naturally consistent

Many servers (horizontal): 

- Service discovery needed  — how does a caller find a currently-
  healthy instance? (Service Discovery chapter)

- Shared state needed        — session data, caches now need to
  live somewhere external and shared (Distributed Cache chapter)

- Consistency becomes a real question — if multiple instances can
  read/write the same data, what does "consistent" even mean now?
  (CAP Theorem, Consistency Models chapters)

- Distributed coordination    — leader election, distributed locks,
  if any instance needs to be "the one" doing something specific
  (Leader Election, Distributed Locks chapters)
```

Worth saying plainly: horizontal scaling isn't free capacity, it's a trade. You give up a single machine's simplicity and take on essentially the entire Distributed Systems section in exchange for scaling past what one box could ever handle.

---

# Real-World Examples

### Kubernetes Horizontal Pod Autoscaler (HPA)

Adjusts running pod replicas based on observed metrics — CPU, or custom application metrics — a direct, widely-used version of the auto-scaling idea above, built into the platform.

---

### AWS Auto Scaling Groups

Same idea at the VM level: launching or terminating EC2 instances based on real-time metrics, so capacity tracks actual demand instead of a fixed count someone set once.

---

### Web Application Tiers

The everyday case — stateless web/API servers behind a load balancer, scaling out during spikes and back down during quiet periods, because keeping them stateless (sessions in Redis or a shared store) makes this trivial.

---

# Common Interview Questions

## Why is statelessness a prerequisite for effective horizontal scaling?

Because a server holding local state forces requests that depend on it back to that specific server — breaking the assumption that any instance can handle any request. Externalize the state, and every instance stays interchangeable, so adding or removing them becomes trivial.

---

## How does auto-scaling work, and what metrics typically trigger it?

It watches real-time metrics — CPU, request rate, sometimes something application-specific like queue depth — and adds or removes instances against configured thresholds, so capacity tracks actual demand instead of a fixed count that's either wasteful or too slow to react.

---

## What new coordination problems does horizontal scaling introduce that a single server never had to deal with?

Service discovery, externalized shared state, consistency questions once multiple instances can read and write the same data, and distributed coordination for anything that needs exactly one instance in charge. None of these exist when everything lives on one machine.

---

## Why might a team choose vertical scaling over horizontal scaling, at least initially?

It sidesteps all of horizontal scaling's coordination costs — no service discovery, no distributed consistency questions, nothing to externalize. That makes it the faster, simpler first move for a lot of systems, especially a primary database, before there's a real need to shard.

---

## Is horizontal scaling always the better choice?

Not necessarily, and not immediately. It trades a single machine's simplicity for real, ongoing coordination costs. Plenty of systems reasonably scale vertically for a long time before that trade actually pays off.

---

# Common Mistakes

❌ Attempting to horizontally scale a stateful service without first externalizing its state.

Breaks the assumption that makes horizontal scaling work at all — any instance handling any request — and drags back in exactly the problems statelessness avoids.

---

❌ Scaling reactively and manually instead of using auto-scaling.

Leads to either wasted cost (over-provisioned for average load) or a bad user experience during spikes (too slow to react) — auto-scaling exists to remove this trade-off.

---

❌ Reaching for horizontal scaling's complexity before actually exhausting vertical scaling.

A lot of systems don't need it yet. Adopting it early just means paying real coordination costs before they're necessary.

---

# Key Takeaways

- Horizontal scaling adds more machines instead of a bigger one, breaking past vertical scaling's ceiling — it's the motivation behind most of Databases and Distributed Systems.
- Statelessness is the core prerequisite: any instance being able to handle any request is what makes adding, removing, or replacing instances simple.
- Auto-scaling is what makes horizontal scaling economically efficient, matching capacity to real demand instead of a fixed count.
- It introduces genuinely new coordination costs — service discovery, externalized state, consistency questions, distributed coordination — a real trade, not free capacity.
- Vertical scaling is often the simpler first move, with horizontal scaling reserved for once that ceiling is actually in sight.
