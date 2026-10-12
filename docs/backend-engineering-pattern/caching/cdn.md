# CDN (Content Delivery Network)

# Why Does a CDN Exist?

Every other cache in this section — Redis, an in-process local cache — sits close to your application server, in the same data center. That solves the "how fast can my backend produce this data" problem. It does nothing for a completely separate cost: the physical distance between your one origin server and a user on the other side of the planet.

```
Origin server: Virginia, USA

User in Mumbai requests a product image

↓

Request travels ~13,000 km to Virginia and back, at the speed of light
through undersea cables and internet infrastructure

↓

Even in a perfect world with zero server processing time,
that round trip alone takes over 100ms — physics, not a bug
```

No amount of backend optimization fixes this — the data has to physically travel a real distance, and light (which network signals approximate but never beat) only moves so fast. A CDN's answer: stop making every user's request travel all the way to one origin server. Instead, cache the content at many locations physically close to users all over the world, so most requests never have to make that long trip at all.

```
Without a CDN:                     With a CDN:

User (Mumbai) → Origin (Virginia)   User (Mumbai) → Edge server (Mumbai)
                                                        ↓ (cache miss, rare)
                                                     Origin (Virginia)
```

---

# What Problem It Actually Solves

- **Latency from physical distance** — serving content from an edge location near the user instead of one distant origin.
- **Origin server load** — the vast majority of requests for cacheable content (images, JS, CSS) never reach the origin at all once the edge cache is warm.
- **Traffic spike absorption** — a sudden burst of requests for the same popular content hits distributed edge servers, not one origin server that would otherwise need to be sized for worst-case global peak load.
- **A side benefit worth knowing:** CDNs sit in front of the origin for *every* request, which makes them a natural place to absorb and filter malicious traffic (DDoS mitigation) before it ever reaches your actual infrastructure.

---

# How It Works

```
1. A CDN operates many edge locations ("Points of Presence")
   distributed geographically around the world

2. DNS resolution routes a user to the nearest (or best-performing) edge location

3. Edge server checks its own cache:

     HIT   →  serve directly from the edge, done
     MISS  →  fetch from the origin server, cache it at the edge,
               THEN serve it — subsequent nearby users get a HIT
```

```
First user in Mumbai requests /logo.png

↓ MISS at Mumbai edge → fetches from origin in Virginia (slow, once)

↓ Mumbai edge now has /logo.png cached

Every subsequent user near Mumbai → HIT at the edge (fast, no trip to Virginia)
```

The first request for any given piece of content from any given region pays the full origin round trip. Every request after that, from anywhere near that same edge location, gets served locally — which is exactly why CDNs are most valuable for content requested repeatedly by many users, not content that's genuinely unique per request.

---

# Cache-Control Headers — The Actual Mechanism

The origin server tells the CDN (and the browser) how to cache a response using standard HTTP headers — this is the real, standardized mechanism underneath everything described above.

```http
Cache-Control: public, max-age=3600
```

```
public       →  cacheable by ANY cache (browser, CDN, any intermediate proxy)
private      →  cacheable only by the end user's own browser, NOT a shared CDN
                 (critical for anything personalized or sensitive)
no-cache     →  can be cached, but must be revalidated with the origin before
                 being served (not "don't cache," despite the name)
no-store     →  never cache this, anywhere, period
max-age       →  how long (seconds) this response is fresh for
```

## `max-age` vs `s-maxage`

```http
Cache-Control: public, max-age=60, s-maxage=3600
```

`max-age` applies to any cache, including the end user's own browser. `s-maxage` applies specifically to shared caches — a CDN — and overrides `max-age` for that layer when present. This split exists for a real, common reason: you might want a user's own browser to revalidate frequently (`max-age=60`, catching changes quickly for that one user) while letting the CDN hold onto its copy far longer (`s-maxage=3600`, since the CDN serves the same cached response to potentially millions of different users, and refreshing it too often would defeat much of the benefit of caching at the edge at all).

## `stale-while-revalidate`

```http
Cache-Control: public, max-age=60, stale-while-revalidate=300
```

The exact pattern from the Cache Stampede chapter, standardized as an HTTP directive — once the `max-age` window passes, the CDN can keep serving the (now stale) cached response immediately for up to another 300 seconds while it revalidates with the origin in the background, rather than making every request during that window wait on a synchronous origin fetch.

---

# Purging (Invalidating) a CDN Cache

This is the Cache Invalidation chapter's core problem, made structurally harder by the CDN's own defining feature — geographic distribution.

```
Invalidating a local Redis key:  ONE operation, against ONE in-memory store,
                                  effectively instant

Invalidating a CDN's cached copy of a URL:  needs to reach potentially
                                             hundreds of edge locations
                                             around the world
```

```
POST /purge
{ "url": "https://cdn.example.com/logo.png" }

↓

Purge request propagates out to edge locations globally

↓

Propagation isn't instantaneous — depending on the CDN, this can take
anywhere from a few seconds to (for some providers/configurations)
significantly longer
```

This is precisely why a well-chosen `max-age` and a deliberate versioning strategy for cacheable assets (covered next) matter more for CDN-cached content than for a local cache you can invalidate near-instantly — a mistake here is live, visibly wrong, and slow to fully correct across every edge location simultaneously.

## Cache-Busting via Versioned URLs

```html
<!-- instead of relying on a purge to update a cached asset -->
<script src="/app.js?v=42"></script>
<script src="/app.a3f9c2.js"></script>   <!-- hash-based filename -->
```

