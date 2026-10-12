# GraphQL

# Why Does GraphQL Exist?

Facebook built GraphQL around 2012 for a very specific, very painful problem: the News Feed on their mobile app.

A single feed screen needs data shaped like this:

```
Post
├── author (name, profile picture)
├── text
├── photos
├── like count
├── top 3 comments
│   └── each comment's author
└── whether the current user has liked it
```

With a REST API modeled around resources, assembling that one screen looked like this:

```
GET /posts/101
GET /posts/101/author
GET /posts/101/photos
GET /posts/101/comments?limit=3
GET /users/55, /users/56, /users/57   (comment authors)
```

Five or six round trips, on a mobile network, to render one screen — and this was the actual, specific, expensive problem Facebook was solving, not a hypothetical one.

Worse, even a single one of those REST calls tends to **over-fetch**. `GET /posts/101` returns every field on a post — timestamps, internal flags, edit history — when the feed screen only needed three of them. Meanwhile the same endpoint **under-fetches** relative to what the screen actually needs, because comments and author details live on separate resources entirely.

GraphQL's answer: instead of the server deciding what shape each endpoint returns, the **client** describes exactly what it needs, in one request, and the server returns exactly that shape — no more, no less.

```graphql
query {
  post(id: 101) {
    text
    author { name, profilePicture }
    photos { url }
    likeCount
    comments(limit: 3) {
      text
      author { name }
    }
  }
}
```

One request. One response, shaped exactly like the query. No over-fetching, no under-fetching, no assembling five calls into one screen on the client.

---

# What Problem It Actually Solves

- **Over-fetching** — a client that needs 3 fields no longer receives the entire object.
- **Under-fetching** — a client that needs data from four related resources gets it in one round trip instead of four.
- **Client-driven shape** — different clients (a mobile app showing a compact card, a web dashboard showing a detailed view) can each ask for exactly what they need from the *same* underlying schema, without the backend needing a separate endpoint per client variant.
- **Schema as a contract with introspection** — the entire graph of types is discoverable and typed, which is what powers autocomplete-driven tools like GraphiQL and strong client-side codegen.

---

# Core Concepts

## Schema

The single source of truth for what data exists and how it relates — defined once, in a strongly-typed schema definition language.

```graphql
type Post {
  id: ID!
  text: String!
  author: User!
  photos: [Photo!]!
  likeCount: Int!
  comments(limit: Int): [Comment!]!
}

type User {
  id: ID!
  name: String!
  profilePicture: String
}
```

`!` means non-nullable — the schema itself documents exactly what a client can rely on always being present, which is a stronger contract than most REST APIs bother to formalize.

## Queries, Mutations, Subscriptions

```graphql
# Read
query {
  post(id: 101) { text }
}

# Write
mutation {
  likePost(postId: 101) {
    likeCount
  }
}

# Real-time
subscription {
  commentAdded(postId: 101) {
    text
    author { name }
  }
}
```

Everything — reads and writes — goes through a single endpoint, typically `POST /graphql`, with the query itself, not the URL, describing the operation.

## Resolvers

Each field in the schema is backed by a resolver function — the actual code that fetches that specific piece of data.

```python
def resolve_post(_, info, id):
    return db.get_post(id)

def resolve_author(post, info):
    return db.get_user(post.author_id)

def resolve_comments(post, info, limit=10):
    return db.get_comments(post.id, limit=limit)
```

GraphQL executes the query by walking the requested fields and calling the matching resolver for each one — which is exactly where the framework's most notorious performance trap lives.

---

# The N+1 Problem

This is the single most common GraphQL interview question, because it's the single most common real GraphQL production bug.

```graphql
query {
  posts {
    text
    author { name }
  }
}
```

A naive resolver implementation:

```python
def resolve_posts(_, info):
    return db.get_posts()  # 1 query — fetches, say, 50 posts

def resolve_author(post, info):
    return db.get_user(post.author_id)  # 1 query, called ONCE PER POST
```

```
1 query to fetch 50 posts

+ 50 separate queries, one per post, to fetch each author

= 51 queries total, to render one screen
```

