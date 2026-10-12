# HTTPS

# Why Does HTTPS Exist?

HTTP has no security built in — no encryption, no authentication, no integrity protection, as covered in the HTTP and TLS chapters. HTTPS is the practical fix: HTTP running inside a TLS-encrypted connection. Most of the modern web now treats it as non-negotiable rather than optional.

```
HTTP:    application data sent in PLAINTEXT over TCP

HTTPS:   the exact same HTTP request/response structure, but sent
         through an ENCRYPTED TLS tunnel established first
```

---

# How It Actually Works, Mechanically

```
1. TCP three-way handshake  (from the TCP chapter)

↓

2. TLS handshake  (from the TLS chapter) — establishes the
    encrypted tunnel, verifies the server's certificate

↓

3. THE ACTUAL HTTP REQUEST/RESPONSE happens INSIDE that
    now-encrypted tunnel — everything from this point on is
    encrypted, including the request method, path, headers, and body
```

```
Client                                          Server

  │  TCP SYN/SYN-ACK/ACK  (from TCP chapter)      │
  │◄──────────────────────────────────────────────►│

  │  TLS handshake  (from TLS chapter)             │
  │◄──────────────────────────────────────────────►│

  │  ── everything below this line is ENCRYPTED ──  │

  │  GET /products/15 HTTP/1.1                     │
  ├────────────────────────────────────────────────►│

  │            HTTP/1.1 200 OK ...                  │
  │◄────────────────────────────────────────────────┤
```

HTTPS doesn't change HTTP's own structure at all. It's the exact same request/response format from the HTTP chapter, just carried inside an encrypted TLS connection instead of a plain TCP one.

---

# Port 80 vs Port 443

```
HTTP:   conventionally uses port 80

HTTPS:  conventionally uses port 443
```

A client requesting `https://example.com` connects to port 443 by default and does the TLS handshake there before any HTTP traffic flows. That convention is how a server knows, just from which port a connection arrives on, whether to expect plain HTTP or start a TLS handshake immediately.

---

# Why "HTTPS Everywhere" Became the Default Expectation

Didn't happen overnight. A few specific forces drove it, and it's a genuinely common thing to be asked to explain.

```
Let's Encrypt (2016):  free, automated certificate issuance —
                        removed the real, recurring cost that
                        previously discouraged smaller sites from
                        adopting HTTPS at all

Browser warnings:      browsers began actively marking plain HTTP
                        pages as "Not Secure," turning what used to
                        be an invisible default into a visible,
                        user-facing warning

Search ranking:        search engines began factoring HTTPS usage
                        into ranking signals, giving site owners a
                        direct incentive beyond security alone

Mixed content warnings: loading even a single plain-HTTP resource
                        (an image, a script) on an otherwise HTTPS
                        page triggers browser warnings/blocking,
                        pushing sites toward being consistently
                        HTTPS end-to-end rather than partially
```

Together, these turned "use HTTPS" from an optional, security-conscious choice into the industry-wide default it is now.

---

# HSTS (HTTP Strict Transport Security)

Closes a real, exploitable gap that HTTPS alone leaves open.

```
Without HSTS:

User types "example.com" (no scheme) → browser defaults to
                                          PLAIN HTTP first

↓

If example.com normally redirects HTTP → HTTPS, this redirect
itself is a moment of vulnerability — an attacker positioned on
the network (a "man in the middle") could intercept that initial
plain HTTP request BEFORE the redirect happens, and simply never
let the redirect occur, keeping the victim on plain HTTP indefinitely
(a "downgrade" or "SSL stripping" attack)
```

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

```
With HSTS:  once a browser has seen this header from a domain
             (even just once), it REMEMBERS, for the specified
             duration, to NEVER attempt plain HTTP for that domain
             again — it rewrites the request to HTTPS internally,
             BEFORE ever sending anything over the network at all
```

The browser never even attempts the vulnerable plain-HTTP request in the first place, for any domain it's already seen this header from. No window left for an attacker to strip away a redirect that would otherwise happen.

---

# Real-World Examples

### Let's Encrypt's Impact

Removed cost as a barrier, which took HTTPS from "a deliberate investment" to "no reason not to" for essentially every site, regardless of size or budget — a huge share of the "HTTPS everywhere" shift traces back here.

---

### Browser "Not Secure" Warnings

Modern browsers actively flag plain HTTP pages, especially ones with forms — a default browser behavior that would've been unthinkable a decade earlier, and a direct reflection of how thoroughly the norm has shifted.

---

### HSTS Preload Lists

Browsers ship with a hardcoded list of domains that should always be treated as HTTPS-only, even on someone's very first visit — solving HSTS's own remaining gap, since a browser can't remember a header it's never seen before that first request.

---

# Common Interview Questions

## What's the actual difference between HTTP and HTTPS, mechanically?

HTTPS is HTTP running inside a TLS-encrypted connection. After the standard TCP handshake, a TLS handshake establishes an encrypted tunnel and verifies the server's certificate, and only then does the actual HTTP request/response — same structure as plain HTTP — get sent, now encrypted, inside that tunnel.

---

## What is HSTS, and what specific attack does it prevent?

A header telling the browser to always use HTTPS for a domain going forward, without ever attempting plain HTTP first. It prevents a downgrade (SSL stripping) attack, where an attacker intercepts the initial plain-HTTP request before an expected redirect to HTTPS, and simply prevents that redirect from happening, keeping the victim on an insecure connection indefinitely.

---

## Why did "use HTTPS everywhere" become the default expectation rather than an optional choice?

Several forces converged: Let's Encrypt made certificates free and automated, browsers started warning on plain HTTP, search engines factored HTTPS into ranking, and mixed-content warnings pushed sites toward being consistently HTTPS end-to-end. Together, they turned HTTPS from a security-conscious choice into a near-universal requirement.

---

## Does HTTPS only provide encryption?

No — it also authenticates the server (via its certificate) and protects data integrity. Encryption alone would still let a connection be encrypted while talking to an impostor; authentication is what rules that out.

---

# Common Mistakes

❌ Thinking of HTTPS as simply "HTTP but encrypted," with no other guarantee.

It also authenticates the server's identity and protects data integrity — treating it as encryption alone misses why the certificate check matters at all.

---

❌ Not understanding what HSTS specifically protects against.

It's not a general security boost — it closes one specific gap: the vulnerable moment during an HTTP-to-HTTPS redirect, before HSTS, where an attacker could intercept and prevent that redirect from completing.

---

❌ Assuming HSTS protects a domain's very first-ever visit from any browser.

A browser can only remember an HSTS policy after seeing the header at least once — the first request to a domain it's never encountered has no protection, unless that domain is on a browser's hardcoded preload list.

---

# Key Takeaways

- HTTPS is HTTP carried inside a TLS-encrypted connection — the request/response structure is unchanged; only the transport underneath is now encrypted and authenticated.
- "HTTPS everywhere" came from several converging forces — free automated certificates, browser warnings, search ranking, mixed-content restrictions — not one single cause.
- HSTS closes a specific vulnerability: the moment during an HTTP-to-HTTPS redirect where an attacker could intercept and strip it away, keeping a victim on an insecure connection.
- HTTPS provides encryption, authentication, and integrity together — not encryption alone, which is why certificate verification matters as much as the encryption itself.
- HSTS preload lists close HSTS's remaining gap — protecting a domain even on a browser's very first visit, by baking a known list of HTTPS-only domains directly into the browser.
