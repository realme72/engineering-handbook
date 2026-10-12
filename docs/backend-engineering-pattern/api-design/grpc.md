# gRPC

# Why Does gRPC Exist?

Google runs an internal architecture with thousands of services calling each other, constantly, at enormous volume — order-of-magnitude more traffic between services than between any external client and the edge. Internally, Google had used a system called **Stubby** for over a decade before open-sourcing its public descendant as **gRPC** in 2015.

The problems Stubby (and later gRPC) needed to solve are different from the problems REST solves, because the traffic is different:

```
External client → API           Occasional, human-facing, browser-friendly needed

Service → Service (internal)    Constant, enormous volume, latency-sensitive,
                                 every microsecond and byte matters at scale
```

At Google's internal volume, the overhead REST just shrugs off — parsing JSON text, the verbosity of field names repeated in every single response, a new TCP connection per request-response cycle on old HTTP/1.1 — actually costs real money and real latency, multiplied across billions of internal calls a day.

gRPC's answer: stop sending human-readable text, and stop treating every call as a brand-new one-off connection.

```
REST:   JSON over HTTP/1.1     — human-readable, verbose, new connection overhead

gRPC:   Protobuf over HTTP/2   — compact binary, strict typed contract, multiplexed connections
```

---

# What Problem It Actually Solves

- **Payload size** — Protocol Buffers encode data as compact binary instead of repeating field names as text in every message, which is significantly smaller on the wire than the equivalent JSON.
- **Serialization speed** — parsing binary into a typed struct is faster than parsing and validating JSON text at high volume.
- **Strict, enforced contracts** — the `.proto` file is the single source of truth for the API shape, and client/server code is generated directly from it — no hand-written client silently drifting out of sync with what the server actually returns, which is a genuinely common bug in loosely-typed REST integrations.
- **Multiplexing over one connection** — HTTP/2 allows many concurrent requests over a single TCP connection, instead of HTTP/1.1's one-request-in-flight-per-connection model, dramatically cutting connection overhead for chatty internal service-to-service traffic.
- **Native streaming** — a single call can stream many messages in either or both directions over one long-lived connection, which REST has no clean native equivalent for.
- **Polyglot by design** — the same `.proto` file generates working client and server code in Go, Java, Python, C++, and a dozen other languages, which matters enormously at a company where every team picks its own language.

---

# Protocol Buffers (The Contract)

Everything starts with a `.proto` file — a strongly-typed schema definition, independent of any programming language.

```protobuf
syntax = "proto3";

message GetUserRequest {
  int32 user_id = 1;
}

message User {
  int32 id = 1;
  string name = 2;
  string email = 3;
}

service UserService {
  rpc GetUser (GetUserRequest) returns (User);
}
```

The `protoc` compiler generates client and server stub code directly from this file, in whatever language you need:

```bash
protoc --python_out=. --grpc_python_out=. user.proto
```

The generated code gives you typed request/response objects and a client that looks and feels like calling a local function — except now the network round trip and serialization are handled for you, correctly, by generated code instead of hand-rolled JSON parsing.

## The Field Numbers Matter More Than the Field Names

```protobuf
message User {
  int32 id = 1;
  string name = 2;
  string email = 3;
}
```

Those `= 1`, `= 2`, `= 3` numbers are what actually gets encoded on the wire — not the field names. That's the single most important fact about protobuf for safe schema evolution, and it's where the mistakes happen (covered below).

---

# Python Implementation

Using the generated code from the `.proto` file above:

```python
# server.py
import grpc
from concurrent import futures
import user_pb2
import user_pb2_grpc

class UserService(user_pb2_grpc.UserServiceServicer):
    def GetUser(self, request, context):
        user = db.get_user(request.user_id)
        return user_pb2.User(id=user.id, name=user.name, email=user.email)

server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
server.add_insecure_port("[::]:50051")
server.start()
server.wait_for_termination()
```

```python
# client.py
import grpc
import user_pb2
import user_pb2_grpc

channel = grpc.insecure_channel("localhost:50051")
stub = user_pb2_grpc.UserServiceStub(channel)

response = stub.GetUser(user_pb2.GetUserRequest(user_id=42))
print(response.name)
```

Notice the client code — `stub.GetUser(...)` — reads almost exactly like calling a local method. That's deliberate. But it's the same trap REST's whole existence was a reaction to: it *looks* like a local function call, but it's still a network call underneath, with all the latency and failure modes that implies. gRPC makes the call ergonomic. It doesn't make it free.

---

# The Four Call Types

## Unary

```protobuf
rpc GetUser (GetUserRequest) returns (User);
```

