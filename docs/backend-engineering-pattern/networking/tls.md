# TLS (Transport Layer Security)

# Why Does TLS Exist?

Plain HTTP travels as readable text, and TCP doesn't protect the content it carries. Anyone with visibility into the path between client and server — a coffee shop's WiFi, an ISP, a compromised router — can read every byte of an unencrypted request: passwords, session tokens, whatever's in there. They can tamper with it too, and neither side would notice.

```
Client → plaintext HTTP request → Server

↓

Anyone on the network path between them can read:
- login credentials
- session cookies
- the actual content of the request/response
```

TLS closes that gap. It encrypts the connection so the content is unreadable in transit, and adds cryptographic guarantees so a client can verify it's actually talking to the server it meant to reach, not an impostor.

---

# What TLS Actually Guarantees

```
Encryption:       the content of the communication is unreadable
                   to anyone intercepting it in transit

Authentication:    the client can verify the server is genuinely
                   who it claims to be (via its certificate)

Integrity:         any tampering with the data in transit is
                   detectable — an attacker can't silently modify
                   the content without it being noticed
```

People tend to think TLS is only about encryption. It isn't — encryption alone would still let a client talk securely to an impostor. Authentication is what closes that gap.

---

# The TLS Handshake

Before any application data goes out, both sides have to agree on encryption parameters and land on a shared secret — while an eavesdropper watches every message that flows during setup.

```
Client                                    Server

  │  ClientHello (supported cipher suites,
  │   a random value)
  ├─────────────────────────────────────►│

  │            ServerHello (chosen cipher suite,
  │             a random value, its CERTIFICATE)
  │◄─────────────────────────────────────┤

  │  (client verifies the certificate,
  │   then both sides derive a shared
  │   symmetric key via key exchange)

  │  Finished (encrypted)
  ├─────────────────────────────────────►│

  │            Finished (encrypted)
  │◄─────────────────────────────────────┤

  ↓

  Encrypted application data now flows
```

The key exchange is the interesting part cryptographically: both sides need to land on the same secret without ever sending it over the wire. Someone watching the entire handshake shouldn't be able to derive that secret from what they saw in plaintext.

---

# Why TLS Uses Both Asymmetric and Symmetric Encryption

A common, good interview question — TLS doesn't pick one. It uses both, at different stages, for different reasons.

```
Asymmetric encryption (public/private key pairs):

  Computationally EXPENSIVE — too slow to encrypt an entire
  ongoing conversation's worth of data with

  BUT solves a real problem: two parties who've never met before
  can use it to safely agree on a shared secret, even while
  being watched by an eavesdropper
```

```
Symmetric encryption (one shared key both sides know):

  Computationally CHEAP and fast — perfectly suited to encrypting
  a large, ongoing volume of application data

  BUT requires BOTH sides to already securely have the same key —
  which is exactly the problem asymmetric encryption just solved
```

```
TLS's actual approach:

1. Use ASYMMETRIC crypto ONLY during the handshake, specifically
   to safely establish a SHARED SYMMETRIC key between two parties
   who've never communicated before

2. Switch to SYMMETRIC encryption for all the actual application
   data that follows, since it's dramatically faster
```

Asymmetric crypto bootstraps trust between two strangers; symmetric crypto handles the actual bulk of the traffic cheaply. Neither one alone gets you both.

---

# Certificates and Certificate Authorities

One question the handshake above glosses over: how does the client know the server's public key genuinely belongs to the domain it claims, and isn't an attacker's key?

```
Server's certificate contains:

- The domain name(s) it's valid for
- The server's public key
- A digital SIGNATURE from a Certificate Authority (CA),
  vouching that this certificate genuinely belongs to this domain
```

```
Browser/OS ships with a built-in list of TRUSTED ROOT CAs

↓

When a server presents its certificate, the browser checks:
"was this certificate signed by a CA I already trust?"

↓

If yes → trust the certificate's claims (this public key really
          does belong to this domain)

If no → warn the user loudly ("Your connection is not private")
```

This is the actual authentication mechanism — not the client independently verifying a server's identity from scratch, but a small number of pre-trusted third parties vouching for it, and the client trusting their signature.

