# Webhooks

# Why Do Webhooks Exist?

Imagine you're integrating with a payment provider. A customer initiates a bank transfer, which can take anywhere from a few seconds to two days to actually settle.

Without webhooks, your only option is to ask, repeatedly:

```
GET /payments/101/status   → "pending"

... wait 2 seconds ...

GET /payments/101/status   → "pending"

... wait 2 seconds ...

GET /payments/101/status   → "pending"

... (this continues for up to 2 days) ...

GET /payments/101/status   → "settled"
```

This is polling, and it's wasteful in a specific, measurable way — you're paying for thousands of requests to learn about one event. Multiply this by every customer, every payment, every provider you integrate with, and you're running a constant background load whose entire purpose is asking "has anything changed yet?" and getting "no" back almost every time.

Webhooks flip the direction of communication. Instead of you repeatedly asking the provider, you give the provider a URL once, and *they* call *you* the instant something actually happens.

```
Polling (pull)                       Webhook (push)

Client → "anything new?" → Server    Event happens on Server
Client → "anything new?" → Server           ↓
Client → "anything new?" → Server    Server → POST → Client's URL
Client → "anything new?" → Server
  ... repeated forever ...
```

A webhook is nothing exotic under the hood — it's just a regular HTTP POST request, sent by the provider, to a URL you registered in advance, carrying a JSON payload describing what happened. The "magic" isn't in the mechanism, it's in who initiates the request.

---

# What Problem It Actually Solves

- **Eliminates wasted polling traffic** — no more thousands of "nothing changed" responses for every one that matters.
- **Near real-time delivery** — the provider notifies you within moments of the event, not on your polling interval.
- **Decouples the provider from your internal logic** — the provider doesn't need to know or care what you do with the event; it just delivers it.
- **Scales far better for the provider** — Stripe would collapse under the request volume if every merchant's backend polled every payment's status every few seconds. Webhooks push that cost down to "one request per actual event."

The trade-off, and the thing that makes webhooks a genuinely hard engineering problem rather than "just a callback URL," is that your server now has to be a reliable HTTP receiver — reachable, fast, idempotent, and secure — for requests that someone else's infrastructure initiates on someone else's schedule.

---

# How Webhooks Work

```
1. You register a URL with the provider (in a dashboard or via API)

   https://api.yourapp.com/webhooks/stripe

2. An event happens on the provider's side
   (a charge succeeds, a subscription renews, an order ships)

3. The provider sends an HTTP POST to your registered URL

   POST /webhooks/stripe
   {
       "event": "payment.succeeded",
       "id": "evt_1Nabc123",
       "data": { "payment_id": "pay_42", "amount": 500 }
   }

4. Your server processes the event and responds

   200 OK   →  provider considers it delivered
   4xx/5xx  →  provider assumes delivery failed and retries later
```

Nothing here requires an open persistent connection (unlike WebSockets or SSE) — it's a one-shot HTTP request, which is exactly why webhooks work well for server-to-server integration between two systems that don't otherwise know anything about each other's infrastructure.

---

# Designing a Webhook Payload

A well-designed webhook payload gives the receiver enough to act without a mandatory follow-up API call.

```json
{
    "id": "evt_1Nabc123",
    "type": "order.shipped",
    "created_at": "2026-07-21T10:00:00Z",
    "data": {
        "order_id": "ord_42",
        "tracking_number": "1Z999AA10123456784",
        "carrier": "UPS"
    }
}
```

Three fields matter more than they look like they should:

- **`id`** — a unique event ID. This is what makes deduplication possible on the receiving end (more on this below — webhooks are delivered *at least once*, not *exactly once*).
- **`type`** — lets one endpoint handle many event kinds via a single dispatch table instead of registering a separate URL per event type.
- **`created_at`** — lets the receiver detect and reject stale or replayed deliveries.

A common design decision: should the payload carry the *full* object (`data.order` with every field) or just enough to identify it (`data.order_id`), forcing the receiver to call back and fetch the rest? Full payloads are more convenient but leak internal shape and go stale if the object changes again before you've finished processing the first event. Thin payloads (just an ID) are always fresh, at the cost of an extra round trip. Stripe does both — a thin reference plus the full object snapshotted at the time of the event.