One request, one response — the direct equivalent of a typical REST call.

## Server Streaming

```protobuf
rpc ListOrders (ListOrdersRequest) returns (stream Order);
```

```python
for order in stub.ListOrders(request):
    print(order.id)
```

One request, a stream of responses over time — useful for large result sets the client wants to start processing before the entire thing has arrived, or live server-pushed updates (stock price ticks, log tailing).

## Client Streaming

```protobuf
rpc UploadMetrics (stream MetricPoint) returns (UploadSummary);
```

The client streams many messages, the server responds once at the end — a natural fit for uploading a large dataset or batching many small events into a single logical call.

## Bidirectional Streaming

```protobuf
rpc Chat (stream ChatMessage) returns (stream ChatMessage);
```

Both sides stream independently over the same long-lived connection — the closest gRPC gets to a persistent, full-duplex connection like a WebSocket, but with the same strict typed contract as every other gRPC call.

---

# Why HTTP/2 Specifically

```
HTTP/1.1                              HTTP/2

One request in flight per connection   Many concurrent requests, one connection
(or pay for more TCP connections)       (multiplexed streams)

Text headers, repeated every request   Compressed, differential header encoding

No native server push / streaming      Native streaming support
```

For chatty internal service-to-service traffic — Service A calling Service B potentially hundreds of times to serve one external request — multiplexing over a single connection removes a meaningful amount of the connection-setup and head-of-line-blocking overhead that HTTP/1.1 forces on high-frequency callers. This is a big part of why gRPC and HTTP/2 are inseparable in practice, not an arbitrary pairing.

---

# gRPC vs REST — Trade-offs

| | REST | gRPC |
|---|---|---|
| Payload format | JSON (text) | Protobuf (binary) |
| Human readable | Yes | No — needs tooling to inspect |
| Browser support | Native | Needs a proxy (grpc-web) |
| Contract enforcement | Optional (OpenAPI, if you bother) | Mandatory — the `.proto` file *is* the contract |
| Streaming | Awkward (SSE, chunked, WebSockets bolted on) | Native, all four call shapes |
| Debuggability with curl/Postman | Trivial | Needs `grpcurl` or similar |
| Typical use | Public APIs, browser clients | Internal service-to-service calls |

The debuggability trade-off is a real, everyday cost, not a footnote — you cannot just `curl` a gRPC endpoint and read the response the way you can with REST. Tooling exists (`grpcurl`, `evans`, gRPC reflection), but it's an extra step every engineer on the team needs to know about, versus REST's "literally paste it into a browser" baseline.

## Not Natively Browser-Friendly

Browsers can't originate raw HTTP/2 trailers-based gRPC calls the way a native gRPC client can. Bridging this requires **grpc-web**, a variant that runs over standard HTTP/1.1 or HTTP/2 through a proxy translating between the browser-friendly wire format and true gRPC on the backend. That's why gRPC dominates internal traffic but rarely faces a browser directly — REST or GraphQL still owns that edge in most architectures, with gRPC taking over once the request crosses into internal territory.

---

# Safe Schema Evolution

Because field numbers, not names, are what's actually encoded on the wire, protobuf has strict rules for changing a message without breaking already-deployed clients running an older version of the schema.

## Safe Changes

```protobuf
message User {
  int32 id = 1;
  string name = 2;
  string email = 3;
  string phone = 4;   // adding a new field with a NEW number — safe
}
```

An old client that doesn't know about field 4 simply ignores it. A new client talking to an old server that doesn't send field 4 gets its default value. Neither side breaks.

## Dangerous Changes

```protobuf
message User {
  int32 id = 1;
  string name = 2;
  // string email = 3;   ← removed
  string phone = 3;      // ← reused number 3 for something else entirely
}
```

```
Old client sends a message with field 3 = "alice@example.com" (a string, meant as email)

↓

New server reads field 3 expecting "phone"

↓

Old data gets silently misinterpreted as the wrong field
```

This is the protobuf equivalent of undefined behavior — reusing a field number is worse than a crash, because it doesn't fail loudly, it silently corrupts data across versions. The correct move when retiring a field is to reserve its number so it can never accidentally be reused later:

```protobuf
message User {
  reserved 3;
  reserved "email";

  int32 id = 1;
  string name = 2;
  string phone = 4;
}
```

---

# Real-World Examples

### Google (Internal)

The original motivating case — Stubby, gRPC's internal predecessor, handling the enormous volume of service-to-service calls inside Google for over a decade before gRPC was open-sourced as its public descendant in 2015.

---

### Kubernetes / Envoy (xDS API)