---

# TLS 1.3 — Faster Than 1.2

```
TLS 1.2 handshake:  typically 2 round trips before encrypted
                     application data can flow

TLS 1.3 handshake:  reduced to 1 round trip (1-RTT), and supports
                     0-RTT resumption for a client reconnecting to
                     a server it's already established a session
                     with recently
```

It also dropped a bunch of older, weaker cipher options that had piled up over the years — a real simplification and speed-up, not just a version bump for the sake of one.

---

# Real-World Examples

### Let's Encrypt

Free, automated certificates removed a real, recurring cost and a lot of operational friction from getting TLS set up. A huge share of the industry's "HTTPS everywhere" shift traces back to this — more in the HTTPS chapter.

---

### Every Modern HTTPS Website

The handshake above runs invisibly before every HTTPS page load. It's happening constantly, underneath nearly every secure connection on the web.

---

### TLS 1.3 Adoption Across Major Browsers and CDNs

Widely adopted specifically for the handshake latency win — a measurable, real improvement from cutting round trips, which matters enormously at the scale of billions of daily connections.

---

# Common Interview Questions

## Explain the TLS handshake at a high level.

The client sends supported cipher suites and a random value; the server responds with its chosen cipher, its own random value, and its certificate. The client verifies the certificate, and both sides use asymmetric key exchange to derive a shared symmetric key without ever sending it directly. Once both sides confirm this with encrypted "Finished" messages, all subsequent application data flows encrypted with that symmetric key.

---

## Why does TLS use both asymmetric and symmetric encryption instead of just one?

Asymmetric encryption solves the hard problem — two strangers agreeing on a shared secret while being observed — but it's too slow to encrypt an entire conversation with. Symmetric encryption is fast enough for that, but needs both sides to already share a key. TLS uses asymmetric crypto only during the handshake to get that key, then switches to symmetric encryption for everything after.

---

## How does a browser know it can trust a server's certificate?

The certificate is signed by a Certificate Authority, and browsers/OSes ship with a built-in list of trusted root CAs. If the certificate was signed by one of those (directly, or through a chain), the browser trusts the identity claim; if not, it warns the user instead of silently trusting something unverified.

---

## What improved in TLS 1.3 compared to TLS 1.2?

The handshake dropped from roughly two round trips to one, with 0-RTT resumption available for reconnecting to a recent session — a real, measurable latency win — plus the removal of several older, weaker cipher options that had accumulated in the protocol.

---

## What's the difference between TLS and SSL?

SSL is TLS's deprecated predecessor. The term "SSL certificate" still gets used colloquially, but the protocol actually running on the modern web is TLS — SSL has known vulnerabilities and isn't in real use anymore.

---

# Common Mistakes

❌ Assuming TLS only provides encryption.

It also provides authentication (verifying the server via its certificate) and integrity (detecting tampering). A connection could be encrypted and still be talking to an impostor — authentication is what rules that out.

---

❌ Using "SSL" and "TLS" interchangeably as if they're the same active protocol.

SSL is deprecated and no longer used; the term just stuck around. TLS is what's actually securing modern connections.

---

❌ Not understanding why TLS bothers with asymmetric crypto at all, if symmetric is faster.

Symmetric's speed doesn't solve the harder problem TLS needs solved first: agreeing on a shared key between two strangers while being watched. That's specifically what the asymmetric handshake step does.

---

# Key Takeaways

- TLS encrypts, authenticates, and protects the integrity of a connection — closing a gap plain HTTP and TCP leave wide open.
- The handshake uses asymmetric encryption to bootstrap a shared symmetric key between two strangers, then switches to fast symmetric encryption for the actual data — a deliberate hybrid, not either/or.
- Certificates, signed by trusted CAs, are how a client verifies a server's identity — trust is bootstrapped from a small set of pre-trusted authorities, not verified from scratch.
- TLS 1.3 cut the handshake to one round trip (with 0-RTT resumption) and dropped older, weaker ciphers — a real improvement, not an incremental bump.
- "SSL" is TLS's deprecated predecessor — the name persists colloquially, but TLS is what's actually running.
