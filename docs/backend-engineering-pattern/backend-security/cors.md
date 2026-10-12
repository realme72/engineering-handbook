# CORS (Cross-Origin Resource Sharing)

# Why Does CORS Exist?

Browsers enforce the **same-origin policy** by default — JavaScript on one site can't read the response of a request it made to a different origin, even if that request actually succeeds. It's a core browser security boundary: without it, a malicious site's script could quietly call another site a victim happens to be logged into and read back whatever comes out. CORS is the mechanism a server uses to deliberately relax that default for specific, trusted callers — an opt-in exception, not a replacement for the policy itself.

```
Without CORS, by default:

JavaScript on evil.com  →  makes a request to yourbank.com

↓

Even if the request SUCCEEDS and yourbank.com responds with data,
the browser BLOCKS evil.com's JavaScript from reading that response
at all — same-origin policy protects the user by default
```

---

# The Critical Distinction: A Browser-Enforced Protection, Not a Server-Side One

This is the single most commonly confused point about CORS: **CORS is not a server-side security feature protecting the server** — it's a restriction the **browser** enforces to protect the **user**, by controlling what a webpage's own JavaScript is allowed to read back from a cross-origin response.

```
Common misconception:  "CORS stops unauthorized requests from
                        reaching my server"

Reality:                the request VERY OFTEN STILL REACHES the
                        server regardless of CORS headers (for many
                        kinds of requests) — CORS only controls
                        whether the BROWSER lets the CALLING PAGE'S
                        JavaScript actually READ the response
```

```
A non-browser client — curl, Postman, another server, a mobile app
— IGNORES CORS ENTIRELY, because CORS is a restriction the BROWSER
enforces on JavaScript, not something the server enforces against
incoming requests at all
```

This distinction has real, practical consequences: CORS headers alone do **not** protect an endpoint from being called by anything other than a browser — actual authentication and authorization on the server itself are still fully necessary, independent of whatever CORS policy is configured.

---

# How It Actually Works

```
1. Browser JavaScript on app.example.com makes a request to
   api.example.com (a DIFFERENT origin)

2. The browser automatically adds an Origin header to the request:

   Origin: https://app.example.com

3. The SERVER decides whether to allow this origin, and responds with:

   Access-Control-Allow-Origin: https://app.example.com

4. The BROWSER checks this response header against the requesting
   page's own origin

   ↓

   MATCH → the calling JavaScript IS allowed to read the response

   NO MATCH (or header absent) → the calling JavaScript is BLOCKED
   from reading the response, even though the request itself may
   have already reached and been processed by the server
```

The server has to explicitly cooperate (by returning the right `Access-Control-Allow-Origin` header) for a foreign origin to be granted read access — but the check itself, and the actual enforcement of the restriction, happens entirely inside the browser, on the calling page's JavaScript.

---

# Preflight Requests

For anything beyond a "simple" request (a `GET`/`POST` with only standard, common headers), the browser first sends an `OPTIONS` **preflight** request asking "would you actually allow this specific request" — before sending the real request at all.

```
Browser wants to send:  PUT /api/orders/42
                         Content-Type: application/json
                         X-Custom-Header: something

↓

Browser FIRST sends an OPTIONS preflight request:

OPTIONS /api/orders/42
Origin: https://app.example.com
Access-Control-Request-Method: PUT
Access-Control-Request-Headers: X-Custom-Header

↓

Server responds with what it actually ALLOWS:

Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, POST, PUT
Access-Control-Allow-Headers: X-Custom-Header

↓

ONLY IF the preflight response confirms this specific request is
permitted does the browser THEN send the ACTUAL PUT request
```

This preflight step exists specifically for requests with the potential to have unintended side effects (a non-simple method like `PUT`/`DELETE`, custom headers, certain content types) — giving the server a chance to explicitly confirm it allows this exact combination before the real, potentially state-changing request is ever actually sent.

---

# Real-World Examples

### A Frontend Calling Its Own Company's API on a Different Subdomain

An extremely common, everyday reason CORS configuration matters in practice — `app.example.com`'s frontend calling `api.example.com`'s backend are technically different origins (different subdomains), so the API needs to explicitly configure CORS headers allowing `app.example.com`, or the browser will block the frontend's own JavaScript from reading the API's responses, even though both are owned and operated by the same company.