Envoy's dynamic configuration protocol (xDS — how Envoy proxies get routing and service discovery updates from a control plane) is built on gRPC, leaning on bidirectional streaming to push configuration continuously over one long-lived connection instead of proxies polling for changes.

---

### Netflix, Square, and Most Large Microservice Shops

Adopted for internal service-to-service communication, where the strict typed contract and performance matter more than browser accessibility — while these same companies' public-facing APIs still tend to be REST or GraphQL, because that's what external clients and browsers actually need.

---

# Common Interview Questions

## When would you choose gRPC over REST?

For internal, high-volume, latency-sensitive service-to-service communication where you control both ends and want a strictly enforced typed contract — not for a public API that needs to be browser-accessible or trivially debuggable with `curl`. The two aren't really competing for the same use case; REST tends to own the external edge, gRPC tends to own internal traffic.

---

## Why is protobuf faster and smaller than JSON?

JSON is text — field names are repeated as strings in every single message, and parsing means tokenizing and validating text. Protobuf encodes field numbers and typed values directly as binary, with no repeated field-name text at all, which is both smaller on the wire and faster to parse into a typed structure.

---

## Why does gRPC use HTTP/2 instead of HTTP/1.1?

HTTP/2 multiplexes many concurrent requests over a single TCP connection, which matters enormously for chatty internal service-to-service traffic that would otherwise pay repeated connection-setup overhead, or be limited by HTTP/1.1's one-request-in-flight-per-connection model. HTTP/2 is also a prerequisite for gRPC's native streaming support.

---

## What are the four types of gRPC calls?

Unary (one request, one response — like a typical REST call), server streaming (one request, a stream of responses), client streaming (a stream of requests, one final response), and bidirectional streaming (both sides stream independently over the same connection).

---

## Why can't you remove a field from a `.proto` message and reuse its number for something new?

Because the field *number*, not the name, is what's actually encoded on the wire. An old client still sending data under the old field's number would have that data silently misinterpreted as whatever the new field means — a silent data-corruption bug across versions, not a loud failure. The safe pattern is marking retired field numbers `reserved` so they can never be accidentally reused.

---

## Why isn't gRPC used directly from browsers?

Browsers can't originate the raw HTTP/2 trailer-based calls gRPC relies on natively. Browser access requires **grpc-web**, a variant running through a proxy that translates between a browser-compatible wire format and true gRPC on the backend — which is part of why REST or GraphQL still typically own the browser-facing edge, with gRPC taking over once traffic moves to internal service-to-service calls.

---

# Common Mistakes

❌ Reusing a removed field's number for a new field.

Silently corrupts data for any client still running an older version of the schema — mark retired numbers `reserved` instead.

---

❌ Exposing gRPC directly to a browser client without grpc-web.

Browsers cannot make native gRPC calls — this requires an explicit proxy layer, not a client-side workaround.

---

❌ Treating a gRPC call as free just because it reads like a local function call.

It's still a network call — latency, timeouts, and partial failure are all still real. Deadline propagation across a chain of gRPC calls (so a slow downstream call doesn't silently outlive the caller's own timeout budget) needs to be handled deliberately.

---

❌ Skipping `grpcurl`/reflection tooling and assuming gRPC APIs are as easy to poke at as REST.

Binary payloads aren't human-readable — plan for the debugging tooling gap upfront instead of discovering it during an incident.

---

❌ Assuming gRPC is strictly "better" and should replace REST everywhere.

It solves a specific problem (fast, strictly-typed, internal service-to-service communication) at the cost of browser-friendliness and easy debuggability — the right choice depends entirely on who's calling the API and why.

---

# Key Takeaways

- gRPC descends from Google's internal Stubby system, built specifically for high-volume, latency-sensitive service-to-service traffic — a different problem than REST's public, browser-facing use case.
- Protocol Buffers give a compact binary format and a strictly enforced, code-generated contract — no hand-written client silently drifting from what the server actually returns.
- HTTP/2 multiplexing is what makes gRPC efficient for chatty internal traffic, and is a prerequisite for gRPC's native streaming support.
- gRPC supports four call shapes — unary, server streaming, client streaming, and bidirectional streaming — with no REST equivalent for the streaming variants.
- Field *numbers*, not names, are encoded on the wire — reusing a retired field number silently corrupts data across schema versions; always mark it `reserved` instead.
- gRPC isn't natively browser-accessible (needs grpc-web) and isn't as easy to debug ad hoc as REST — which is exactly why it dominates internal service-to-service traffic while REST/GraphQL typically still own the external, browser-facing edge.
