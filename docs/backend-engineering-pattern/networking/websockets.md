# WebSockets

# Why Do WebSockets Exist?

Every version of HTTP covered so far — 1.1, 2, 3 — shares one unavoidable structural assumption: the **client** initiates every exchange. A server can never spontaneously send data to a client; it can only respond to a request the client already made. That assumption breaks down completely for a real class of applications that need the opposite — a chat message arriving, a live notification, another user's cursor moving in a collaborative document — where the **server** needs to push data to the client the instant something happens, without the client having asked first.

```
HTTP's fundamental shape:

Client → request → Server → response → (done, connection can close)

↓

There's no way for the server to say "here's something new"
UNLESS the client asks again first
```

WebSockets exist to provide a genuinely different shape: a persistent, full-duplex connection where either side can send a message to the other, at any time, independently — not a request/response exchange at all once established.

---

# The Workarounds Before WebSockets

## Polling

```
Client: "anything new?" → Server: "no"
... wait a few seconds ...
Client: "anything new?" → Server: "no"
... wait a few seconds ...
Client: "anything new?" → Server: "yes, here it is"
```

The exact same wasteful pattern covered in the Webhooks chapter's opening — repeatedly asking, mostly getting "no," at the cost of both wasted requests and real latency (the update sits waiting until the next poll interval, however long that is).

## Long Polling

```
Client: "anything new?" → Server HOLDS the request open,
                            doesn't respond yet

↓ (server waits until something actually happens)

Server: "yes, here it is" → responds

↓

Client IMMEDIATELY re-issues the same request, and the cycle repeats
```

Better than plain polling — the server responds the moment something's actually available rather than making the client wait for its next scheduled check — but it's still fundamentally a sequence of separate HTTP request/response cycles, each with its own overhead, dressed up to look continuous.

---

# The WebSocket Handshake

A WebSocket connection begins as an entirely ordinary HTTP request — this matters, because it means WebSockets can work through the same infrastructure (proxies, firewalls) that already understands HTTP.

```http
GET /chat HTTP/1.1
Host: example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
```

```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

```
Client sends a normal HTTP request, with an "Upgrade: websocket" header

↓

If the server agrees (responds with 101 Switching Protocols)

↓

The SAME underlying TCP connection is repurposed — it's no longer
carrying HTTP semantics at all from this point forward, just raw,
framed WebSocket messages
```

This is a genuinely important detail: after the handshake completes, the connection is no longer "HTTP" in any meaningful sense — it's a raw, persistent socket that happens to have started its life as an HTTP request specifically to get through standard web infrastructure and negotiate the upgrade.

---

# Full-Duplex Communication

```
HTTP:        Client → request → Server → response
             (strictly one direction, then the other, per exchange)

WebSocket:   Client ⟷ Server
             (either side can send a message AT ANY TIME,
              independently, with no request/response pairing at all)
```

```python
# server side, conceptually
async def on_message(websocket, message):
    # a message arrived from the client — respond, broadcast, or
    # do nothing at all, on the server's own schedule
    await broadcast_to_other_clients(message)

# the server can ALSO push a message to this client at any moment,
# with no client request having triggered it
await websocket.send("Someone else just joined the chat")
```

This is the actual capability that makes WebSockets fit for chat applications, live collaborative editing, and real-time multiplayer state — data can flow in either direction the instant it's ready, with no polling, no waiting for the next client-initiated request, and none of the round-trip overhead of establishing a brand-new HTTP connection for every single exchange.

---

# The Real Operational Cost: Long-Lived, Stateful Connections

Worth being explicit about, since it's a genuine trade-off and not just a footnote: a WebSocket connection stays open, tying up server-side resources (memory, a held-open socket) for its entire lifetime — potentially minutes or hours — unlike a typical HTTP request, which completes quickly and frees its resources almost immediately.

```
HTTP request/response:  server resources held briefly, then freed

WebSocket connection:   server resources held for the ENTIRE
                        duration the connection stays open —
                        which could be a very long time
