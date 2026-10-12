# HTTP/3

# Why Does HTTP/3 Exist?

HTTP/2's multiplexing genuinely fixed head-of-line blocking at the HTTP layer — but as the HTTP/2 chapter's closing point made clear, it still runs on top of TCP, and TCP's own strict, connection-wide in-order delivery guarantee means a single lost packet blocks **every** multiplexed stream sharing that connection, not just the one stream the lost data actually belonged to.

```
HTTP/2 over TCP, multiplexing streams 1, 2, 3

↓

ONE packet, belonging to stream 1, is lost

↓

TCP refuses to deliver ANY subsequent data on the connection —
including data for streams 2 and 3 that already arrived
successfully — until the lost packet is retransmitted

↓

Streams 2 and 3 are blocked, even though the actual problem has
nothing to do with them at all
```

This is a problem baked into TCP itself, at the transport layer — no amount of clever work at the HTTP layer (like HTTP/2's multiplexing) can fix it, because the blocking is happening one layer down, outside of HTTP's control entirely. HTTP/3 exists to solve this by changing the transport layer itself.

---

# The Fix: Build on QUIC Instead of TCP

```
HTTP/2:  HTTP semantics  →  runs on top of  →  TCP

HTTP/3:  HTTP semantics  →  runs on top of  →  QUIC  →  runs on top of  →  UDP
```

QUIC is a new transport protocol, built on top of UDP (from the UDP chapter) rather than TCP — but it doesn't give up reliability the way raw UDP does. Instead, QUIC reimplements reliability and ordering itself, deliberately **per stream** instead of per connection, which is precisely the design choice that fixes the remaining problem.

```
QUIC connection, multiplexing streams 1, 2, 3 (same idea as
HTTP/2's multiplexing, but now implemented WITHIN the transport
layer itself, not layered on top of it)

↓

ONE packet, belonging to stream 1, is lost

↓

QUIC retransmits ONLY the missing piece belonging to stream 1

↓

Streams 2 and 3 are COMPLETELY UNAFFECTED — their data continues
to be delivered and processed normally, since QUIC tracks
reliability independently, per stream, rather than as one single
in-order guarantee across the entire connection
```

This is the core insight: by moving multiplexing (and the reliability guarantee that goes with it) down into the transport layer itself, rather than layering it on top of a transport (TCP) that only knows how to guarantee order across an entire connection, QUIC can scope "what's blocked by a lost packet" down to just the one affected stream.

---

# TLS Built Directly Into QUIC

Another meaningful difference: in the HTTP/2-over-TCP world, establishing a secure connection means a TCP handshake *followed by* a separate TLS handshake (from the TLS chapter) — two separate negotiations, back to back.

```
Traditional (HTTP/2 over TCP):

TCP handshake (1 round trip)  →  THEN  →  TLS handshake (1+ round trips)

↓

Total: multiple round trips before any application data can flow
```

```
QUIC:

TLS is built directly INTO the QUIC transport handshake itself,
rather than layered on top separately afterward

↓

Total: often just 1 round trip (1-RTT) — sometimes ZERO additional
round trips (0-RTT) for a client reconnecting to a server it's
recently established a session with
```

Combining what used to be two separate negotiations into one meaningfully reduces the number of round trips before real data can start flowing — a direct, measurable latency win, especially pronounced on high-latency connections like mobile networks.

---

# Connection Migration

A genuinely practical, concrete benefit worth calling out on its own: QUIC identifies a connection by a **connection ID**, not by the traditional (source IP, source port) tuple TCP relies on.

```
TCP:   a connection is identified by (client IP, client port,
        server IP, server port) — if the client's IP changes
        (switching from WiFi to cellular), the connection is
        no longer recognized as the same one and must be
        re-established from scratch

QUIC:  a connection is identified by a CONNECTION ID that stays
        the same regardless of the client's underlying network
        path — a client switching from WiFi to cellular can KEEP
        the same QUIC connection alive, with no need to
        renegotiate the handshake at all
```

```
User on WiFi, mid-download, walks out of range

↓

Phone switches to cellular data — IP address CHANGES

↓

TCP-based connection: broken, must reconnect from scratch (new
                       handshake, new TLS negotiation, lost
                       in-flight state)

QUIC-based connection: SAME connection ID recognized, download
                        continues seamlessly with no renegotiation
```

This is a real, user-visible improvement specifically for mobile clients, where switching networks mid-session is common and previously meant a visible interruption while everything reconnected from scratch.

---

# Is HTTP/3 "Less Reliable" Because It's UDP-Based?

A very natural, and incorrect, assumption worth addressing directly: no. QUIC builds its own robust reliability layer directly on top of raw UDP — retransmission, ordering, and flow control are all still present, just implemented per-stream instead of per-connection. HTTP/3 gets UDP's flexibility (no connection-wide ordering constraint forcing unrelated streams to block each other) without giving up the actual guarantee that data arrives correctly — it's not "UDP with no guarantees," it's "a new, more sophisticated set of guarantees, built directly for this exact problem, on top of UDP instead of TCP."

---

# Real-World Examples

### Google (QUIC's Origin)

QUIC was originally developed at Google and used to accelerate its own services (initially Chrome and Google's servers) before being standardized as the foundation for HTTP/3 — Google's own large-scale, real production traffic was the original proving ground for whether this transport-layer redesign actually delivered measurable benefits.

---

### YouTube, Cloudflare, and Facebook

All have publicly adopted HTTP/3 and reported measurable performance improvements, particularly on flaky or high-latency mobile networks — exactly the conditions where TCP-level head-of-line blocking and repeated reconnections after network switches are most costly, and where QUIC's design advantages matter most.

---

### Video Streaming on Mobile Networks

A directly relevant real-world case for connection migration specifically — a user streaming video while moving between WiFi and cellular coverage benefits enormously from a connection that survives the network switch, rather than visibly stalling and reconnecting.

---

# Common Interview Questions

## Why does HTTP/3 use QUIC over UDP instead of building further on TCP?

Because the remaining head-of-line blocking problem after HTTP/2 is baked into TCP itself — its connection-wide, strict in-order delivery guarantee means a single lost packet blocks every multiplexed stream sharing that connection. This can't be fixed at the HTTP layer; it requires a transport layer that implements reliability per-stream instead of per-connection, which is exactly what QUIC does, built on UDP specifically because UDP doesn't impose TCP's connection-wide ordering constraint in the first place.

---

## How does HTTP/3 solve the TCP-level head-of-line blocking problem that HTTP/2 couldn't?

By implementing reliability and ordering per stream, within QUIC itself, rather than relying on TCP's single, connection-wide ordering guarantee. A lost packet only blocks the one stream it belongs to — every other multiplexed stream on the same QUIC connection continues being delivered and processed normally.

---

## What is connection migration, and why does it matter for mobile clients?

QUIC identifies a connection by a connection ID rather than the traditional IP-and-port tuple TCP uses — meaning a client switching networks (WiFi to cellular) can keep the same underlying connection alive without needing to renegotiate a new handshake from scratch. This avoids a visible interruption that a TCP-based connection would suffer the moment the client's IP address changes.

---

## Is HTTP/3 less reliable than HTTP/2 because it's built on UDP?

No — QUIC implements its own robust reliability layer (retransmission, ordering, flow control) directly on top of raw UDP, just scoped per-stream instead of per-connection. It gets UDP's flexibility (no connection-wide ordering constraint) without sacrificing the actual guarantee that data arrives correctly; it's a different, more granular reliability model, not an absence of one.

---

## Why does combining TLS into QUIC's own handshake reduce latency?

Because it avoids the traditional back-to-back sequence of a separate TCP handshake followed by a separate TLS handshake — QUIC negotiates both together, typically in a single round trip (and sometimes zero additional round trips for a resumed connection), directly reducing the time before real application data can start flowing.

---

# Common Mistakes

❌ Assuming "built on UDP" means HTTP/3 sacrifices reliability.

QUIC adds its own comprehensive reliability layer directly on top of raw UDP — the difference from TCP is that this reliability is scoped per-stream, not that it's absent.

---

❌ Thinking HTTP/2's multiplexing and HTTP/3's improvement are solving the same problem at the same layer.

HTTP/2 solved head-of-line blocking at the HTTP layer; HTTP/3 solves the *remaining* head-of-line blocking problem that exists one layer down, at the transport layer, which HTTP/2 structurally could not fix since it was still running on top of TCP.

---

❌ Underestimating the practical value of connection migration.

It's not a minor detail — for mobile clients switching networks mid-session, it's the difference between a session continuing seamlessly and a visible, disruptive reconnection.

---

# Key Takeaways

- HTTP/3 exists to fix TCP-level head-of-line blocking, a problem HTTP/2's HTTP-layer multiplexing structurally could not solve, since it was still built on top of TCP.
- QUIC, built on UDP, reimplements reliability and ordering per stream instead of per connection — a lost packet only blocks the one stream it belongs to, not every multiplexed stream sharing the connection.
- TLS is integrated directly into QUIC's own handshake, typically reducing the connection setup to a single round trip (or zero, for resumed connections) instead of two separate back-to-back handshakes.
- Connection migration — identifying a connection by ID rather than IP-and-port — lets a QUIC connection survive a client switching networks, a real, user-visible benefit especially for mobile clients.
- HTTP/3 being UDP-based doesn't mean it's less reliable — QUIC provides its own robust, per-stream reliability guarantees, just implemented differently than TCP's connection-wide approach.
