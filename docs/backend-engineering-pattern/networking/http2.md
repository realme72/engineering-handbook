# HTTP/2

# Why Does HTTP/2 Exist?

HTTP/1.1's head-of-line blocking forced browsers into a wasteful workaround — opening several parallel TCP connections to the same host (about six, typically) just so one slow response wouldn't block faster ones queued behind it. Every extra connection pays its own handshake and slow-start cost, purely to route around a limitation in how HTTP/1.1 handles concurrent requests.

```
HTTP/1.1's workaround:  open MORE connections to avoid blocking
                        on any single one — wasteful, but effective

HTTP/2's actual fix:    solve head-of-line blocking directly, at
                        the HTTP layer, so a SINGLE connection can
                        handle many concurrent requests without
                        one slow response blocking the others
```

HTTP/2 makes that workaround unnecessary — genuine concurrency over one connection, instead of faking it with several.

---

# Multiplexing

The core mechanism: requests and responses get broken into small units called frames, each tagged with a stream ID, and interleaved over a single TCP connection. Reassembled on the other end based on which stream each frame belongs to.

```
Single TCP connection:

Frame (stream 1) → Frame (stream 3) → Frame (stream 1) → Frame (stream 2) → ...

↓

Reassembled at the receiver:

Stream 1: [complete response]
Stream 2: [complete response]
Stream 3: [complete response]
```

```
HTTP/1.1:  Request A ──wait for full response──► Request B ──wait──► Request C
           (strictly sequential per connection, or parallel connections needed)

HTTP/2:    Request A, B, C all in flight SIMULTANEOUSLY, interleaved as
           frames on ONE connection — a slow response for A doesn't
           block B and C's frames from being delivered and processed
```

This actually solves HTTP-level head-of-line blocking. A slow response no longer blocks faster ones behind it, since there's no longer a "responses must return in request order" rule — each stream just progresses independently.

---

# Header Compression (HPACK)

Requests and responses carry a lot of repetitive header data — cookies, user-agent strings, accept headers — nearly identical across many requests to the same host. HPACK compresses this with a shared, evolving table both sides maintain, so repeated headers don't get resent as full text every time.

```
Request 1 headers: full text sent, AND added to a shared
                    compression table both sides maintain

Request 2 headers: if identical (or similar) to Request 1's,
                    reference the shared table instead of
                    resending the same bytes again
```

Since multiplexing encourages keeping one connection open for a lot of requests to the same host, this adds up to a real bandwidth savings over HTTP/1.1's habit of resending near-identical headers on every request.

---

# Server Push — And Why It's Mostly Gone

HTTP/2 let a server proactively send resources a client hadn't asked for yet — if a client requested an HTML page, the server could guess it would also need the linked CSS and JS and push them ahead of time.

It didn't hold up well in practice. It fought with browser caching (pushing something the client already had cached just wasted bandwidth), and the real-world gains were inconsistent enough that major browsers eventually dropped support entirely. Worth knowing it existed — a good example of a well-intentioned feature that didn't survive contact with how caching actually works — not something to rely on today.

---

# What HTTP/2 Does *Not* Fix

Here's the nuance that sets up the next chapter: multiplexing fixes head-of-line blocking at the HTTP layer, but HTTP/2 still runs on top of TCP, and TCP's own head-of-line blocking is completely untouched.

```
HTTP/2 connection, multiplexing streams 1, 2, and 3

↓

A single TCP PACKET is lost — and that packet happens to contain
data belonging to stream 1

↓

TCP's own in-order delivery guarantee means EVERY stream sharing
this one TCP connection is blocked — not just stream 1 — because
TCP itself won't deliver ANY subsequent data on the connection
until the lost packet is retransmitted and arrives, regardless of
which HTTP/2 stream that data actually belongs to
```

There's a genuinely subtle twist here worth having ready in an interview: by concentrating many independent streams onto one shared TCP connection, HTTP/2 actually made TCP-level packet loss *more* costly than before — one lost packet now blocks every multiplexed stream on that connection, not just the single request HTTP/1.1's separate-connections approach would've affected. That's the exact gap HTTP/3 closes.

---

# Real-World Examples

### Virtually All Major Websites and CDNs

HTTP/2 support is close to universal — browsers, CDNs (Cloudflare, Fastly), major sites. It layers onto existing HTTPS infrastructure cleanly enough that adoption was straightforward, and the multiplexing win was big enough to make it the practical default rather than an optional upgrade.

---

### gRPC's Reliance on HTTP/2

Covered in the gRPC chapter — gRPC builds directly on HTTP/2 specifically to get multiplexing (many concurrent RPC calls over one connection) natively instead of reinventing it.

---

# Common Interview Questions

## How does HTTP/2 solve HTTP-level head-of-line blocking?

Multiplexing — requests and responses break into frames tagged with a stream ID and interleave over a single connection, so multiple requests are in flight at once without needing to return in strict order. A slow response no longer blocks faster ones behind it, since each stream progresses independently.

---

## What is multiplexing, precisely — is it the same as just using more parallel connections?

No. Multiplexing interleaves multiple logical streams over a single connection; HTTP/1.1's workaround used multiple separate connections instead. Multiplexing skips the overhead — handshake, slow start — of those extra connections, achieving concurrency within one instead of faking it with several.

---

## Does HTTP/2 completely eliminate head-of-line blocking?

No — only at the HTTP layer. It still runs on TCP, and TCP's strict in-order delivery means a single lost packet blocks every multiplexed stream sharing that connection, not just the one the lost data belonged to. That remaining gap is exactly what HTTP/3 was built to close.

---

## What is HPACK, and why does header compression matter for HTTP/2?

A compression scheme using a shared, evolving context between client and server, so repetitive headers don't get resent as full text every request. Since multiplexing encourages keeping one connection open for many requests to the same host, this adds up to real bandwidth savings over HTTP/1.1's habit of resending near-identical headers constantly.

---

## What happened to HTTP/2 Server Push?

Mostly deprecated or removed from major browsers. It fought with browser caching — pushing something the client already had wasted bandwidth — and its real-world benefit was inconsistent enough that the industry moved away from relying on it, despite it being part of the original spec.

---

# Common Mistakes

❌ Assuming HTTP/2 completely eliminates head-of-line blocking.

Only at the HTTP layer — TCP-level blocking remains, and multiplexing actually makes a single lost packet affect more streams at once than HTTP/1.1's separate-connections approach ever would have.

---

❌ Confusing multiplexing with simply opening more parallel connections.

Multiplexing interleaves frames from multiple streams over one connection — a genuinely different mechanism from HTTP/1.1's workaround of opening several TCP connections.

---

❌ Assuming HTTP/2 Server Push is still a commonly relied-upon feature.

Its benefit didn't hold up against real-world browser caching, and it's been deprecated or removed from major browsers — worth knowing it existed, not treating it as current best practice.

---

# Key Takeaways

- HTTP/2 eliminates HTTP-level head-of-line blocking through multiplexing — interleaving multiple requests' frames over one connection so a slow response can't block faster ones behind it.
- Multiplexing achieves this within a single connection, skipping the overhead HTTP/1.1's multiple-parallel-connections workaround pays for the same practical effect.
- HPACK's shared header-compression context meaningfully cuts the repetitive header overhead of many requests to the same host.
- HTTP/2 doesn't fix TCP-level head-of-line blocking — a lost packet still blocks every multiplexed stream on that connection, an even more consequential problem than under HTTP/1.1, and exactly the gap HTTP/3 closes.
- Server Push, part of the original spec, has largely fallen out of use due to poor interaction with browser caching and inconsistent real-world benefit.