This is the "N+1" — one query for the parent list, plus N more queries, one per child, executed independently because each resolver has no idea the sibling resolvers exist or what they're about to ask for.

## The Fix: Batching (DataLoader)

The standard solution is to batch and deduplicate the individual lookups within a single request tick, instead of firing them immediately one at a time.

```python
from collections import defaultdict

class UserLoader:
    def __init__(self):
        self._pending_ids = set()
        self._cache = {}

    def load(self, user_id):
        self._pending_ids.add(user_id)
        return self._resolve_later(user_id)  # returns a deferred/promise-like value

    def _batch_fetch(self):
        ids = list(self._pending_ids)
        users = db.get_users_by_ids(ids)  # ONE query for all pending IDs
        self._cache.update({u.id: u for u in users})
        self._pending_ids.clear()
```

```
50 posts trigger 50 calls to loader.load(author_id)

↓

Instead of firing immediately, IDs are collected across the tick

↓

ONE batched query: SELECT * FROM users WHERE id IN (id1, id2, ..., id50)

↓

Result: 1 query for posts + 1 batched query for all authors = 2 total
```

This is exactly what the `DataLoader` pattern (originally from Facebook, ported into essentially every GraphQL server library) does automatically — it's not optional infrastructure, it's close to mandatory for any GraphQL API with nested relationships and real traffic.

---

# Trade-offs

## Caching Is Genuinely Harder

REST's `GET /posts/101` is a stable, cacheable URL — a CDN or browser cache can key on it directly. GraphQL's single `POST /graphql` endpoint, with a different query body every time, has no natural URL-based cache key at all.

```
REST:     GET /posts/101              →  cache key: the URL itself

GraphQL:  POST /graphql               →  same URL, different body every time
          { query: "{ post(id:101){text} }" }
```