---

# The Hard Parts

This is where webhook design actually separates from "just POST some JSON somewhere." Everything below is a lesson someone learned the hard way in production, not a theoretical concern.

## 1. Delivery Is At-Least-Once, Never Exactly-Once

If your endpoint is slow, briefly down, or the network drops the response on the way back to the provider, the provider cannot distinguish "you never got it" from "you got it but I didn't hear back." It has exactly one safe option: retry.

```
Provider sends event → your server processes it → charges applied → your server crashes before responding

↓

Provider never received a 200

↓

Provider retries → SAME event delivered again
```

This means your webhook handler **must** be idempotent — the exact same problem, and the exact same solution (track processed event IDs, skip duplicates), as designing an idempotent API endpoint. If you haven't yet, it's worth reading up on idempotency directly — webhooks are one of the most common real-world places that concept shows up.

## 2. Your Endpoint Must Respond Fast

Providers enforce a response timeout (Stripe: a few seconds). If your handler does the real work — hits your database, calls three other services, sends a confirmation email — synchronously before responding, you risk the provider timing out, marking the delivery as failed, and retrying it, even though your server actually did process it. Now you're processing the same event twice, slowly, forever falling further behind.

The fix: acknowledge immediately, process asynchronously.

```
POST /webhooks/stripe

↓

Verify signature (fast)

↓

Enqueue event for background processing

↓

Return 200 OK   (milliseconds later)

↓

(separately) Worker picks event off the queue and does the real work
```

## 3. Verifying Authenticity

Your webhook URL is a public endpoint. Nothing stops anyone from finding it and POSTing a fake `payment.succeeded` event to it, claiming a payment happened when it didn't.

Providers solve this with a signature — they sign the payload with a shared secret, and you verify that signature before trusting anything in the body.

```
Provider:  signature = HMAC-SHA256(secret, timestamp + "." + payload)
           sends payload + signature in a header

You:       recompute HMAC-SHA256(secret, timestamp + "." + received_payload)
           compare to the signature header
           reject if they don't match
```

An unverified webhook handler is a direct path to fraud — "mark this order as paid" is exactly the kind of action an attacker would love to trigger for free.

## 4. Preventing Replay Attacks

Even a *correctly signed* request can be captured and resent later by an attacker who intercepted it once. The fix is including a timestamp in what gets signed, and rejecting anything too old.

```
Received timestamp: 10:00:00
Current time:        10:07:00
Tolerance:            5 minutes

→ REJECT (outside tolerance, likely a replay)
```

## 5. Ordering Is Not Guaranteed

Retries, network jitter, and provider-side queuing mean event B can arrive before event A, even if A happened first.

```
order.created   →  sent at 10:00:00, arrives at 10:00:05 (delayed by a retry)
order.shipped   →  sent at 10:00:02, arrives at 10:00:03
```

If your handler for `order.shipped` assumes `order.created` already ran, you have a bug waiting to happen the first time delivery isn't perfectly in order. Include a timestamp or sequence number in the payload and design handlers to tolerate out-of-order arrival — or explicitly fetch current state from the source of truth instead of trusting the event's implied ordering.

## 6. Handling Sustained Endpoint Downtime

What if your server is down for an hour during a deploy? A responsible provider retries with exponential backoff for a bounded period (Stripe retries for up to 3 days) and then gives up.

```
Attempt 1  → fails →  wait 1 min
Attempt 2  → fails →  wait 5 min
Attempt 3  → fails →  wait 30 min
...
Attempt N  → fails →  give up, mark as permanently failed
```

This is why serious integrations pair webhooks with a reconciliation job — a periodic API poll that catches anything a webhook might have missed entirely. Webhooks are the fast path; polling-as-a-safety-net is the correctness guarantee. Treat webhooks as "important but not the only source of truth" for anything financially critical.

---

# Python Implementation

## Sending a Webhook (Provider Side)

