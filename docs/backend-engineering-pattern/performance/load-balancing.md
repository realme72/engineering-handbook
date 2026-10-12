# Load Balancing

# Why Does Load Balancing Exist?

Every server has a ceiling — some number of requests per second beyond which it queues, slows down, or falls over. Past that ceiling you need more than one server, which immediately raises a new problem: which server handles any given request? Load balancing is the answer — spreading traffic across backend instances so none of them drowns while others sit idle.

```
Client requests

↓

Load Balancer

↓          ↓          ↓

Server A  Server B  Server C
```

Without this layer, either every client has to know about and choose among all available servers itself (client-side discovery, from the Service Discovery chapter), or traffic gets split by some rigid, manual rule. Neither scales well as instances come and go.

---

# Load Balancing Algorithms

## Round Robin

```
Request 1 → Server A
Request 2 → Server B
Request 3 → Server C
Request 4 → Server A  (cycle repeats)
```

The simplest option — cycle through servers in order. Fine when every server has similar capacity and requests take similar time. Breaks down the moment either assumption stops holding.

## Least Connections

```
Route the next request to whichever server CURRENTLY has the
fewest active connections
```

Accounts for the fact that requests don't all take the same time. A server buried in a few slow, long-running requests shouldn't get handed the next one just because round robin says it's its turn — this adapts to actual load instead of blindly cycling.

## Weighted (Round Robin or Least Connections)

```
Server A: weight 3   (more powerful hardware, handle 3x the traffic)
Server B: weight 1
Server C: weight 1
```

For when backend capacity genuinely differs — heterogeneous hardware, or a new instance still warming up — so traffic lands proportionally instead of assuming every server is identical.

## IP Hash / Consistent Hashing

```
hash(client_ip) → determines which server handles this client's requests

↓

The SAME client is consistently routed to the SAME server, every time
```

Useful for session affinity — if a server holds session state locally, routing the same client back to it every time avoids sharing that state elsewhere. Same consistent hashing idea from the Sharding and Distributed Cache chapters, just routing traffic instead of sharding data.

---

# Layer 4 vs Layer 7 Load Balancing

Briefly introduced in the API Gateway chapter — here's the full picture.

```
Layer 4 (Transport Layer):  operates on raw TCP/UDP connections —
                              routes based on IP address and port,
                              with NO understanding of what's inside
                              the connection (no HTTP awareness at all)

Layer 7 (Application Layer): understands HTTP — can route based on
                               the request PATH, HEADERS, or even
                               the request BODY, not just the
                               underlying connection
```

```
L4 example:  "route this TCP connection to one of these three
              backend IPs" — fast, simple, no visibility into
              what's actually being requested

L7 example:  "route requests to /api/orders/* to the Orders
              Service, and /api/payments/* to the Payments
              Service" — requires actually parsing HTTP to make
              this decision
```

L4 is faster and simpler because it never looks at application content — but it also can't make any decision based on what's actually being requested. L7 costs more processing per request (it has to parse HTTP), but that's what enables path- and header-based routing, which you need for anything past "spread connections evenly across identical backends."

---

# Health Checks

A load balancer is only as good as its idea of who's healthy — the same health-checking concept from the Service Discovery chapter, applied here.

```
Load balancer periodically checks each backend:

GET /health → 200 OK  → keep routing traffic to this server

GET /health → timeout/error → STOP routing traffic to this server
                                until it passes health checks again
```

Skip active health checks, and a load balancer keeps sending traffic to a server that's already crashed — making an outage worse for whoever gets routed there, instead of quietly steering around it.

---

# Sticky Sessions — And Why They're Often Discouraged

Pinning a client to one specific server, via IP hash or a cookie the load balancer sets, is a real option. It has a real cost too.

```
WITHOUT sticky sessions:  ANY server can handle ANY client's
                          request — servers are interchangeable,
                          horizontal scaling and failover are simple

WITH sticky sessions:      a specific client is bound to a specific
                            server — if THAT server fails, the
                            client's session-dependent state
                            (whatever made stickiness necessary in
                            the first place) may be lost entirely
```

This is the statelessness principle from the REST chapter meeting the requirement from Horizontal Scaling. Externalize session state to a shared store — Redis, a database — instead of keeping it on one server, and any server can handle any request, no stickiness needed. Most modern architectures go this route, because it keeps scaling and failover simple instead of quietly reintroducing a dependency on one instance.

---

# Real-World Examples

### NGINX / HAProxy

Battle-tested software load balancers supporting round robin, least connections, and weighted algorithms — commonly deployed as the L7 layer in front of application servers.

---

### AWS ELB / ALB

ALB operates at L7, with path- and host-based routing built in. NLB operates at L4, for cases where raw TCP/UDP throughput matters more than content-aware routing.

---

### Envoy

A widely-adopted proxy that works both as a standalone load balancer and as the sidecar underlying many service mesh setups (the same concept from the API Gateway chapter's east-west traffic discussion) — with sophisticated L7 routing, health checking, and circuit breaking built in.

---

# Common Interview Questions

## Round robin vs least connections — when would you choose each?

Round robin when servers are roughly equivalent and requests take similar time — it's simple and needs no load tracking. Least connections when processing times vary meaningfully, since it reacts to actual current load instead of blindly cycling.

---

## What's the difference between L4 and L7 load balancing?

L4 routes on raw TCP/UDP — fast, simple, but limited to IP and port. L7 understands HTTP and can route on path, headers, or content, at the cost of extra per-request processing to actually parse the request.

---

## Why are sticky sessions often discouraged in modern architectures?

They reintroduce a dependency on one specific server — if it fails, whatever needed stickiness in the first place can be lost. Externalizing session state to a shared store keeps servers stateless and interchangeable, avoiding that trade-off entirely.

---

## How does a load balancer know a backend instance is unhealthy?

Active health checks — periodic requests to a health endpoint, removing a backend from the pool if it fails and adding it back once it recovers. Same mechanism as the Service Discovery chapter, applied to traffic routing.

---

## When would you use weighted load balancing?

When backend capacity genuinely differs — heterogeneous hardware, or an instance still warming up after a deploy — so traffic lands proportionally instead of assuming every server can take the same load.

---

# Common Mistakes

❌ Using plain round robin when backend servers have meaningfully uneven capacity.

Overwhelms weaker instances while stronger ones sit idle — use weighted routing instead.

---

❌ Relying on sticky sessions instead of externalizing session state.

Reintroduces a dependency on one server, undermining the simplicity horizontal scaling and failover are supposed to provide.

---

❌ Not implementing active health checks.

Keeps routing traffic to a crashed server, worsening an outage instead of routing around it automatically.

---

# Key Takeaways

- Load balancing exists because a single server has a finite ceiling — spreading traffic across instances is how a system serves more than any one machine could handle alone.
- Round robin, least connections, and weighted algorithms fit different assumptions about server capacity and request time — pick the wrong one and you get avoidable imbalance.
- L4 is fast but content-blind, routing only on IP/port; L7 understands HTTP and enables path/header-based routing at the cost of extra processing.
- Active health checks let a load balancer stop (and later resume) routing to instances based on real, current health, instead of assuming everyone's always up.
- Sticky sessions reintroduce a per-server dependency that undermines scaling and failover — externalizing session state to a shared store is the better default.
