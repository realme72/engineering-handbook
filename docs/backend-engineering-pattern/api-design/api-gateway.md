# API Gateway

# Why Does an API Gateway Exist?

Imagine you started with one monolithic backend. Over a few years, it split into fifteen microservices — orders, payments, inventory, users, notifications, and so on. Nobody sat down and planned this split maliciously; it happened for good reasons, one service at a time.

Now think about what your mobile client has to deal with.

```
Mobile App

├── auth.internal.company.com     → login
├── orders.internal.company.com   → orders
├── payments.internal.company.com → payments
├── inventory.internal.company.com → stock
└── notifications.internal.company.com → alerts
```

Every one of those services now independently needs to:

```
Verify the JWT
Rate-limit the caller
Handle CORS
Terminate TLS
Log the request
Emit metrics
```

That's six cross-cutting concerns, duplicated fifteen times, once per service, all subtly drifting out of sync as different teams implement "the same" auth check slightly differently. And the mobile client now needs to know fifteen different hostnames, handle fifteen different failure modes, and update itself every time a service moves or gets renamed internally.

An API Gateway exists to collapse this back down to one thing the client actually has to know about:

```
Mobile App

↓

api.company.com   (the Gateway)

↓

routes internally to whichever service actually owns this request
```

The client sees one stable address. Everything about how many services exist behind it, and how they're organized, becomes an internal implementation detail the gateway can change without the client ever noticing.

---

# What Problem It Actually Solves

- **Single entry point** — clients talk to one address regardless of how many services exist behind it, and however that internal topology changes over time.
- **Centralizes cross-cutting concerns** — authentication, rate limiting, logging, and TLS termination get implemented once, correctly, instead of fifteen times, inconsistently.
- **Decouples client contract from internal architecture** — a service can be split into two, merged into one, or rewritten in a different language, and as long as the gateway's routing is updated, no client code changes.
- **Protocol translation** — clients speak REST/JSON at the edge while internal services speak gRPC or another protocol optimized for service-to-service traffic; the gateway bridges the two.
- **Aggregation** — a single client request can fan out to multiple backend services and return one combined response, instead of forcing the client to make three round trips and stitch the results together itself.

---

# How It Works

```
Client

↓

HTTPS Request

↓

              API Gateway
              ┌─────────────────────┐
              │ TLS Termination      │
              │ Authentication       │
              │ Rate Limiting        │
              │ Request Routing      │
              │ Logging / Metrics    │
              └─────────────────────┘

↓          ↓            ↓            ↓

Orders    Payments    Inventory   Notifications
Service   Service     Service     Service
```

Routing is typically based on the request's path, host, or headers:

```
/orders/*        →  Orders Service
/payments/*      →  Payments Service
/inventory/*     →  Inventory Service
```

By the time a request reaches an internal service, the gateway has already done the expensive/repetitive work — the service can trust that the caller is authenticated and within rate limits, and just focus on its own business logic.

---

# Core Responsibilities

## Authentication & Authorization Offloading

The gateway verifies the token once, at the edge, and forwards trusted identity information downstream instead of making every service re-verify a JWT independently.

```http
Client → Gateway:    Authorization: Bearer <jwt>

Gateway → Service:   X-User-Id: 42
                     X-User-Roles: admin
```

Internal services trust these headers because they only ever receive traffic that's already passed through the gateway — the network itself is configured so nothing can reach them directly from outside.

## Rate Limiting

The same rate limiting concepts covered elsewhere (token bucket, sliding window) live here, enforced once per client/API key at the edge, instead of duplicated per service — and rejected before ever consuming a downstream service's resources.

## Request Routing / Load Balancing

Path-based, host-based, or header-based routing to the correct backend, plus distributing load across multiple healthy instances of that backend.

## Protocol Translation

```
Client speaks:     REST / JSON  (browser and mobile friendly)

Gateway translates:  →  gRPC     (internal service-to-service)

Internal services speak:  gRPC
```

External clients get the ergonomics of REST; internal services get the performance and strict contracts of gRPC — the gateway is the seam between two different worlds instead of forcing one protocol choice on both.

## Response Aggregation (Backend for Frontend)

```
Client requests: GET /dashboard

↓

Gateway fans out internally:

  → Orders Service      (recent orders)
  → Notifications       (unread count)
  → User Service        (profile info)

↓

Gateway combines all three into one response

↓

Client receives ONE response instead of THREE round trips
```

