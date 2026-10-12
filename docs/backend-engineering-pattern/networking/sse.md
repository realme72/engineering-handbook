# SSE (Server-Sent Events)

# Why Does SSE Exist?

WebSockets solve real-time server-to-client push by providing genuine, full bidirectional communication — but a large share of real use cases don't actually need the client to send anything back over that same channel at all. A live sports score ticker, a notification feed, or a stream of tokens from an AI model generating a response only ever need data flowing in **one direction**: server to client. Building all of WebSockets' bidirectional complexity — a protocol upgrade, a persistent full-duplex socket, its own message framing — is more machinery than the actual problem requires.

```
Use case needs:  server pushes updates to client, continuously,
                  over time — client never needs to send anything
                  back over this same channel

WebSockets give you:  full bidirectional communication (more than needed)

SSE gives you:         exactly one-way server push, and nothing more
```

SSE exists specifically to fill this gap — a simpler mechanism for the common case where only server-to-client push is actually required.

---

# How It Works — It's Just HTTP

This is the single most important thing to understand about SSE, and what distinguishes it structurally from WebSockets: there's no protocol upgrade at all. It's an entirely ordinary HTTP request whose response simply never finishes — the server keeps the connection open and streams new data over time, formatted as plain text events.

```http
GET /events HTTP/1.1
Accept: text/event-stream
```

```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"score": "2-1"}

data: {"score": "2-2"}

data: {"score": "3-2"}

```

```
Client makes ONE ordinary HTTP request

↓

Server responds with Content-Type: text/event-stream, and simply
KEEPS THE CONNECTION OPEN, writing new "data: ..." lines to the
response body over time, as events occur

↓

The client (via the browser's built-in EventSource API) reads
these events as they arrive, without ever closing the connection
or making a new request
```

Because this is fundamentally just a long-lived, ordinary HTTP response — not a protocol upgrade to something else — it passes through existing HTTP-aware infrastructure (proxies, load balancers) far more naturally than WebSockets sometimes do, since none of that infrastructure needs to understand anything beyond normal HTTP at all.

---

# Automatic Reconnection, Built In

A genuinely convenient, often-overlooked detail: the browser's built-in `EventSource` API automatically reconnects if the connection drops, with no extra code required.

```javascript
const events = new EventSource("/events");

events.onmessage = (event) => {
    console.log("New event:", event.data);
};

// if the connection drops for any reason, EventSource automatically
// reconnects on its own — no manual retry logic needed
```

This comes essentially for free specifically because SSE is built directly on standard HTTP semantics — the browser already knows how to retry an HTTP request, and `EventSource` simply applies that familiar behavior automatically on disconnect, without the application needing to implement its own reconnection logic the way a raw WebSocket client typically would.

---

# SSE vs WebSockets — The Trade-off

| | SSE | WebSockets |
|---|---|---|
| Direction | One-way (server → client) only | Full bidirectional |
| Protocol | Plain HTTP, no upgrade | Requires a protocol upgrade |
| Reconnection | Automatic, built into `EventSource` | Manual, application-implemented |
| Infrastructure compatibility | Works through standard HTTP infra naturally | Can require special proxy/load balancer support |
| Best for | Notifications, live feeds, one-way streaming | Chat, collaborative editing, anything genuinely two-way |

If the client ever needs to send data back over the *same* channel — not just make an occasional separate, ordinary HTTP request, but genuinely push data back continuously — SSE's one-way limitation makes WebSockets the better fit. If the requirement is purely "the server needs to push updates to the client over time," SSE is the simpler, lighter, more infrastructure-friendly choice.

---

# Real-World Examples

### Live Sports Score Updates

A textbook one-way streaming use case — scores update continuously, pushed from the server, with no need for the client to send anything back over the same channel at all.

---

### Notification Feeds

A running feed of new notifications pushed to a connected client as they occur — again, purely one direction, making SSE's simpler model a natural fit over WebSockets' added bidirectional complexity.