```

At scale, this is a real, meaningful capacity-planning consideration — a server that could comfortably handle tens of thousands of quick HTTP requests per second might only be able to sustain a much smaller number of simultaneously open, long-lived WebSocket connections, purely because each one is holding onto resources continuously rather than briefly.

---

# Real-World Examples

### Chat Applications (Slack, Discord)

The canonical WebSocket use case — messages need to arrive at every connected client the instant they're sent, with no polling delay, and users need to be able to send messages at any time without waiting on a server-initiated request first.

---

### Collaborative Editing (Google Docs–Style)

Every keystroke or cursor movement from any connected user needs to propagate to every other connected user in near real time — a genuinely bidirectional, continuous stream of small updates in both directions, exactly the shape WebSockets are built for.

---

### Real-Time Multiplayer Game State

Player actions and world state updates need to flow continuously in both directions between client and server, often layered on top of additional application-level protocols for handling the specific latency and ordering needs of game state (sometimes UDP-based instead, depending on the game's specific tolerance for loss vs latency, as covered in the UDP chapter).

---

# Common Interview Questions

## Why can't you just use regular HTTP requests for real-time, bidirectional communication?

Because HTTP's fundamental model requires the client to initiate every exchange — a server can never spontaneously push data to a client without the client having asked first. Polling and long polling both work around this by having the client repeatedly ask, but neither provides genuine, low-latency, bidirectional communication the way a persistent WebSocket connection does.

---

## Walk through the WebSocket handshake.

The client sends a normal HTTP request with an `Upgrade: websocket` header. If the server agrees, it responds with a `101 Switching Protocols` status, and from that point forward, the same underlying TCP connection is repurposed to carry raw WebSocket frames instead of HTTP semantics — it's no longer really "HTTP" after the handshake completes.

---

## Does a WebSocket connection still use HTTP after the handshake?

No — the handshake itself is an HTTP request specifically to negotiate the upgrade (and to work through existing HTTP-aware infrastructure like proxies), but once the server agrees and the connection upgrades, it becomes a persistent, raw socket carrying WebSocket frames, with none of HTTP's request/response semantics applying to the ongoing communication anymore.

---

## Long polling vs WebSockets — what's the trade-off?

Long polling reuses ordinary HTTP infrastructure and requires no protocol upgrade, but still involves repeated request/response cycles, each with its own overhead, dressed up to feel continuous. WebSockets provide genuine, low-overhead, bidirectional communication over one persistent connection, at the cost of that connection staying open and consuming server-side resources for its entire lifetime, which is a real operational and capacity-planning consideration at scale.

---

## What's the operational cost of using WebSockets at scale?

Each open WebSocket connection holds server-side resources (memory, a held-open socket) continuously for as long as it stays open — potentially minutes or hours — unlike a typical HTTP request, which completes and frees its resources quickly. This means a server's realistic capacity for simultaneous WebSocket connections is a genuinely different, and often much lower, number than its capacity for quick HTTP requests per second.

---

# Common Mistakes

❌ Assuming WebSockets are still "HTTP requests" after the handshake completes.

The connection upgrades away from HTTP semantics entirely — it's a persistent, raw socket from that point on, only having started as an HTTP request to negotiate the upgrade itself.

---

❌ Reaching for WebSockets without considering the operational cost of many long-lived connections.

Unlike stateless HTTP requests that complete and free resources quickly, each open WebSocket ties up server resources for its full lifetime — a real scaling consideration that needs deliberate capacity planning, not an assumption that it behaves like ordinary request traffic.

---

❌ Using WebSockets for a use case that only needs one-way, server-to-client push.

Full bidirectional communication is more protocol complexity than the problem requires if the client never actually needs to send data back over the same channel — worth checking whether a simpler, one-way mechanism (covered in the SSE chapter) would fit the actual requirement better.

---

# Key Takeaways

- WebSockets exist because HTTP's request/response model fundamentally requires the client to initiate every exchange, which doesn't fit real-time, bidirectional use cases like chat, collaborative editing, or live multiplayer state.
- The connection begins as a normal HTTP request with an `Upgrade` header — if the server agrees, the same underlying TCP connection is repurposed into a persistent, full-duplex WebSocket connection, no longer carrying HTTP semantics.
- Full-duplex means either side can send a message at any time, independently — a fundamentally different shape than HTTP's strict request-then-response pattern.
- Each open WebSocket connection holds server-side resources for its entire lifetime, unlike a quick, stateless HTTP request — a real, meaningful capacity-planning consideration at scale.
- WebSockets are the right choice specifically when genuine bidirectional communication is needed — a simpler one-way mechanism may be a better fit when only server-to-client push is actually required.