This variant — a gateway tailored to exactly what one specific client type needs — is commonly called a **Backend for Frontend (BFF)**. A mobile app and a web dashboard often want meaningfully different shapes of the same underlying data; rather than forcing both through one generic gateway contract, some architectures run a separate BFF per client type, each doing its own aggregation suited to that client.

## Circuit Breaking

If the Payments service starts timing out, the gateway can detect the failure pattern and stop forwarding requests to it temporarily — failing fast with an error instead of piling up slow, doomed requests and making the outage worse across every client hitting that path.

## Observability

Every request passes through one place, which makes it the natural spot to centralize logging, request tracing (assigning a trace ID at the edge that propagates through every downstream call), and metrics — instead of stitching together fifteen services' independent logs after the fact to reconstruct what happened for one request.

---

# API Gateway vs Load Balancer

This is a frequent point of confusion, and a common interview question.

| | Load Balancer | API Gateway |
|---|---|---|
| Layer | Typically L4 (TCP) or basic L7 | Always L7 (understands HTTP semantics) |
| Awareness | Distributes traffic across healthy instances | Understands routes, auth, rate limits, request/response shape |
| Routing logic | "Which instance is healthy and least loaded?" | "Which *service* does `/orders/*` belong to, and is this caller allowed to hit it?" |
| Typical scope | In front of one service's instances | In front of an entire system of many services |

In practice, a load balancer often sits *behind* the gateway, distributing traffic across instances of whichever service the gateway routed to — they're complementary layers, not competing choices.

---

# API Gateway vs Service Mesh

Another common point of confusion once systems get large enough to have both.

```
North-South Traffic         East-West Traffic

Client → Gateway → Service   Service A → Service B → Service C
   (external → internal)        (internal → internal)
```

An API Gateway sits at the edge, handling traffic coming *into* the system from outside (north-south). A service mesh (Envoy, Istio/Linkerd sidecars) handles traffic *between* internal services (east-west) — service-to-service auth (mTLS), retries, internal load balancing, and internal circuit breaking.

They solve structurally similar problems (routing, auth, resilience) at different layers of the same system, and large architectures commonly run both simultaneously — a gateway at the edge, a mesh internally.

---

# Python Implementation

A deliberately minimal gateway, built with FastAPI, tying together authentication and rate limiting (covered in depth elsewhere in this handbook) before proxying to a backend service:

```python
import time
import httpx
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

SERVICE_ROUTES = {
    "orders": "http://orders-service:8001",
    "payments": "http://payments-service:8002",
}

rate_limit_state = {}  # client_id -> (tokens, last_refill) — see rate-limiting.md
RATE_LIMIT_CAPACITY = 100
RATE_LIMIT_REFILL_PER_SEC = 1


def check_rate_limit(client_id: str) -> bool:
    now = time.time()
    tokens, last = rate_limit_state.get(client_id, (RATE_LIMIT_CAPACITY, now))
    tokens = min(RATE_LIMIT_CAPACITY, tokens + (now - last) * RATE_LIMIT_REFILL_PER_SEC)
    if tokens < 1:
        rate_limit_state[client_id] = (tokens, now)
        return False
    rate_limit_state[client_id] = (tokens - 1, now)
    return True


def verify_token(authorization: str) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    # in reality: decode + verify the JWT signature and claims here
    return {"user_id": 42, "roles": ["user"]}


@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def gateway(service: str, path: str, request: Request):
    if service not in SERVICE_ROUTES:
        raise HTTPException(status_code=404, detail="Unknown service")

    identity = verify_token(request.headers.get("authorization"))

    if not check_rate_limit(str(identity["user_id"])):
        raise HTTPException(status_code=429, detail="Too many requests")

    upstream_url = f"{SERVICE_ROUTES[service]}/{path}"
    forwarded_headers = {
        "X-User-Id": str(identity["user_id"]),
        "X-User-Roles": ",".join(identity["roles"]),
    }

    async with httpx.AsyncClient() as client:
        upstream_response = await client.request(
            request.method,
            upstream_url,
            headers=forwarded_headers,
            content=await request.body(),
            params=request.query_params,
        )

    return upstream_response.json()
```

Notice what the downstream service never has to do: parse or verify a JWT, or implement its own rate limiting. It receives `X-User-Id`/`X-User-Roles` as trusted facts, because the gateway already did that work — this is the entire point of centralizing cross-cutting concerns in one place instead of fifteen.

---

# Real-World Examples

### Amazon API Gateway

Sits in front of Lambda functions and other AWS backends, handling auth (via Cognito/IAM), throttling, request/response transformation, and caching — a fully managed version of everything described above, common in serverless architectures where you don't want to hand-roll any of this infrastructure yourself.