---

### `Access-Control-Allow-Origin: *` on a Public, Unauthenticated API

A legitimate use of a fully permissive CORS policy. For a public API returning non-sensitive, non-personalized data — reference data, say — letting any origin read the response carries no real risk, since there's nothing sensitive or user-specific in it.

---

### curl and Postman Ignoring CORS Entirely

A common, useful illustration of the distinction covered above — a developer testing an API endpoint with curl or Postman never encounters a CORS error at all, even against an API with a very restrictive CORS policy, precisely because CORS is enforced by the browser's own JavaScript execution environment, not by the server rejecting the request itself.

---

# Common Interview Questions

## What is CORS, and is it a server-security feature or a browser-security feature?

CORS is a browser-enforced restriction, not a server-side security feature — same-origin policy is the browser's default protection preventing a page's JavaScript from reading cross-origin responses, and CORS is the mechanism for a server to explicitly, deliberately relax that restriction for specific trusted origins. The distinction matters because the underlying request can still reach and be processed by the server regardless of CORS headers — CORS only controls whether the calling page's JavaScript is allowed to read the response.

---

## What's the difference between a simple request and a preflighted request?

A simple request (a basic GET or POST with only standard headers) is sent directly, with the browser checking the CORS response headers after the fact to decide whether the calling JavaScript can read the response. A preflighted request — for non-simple methods, custom headers, or certain content types — has the browser first send an OPTIONS request asking what's actually allowed, and only sends the real request if the preflight response confirms it's permitted.

---

## Why does curl or Postman ignore CORS restrictions that a browser enforces?

Because CORS is enforced entirely within a browser's own JavaScript execution environment, restricting what a webpage's script is allowed to read from a cross-origin response — it has nothing to do with the server rejecting requests from non-browser clients. Tools like curl and Postman aren't running any JavaScript subject to that same-origin restriction, so they never encounter a CORS error at all.

---

## What's wrong with setting `Access-Control-Allow-Origin: *` on an endpoint returning sensitive, authenticated data?

It defeats CORS's entire protective purpose for that specific data — any malicious site's JavaScript could then successfully read the sensitive response, since the server has explicitly told every browser it's fine for any origin to access it. Wildcard CORS is only safe for genuinely public, non-sensitive, non-personalized data.

---

## Does CORS protect a server from receiving unauthorized requests at all?

No — CORS controls whether a browser lets calling JavaScript *read* a response, not whether the request reaches the server in the first place. Actual authentication and authorization on the server itself are still fully necessary regardless of CORS configuration, since a non-browser client (or a browser making a "simple" request without needing to read the response) isn't restricted by CORS at all.

---

# Common Mistakes

❌ Setting `Access-Control-Allow-Origin: *` on an endpoint that returns sensitive, authenticated, per-user data.

Completely defeats CORS's protective purpose for that data — any origin's JavaScript can then read it, which is exactly the scenario same-origin policy was meant to prevent by default.

---

❌ Believing CORS protects the server from unauthorized requests reaching it at all.

CORS only controls whether a browser lets calling JavaScript read the response — actual authentication and authorization on the server are still fully necessary and entirely independent of CORS configuration.

---

❌ Being confused when curl or a mobile app successfully calls an API that a browser's JavaScript is blocked from calling.

This is expected, correct behavior — CORS restricts only browser-enforced JavaScript execution contexts, not any other kind of client making the same underlying HTTP request.

---

# Key Takeaways

- CORS is a browser-enforced mechanism, not a server-side security feature — it's the deliberate, explicit exception a server grants to relax the browser's default same-origin policy for specific trusted origins.
- The underlying request can still reach and be processed by the server regardless of CORS headers — CORS only controls whether the calling page's JavaScript is allowed to read the response.
- Preflight (`OPTIONS`) requests let the browser confirm a non-simple request (custom methods, headers) is actually permitted before sending the real, potentially state-changing request.
- A wildcard `Access-Control-Allow-Origin: *` is safe only for genuinely public, non-sensitive data — using it on authenticated or personalized endpoints defeats CORS's entire protective purpose.
- CORS never protects a server from unauthorized requests reaching it in the first place — actual server-side authentication and authorization remain fully necessary regardless of CORS configuration.
