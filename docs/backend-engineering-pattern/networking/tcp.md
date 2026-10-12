# TCP (Transmission Control Protocol)

# Why Does TCP Exist?

The raw network underneath everything — routers, switches, physical links — makes no promises at all. Packets get lost, arrive out of order, arrive duplicated, or show up corrupted. Most applications can't tolerate any of that. A file transfer with silently missing bytes, or a webpage whose HTML arrives scrambled, is just broken.

```
Raw network reality:

Packet 1 sent → arrives
Packet 2 sent → LOST, never arrives
Packet 3 sent → arrives BEFORE packet 2 would have (if it existed)
Packet 4 sent → arrives, but CORRUPTED

↓

An application receiving this raw stream has no way to know
anything went wrong, unless something detects and fixes it
```

TCP sits on top of that mess and provides the illusion of a reliable, ordered, error-checked byte stream — so HTTP, database connections, and SSH never have to think about packet loss, reordering, or corruption at all.

---

# The Three-Way Handshake

Before any data flows, both sides need to agree they're ready and synchronize initial sequence numbers.

```
Client                          Server

  │  SYN (seq=X)                  │
  ├───────────────────────────────►│

  │            SYN-ACK (seq=Y, ack=X+1)
  │◄───────────────────────────────┤

  │  ACK (ack=Y+1)                 │
  ├───────────────────────────────►│

  ↓

  Connection ESTABLISHED — data can now flow
```

```
SYN:      "I'd like to start a connection, here's my starting
           sequence number"

SYN-ACK:  "Acknowledged, here's MY starting sequence number too"

ACK:      "Acknowledged — we're both ready"
```

Both sides confirm the other's initial sequence number before real data flows, and that's what lets each side track "what's been sent and acknowledged" for the rest of the connection.

---

# Reliability Mechanisms

## Sequence Numbers and Acknowledgments

```
Sender sends: bytes 1-100 (sequence number 1)

↓

Receiver replies: "ACK 101" (meaning: "I've received everything
                              through byte 100, send me 101 next")
```

Every byte is numbered, and the receiver's acknowledgments tell the sender exactly what got through — the mechanism that makes retransmission possible at all.

## Retransmission

```
Sender sends bytes 1-100

↓

Times out waiting for an ACK (or receives duplicate ACKs suggesting
a gap) → assumes the segment was LOST

↓

RESENDS bytes 1-100
```

Miss an expected acknowledgment past the timeout, and TCP assumes loss and resends. The application above never sees any of this — it just eventually gets the complete, correctly-ordered stream.

## Checksums

Every segment carries a checksum. The receiver recomputes it on arrival; a mismatch means corruption, and triggers the same retransmission path as an outright loss.

---

# Flow Control — Protecting the Receiver

```
Receiver's buffer: currently has room for 5,000 more bytes

↓

Receiver advertises: "window size = 5,000" in every ACK

↓

Sender will NOT send more than 5,000 bytes beyond what's already
been acknowledged, until the receiver's window opens back up
```

Flow control stops a fast sender from overwhelming a slower receiver. The receiver just tells the sender how much it can handle right now, and the sender respects it.

---

# Congestion Control — Protecting the Network

A separate concern: even if the receiver could take more data, the network path in between — routers, links — might not be able to. Congestion control keeps the sender from overwhelming the network itself, regardless of receiver capacity.

```
Slow Start:  a new connection begins sending CONSERVATIVELY,
             gradually increasing how much data it sends per
             round trip, doubling roughly each time, until it
             either reaches a steady state or detects loss

↓

Congestion Avoidance:  once a reasonable sending rate is found,
                        increase more cautiously, backing off
                        significantly the moment packet loss
                        suggests the network path is congested
```

```
Flow control:        "how much can the RECEIVER handle?"
Congestion control:   "how much can the NETWORK ITSELF handle?"
```

This is why a brand-new TCP connection can feel slower than one that's been running a while — slow start means it ramps up gradually rather than blasting at full speed from the first packet. It's also a concrete instance of backpressure: congestion control is TCP's own way of backing off when the network signals it's overloaded.

