# CSRF (Cross-Site Request Forgery)

# Why Does CSRF Exist as a Vulnerability?

Browsers attach a user's cookies to every request sent to a domain — session cookies included — no matter which site actually triggered that request. CSRF lives entirely inside that gap: a malicious site tricks the victim's browser into sending a request to a site they're already logged into, and the browser dutifully attaches the valid session cookie, making the forged request look completely authentic.

```
Victim is logged into their bank (has a valid session cookie for bank.com)

↓

Victim visits a malicious site, which contains:

<img src="https://bank.com/transfer?to=attacker&amount=1000">

↓

The victim's BROWSER automatically sends this request to bank.com
WITH the victim's valid session cookie attached — the browser has
no concept of "which site told me to make this request," it just
sees "a request to bank.com" and attaches bank.com's cookie
```

```
From the bank's server's point of view:

A request arrived, WITH a completely valid session cookie attached
→ this looks exactly like a request the logged-in user genuinely
   intended to make → the server has NO WAY to tell the difference
```

Nothing's broken. The browser's cookie behavior is working as designed, and the session is genuinely valid. The gap is that the server can't tell "the user meant to do this" from "a different site the user happened to have open made them do this."

---

# The Fix: CSRF Tokens

A unique, unpredictable token embedded in every legitimate form or request on your site. The server checks it matches on submission.

```html
<form action="/transfer" method="POST">
    <input type="hidden" name="csrf_token" value="a1b2c3d4e5f6...">
    <!-- other form fields -->
</form>
```

```
Server receives a POST to /transfer

↓

Checks: does the submitted csrf_token match what THIS user's
session was actually given?

↓

MATCH → process the request (a genuine, intentional submission
         from your own site's form)

NO MATCH (or missing) → REJECT the request
```

```
A malicious third-party site has NO WAY to know or guess this
token — it's embedded in YOUR site's own page, and same-origin
policy prevents the malicious site's JavaScript from reading it
(it can't make a cross-origin request to fetch your page's HTML
and extract the token, thanks to the same browser security
boundary the CORS chapter covers)

↓

Its forged request is missing (or has an incorrect) token, and
gets REJECTED
```

---

# SameSite Cookies — A More Modern, Complementary Defense

A cookie attribute that tells the browser not to send that cookie on cross-site requests at all — fixing the problem at its root, the browser's default cookie-attaching behavior, instead of relying on an application-level token check.

```http
Set-Cookie: session_id=abc123; SameSite=Strict
```

```
SameSite=Strict:  the cookie is NEVER sent on a cross-site request,
                   even one that came from the user clicking a
                   legitimate link on another site

SameSite=Lax:      the cookie IS sent for top-level navigation
                   (clicking a link), but NOT for background/
                   embedded requests (images, forms auto-submitted
                   via JavaScript, iframes) — this is what most
                   modern browsers now use as their DEFAULT if a
                   site doesn't explicitly set the attribute
```

Set `SameSite` right, and the malicious `<img>` tag from the opening example never gets the session cookie attached in the first place. The browser stops the attack on its own — no CSRF token mechanism needed — for the large majority of browsers that respect the attribute today.

---

# Why Bearer-Token APIs Are Less Susceptible to CSRF

Worth knowing, and often cited: APIs authenticated with an `Authorization: Bearer <token>` header rather than a cookie are much harder to hit with CSRF, for a specific reason.

```
Cookie-based auth:  the BROWSER automatically attaches the cookie
                    to every request to that domain, INCLUDING
                    forged ones from a malicious site — this is
                    exactly the mechanism CSRF exploits

Bearer token auth:   a malicious page's forged request has NO WAY
                    to make the victim's browser attach a CUSTOM
                    Authorization header — the browser doesn't
                    automatically attach headers the way it does
                    cookies, and JavaScript on the malicious page
                    can't read the token to attach it manually
                    either (it's not stored anywhere the malicious
                    page's script has access to, assuming it isn't
                    exfiltrated via a separate XSS vulnerability)
```