Rather than purging an old cached URL, ship the *new* content under a brand-new URL (a version number or content hash baked into the filename). The old URL's stale cached copy simply becomes irrelevant — nobody references it anymore — and can be given an extremely long `max-age` (since its content, by construction, never changes once published) without any invalidation coordination needed at all. This sidesteps CDN purge propagation delay entirely for the most common case: shipping a new version of a static asset.

---

# Dynamic Content at the Edge

CDNs historically only cached static assets (images, JS, CSS) — genuinely identical for every user. Modern CDNs increasingly cache (and even compute) dynamic, personalized-adjacent content too, using the same `Cache-Control` mechanics plus edge compute platforms (Cloudflare Workers, Lambda@Edge) that run actual application logic at the edge location itself, close to the user, rather than only serving pre-cached static files.

```
Static asset      →  identical for every user → cache directly, long max-age

Personalized page →  different per logged-in user → typically NOT cached at
                       a shared CDN layer (private, or no-store) —
                       but the EDGE COMPUTE platform can still run
                       personalization logic physically close to the user,
                       even without caching the final output
```

The line between "a CDN" and "a globally distributed compute platform" has blurred considerably as a result — but the underlying caching mechanics (headers, purge propagation, versioned URLs) remain the same regardless of how sophisticated the edge logic sitting alongside the cache becomes.

---

# Real-World Examples

### Cloudflare / Fastly / Akamai

The major CDN providers, all built around the same core mechanics described here — edge caching driven by standard `Cache-Control` headers, purge APIs with real (if usually short) propagation delay, and increasingly, edge compute platforms layered on top of the caching infrastructure.

---

### AWS CloudFront + S3

A common pattern for serving static assets (images, videos, downloadable files) — S3 as the durable origin store, CloudFront as the CDN layer in front of it, with cache behaviors and TTLs configured per path or file type.

---

### Video Streaming (Netflix, YouTube)

CDN edge caching is foundational to how video streaming works at global scale at all — video content is enormous, requested repeatedly by huge numbers of users, and extremely latency-sensitive (buffering is immediately noticeable) — exactly the profile of content a CDN is built to serve well.

---

# Common Interview Questions

## How does a CDN actually reduce latency?

By serving content from an edge location physically close to the user instead of routing every request to one distant origin server — the physical distance a signal has to travel is the dominant source of latency for geographically distant requests, and no backend optimization can shrink that distance; only serving from somewhere closer can.

---

## What's the difference between `max-age` and `s-maxage`?

`max-age` applies to any cache, including the end user's own browser. `s-maxage` applies specifically to shared caches (a CDN) and overrides `max-age` at that layer — commonly used to let a CDN hold a cached response far longer than an individual user's browser would, since the CDN serves the same cached copy to many different users at once.

---

## Why is purging a CDN cache harder than invalidating a local application cache?

Because a CDN's whole value proposition is distributing cached copies across many geographically separate edge locations — a purge has to propagate to all of them, which takes real, non-zero time, unlike a single `DELETE` against one local in-memory store. This is exactly why deliberate `max-age` choices and cache-busting via versioned URLs matter more here than for a cache you can invalidate near-instantly.

---

## What is cache-busting, and why is it often preferred over purging?

Shipping new content under a brand-new URL (a version number or content hash in the filename) instead of updating content at an existing, already-cached URL. The old URL's cache becomes irrelevant rather than needing to be actively purged, and the new URL can be treated as immutable with an extremely long `max-age`, since by construction its content will never change once published — sidestepping CDN purge propagation delay entirely.

---

## Would you ever cache dynamic, personalized content at a CDN?

Generally not at the shared CDN cache layer itself — personalized content is typically marked `private` or `no-store` specifically because it shouldn't be served to a different user than the one it was generated for. Modern CDNs address the latency problem for dynamic content differently, via edge compute platforms that run application logic physically close to the user, rather than trying to cache genuinely per-user output at a shared layer.

---

# Common Mistakes

❌ Marking personalized or sensitive content as `public` in `Cache-Control`.

A shared CDN cache could then serve one user's personalized (or sensitive) response to a completely different user — a real security/privacy leak, not just a caching inefficiency.

---

❌ Assuming a CDN purge is instantaneous everywhere.

Propagation across many geographically distributed edge locations takes real time — treating a purge as an instant fix for urgently wrong cached content can be a costly assumption during an incident.

---

❌ Not setting `Cache-Control` headers deliberately, and relying on CDN default behavior.

Under-caching wastes the CDN's entire benefit for content that's genuinely safe to cache long-term; over-caching can serve stale or, worse, incorrect content to users for far longer than intended.

---

❌ Updating content at an existing cached URL instead of using a versioned URL for static assets.

Forces you to rely on purge propagation (with its real, non-zero delay) instead of sidestepping the invalidation problem entirely by simply shipping new content under a new, immutable URL.

---

# Key Takeaways

- A CDN solves the latency cost of physical distance between an origin server and a geographically distant user — by caching content at edge locations near users, most requests never have to travel to the origin at all.
- `Cache-Control` headers (`public`/`private`, `max-age`, `s-maxage`, `stale-while-revalidate`) are the real, standardized mechanism controlling how a CDN (and a browser) cache a response.
- `s-maxage` lets a CDN cache a response far longer than an individual browser would, since the CDN serves the same cached copy to many different users at once.
- Purging a CDN cache is inherently slower than invalidating a local cache, because it has to propagate across many geographically distributed edge locations — versioned, cache-busted URLs for static assets sidestep this entirely by making the old cached copy simply irrelevant rather than something that needs active purging.
- Personalized or sensitive content should generally never be marked cacheable by a shared CDN layer — modern CDNs address dynamic content's latency problem via edge compute instead, not by caching per-user output.