---

# Connection Teardown

```
Client                          Server

  │  FIN                          │
  ├───────────────────────────────►│

  │            ACK                 │
  │◄───────────────────────────────┤

  │            FIN                 │
  │◄───────────────────────────────┤

  │  ACK                           │
  ├───────────────────────────────►│

  ↓

  Connection CLOSED
```

Each side signals it's done sending (a `FIN`) and acknowledges the other's — a graceful, symmetric close rather than one side just stopping. Both sides get to confirm everything actually arrived before the connection goes away.

---

# Real-World Examples

### Essentially Everything

HTTP, database connections (Postgres, MySQL), SSH, and mail protocols (SMTP, IMAP) all sit on top of TCP by default — it's the foundational transport underneath almost every application protocol that actually needs reliable, ordered delivery.

---

### Why a Fresh TCP Connection Feels Slower Than a Warm One

A directly observable consequence of slow start. A brand-new connection hasn't ramped up its sending rate yet; one that's been transferring data for a while already found a faster steady state. Part of why connection reuse (HTTP keep-alive) helps beyond just skipping repeated handshakes.

---

# Common Interview Questions

## Explain the TCP three-way handshake and why it's needed.

The client sends a SYN with an initial sequence number; the server responds with a SYN-ACK carrying its own sequence number and an acknowledgment of the client's; the client sends a final ACK. Both sides need to agree on starting sequence numbers before data flows, since TCP's whole reliability mechanism depends on tracking exactly which bytes have been sent and acknowledged.

---

## What's the difference between flow control and congestion control?

Flow control protects the receiver — it stops a sender from outpacing what the receiver can actually process, based on the receiver's advertised window. Congestion control protects the network path itself — it stops the sender from pushing more than the network can handle, independent of what the receiver could absorb, using mechanisms like slow start and aggressive backoff on detected loss.

---

## Does TCP guarantee fast delivery?

No — it guarantees reliable, ordered, error-checked delivery, not speed. Retransmission and congestion control's deliberate throttling both add latency compared to a protocol with no such guarantees, like UDP. TCP trades some speed for correctness, which is the right call for most applications but not all of them.

---

## Why might a brand-new TCP connection be slower than one that's been open a while?

Slow start. A new connection ramps up its sending rate gradually over successive round trips instead of going full speed immediately. A connection that's already been transferring data has typically found a faster steady-state rate.

---

## How does TCP detect and recover from a lost segment?

Every segment is numbered, and the receiver acknowledges what it's received. If an expected acknowledgment doesn't show up within a timeout — or duplicate ACKs suggest a gap — the sender assumes loss and retransmits, all transparently below the application layer.

---

# Common Mistakes

❌ Confusing flow control with congestion control.

Different targets — flow control protects a slower receiver from being overwhelmed; congestion control protects the network path itself, regardless of the receiver's own capacity.

---

❌ Assuming TCP guarantees low latency.

Its reliability guarantees are a deliberate trade against raw speed — retransmission and congestion-driven throttling both cost time. That's exactly why some latency-sensitive applications reach for UDP instead.

---

❌ Not accounting for TCP slow start when reasoning about a new connection's initial performance.

A fresh connection ramping up gradually is normal, not a problem — and a big part of why reusing existing connections beats opening a new one per request.

---

# Key Takeaways

- TCP provides a reliable, ordered, error-checked byte stream on top of a network that guarantees none of that on its own — loss, reordering, duplication, and corruption are all handled below the application layer.
- The three-way handshake establishes agreed-upon sequence numbers before data flows, which is what makes tracking "sent and acknowledged" possible for the rest of the connection.
- Flow control protects the receiver; congestion control protects the network — related but distinct, and both essential to how TCP actually behaves.
- Slow start ramps a new connection's sending rate up gradually — a real, observable reason fresh connections feel slower than reused ones.
- TCP optimizes for correctness and ordering, not speed — a trade that's right for most applications, though not universally (see UDP).
