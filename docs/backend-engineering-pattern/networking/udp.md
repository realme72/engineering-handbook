# UDP (User Datagram Protocol)

# Why Does UDP Exist?

TCP's reliability isn't free. A handshake before any data flows, retransmission delays when something's lost, deliberate throttling to avoid swamping the network — all of that costs latency. Some applications can't afford it, and don't even want the guarantee in the first place.

```
Live video call: frame 47 is lost in transit

↓

TCP's approach: STOP, wait for frame 47 to be retransmitted and
                 confirmed, THEN deliver frames 47, 48, 49... in order

↓

By the time frame 47 finally arrives (retransmitted), it's already
useless — the call has moved on, and the viewer needed frame 51
to be showing NOW, not frame 47 arriving late
```

UDP is built for exactly that case: when a lost piece of data is better skipped than retransmitted late — fast and occasionally imperfect over correct but delayed.

---

# What UDP Actually Provides

```
UDP:  no handshake, no guaranteed delivery, no ordering,
      no flow control, no congestion control

      Just: send a datagram, fire-and-forget
```

```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(b"hello", ("example.com", 9999))
# sent — no confirmation, no retry, no guarantee it ever arrives
```

No connection to set up, no acknowledgment expected, no built-in way to notice a lost, duplicated, or reordered packet. If an application wants reliability, it has to build it itself.

---

# TCP vs UDP — The Direct Comparison

| | TCP | UDP |
|---|---|---|
| Connection | Handshake required (3-way) | None — connectionless |
| Delivery guarantee | Reliable — retransmits lost data | None — lost data stays lost |
| Ordering | Guaranteed | Not guaranteed |
| Speed | Slower (reliability overhead) | Faster (no overhead) |
| Flow/congestion control | Built-in | None (application's responsibility, if any) |
| Best for | Data where correctness matters more than latency | Data where latency matters more than occasional loss |

---

# Why Some Applications Prefer UDP

## Real-Time Media (Video/Voice Calls)

A glitchy frame or a moment of static is a minor, forgettable annoyance. A frame that arrives correctly but *late* — because TCP insisted on retransmitting and delivering in order — has already missed its moment. UDP lets the application skip a lost piece and keep moving, instead of freezing for a retransmission that's already stale on arrival.

## DNS Queries

A DNS query and its response are small enough that resending the whole thing after a loss is cheaper and faster than paying TCP's connection setup for every lookup. UDP's lack of a handshake is a straight win here, with application-level retry handling the rare drop.

## Online Gaming

Only the *most recent* position matters. A stale position packet arriving late — because it was waiting on retransmission — is worse than useless, since the game has already moved past it. Losing an intermediate update and using whatever arrives next is correct, not a bug.

---

# Head-of-Line Blocking — Why TCP's Guarantees Actively Hurt These Use Cases

The specific mechanism worth naming precisely.

```
TCP connection, sending frames 47, 48, 49, 50, 51 in order

↓

Frame 48 is LOST

↓

TCP's ordering guarantee means frames 49, 50, 51 — even though
they've ALREADY ARRIVED successfully — cannot be delivered to the
application yet, because frame 48 hasn't arrived, and TCP refuses
to deliver data out of order

↓

The application is BLOCKED waiting on frame 48's retransmission,
even though frames 49-51 are sitting right there, ready to go
```

That's head-of-line blocking — one lost piece of data blocks everything behind it, purely because of TCP's strict ordering guarantee. For a file download, that's exactly the right behavior; you need every byte, in order. For a live video call, it's actively harmful — the viewer would rather see frames 49-51 immediately and just lose 48.

---

# The Trade-off Isn't "UDP Is Worse"

UDP isn't a stripped-down, lesser TCP. It's a deliberately minimal protocol that skips guarantees some applications don't want, so they don't pay for them. Anything that needs some, but not all, of TCP's guarantees can build exactly what it needs on top of UDP — which is precisely what QUIC (the foundation of HTTP/3) does: reliability and ordering, but per-stream instead of per-connection, sidestepping TCP's head-of-line blocking while still recovering loss where it actually matters.

---

# Real-World Examples

### DNS

The canonical case — a small query, cheaply resent if lost, faster overall than paying TCP's setup cost for every lookup. (DNS falls back to TCP for larger responses like zone transfers, where UDP's datagram size limit becomes a constraint, but the common case is UDP.)