---

### Streaming AI-Generated Responses, Token by Token

A directly relevant, modern example — a chat interface displaying an AI model's response as it's generated, one token or chunk at a time, is exactly SSE's use case: the server pushes each new piece of the response as it becomes available, and the client has no need to send anything back over that same streaming connection.

---

# Common Interview Questions

## SSE vs WebSockets — when would you choose each?

SSE when the requirement is purely one-way, server-to-client push — live feeds, notifications, streaming a response incrementally — since it's simpler, works over plain HTTP with no protocol upgrade, and gets automatic reconnection for free. WebSockets when the client genuinely needs to send data back over the same persistent channel, not just occasionally make a separate request — chat applications, collaborative editing, anything truly bidirectional.

---

## How does SSE work if it's "just HTTP"?

The client makes a completely ordinary HTTP request, and the server's response simply never finishes — it keeps the connection open and writes new, plain-text-formatted events to the response body over time (`Content-Type: text/event-stream`). The browser's `EventSource` API reads these events as they arrive, without the connection ever needing to be closed and reopened, or upgraded to a different protocol.

---

## Why does SSE get automatic reconnection essentially for free, while WebSockets don't?

Because SSE is built directly on standard HTTP request/response semantics, and browsers already know how to retry an HTTP request — the built-in `EventSource` API simply applies that familiar retry behavior automatically if the connection drops. WebSockets, being a distinct protocol after the upgrade, require the application to implement its own reconnection logic explicitly, since there's no equivalent built-in browser mechanism assuming "just retry the request" the way there is for ordinary HTTP.

---

## Why might SSE be easier to deploy through existing infrastructure than WebSockets?

Because it never leaves HTTP semantics at all — no protocol upgrade occurs, so proxies, load balancers, and other HTTP-aware infrastructure that already understand ordinary long-lived HTTP responses can handle it without any special-cased support, unlike WebSockets, which sometimes require explicit configuration to correctly handle the protocol upgrade.

---

## Would SSE work for a chat application?

Only partially — SSE could push incoming messages to a client just fine, but the client would still need a separate mechanism (an ordinary HTTP POST request) to send its own messages, since SSE itself is strictly one-way. A genuinely bidirectional use case like chat is usually a better fit for WebSockets, where both directions share the same persistent connection natively.

---

# Common Mistakes

❌ Reaching for WebSockets by default when the actual requirement is one-way server push.

SSE is simpler, lighter, and easier to operate through standard HTTP infrastructure for exactly that case — defaulting to WebSockets' added bidirectional complexity when it isn't needed is unnecessary overhead.

---

❌ Assuming SSE requires any special protocol upgrade or non-standard infrastructure support.

It's built entirely on plain HTTP semantics — no upgrade occurs at all, which is precisely what makes it compatible with existing HTTP-aware infrastructure without special handling.

---

❌ Not realizing SSE is strictly one-way.

If a use case genuinely needs the client to push data back continuously over the same channel, SSE alone doesn't provide that — it would need to be paired with separate, ordinary HTTP requests for the client-to-server direction, or the use case may be better served by WebSockets entirely.

---

# Key Takeaways

- SSE exists for the common case where only one-way, server-to-client push is needed — a lighter alternative to WebSockets' full bidirectional complexity for exactly that scenario.
- It's built entirely on ordinary HTTP — the server's response simply never finishes, streaming plain-text-formatted events over time, with no protocol upgrade involved at all.
- Automatic reconnection comes essentially for free through the browser's `EventSource` API, since SSE relies on familiar HTTP retry behavior rather than requiring custom reconnection logic.
- Because it never leaves HTTP semantics, SSE tends to work more naturally through existing HTTP-aware infrastructure (proxies, load balancers) than WebSockets sometimes do.
- Choose SSE for one-way streaming needs (live feeds, notifications, incremental AI response streaming); choose WebSockets when the client genuinely needs to push data back over the same persistent connection.