Real GraphQL systems solve this with normalized client-side caches (Apollo Client, Relay, keyed by each object's `id` + `__typename`) and, on read-heavy public APIs, **persisted queries** — the client sends a hash of a pre-registered query instead of the full query text, which restores a stable, cacheable identifier per query shape.

## No HTTP Status Code Semantics

A GraphQL error — even "you don't have permission" or "that post doesn't exist" — is typically still returned with `200 OK`, with the actual error described inside the response body.

```json
{
  "data": { "post": null },
  "errors": [
    { "message": "Post not found", "path": ["post"] }
  ]
}
```

This surprises engineers coming from REST, where status codes carry real meaning that infrastructure (caching, monitoring, retries) can act on automatically. GraphQL deliberately gives that up in exchange for being able to return **partial** results — some fields successfully resolved, others errored — in a single response, which a strict all-or-nothing HTTP status code can't represent.

## Query Complexity Is an Attack Surface

Because the client controls the shape of the query, nothing stops a malicious or careless client from writing something like this:

```graphql
query {
  posts {
    comments {
      author {
        posts {
          comments { author { posts { ... } } }
        }
      }
    }
  }
}
```

A deeply nested query can force the server to do an enormous, exponentially-growing amount of work from one small request body. Production GraphQL servers defend against this with **query depth limiting** and **query cost analysis** (assigning a computed "cost" to a query before executing it, and rejecting anything over a budget) — this is not optional hardening, it's a baseline requirement before exposing GraphQL publicly.

## No Versioning, By Design

GraphQL's official guidance is to never version the schema at all — only add new fields and types, and mark old ones `@deprecated` rather than removing them.

```graphql
type Post {
  text: String!
  legacyBody: String @deprecated(reason: "Use `text` instead")
}
```

Because clients explicitly request only the fields they want, adding new fields never breaks an existing client — it's structurally the same "additive-only evolution" strategy discussed in API versioning, except GraphQL's query model makes it close to automatic rather than a discipline you have to enforce by hand.

---

# Real-World Examples

### GitHub GraphQL API (v4)

GitHub runs both a REST API (v3) and a GraphQL API (v4) side by side — GraphQL specifically for cases where a client needs to assemble data from many related resources (a repo, its issues, its pull requests, and their authors) in one request instead of a dozen REST calls.

---

### Shopify Storefront API

Shopify exposes its entire product catalog, cart, and checkout data through GraphQL specifically because storefronts built by different merchants need wildly different subsets and shapes of the same underlying product data — exactly the "different clients, same schema, different needed shape" problem GraphQL was built for.

---

### Facebook

The original motivating case — assembling a News Feed screen's deeply nested, per-post data (author, photos, comments, like status) in one request instead of the cascade of REST calls it used to take.

---

# Common Interview Questions

## REST vs GraphQL — when would you actually choose GraphQL?

When clients have genuinely different data-shape needs from the same underlying resources (mobile vs web vs third-party), or when a screen requires assembling deeply nested, related data that would otherwise take many REST round trips. It's a worse fit when you need strong HTTP-level caching, simple public CRUD semantics, or a team without the operational maturity to guard against expensive/malicious queries.

---

## What is the N+1 problem, and how do you solve it?

A naive resolver fetches a list (1 query), then independently fetches a related field for each item in that list (N more queries) — 51 queries to render 50 posts with their authors, instead of 2. The fix is batching: a `DataLoader`-style layer that collects all the individual lookups requested within one execution tick and issues one batched query (`WHERE id IN (...)`) instead of firing them one at a time.

---

## Why is GraphQL harder to cache than REST?

REST's per-resource URLs give a CDN or browser a natural, stable cache key. GraphQL's single endpoint with a varying request body has no equivalent — solved in practice with normalized client-side caching (keyed by object ID) and persisted queries (a hash standing in for the full query text) to restore a stable cache key per query shape.

---

## Why does GraphQL usually return 200 even on errors?

Because a single query can partially succeed — some fields resolve, others fail — and a single HTTP status code can't represent "half of this worked." Errors are instead described inside the response body alongside whatever data did resolve successfully, which trades away HTTP-level error semantics in exchange for genuinely partial responses.

---

## How do you prevent a malicious or careless client from sending an extremely expensive query?

Query depth limiting (reject queries nested beyond N levels) and query cost analysis (assign each query a computed cost before executing it, based on field counts and expected result sizes, and reject anything over budget). Without either, the client fully controls how much work the server does per request — a direct denial-of-service vector if left unguarded.

---

## How does GraphQL handle API evolution without versioning?

By convention, schemas only grow — new fields and types are added, and old ones are marked `@deprecated` rather than removed, following the same additive-only philosophy as REST APIs that avoid explicit versioning. Because clients only ever request the specific fields they ask for, adding new ones is inherently non-breaking.

---

# Common Mistakes

❌ Writing naive nested resolvers without batching.

The N+1 problem isn't a rare edge case — it's the default behavior of any resolver with a relationship, the moment there's more than a handful of rows involved.

---

❌ Exposing the full schema publicly with no query cost limits.

Turns "how expensive can one request be?" entirely over to whoever's calling your API — an open invitation for accidental or deliberate denial-of-service.

---

❌ Assuming GraphQL is a strict upgrade over REST in every situation.

It solves a specific problem (flexible, client-shaped data fetching across relationships) at the cost of HTTP-level caching and status-code semantics. A simple public CRUD API with no complex nested relationships often has less to gain from GraphQL than the added operational complexity costs.

---

❌ Treating `200 OK` with an `errors` array as "nothing went wrong."

Client code that only checks the HTTP status and never inspects the `errors` field will silently swallow real failures.

---

# Key Takeaways

- GraphQL exists to solve over-fetching and under-fetching — the client specifies exactly the shape of data it needs, across related resources, in a single request.
- The N+1 problem is the framework's signature production pitfall — naive resolvers issue one query per related field per item; batching (`DataLoader`) collapses that into one query per relationship per request.
- Caching is genuinely harder than REST because there's no per-resource URL — solved via normalized client caches and persisted queries, not for free.
- Errors typically return `200 OK` with error detail in the response body, because a single query can partially succeed — client code must check the `errors` field explicitly.
- Query depth/cost limits are not optional hardening for a public GraphQL API — without them, the client controls how expensive each request is to serve.
- GraphQL schemas evolve by convention through additive-only changes and `@deprecated` markers rather than explicit versioning.