---

### WebRTC (Video/Voice Calls)

Built around UDP for real-time media specifically to dodge head-of-line blocking — a momentarily glitchy frame beats the whole call visibly stalling to wait for a stale, retransmitted one.

---

### Online Multiplayer Games

Position and action updates go over UDP because only the most recent state matters — a stale packet held up by retransmission would already be obsolete by the time it arrived.

---

### QUIC / HTTP/3

Builds its own reliability and ordering on top of UDP, per-stream instead of per-connection, specifically to sidestep TCP's connection-wide head-of-line blocking — covered in full in the HTTP/3 chapter.

---

# Common Interview Questions

## TCP vs UDP — walk through a concrete example of when you'd choose each.

TCP for a file download or an API call, where every byte matters and has to arrive correctly and in order. UDP for a live video call, where a lost frame is better skipped than retransmitted late — by the time a retransmitted frame shows up, the conversation has already moved past it.

---

## Why does DNS typically use UDP instead of TCP?

Because a query and response are small, and resending an occasional lost query costs less than establishing a full TCP connection for every single lookup. UDP's lack of connection setup is a real win for this small, quick request/response pattern.

---

## Why does real-time video prefer UDP over TCP, specifically?

Head-of-line blocking. TCP's strict ordering means one lost packet blocks everything behind it — even data that already arrived — until the lost piece is retransmitted. For live video, a late, retransmitted frame is already useless; skipping it and moving on is the better outcome.

---

## What is head-of-line blocking?

One lost or delayed piece of data blocking delivery of everything behind it in a stream, purely because of an ordering guarantee. TCP enforces this at the connection level — even successfully-received data waits for an earlier, missing piece before the application ever sees it.

---

## Is UDP just a "worse" version of TCP?

No — it's a minimal protocol that skips TCP's guarantees so applications that don't need them don't pay for them (handshake latency, retransmission delay, head-of-line blocking). Applications that need partial reliability build exactly what they need on top of it, which is what QUIC does for HTTP/3.

---

# Common Mistakes

❌ Treating UDP as strictly inferior to TCP.

It's a different tool for a different job. Preferring fast, occasionally-imperfect delivery over guaranteed, ordered delivery is a deliberate, correct trade-off, not a compromise.

---

❌ Not understanding why head-of-line blocking specifically hurts real-time applications.

It's not that TCP is "slow" in the abstract — its ordering guarantee actively withholds already-received data until an earlier piece is retransmitted, which is exactly the wrong behavior for time-sensitive data that's worthless once stale.

---

❌ Assuming an application using UDP has no reliability at all.

Real UDP-based systems (QUIC, custom game networking) build their own reliability layer on top of it — deliberately, exactly where and how the application needs it, instead of inheriting TCP's one-size-fits-all version.

---

# Key Takeaways

- UDP exists because TCP's reliability costs latency some applications — real-time media, quick lookups, games — would rather not pay, especially when a lost piece of data is better skipped than delivered late.
- It provides no handshake, no guaranteed delivery, no ordering, no built-in flow or congestion control — any reliability needed has to be built on top.
- Head-of-line blocking is why TCP is a poor fit for real-time use cases — one lost packet blocks all the already-received data behind it until it's retransmitted.
- UDP isn't a worse TCP — it's a minimal foundation applications can build exactly the reliability they need on top of, which is the approach QUIC takes for HTTP/3.
- DNS, real-time video/voice, and online gaming are the classic cases where UDP's trade-offs are the right call, since stale retransmitted data is worse than simply losing it.
