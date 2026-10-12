# Replay Attacks

# Why Do Replay Attacks Exist as a Vulnerability?

An attacker doesn't need to decrypt, understand, or forge anything at all to cause real harm — simply capturing a legitimate, validly-signed request or message and resending it later, exactly as-is, can cause the same action to happen a second time, even though the attacker never learned any secret, password, or key. This is exactly why "the request looked completely valid and authenticated" isn't automatically sufficient proof that it's safe to process — it might be an authentic copy of something that already happened once.

```
Attacker captures a LEGITIMATE, validly-signed request:

POST /transfer
Signature: <a genuinely valid signature, correctly computed>
{ "to": "alice", "amount": 100 }

↓

Attacker simply RESENDS this EXACT SAME request later —
unmodified, still carrying a perfectly valid signature (because
it's a literal, byte-for-byte copy of a real request)

↓

If the server has no way to detect this is a REPLAY of an
already-processed request, rather than a new, distinct one —
the transfer happens AGAIN
```

---

# How This Connects to Concepts Already Covered

This chapter's specific framing is the deliberate, adversarial angle on two concepts already covered in depth elsewhere in this handbook.

```
Idempotency (API Design section):  making an operation safe to
                                    repeat — framed primarily
                                    around ACCIDENTAL retries from
                                    network failures and timeouts

Replay Attacks (here):              the SAME underlying protection
                                    (recognizing and rejecting an
                                    already-processed request), but
                                    framed around a DELIBERATE,
                                    ADVERSARIAL resubmission by an
                                    attacker specifically trying to
                                    cause an unwanted repeated effect
```

```
Webhooks chapter's replay-prevention:  timestamp + signature +
                                        tolerance window — the
                                        EXACT SAME mechanism this
                                        chapter reuses, just framed
                                        here explicitly as a
                                        security concern rather
                                        than a delivery-reliability one
```

The mechanisms are genuinely identical; the framing and threat model are what differ — idempotency worries about your own system's retries; replay-attack prevention worries about someone else deliberately trying to exploit the fact that a valid-looking request can be captured and resent.

---

# The Fixes

## Nonces

```
Each legitimate request/message must include a UNIQUE,
NEVER-BEFORE-SEEN random value (a "number used once")

↓

Server tracks nonces it's already seen, and REJECTS any request
carrying a nonce it's encountered before, even if the signature
itself is perfectly valid
```

```
Original request:  nonce=a1b2c3, signature=<valid>  → processed,
                    nonce a1b2c3 recorded as SEEN

Replayed request:   nonce=a1b2c3, signature=<valid — it's a
                    literal copy>  → REJECTED, because a1b2c3
                    was already seen
```

This is directly analogous to an idempotency key — a unique value scoped to one specific, legitimate attempt, with the server tracking which ones it's already processed.

## Timestamps + a Tolerance Window

```
Every signed request/message includes a TIMESTAMP of when it was created

↓

Server REJECTS anything with a timestamp OLDER than some
reasonable tolerance window (e.g. 5 minutes), REGARDLESS of
whether the signature is otherwise valid
```

Exactly the mechanism covered in the Webhooks chapter's replay-prevention section, applied here to the broader, general security concern rather than webhook delivery specifically — bounding how large a window an attacker has to capture and successfully replay a request before it naturally expires.

## Sequence Numbers

```
Each message includes a STRICTLY INCREASING number

↓

Receiver tracks the highest sequence number seen so far, and
REJECTS anything at or BELOW a number it's already processed
```

A useful variant specifically when messages have a natural, meaningful order (a stream of commands that must be processed in sequence) — combining replay protection with an explicit ordering guarantee in one mechanism.

---

# Real-World Examples

### Stripe's Webhook Signature Verification

The exact example already covered in the Webhooks chapter — Stripe's webhook signing includes a timestamp specifically bounding the replay window, so a captured, validly-signed webhook payload can't be resent successfully after that window has passed, regardless of how valid the signature itself remains.