```python
import hashlib
import hmac
import json
import time
import requests

WEBHOOK_SECRET = b"shared_secret_key"

def send_webhook(url: str, payload: dict, max_retries: int = 5):
    body = json.dumps(payload, sort_keys=True).encode()
    timestamp = str(int(time.time()))

    signed_payload = f"{timestamp}.{body.decode()}".encode()
    signature = hmac.new(WEBHOOK_SECRET, signed_payload, hashlib.sha256).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "Webhook-Timestamp": timestamp,
        "Webhook-Signature": signature,
    }

    backoff = 1
    for attempt in range(max_retries):
        try:
            response = requests.post(url, data=body, headers=headers, timeout=5)
            if response.status_code == 200:
                return  # delivered successfully
        except requests.RequestException:
            pass  # network error — fall through to retry

        time.sleep(backoff)
        backoff *= 5  # exponential backoff

    # exhausted retries — log for manual investigation / dead-letter queue
    mark_delivery_failed(url, payload)
```

## Receiving a Webhook (Consumer Side)

```python
import hashlib
import hmac
import time
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()
WEBHOOK_SECRET = b"shared_secret_key"
REPLAY_TOLERANCE_SECONDS = 300
processed_events = set()  # use Redis in production, not an in-memory set


def verify_signature(timestamp: str, body: bytes, signature: str) -> bool:
    if abs(time.time() - int(timestamp)) > REPLAY_TOLERANCE_SECONDS:
        return False  # too old — reject as a possible replay

    signed_payload = f"{timestamp}.{body.decode()}".encode()
    expected = hmac.new(WEBHOOK_SECRET, signed_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)  # constant-time comparison


@app.post("/webhooks/provider")
async def receive_webhook(request: Request):
    body = await request.body()
    timestamp = request.headers.get("Webhook-Timestamp", "")
    signature = request.headers.get("Webhook-Signature", "")

    if not verify_signature(timestamp, body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = await request.json()

    if event["id"] in processed_events:
        return {"status": "already processed"}  # duplicate delivery — safe no-op

    processed_events.add(event["id"])
    enqueue_for_processing(event)  # hand off to a background worker, don't block here

    return {"status": "accepted"}
```

Two details worth calling out: `hmac.compare_digest` is used instead of `==` specifically to avoid timing attacks on the signature comparison, and the handler enqueues the event and returns immediately rather than doing the real work inline — exactly the "acknowledge fast, process async" pattern from above.

---

# Real-World Examples

### Stripe

```http
POST /webhooks/stripe
Stripe-Signature: t=1721568000,v1=5257a869e7bfa8f...
```

Stripe signs every webhook with a timestamp + HMAC-SHA256 signature, retries failed deliveries with backoff for up to 3 days, and explicitly documents that your endpoint must be idempotent because "Stripe’s webhook events may be delivered more than once." This is exactly the design discussed above, from the company most exposed to the cost of getting it wrong.

---

### GitHub

```http
POST /your-webhook-endpoint
X-Hub-Signature-256: sha256=aad...
X-GitHub-Event: pull_request
```

GitHub signs payloads with `X-Hub-Signature-256` and includes the event type directly as a header (`X-GitHub-Event`) rather than only inside the body, letting you route without even parsing JSON first.

---

### Slack

Slack's Events API requires a one-time "URL verification" handshake before it will ever send real events: when you register a URL, Slack POSTs a `challenge` value to it, and your endpoint must echo that exact value back before Slack trusts the endpoint is real and under your control. This is Slack's answer to a subtle problem — proving upfront that whoever registered the URL actually controls it, before committing to send potentially sensitive event data there.

---

# Common Interview Questions

## Webhooks vs polling — when would you choose polling anyway?

Webhooks win when you control both the sender and can rely on push delivery. Polling still makes sense when there's no reliable way to receive inbound connections (e.g. a client behind NAT/firewall with no public endpoint), or when you need a guaranteed-consistent view regardless of missed events — which is exactly why serious integrations often keep a polling-based reconciliation job even after adopting webhooks, as a correctness backstop.

---

## Webhooks vs WebSockets vs SSE — what's the actual difference?