---

### Kong / NGINX

Self-hosted gateways used heavily in Kubernetes-based microservice architectures, typically configured declaratively (routes, plugins for auth/rate-limiting/logging) rather than by writing custom gateway code like the example above — the same responsibilities, implemented as configuration instead of application code.

---

### Netflix Zuul

One of the earliest widely-discussed API gateways at scale, built specifically to handle routing, filtering (auth, logging), and resilience for Netflix's enormous number of internal microservices sitting behind one edge — a lot of the "why gateways matter at scale" thinking in the industry traces back to Netflix's public writing about this system.

---

# Common Interview Questions

## What's the difference between an API Gateway and a load balancer?

A load balancer distributes traffic across healthy instances of typically one service, often without understanding anything about HTTP semantics beyond basic health checks. An API Gateway operates at the application layer — it understands routes, authentication, rate limits, and can route to entirely different services based on the request, not just spread load across copies of the same thing. In real systems, a load balancer often sits behind the gateway, in front of each individual service's instances.

---

## What's the difference between an API Gateway and a service mesh?

A gateway handles north-south traffic — external clients coming into the system. A service mesh handles east-west traffic — internal service-to-service calls. Both provide similar capabilities (routing, auth, resilience), but at different layers; large systems commonly run both at once.

---

## Isn't the gateway a single point of failure?

Yes, structurally — every request passes through it, so it has to be treated with the same seriousness as any other tier that everything depends on: horizontally scaled behind its own load balancer, deployed across multiple availability zones, with aggressive health checks and fast failover. "Single entry point" is a deliberate trade — you're accepting one well-engineered, heavily-invested-in point of centralization in exchange for not duplicating auth and rate limiting fifteen times, inconsistently.

---

## What is a BFF (Backend for Frontend), and why would you use one instead of a single generic gateway?

A BFF is a gateway variant tailored to one client type's needs — aggregating and shaping responses for, say, a mobile app, instead of exposing one generic contract that has to satisfy mobile, web, and third-party consumers at once. Reach for it when different client types need meaningfully different data shapes from the same underlying services, and a one-size-fits-all gateway is forcing compromises on all of them.

---

## Where should authentication actually happen — the gateway, or each service?

The gateway verifies the token/identity once, at the edge, and forwards trusted identity claims downstream (e.g. `X-User-Id`) so services don't redundantly re-verify a JWT on every internal call. Authorization for *specific* actions (can this user delete *this* particular resource) often still needs to happen in the owning service, since only that service has the business context to make that specific ownership/permission decision.

---

# Common Mistakes

❌ Putting real business logic inside gateway configuration.

The gateway should route, authenticate, and enforce cross-cutting policy — not encode "if order status is X, do Y." That belongs in the owning service, or it becomes an unversioned, untested, hard-to-reason-about layer of hidden business rules.

---

❌ Under-provisioning or under-testing the gateway's own availability.

Since every request passes through it, an under-scaled or poorly-monitored gateway takes down every service behind it at once, even if all of them are individually healthy.

---

❌ Using an API Gateway for internal service-to-service traffic instead of a service mesh.

Adds an unnecessary extra hop and a shared bottleneck for traffic that's better served by a mesh's per-service sidecar model, which distributes the concern instead of centralizing it for traffic that doesn't need a single edge.

---

❌ Trusting forwarded identity headers without locking down network access to the services behind the gateway.

If a service can be reached directly, bypassing the gateway, then trusting an `X-User-Id` header without independent verification becomes a spoofable authentication bypass. The trust model only holds if the network genuinely prevents anything from reaching internal services except through the gateway.

---

# Key Takeaways

- An API Gateway exists to give clients one stable entry point while the internal service topology behind it changes freely over time.
- It centralizes cross-cutting concerns — auth, rate limiting, routing, TLS termination, logging — that would otherwise be duplicated and drift out of sync across every individual service.
- A gateway operates at the application layer (understands routes, auth, request shape); a load balancer typically just distributes traffic across instances — they're complementary, not competing.
- Gateways handle north-south (external-to-internal) traffic; service meshes handle east-west (internal-to-internal) traffic — large systems often run both.
- A BFF is a gateway tailored to one specific client type's data needs, useful when mobile, web, and third-party consumers need meaningfully different shapes of the same data.
- Because every request passes through it, the gateway must be engineered and scaled with the same seriousness as any single-point-of-failure tier — horizontally scaled, multi-zone, aggressively health-checked.