---

### Authentication Handshake Protocols

A captured login handshake — even one that's genuinely, validly signed or encrypted — shouldn't be replayable to authenticate a session again without the real credentials being involved a second time; well-designed authentication protocols incorporate nonces or timestamps specifically to prevent a captured handshake from being reusable later.

---

### API Request Signing With Timestamps (AWS Signature Version 4, and Similar Schemes)

Many API signing schemes (AWS's own request-signing protocol among them) explicitly include a timestamp as part of what gets signed, specifically bounding how long a captured, validly-signed request remains usable before it's rejected purely on the basis of being too old.

---

# Common Interview Questions

## What is a replay attack, and how is it different from an attacker having to actually break encryption or authentication?

A replay attack doesn't require breaking anything at all — the attacker simply captures a legitimate, validly-signed or authenticated request and resends it later, unmodified. Since it's a genuine, byte-for-byte copy of something that really happened once, it passes every cryptographic check a server might perform — the vulnerability is the server's inability to recognize it as an already-processed duplicate, not a weakness in the cryptography itself.

---

## How do nonces prevent replay attacks?

Each legitimate request includes a unique, never-before-seen random value, and the server tracks which nonces it's already processed. A resent, replayed request carries the exact same nonce as the original — even with a perfectly valid signature, the server rejects it because that nonce has already been seen.

---

## Why does a timestamp with a tolerance window help, even without a nonce?

It bounds how long a captured request remains replayable — any request older than the tolerance window gets rejected outright, regardless of signature validity, limiting the practical window an attacker has to capture and successfully resend a request before it naturally expires.

---

## How does this relate to the idempotency concept covered elsewhere in this handbook?

They share the exact same underlying mechanism — recognizing and rejecting an already-processed request — but differ in framing and threat model. Idempotency is primarily concerned with accidental retries from network failures and timeouts within your own system; replay-attack prevention is concerned with a deliberate, adversarial resubmission by an attacker specifically trying to trigger an unwanted repeated effect.

---

## Is a validly signed request automatically safe to process?

No — a valid signature only proves the request genuinely originated from a legitimate source at some point; it doesn't prove the request is being seen for the first time. Without a nonce, timestamp, or sequence number check, a captured, validly-signed request can be replayed successfully, since the signature itself remains perfectly valid on a literal copy.

---

# Common Mistakes

❌ Assuming a validly signed or authenticated request is automatically safe to process.

A valid signature proves origin, not freshness — without a separate check (a nonce, a timestamp, a sequence number), a captured and resubmitted copy of a legitimate request passes every cryptographic check while still being an unwanted replay.

---

❌ Not including a nonce or timestamp in signed requests or tokens at all.

Leaves no mechanism to distinguish an original request from a replayed copy of it — the signature alone can't make this distinction on its own.

---

❌ Setting an overly generous timestamp tolerance window.

Gives an attacker a wide window to capture and successfully replay a request, even with timestamp checking nominally in place — the tolerance window should be as tight as practically possible for the specific use case.

---

# Key Takeaways

- A replay attack requires no cryptographic breakthrough at all — capturing a legitimate, validly-signed request and resending it later can cause the same effect to happen again, since the copy passes every cryptographic check unchanged.
- Nonces, timestamps with a tolerance window, and sequence numbers are the standard fixes, each giving the server a way to recognize and reject an already-processed request regardless of signature validity.
- This chapter's mechanisms are identical to the Webhooks chapter's replay-prevention discussion and closely related to the general idempotency concept — the difference is framing: idempotency guards against accidental retries, replay-attack prevention guards against deliberate, adversarial resubmission.
- A valid signature proves a request's origin, not its freshness — without a separate freshness check, a captured copy of a legitimate request remains just as "valid" as the original.
- Real systems (Stripe's webhook signing, AWS's request signing) universally pair a signature with a timestamp specifically to bound how long a captured request remains replayable.