That's a real, structural mitigation, not luck — it's one reason some APIs prefer Bearer tokens over cookies, on top of whatever else the JWT and Access/Refresh Tokens chapters already factor into that choice.

---

# Real-World Examples

### Chrome's SameSite=Lax Default

Chrome (and other major browsers) made `SameSite=Lax` the default for cookies that don't set the attribute explicitly — a broad, browser-level fix that cut CSRF's practical impact across the whole web, even for sites that never bothered building their own token mechanism.

---

### Bank Transfer Forms as the Textbook CSRF Target

The example everyone reaches for, and for good reason: any state-changing action reachable through a simple, predictable request — a transfer, an email change, an account deletion — is a natural target if the endpoint has no token check and no SameSite protection.

---

### CSRF Tokens as a Standard Feature in Web Frameworks

Django, Rails, and Spring all bake in CSRF token generation and validation by default. That's how essential this protection has become for any cookie-authenticated web app.

---

# Common Interview Questions

## How does CSRF actually work? Walk through a concrete example.

Browsers attach a user's cookies to every request to a domain, regardless of what triggered it. A malicious site embeds a request to a trusted site — a bank transfer URL in an image tag, say — and the victim's browser automatically attaches their valid session cookie. The forged request looks completely legitimate to the server, which has no way to tell it apart from one the user actually meant to send.

---

## How do CSRF tokens prevent this?

A unique token is embedded in every legitimate form on your site, and the server checks it on submission. A malicious third-party site can't read or guess that token — same-origin policy blocks it from reading your page's content — so its forged request is missing the token and gets rejected.

---

## What is the SameSite cookie attribute, and how does it provide a complementary or alternative defense?

An attribute telling the browser not to send a cookie on cross-site requests at all (`SameSite=Strict`), or only for top-level navigation and not background requests (`SameSite=Lax`). It fixes the problem at the source — the browser's automatic cookie attachment — without needing an application-level token check, for browsers that respect it.

---

## Why are Bearer-token APIs generally less susceptible to CSRF than cookie-based ones?

Because a forged request from a malicious page has no way to attach a custom `Authorization` header the way the browser automatically attaches cookies. And the malicious page's JavaScript can't read the token to add it manually either, since it isn't stored anywhere that script can reach.

---

## Does CSRF only matter for login forms?

No. It applies to any state-changing request authenticated by cookies. A transfer, an email change, a delete action — any predictable request that changes state is a potential target if it skips token validation and SameSite protection.

---

# Common Mistakes

❌ Not implementing CSRF protection on every state-changing endpoint.

Assuming CSRF only matters for a login form misses that any cookie-authenticated request that changes state is a potential target, not just authentication itself.

---

❌ Relying on SameSite alone without considering edge cases or older browsers that don't fully respect it.

While `SameSite` is a strong, broad mitigation, defense in depth (pairing it with CSRF tokens) covers gaps that a single layer alone might miss.

---

❌ Confusing CSRF with XSS.

Different vulnerabilities, different problems — CSRF forges a request using the victim's existing valid session; XSS injects and runs a script in the victim's browser. Worth noting they can interact: a successful XSS attack can directly read a CSRF token off the page and bypass the protection entirely, which is exactly why both need their own independent defenses.

---

# Key Takeaways

- CSRF exploits the browser's automatic cookie-attaching behavior — a malicious site tricks a victim's browser into sending a forged request to a trusted site, with the valid session cookie attached automatically.
- CSRF tokens — unique values embedded in legitimate forms and verified on submission — are the standard application-level defense, since a malicious site has no way to read or guess them.
- The `SameSite` cookie attribute is a complementary, browser-level defense that stops cookies from being sent on cross-site requests at all, and has become a broad industry default.
- Bearer-token authentication is structurally less susceptible to CSRF than cookies, since browsers don't auto-attach custom headers to forged cross-site requests.
- CSRF protection needs to cover every state-changing endpoint, not just login.
