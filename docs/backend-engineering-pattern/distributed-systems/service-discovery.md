# Service Discovery

# Why Does Service Discovery Exist?

In a static system, calling another service is simple — hardcode its IP address, done. That assumption collapses immediately in any modern, elastic environment: containers get scheduled onto different hosts every deploy, instances scale up and down constantly based on load, and IP addresses that were valid five minutes ago might now belong to a completely different, unrelated process.

```
Order Service needs to call Payment Service

↓

Hardcoded: http://10.0.4.17:8080

↓

Payment Service gets redeployed → new container → NEW IP address

↓

Order Service is now calling a dead or completely wrong address
```

Service discovery exists to answer, dynamically and continuously, the question "where is Payment Service *right now*?" — instead of an address baked in once and silently going stale the moment the underlying infrastructure changes.

---

# The Service Registry

The core piece of infrastructure underneath any service discovery mechanism: a continuously-updated directory of which service instances currently exist and are healthy.

```
Service Registry:

payment-service  →  10.0.4.22:8080  (healthy)
                  →  10.0.4.31:8080  (healthy)
                  →  10.0.4.09:8080  (FAILED health check — removed)

order-service    →  10.0.5.14:8080  (healthy)
```

Instances register themselves (or are registered by the platform) on startup, are continuously health-checked, and are automatically removed from the registry the moment they stop responding — keeping the directory an accurate, live reflection of what's actually running and reachable, not a static configuration file someone has to remember to update by hand.

---

# Client-Side Discovery

The calling service itself queries the registry directly, gets back a list of healthy instances, and picks one (often with its own load-balancing logic).

```
Order Service

↓

Query registry: "where is payment-service?"

↓

Registry returns: [10.0.4.22:8080, 10.0.4.31:8080]

↓

Order Service picks one (round-robin, random, etc.) and calls it DIRECTLY
```

The client has full control over its own load-balancing strategy, at the cost of every single client needing to implement (or link in a library implementing) registry-querying and load-balancing logic itself — a real, distributed maintenance burden across every service in the system.

---

# Server-Side Discovery

The calling service talks to a fixed, well-known address (a load balancer or proxy), which itself queries the registry and handles routing — the caller does no discovery work at all.

```
Order Service

↓

Calls a FIXED address: http://payment-service.internal

↓

Load Balancer / Proxy: queries the registry itself,
                         picks a healthy instance, routes the request

↓

Payment Service instance
```

The calling service's code stays completely unaware that discovery is even happening — it just calls a stable name. This shifts the discovery and load-balancing complexity into shared, centralized infrastructure instead of duplicating it inside every single client — generally the simpler, more maintainable choice for most application teams, at the cost of the load balancer/proxy layer itself needing to be highly available (the same single-point-of-failure consideration covered in the API Gateway chapter).

---

# DNS-Based Discovery

A specific, extremely common implementation of server-side discovery — instead of a dedicated registry protocol, service names are resolved via ordinary DNS, with the underlying set of healthy IPs updated dynamically behind the scenes.

```
Application calls: http://payment-service.default.svc.cluster.local

↓

DNS resolves this name → returns a currently-healthy instance's IP
(Kubernetes updates the underlying DNS records as instances come and go)
```

This is Kubernetes's default approach — a `Service` object gets a stable internal DNS name, and Kubernetes's own networking layer (`kube-proxy` and the cluster DNS) transparently handles routing that name to whichever pod instances are currently healthy, without the application needing any service-discovery-specific code or library at all. The appeal is huge: any application, in any language, that can make a normal DNS lookup and HTTP call already knows how to "do" service discovery in this model, with zero special integration required.

---

# Dedicated Service Registries

For environments without Kubernetes's built-in mechanism, dedicated tools provide the same registry-plus-health-checking capability directly.

```
Consul:   a registry with built-in health checking, exposed via both
          a DNS interface AND an HTTP API, plus key-value configuration
          storage

Eureka:   Netflix's client-side discovery service — historically paired
          with client libraries (Ribbon) that queried Eureka directly
          and handled load balancing on the client side

Zookeeper: sometimes used for service discovery in addition to its more
           common role as a consensus/coordination service (leader
           election, distributed locks)
```

---

# What Happens If the Registry Itself Is Unavailable

This is a genuine, important operational question — the registry is itself a critical piece of shared infrastructure, and its own availability matters enormously.

```
Registry becomes unreachable

↓

Options:

1. Cache the last-known-good list of instances locally, and keep
   using it temporarily (stale but functional, rather than failing
   outright)
2. Fail closed — refuse to route any requests until the registry
   recovers (safer in some contexts, but a real availability cost)
```

