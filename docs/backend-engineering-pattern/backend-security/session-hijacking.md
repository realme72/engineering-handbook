# Session Hijacking

# Why Does Session Hijacking Exist as a Vulnerability?

Once a user logs in, their session — a session ID, or a JWT, covered in the Authentication section — is the only thing proving "this is a logged-in user" on every request after that. Get hold of a victim's session by any means, and you're that user, no password required. The interesting part isn't the impersonation itself; it's the different, specific **ways** a session actually gets stolen, each needing its own fix.

```
Session ID / token = "proof of being logged in"

↓

If an ATTACKER obtains this value, by ANY means, they can send
requests carrying it and the server has NO WAY to distinguish
them from the genuine, original user
```

---

# The Distinct Attack Vectors

## Theft via XSS

```
Attacker's injected script (from a successful XSS attack) reads
document.cookie directly, exfiltrating the victim's session cookie
to the attacker
```

One of XSS's most damaging real payoffs — covered there in more depth. Marking session cookies `HttpOnly` blocks JavaScript from reading the cookie at all, closing this specific vector even if an XSS bug exists somewhere else on the site.

## Theft via Network Eavesdropping

```
Session cookie/token transmitted over an UNENCRYPTED (plain HTTP)
connection

↓

Anyone with visibility into the network path (shared WiFi, a
compromised router, an ISP) can simply READ the session token
directly off the wire
```

This is why HTTPS matters for session security specifically, not just data privacy in the abstract. TLS's encryption is what makes this vector impossible for an eavesdropper who only ever sees encrypted bytes.

## Session Fixation

A subtler one, worth understanding on its own terms: the attacker doesn't steal an existing session at all. They trick the victim into using a session ID the attacker already knows, before the victim ever logs in.

```
1. Attacker visits your-site.com themselves, and obtains a
   session ID: sess_abc123 (not yet authenticated to anything)

2. Attacker sends the VICTIM a crafted link:
   https://your-site.com/login?session_id=sess_abc123

3. Victim clicks the link, and LOGS IN — the site accepts and
   REUSES the session ID from the URL (sess_abc123) rather than
   generating a brand new one upon successful authentication

4. The session sess_abc123 is now AUTHENTICATED as the victim —
   and the ATTACKER ALREADY KNOWS this exact session ID, since
   they created it themselves in step 1

5. Attacker uses sess_abc123 directly — now a fully authenticated
   session belonging to the victim, without ever needing to steal
   anything from the victim's own browser at all
```

Nothing was ever stolen from the victim's browser. They were tricked into logging into a session the attacker had already prepared.

## Physical/Local Access

The mundane one — a shared or compromised device with an active session gives whoever's sitting at it the same access as the legitimate user, no cleverness required.

---

# The Fixes, Matched to Each Vector

```
Against XSS-based theft:        HttpOnly cookie flag (prevents
                                JavaScript from reading the cookie
                                at all, from the XSS chapter)

Against network eavesdropping:   HTTPS everywhere, and the Secure
                                cookie flag (ensures the cookie is
                                NEVER sent over plain HTTP even if
                                a page somehow loads unencrypted)

Against session fixation:        REGENERATE the session ID
                                IMMEDIATELY upon successful
                                authentication — even if an
                                attacker pre-set a known session
                                ID, that ID is DISCARDED and
                                replaced with a brand new one the
                                moment real authentication
                                succeeds, making the attacker's
                                pre-known ID useless

Limiting the DAMAGE regardless
of vector:                       reasonable session expiration/
                                timeout (bounding how long a
                                stolen or fixated session token
                                remains useful to an attacker,
                                even if one is somehow obtained),
                                and binding a session to
                                additional signals like IP address
                                or user agent as an imperfect,
                                additional layer of anomaly
                                detection (imperfect since these
                                CAN legitimately change for a real user)
```

Regenerating the session ID on login kills fixation outright — it doesn't matter that the attacker knew the pre-login ID, because that ID stops existing the instant real authentication succeeds.

---

# Real-World Examples

### Session Fixation in Older Web Frameworks

A well-known historical gap — plenty of older frameworks didn't regenerate session IDs on login by default, which is exactly what made fixation a real, exploitable issue until "regenerate on authentication" became a standard default.

---

### The Ongoing Importance of HTTPS, Specifically Because of Session Theft Risk

A single request served over plain HTTP, even once, is enough for a network eavesdropper to grab a valid session token and fully impersonate that user. That's the concrete reason modern practice treats HTTPS as mandatory rather than a nice-to-have for anything session-related.

---

### HttpOnly and Secure Cookie Flags as Standard, Expected Defaults

Nearly universal in modern frameworks' session cookie config now — a good sign of how well-understood and necessary these two mitigations have become.

---

# Common Interview Questions

## What are the different ways a session can be hijacked or stolen?

Theft via XSS (an injected script reading the cookie directly), theft via network eavesdropping on an unencrypted connection, session fixation (tricking a victim into authenticating a session ID the attacker already knows), and physical or local access to a device with an active session.

---

## What is session fixation specifically, and how does regenerating the session ID on login prevent it?

An attacker gets a session ID without logging in, tricks a victim into using that same ID — often via a crafted link — and once the victim logs in, that now-authenticated ID is one the attacker already knows. Regenerating the session ID on successful authentication defeats it: the attacker's pre-known ID is discarded and replaced the instant real login succeeds, so knowing it in advance buys them nothing.

---

## Why does the HttpOnly cookie flag matter specifically for session hijacking?

It stops JavaScript — including a script injected via XSS — from reading the session cookie via `document.cookie`. It doesn't prevent XSS itself, but it blocks one of the most common ways a stolen session actually leaves the browser.

---

## Why is HTTPS not just a "nice to have" but essential for session security specifically?

Because a session token sent over an unencrypted connection can be read directly by anyone with visibility into the network path. One plaintext transmission is enough to capture a valid token and fully impersonate the user — no amount of authentication strength elsewhere makes up for that.

---

## Does limiting session expiration time actually prevent session hijacking?

Not on its own. It doesn't stop a session from being stolen, but it caps how long an already-stolen or fixated token stays useful before it expires — damage control, not prevention.

---

# Common Mistakes

❌ Not regenerating the session ID upon successful login.

Leaves session fixation as a real, exploitable vector — an attacker's pre-known session ID remains valid and authenticated after the victim logs in, exactly as if nothing had changed.

---

❌ Serving any authenticated page or cookie over unencrypted HTTP, even once.

A single plaintext transmission is enough for a network eavesdropper to capture a valid session token — there's no partial safety in "mostly" using HTTPS.

---

❌ Setting overly long session expiration times.

Extends how long a stolen or fixated session token remains dangerously useful to an attacker, even after the underlying theft vector itself has been otherwise addressed.

---

# Key Takeaways

- Session hijacking covers several distinct attack vectors — XSS-based cookie theft, network eavesdropping, session fixation, and physical device access — each with its own specific fix.
- HttpOnly and Secure cookie flags, plus HTTPS everywhere, close off the XSS-theft and eavesdropping vectors.
- Session fixation is defeated by regenerating the session ID immediately on successful authentication, regardless of what the attacker knew beforehand.
- Reasonable session expiration limits damage even when the underlying theft vector isn't fully prevented.
- HTTPS matters here specifically, not just for general privacy — one unencrypted transmission is enough to hand over a working session.
