# REST APIs

Imagine you're the tenth engineer to join a company. Four different teams built four different parts of the product, and each team needed an endpoint to create a user.

Team A wrote `POST /createUser`. Team B wrote `POST /registerUser`. Team C wrote `POST /addUser`. Team D wrote `POST /saveUser`.

They all do the exact same thing. But now every client — mobile app, frontend, third-party integrator — has to memorize four different naming conventions for one operation. Multiply that across every feature in the company (create, update, delete, approve, cancel, refund...) and you get an API surface that nobody can predict without reading the docs every single time.

This is the actual problem REST solves. It's not about JSON, and it's not some academic ivory-tower idea — it's a naming discipline that makes APIs predictable.

## The one shift in thinking

Here's the trick: stop thinking about the *actions* your API needs to expose, and start thinking about the *things* your system manages.

Your system manages users, orders, products, payments. Those are **resources** — nouns. Every resource gets one URL. What you *do* to that resource is expressed by the HTTP method, not by inventing a new endpoint name.

```
POST   /users        → create a user
GET    /users/42      → read user 42
PATCH  /users/42      → update user 42
DELETE /users/42      → delete user 42
```

Notice the URL never changes. Only the verb does. That's the entire insight. Once you get this, you can predict 90% of any well-designed REST API without ever opening its docs — if you know `/products` works this way, you already know how `/orders` and `/invoices` work too. That's the whole value proposition, and it's why REST won over the alternatives, which brings us to what REST actually replaced.

## Why this wasn't always the default

Before REST, distributed systems mostly talked using SOAP, XML-RPC, or CORBA. The mental model there was: calling a remote server should feel just like calling a function in your own code.

```
createUser()
approvePayment()
cancelOrder()
```