Most production discovery mechanisms lean toward caching a recent snapshot specifically to avoid the registry becoming a single point of failure for the entire system's ability to function — combined with the Circuit Breaker pattern's fail-fast philosophy for handling calls to instances that turn out to be unhealthy despite appearing in a slightly-stale cached list.

---

# Real-World Examples

### Kubernetes

The dominant modern example — DNS-based, server-side discovery built directly into the platform, requiring zero service-discovery-specific application code. A `Service` resource provides a stable name and IP, and Kubernetes's networking layer transparently handles the actual routing to healthy pod instances behind it.

---

### Netflix Eureka + Ribbon (Classic Netflix OSS Stack)

A widely cited, historically influential example of client-side discovery — services registered themselves with Eureka, and client libraries (Ribbon) queried Eureka directly and applied client-side load-balancing logic before calling a chosen instance, predating the now-more-common DNS-based, platform-managed approach.

---

### Consul

A common choice for environments running outside Kubernetes (or alongside it) needing both service discovery and general-purpose distributed configuration, offering both a DNS interface (for simple, zero-integration lookups) and a richer HTTP API (for clients that want more control, like explicit health status).

---

# Common Interview Questions

## Why is service discovery necessary in a modern microservices or containerized environment?

Because instances' network addresses change constantly — containers get rescheduled to different hosts, instances scale up and down based on load — making hardcoded addresses unreliable almost immediately. Service discovery provides a live, continuously-updated way to answer "where is this service right now," instead of a static configuration that goes stale the moment the underlying infrastructure changes.

---

## Client-side vs server-side discovery — what's the trade-off?

Client-side discovery gives each calling service full control over its own load-balancing strategy, at the cost of every client needing its own registry-querying and load-balancing logic. Server-side discovery centralizes that complexity into a load balancer or proxy, letting calling services stay completely unaware that discovery is even happening — generally simpler to maintain across many services, at the cost of that centralized layer itself needing to be highly available.

---

## How does Kubernetes implement service discovery?

Primarily via DNS — a `Service` object gets a stable internal DNS name, and Kubernetes's networking layer (cluster DNS plus `kube-proxy`) transparently updates and routes that name to whichever pod instances are currently healthy, requiring no service-discovery-specific code in the application itself.

---

## What happens if the service registry itself becomes unavailable?

Most production systems cache the last-known-good set of healthy instances locally and continue operating on that (slightly stale) information rather than failing outright the instant the registry is unreachable — treating the registry as important shared infrastructure that shouldn't become a single point of failure for the entire system's ability to route requests at all.

---

## How does service discovery relate to health checking?

A registry is only useful if it reflects reality — instances need to be continuously health-checked and automatically removed the moment they stop responding correctly, or the registry ends up directing traffic to dead or unhealthy instances, which defeats much of its purpose.

---

# Common Mistakes

❌ Hardcoding service addresses in a dynamic, elastic environment.

Breaks essentially immediately the first time an instance is rescheduled, restarted, or a deployment changes the underlying set of addresses.

---

❌ Registering instances without continuous health checking.

A registry that only reflects "who registered at some point" rather than "who's actually healthy right now" can route traffic to dead instances just as easily as no registry at all.

---

❌ Treating the service registry as infallible, with no fallback for its own unavailability.

The registry is itself a critical dependency — without a caching or fallback strategy, its unavailability can take down every service's ability to discover and call every other service simultaneously.

---

❌ Implementing client-side discovery logic independently, inconsistently, across many services.

Duplicated, inconsistent discovery and load-balancing logic across services is exactly the maintenance burden server-side/DNS-based discovery is designed to avoid by centralizing it once.

---

# Key Takeaways

- Service discovery exists because hardcoded network addresses break down almost immediately in any environment where instances are dynamically scheduled, scaled, or replaced.
- A service registry is only useful if it's continuously updated via health checks — an inaccurate registry can route traffic to dead instances just as easily as having no registry at all.
- Client-side discovery puts load-balancing control (and complexity) in every caller; server-side/DNS-based discovery centralizes that complexity into shared infrastructure, generally the simpler default for most teams.
- Kubernetes's DNS-based, platform-managed discovery requires zero service-discovery-specific application code, which is a large part of why it's become the dominant modern default.
- The registry itself is critical shared infrastructure — production systems generally cache a recent snapshot of healthy instances rather than treating registry unavailability as an outright system-wide failure.
