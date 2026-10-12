# HTTP

# Why Does HTTP Exist?

TCP gives you a reliable byte stream between two machines, but it has no idea what "a request" or "a response" even means — it's just an undifferentiated flow of bytes. HTTP is the structure layered on top, specifically for the "client asks, server responds" pattern — the protocol underneath essentially the entire web.

```
Raw TCP: just a stream of bytes

↓

HTTP defines STRUCTURE on top of that stream:

Request:   METHOD PATH HTTP-VERSION
           Headers
           (optional body)

Response:  HTTP-VERSION STATUS-CODE STATUS-TEXT
           Headers
           (optional body)
```

Without this shared structure, every client and server would need its own private agreement about how to talk. HTTP is what lets any client — a browser, curl, a mobile app — talk to any server with zero custom integration work.

---

# Request and Response Structure

```http
GET /products/15 HTTP/1.1
Host: example.com
Accept: application/json
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 128

{"id": 15, "name": "Wireless Mouse", "price": 25}
```

A request line, headers, an optional body. The response mirrors it. Same shape, covered in more depth from a design angle in the REST chapter — this is what every HTTP client and server agree on, regardless of language or framework.

---

# Statelessness

Each request stands alone. The protocol carries no memory of previous ones. Whatever "session" a web app appears to have is built on top of HTTP, not provided by it — usually a cookie carrying a session ID the server looks up on every request, covered in the Sessions and Cookies chapters. HTTP itself remembers nothing.

---

# HTTP/1.0 vs HTTP/1.1

## Persistent Connections

```
HTTP/1.0:  a NEW TCP connection for every single request
            (full three-way handshake, every time)

HTTP/1.1:  persistent connections by default (Connection: keep-alive)
            — the same TCP connection is reused for multiple
            sequential requests
```

Reusing a connection skips paying TCP's handshake (and slow-start ramp-up) on every request — a real performance win that HTTP/1.1 made the default instead of something you had to ask for.

## Pipelining — An Attempt That Mostly Failed in Practice

HTTP/1.1 also tried pipelining — sending several requests without waiting for each response, over one connection. Should've helped throughput. Barely used in practice, for the reason below.

---

# HTTP-Level Head-of-Line Blocking

The problem HTTP/2 was built to fix, and worth keeping separate in your head from TCP-level head-of-line blocking (from the TCP and UDP chapters) — related symptom, different layer.

```
Client sends Request 1, Request 2, Request 3 (pipelined, same connection)

↓

Responses MUST come back in the SAME ORDER requests were sent

↓

Request 1's response is SLOW to generate (e.g. a slow database query)

↓

Response 2 and Response 3 are ready and waiting, but CANNOT be
delivered yet — HTTP/1.1 requires responses on one connection to
arrive in request order, so they're stuck queued behind Response 1
```

Nothing's actually wrong with the underlying TCP connection here — this isn't a lost packet. It's HTTP/1.1's own rule that responses must return in request order, and that rule alone is enough to block fast responses behind a slow one.

## The Workaround Browsers Used

```
Browsers open MULTIPLE parallel TCP connections to the same host
(typically around 6) specifically to work around HTTP-level
head-of-line blocking — if one connection is stuck behind a slow
response, other requests can proceed on a different connection
```

It works, but it's wasteful — every extra connection pays its own handshake and slow-start cost, and there's a practical limit to how many are worth opening. That waste is the direct motivation for HTTP/2's multiplexing, covered in its own chapter.

---

# Real-World Examples

### Essentially the Entire Web

Browser requests, most API calls, most inter-service communication that isn't gRPC or something equally specialized — all HTTP. It's the default application-layer protocol for request/response over the internet.

---

### Browser Connection Limits as a Real, Observable Constraint

Open your browser's dev tools during a page load and you'll see several simultaneous connections to the same domain — the parallel-connections workaround, live and visible, shaping actual browser behavior.

---

# Common Interview Questions

## What's the difference between HTTP/1.0 and HTTP/1.1?

HTTP/1.1 made persistent connections the default — reusing one TCP connection across requests instead of opening a new one every time, which HTTP/1.0 did. Skips repeatedly paying the handshake and slow-start cost.

---

## What is HTTP-level head-of-line blocking, and how is it different from TCP-level head-of-line blocking?

HTTP-level blocking comes from HTTP/1.1's rule that responses on one connection must arrive in request order — a slow response blocks faster, already-ready ones queued behind it, purely because of that ordering rule. TCP-level blocking is a different problem, one layer down: a single lost packet blocks all subsequent data on the connection, even data that already arrived, because TCP guarantees strict in-order delivery. Same symptom, different cause, different layer.

---

## How did browsers work around HTTP/1.1's head-of-line blocking before HTTP/2?

By opening several parallel TCP connections to the same host — usually around six — so a slow response on one connection doesn't block requests going out on another. Works, but wastes resources, since every extra connection pays its own handshake and slow-start cost. Exactly what HTTP/2's multiplexing was built to eliminate.

---

## Why is HTTP considered stateless?

Because the protocol carries no memory between requests — each one is handled independently, with no built-in concept of a session. Anything that looks like a session (staying logged in) is built on top, usually via a cookie and server-side lookup, not something HTTP provides itself.

---

# Common Mistakes

❌ Confusing HTTP-level head-of-line blocking with TCP-level head-of-line blocking.

Same symptom, different cause — one's a protocol-level ordering rule about responses; the other's a lost packet blocking everything behind it at the transport layer.

---

❌ Assuming HTTP/1.1's pipelining feature is widely used in practice.

It's rarely used, precisely because it never solved head-of-line blocking — a slow response still blocks the faster ones queued behind it.

---

❌ Not recognizing that opening many parallel connections is a workaround, not a fix.

Each connection carries its own handshake and slow-start cost. It papers over the symptom without touching the root cause, which is exactly why HTTP/2 exists.

---

# Key Takeaways

- HTTP defines the request/response structure on top of TCP's raw byte stream, letting any client and server interoperate without a private agreement.
- HTTP/1.1 made persistent connections the default, skipping a fresh TCP handshake on every request — a real improvement over HTTP/1.0.
- HTTP-level head-of-line blocking — a slow response blocking faster ones behind it, because of HTTP/1.1's strict ordering rule — is a distinct problem from TCP-level head-of-line blocking, at a different layer.
- Browsers historically worked around this with multiple parallel connections per host — real, but wasteful, and exactly the gap HTTP/2 was built to close.
- HTTP itself is stateless — any session behavior is built on top via cookies and server-side lookup, not something HTTP provides natively.