Seems reasonable on paper. But a network call is *not* a function call, no matter how much you disguise it as one. A function call never times out, never partially fails, never needs a retry, never hits a version mismatch between caller and callee. A network call does all of those things, constantly. Pretending otherwise just meant these RPC-style systems ended up brittle — tightly coupled, painful to version, and (in SOAP's case) buried under verbose XML contracts that were miserable to debug.

Roy Fielding's insight, in his 2000 dissertation, was almost anti-climactic: the web had *already* solved this problem, at a scale of billions of clients and servers, using plain HTTP. Nobody needed to invent a new protocol. They just needed to actually use HTTP the way it was designed. That architectural discipline is what we now call REST.

## The principles — and why each one earns its place

It's easy to memorize "REST is: resource-based, stateless, uniform interface, client-server separation" as a flashcard. It's much more useful to know what breaks if you violate each one.

**Resource-based.** If you catch yourself writing `POST /approveOrder`, stop — you're modeling an action, not a resource. The REST version is `PATCH /orders/42` with a body that flips the order's status from `PENDING` to `APPROVED`. The order is the resource; approval is just a state change on it. This discipline is what stops your API surface from growing one bespoke endpoint per new feature forever.

**Stateless.** Every single request has to carry everything the server needs to handle it — auth token, parameters, all of it. The server isn't allowed to "remember" your last request. Why does this matter so much? Because it's the only reason horizontal scaling is simple. If the server had to remember you, you'd need sticky sessions — every request from you would have to be routed to the *same* server, which defeats the point of a load balancer spreading traffic across ten machines. Statelessness means any of your ten servers can pick up any request, at any time, and nothing breaks.

One honest caveat here: if your API uses server-side sessions for auth, you've technically already broken statelessness, since the server is storing state about you. JWTs are the "purer" way to do this. But plenty of production systems use sessions anyway, because it's simpler to build — and REST purity loses to shipping working software more often than textbooks admit.

**Uniform interface.** This is really just the payoff of resource-based design. Once you've learned how `/users` behaves, you already know how `/products` and `/orders` behave. A new engineer joining your team shouldn't need a meeting to learn how to hit a new endpoint — they should be able to guess it correctly.

**Client-server separation.** The frontend only needs to agree with the backend on one thing: the shape of the contract (URLs in, JSON out). The backend team can rewrite their service in Go tomorrow, and the mobile app doesn't need to know or care. This is what let REST become the default for public APIs used by clients you don't control at all — you're making a promise about a URL and a JSON shape, not about your internal implementation.

## The part that actually bites people in production: idempotency

Here's a scenario. A customer is checking out. Their phone loses signal for two seconds right as `POST /payments` goes out. The client, doing the responsible thing, retries the request.

Question: did the customer just get charged once, or twice?

The honest answer is — it depends entirely on whether *you* designed for this, because REST does not protect you here automatically. This is the idea of idempotency: an operation is idempotent if calling it once has the exact same effect as calling it five times.

```
GET     → idempotent (reading never changes anything)
PUT     → idempotent (replacing with the same data twice = same end state)
DELETE  → idempotent (it's gone either way)
PATCH   → not guaranteed idempotent
POST    → not idempotent
```

`DELETE /orders/101` called once or five times — the order is deleted either way, no different outcome. But `POST /payments` called twice creates two payments, full stop, because POST's entire job is "make a new thing," and the server has no built-in way of knowing your second request is a *retry* of the first one rather than a brand new charge.

This is exactly why Stripe (and every serious payments API) makes you send an `Idempotency-Key` header alongside `POST /payments`. The server remembers "I've already processed this exact key" and just replays the original response instead of charging the card again. It's a deliberate, manual fix the API designer has to build — REST gives you zero of this for free. If you take one thing from this whole document into an interview, make it this one, because it's the difference between someone who's memorized the theory and someone who's actually shipped payment infrastructure.

## Status codes are a contract, not decoration

Picture debugging a production incident at 2am. Every request in your logs shows `200 OK`. Your monitoring dashboard is green. Your load balancer thinks everything is fine. Except users are furious because half their requests are silently failing — because some engineer decided to always return `200` and bury the real error inside the JSON body:

```json
{ "status": "error", "message": "User not found" }
```

This is the single most common way people quietly sabotage their own REST API. Every piece of infrastructure sitting between your server and the client — caches, monitoring tools, retry logic, API gateways — inspects the HTTP status line, not the body. Lie about the status code, and all of that tooling becomes useless without extra custom parsing.

The fix is just: use the status code that matches what actually happened.

| Code | What it means | You'd see it when |
|---|---|---|
| 200 | OK | Normal success |
| 201 | Created | `POST /users` worked |
| 204 | No Content | `DELETE` succeeded, nothing to send back |
| 400 | Bad Request | Malformed JSON |
| 401 | Unauthorized | Token missing/expired |
| 403 | Forbidden | Valid user, wrong permissions |
| 404 | Not Found | `GET /users/999999` |
| 409 | Conflict | Signup with an email that already exists |
| 422 | Unprocessable Entity | Valid JSON, invalid data (negative price) |
| 429 | Too Many Requests | Rate limit hit |
| 500 | Internal Server Error | You broke something |

## Pagination: why "just use offset and limit" stops working

`GET /orders?limit=20&offset=40` is the first thing everyone reaches for, and it's fine — until your table has ten million rows and someone requests `offset=9000000`. The database still has to count through nine million rows to know where to start. It also silently corrupts itself if rows are being inserted or deleted while someone's paging through — page 2 might repeat rows from page 1, or skip some entirely.

Cursor-based pagination fixes both problems by encoding a *position* instead of a *count* — usually "the last ID you saw":

```http
GET /orders?limit=20&cursor=eyJpZCI6MTAwfQ==
```

The database can jump straight to "give me the next 20 after this ID" without counting anything, and it stays correct even while the underlying data keeps changing. This is exactly why GitHub, Stripe, and Slack all standardized on cursors for anything that can grow large — it's not a preference, it's the only approach that doesn't degrade at scale.

## Versioning: the tension between "correct" and "usable"

Your API is live, third parties depend on it, and now you need to make a breaking change. Two camps exist:

- **URI versioning** — `GET /v1/users/42` vs `/v2/users/42`. Dead simple, visible in every log line, and caches happily key on it. Stripe and Twitter both do this.
- **Header versioning** — `GET /users/42` with `Accept: application/vnd.myapi.v2+json`. The "more correct" REST purist answer, because a resource's identity (its URL) shouldn't change just because you added a field. But it's genuinely harder to test by hand, and clients forget to send the header constantly.

Almost everyone picks URI versioning in practice, for the same reason sessions beat JWTs in a lot of real systems: operational simplicity wins over theoretical correctness.

## When REST isn't the answer

REST is the default, not the only tool. If a mobile app needs data assembled from five different resources in one screen, REST forces five round trips — that's under-fetching, and it's exactly the problem GraphQL exists to solve. If two internal microservices need a strict typed contract and minimal latency, gRPC beats REST because it isn't fighting HTTP's generality. And if you need a persistent live connection — chat, live scores, trading data — REST's request/response model isn't built for that; WebSockets are.

None of these tools replaced REST. They each solve a specific gap REST leaves open, which is exactly why all of them coexist in most real systems today.

## If someone asks you to explain REST in one breath

*"REST is an architectural style, not a protocol — HTTP is the protocol. It says: model your system as resources, identify each one with a URL, and use HTTP methods to describe what you're doing to it, instead of inventing a new endpoint name for every action. Do that consistently and statelessly, and you get an API that's predictable, scales horizontally without effort, and works with every caching and monitoring tool already built for HTTP."*

If you can say that sentence and then immediately explain why POST isn't idempotent and why that matters for payments — you're not reciting REST, you understand it. That's the actual bar.

## Fast-recall table for interviews

| Question | Answer |
|---|---|
| PUT vs PATCH? | PUT replaces the whole resource; PATCH updates part of it |
| Is REST really stateless with sessions? | No — sessions store server state; JWTs are the purer fit |
| Why does idempotency matter? | Determines if a retried request is safe or causes duplicates |
| How to version a public API? | URI versioning in practice; header versioning is "cleaner" |
| Does anyone use HATEOAS? | Barely — mostly matters for long-lived public APIs, not internal ones |
| REST vs GraphQL vs gRPC? | REST for public CRUD, GraphQL to avoid over/under-fetching, gRPC for internal low-latency typed calls |