Webhooks are one-shot, server-to-server HTTP callbacks with no persistent connection — the receiver doesn't even need to be "listening" in real time, just reachable when the event fires. WebSockets and SSE both require a long-lived, held-open connection, and are typically server-to-*browser/client*, used when you need continuous, low-latency updates to an actively connected client (a live chat, a live dashboard) rather than an occasional server-to-server notification.

---

## How do you verify a webhook actually came from the provider?

Recompute the HMAC signature over the raw payload (plus a timestamp) using the shared secret, and compare it — using a constant-time comparison — to the signature header the provider sent. Never trust the payload's contents without this check; the endpoint is public and anyone can guess its shape.

---

## Why include a timestamp in the signed payload?

To prevent replay attacks — an attacker who captures a validly-signed request in transit (or via a compromised log) could resend it later and have it accepted, since the signature alone is still technically valid. A timestamp plus a tolerance window (reject anything older than a few minutes) closes that gap.

---

## Why must webhook handlers be idempotent?

Because delivery is guaranteed at-least-once, never exactly-once — retries after a timeout, a crash before acknowledgment, or provider-side redelivery can all cause the same event to arrive more than once. The handler needs to recognize an already-processed event ID and skip reprocessing, otherwise a payment gets applied twice or an email gets sent twice.

---

## Why should a webhook handler respond quickly instead of doing the real work inline?

Providers enforce a response timeout. If your handler is still doing slow synchronous work (multiple DB writes, downstream API calls) when the timeout hits, the provider assumes delivery failed and retries — even though you already received and are processing it — leading to duplicate processing on top of the original delay. Acknowledge immediately, then process asynchronously off a queue.

---

## What do you do if your endpoint is down for an extended period?

Rely on the provider's retry-with-backoff window to catch most cases, but for anything financially significant, don't treat webhooks as the sole source of truth — pair them with a periodic reconciliation poll against the provider's API to catch events that were missed entirely once the provider's retry window expires.

---

# Common Mistakes

❌ Trusting the webhook payload without verifying the signature.

Turns your webhook endpoint into a free "trigger any state change" button for anyone who finds the URL.

---

❌ Processing the event synchronously before responding.

Risks a provider-side timeout, which triggers a retry, which causes duplicate processing on top of the original slow request.

---

❌ Not deduplicating by event ID.

Since delivery is at-least-once, any handler that isn't idempotent will eventually double-process a real event — this isn't a rare edge case, it's an expected, routine occurrence at any real volume.

---

❌ Assuming events arrive in the order they happened.

Retries and provider-side queuing can and will reorder deliveries. Design handlers that don't depend on receiving events in a specific sequence.

---

❌ Treating webhooks as the only source of truth for critical state.

If the provider's retry window expires before your endpoint recovers, that event is gone unless you also reconcile via polling. Critical financial or state-changing data deserves a fallback path.

---

❌ Accepting a customer-supplied webhook URL without validating it.

If you let users register arbitrary URLs for outbound webhooks *you* send, an attacker can point that URL at your own internal network (`http://169.254.169.254/`, `http://localhost:9200`) and use your server as an SSRF proxy into your own infrastructure. Validate and restrict destination URLs before ever sending a request to one a user supplied.

---

# Key Takeaways

- Webhooks invert the polling model — instead of repeatedly asking "did anything change?", the provider pushes an HTTP POST the moment something actually happens.
- Delivery is at-least-once, never exactly-once — every webhook handler must be idempotent, using the same event-ID deduplication pattern as idempotent API design.
- Respond fast and process asynchronously — a slow synchronous handler risks a provider-side timeout, which triggers a retry and duplicate processing.
- Always verify the signature (HMAC) and a timestamp before trusting the payload — an unverified webhook endpoint is an open door for forged events.
- Never assume delivery order — design handlers that tolerate out-of-order events.
- Don't treat webhooks as the sole source of truth for critical state — pair them with periodic reconciliation polling as a correctness backstop.
- If your system sends outbound webhooks to user-supplied URLs, validate those URLs to prevent SSRF against your own internal infrastructure.
