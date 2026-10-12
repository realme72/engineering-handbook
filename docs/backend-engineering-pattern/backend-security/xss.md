# XSS (Cross-Site Scripting)

# Why Does XSS Exist as a Vulnerability?

A browser can't tell the difference between "code the site's developers wrote" and "data a user typed in" once both end up in the same HTML. Render user input into a page unescaped, and a `<script>` tag hiding inside it runs exactly like the site's own JavaScript — same privileges, same access to cookies, same ability to make authenticated requests.

```
User submits a comment:  Great post! <script>steal_cookies()</script>

↓

If rendered into the page WITHOUT escaping:

<div>Great post! <script>steal_cookies()</script></div>

↓

Every browser that loads this page EXECUTES that script, exactly
as if it were the site's own legitimate code
```

---

# The Three Types of XSS

## Stored XSS

```
Malicious script is PERMANENTLY stored (in a database, typically)
and served to EVERY user who subsequently views the affected page
```

The worst variant. One successful injection — a malicious comment, a malicious bio — attacks every future visitor automatically. No further effort from the attacker required.

## Reflected XSS

```
Malicious script is part of a URL or request parameter, and
REFLECTED BACK immediately in the response — requires tricking a
SPECIFIC victim into clicking a specially crafted link
```

```
https://example.com/search?q=<script>steal_cookies()</script>

↓

If the search page renders "q" directly into the results page
without escaping ("You searched for: <script>...</script>"),
the script executes for whoever clicks that specific link
```

This one needs a bit of social engineering — someone has to click the crafted link — but it's still a serious, common vulnerability class.

## DOM-Based XSS

```
The vulnerability exists ENTIRELY in client-side JavaScript,
manipulating the DOM based on untrusted data — the server may
never even be involved in the vulnerable step at all
```

```javascript
// Vulnerable client-side code
document.getElementById("greeting").innerHTML =
    "Welcome, " + new URLSearchParams(location.search).get("name");
```

If `name` in the URL contains a script tag, this code injects it right into the page, entirely inside the browser. The server never sees the payload at all.

---

# The Fix: Output Encoding

Convert special HTML characters (`<`, `>`, `&`, quotes) into their safe entity equivalents before rendering user-supplied data into HTML. The browser then shows it as literal, visible text instead of running it as markup.

```
Raw input:    <script>alert('xss')</script>

Encoded for
HTML output:  &lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;

↓

The BROWSER renders this as the literal TEXT
"<script>alert('xss')</script>" on the page — visible, harmless
text — rather than executing it as a script tag
```

## Modern Frameworks Auto-Escape by Default — But Can Be Bypassed

```jsx
// React auto-escapes by default — SAFE
<div>{userComment}</div>

// EXPLICITLY opting out of escaping — DANGEROUS if userComment is untrusted
<div dangerouslySetInnerHTML={{ __html: userComment }} />
```

```django
{# Django auto-escapes by default — SAFE #}
{{ user_comment }}

{# EXPLICITLY opting out of escaping — DANGEROUS if user_comment is untrusted #}
{{ user_comment|safe }}
```

Auto-escaping is a solid default, and most frameworks ship it. But every one of them also gives you an escape hatch (`dangerouslySetInnerHTML`, `|safe`) for the cases where raw HTML is actually intended — and the real-world risk almost always shows up there, a developer reaching for it without re-checking the data is actually safe.

---

# Content Security Policy (CSP) — Defense in Depth

A second, independent layer beyond output encoding: an HTTP header that tells the browser exactly which sources of scripts and content it's allowed to load or run at all.

```http
Content-Security-Policy: script-src 'self' https://trusted-cdn.com
```

```
Even if an attacker somehow manages to inject a <script> tag
DESPITE output encoding failing somewhere...

↓

The BROWSER checks the injected script against the CSP policy

↓

If the injected script's source doesn't match the allowed policy
(e.g. an inline script when the policy only allows 'self' and a
specific trusted CDN), the browser REFUSES TO EXECUTE IT AT ALL
```

CSP's value is that it doesn't depend on every output-encoding decision across an entire codebase being correct forever. Miss one spot, and CSP can still stop the injected script from running.

---

# HttpOnly Cookies — Limiting the Damage, Not Preventing the Attack

Ties back to the Cookies chapter: mark a session cookie `HttpOnly`, and JavaScript — including an attacker's injected script — can't read its value at all, even after a successful XSS attack.

```http
Set-Cookie: session_id=abc123; HttpOnly
```

```
XSS attack succeeds, attacker's script runs in the victim's browser

↓

document.cookie  →  does NOT include the HttpOnly-flagged
                    session cookie at all

↓

The attacker's script CANNOT exfiltrate the session cookie via
document.cookie, even though the XSS itself succeeded
```

The script still runs — it can still deface the page or make authenticated requests using the victim's ambient session. But it blocks one of XSS's most common paydays: stealing the session token outright.

---

# Real-World Examples

### Stored XSS in Comment Sections and Forums

One of the oldest, most common places this bug has shown up — user-generated content rendered without escaping has caused real, documented incidents across the web's entire history.

---

### CSP Adoption at Major Sites

Widely adopted by security-conscious teams as a defense-in-depth layer, because trusting every developer to get output encoding right, everywhere, forever, in a large and evolving codebase is a fragile bet.

---

### `dangerouslySetInnerHTML` as a Recurring Real-World Risk

Comes up constantly in React codebases. A developer wants to render rich content — Markdown converted to HTML, say — reaches for the escape hatch, and skips sanitizing the underlying content first.

---

# Common Interview Questions

## Explain the three types of XSS, with examples.

Stored XSS persists a malicious script — in a database, typically — that's served to every subsequent viewer of the page. Reflected XSS bounces a script back immediately from a URL or request parameter, requiring a specific victim to click a crafted link. DOM-based XSS lives entirely in client-side JavaScript manipulating the DOM from untrusted data, without the server necessarily seeing the payload at all.

---

## How does output encoding prevent XSS?

It converts special HTML characters into their safe entity equivalents before user-supplied data hits the page. The browser displays that data as literal text instead of running it as markup or script — which is exactly what neutralizes the injection.

---

## What is CSP, and how does it provide defense in depth beyond output encoding?

A `Content-Security-Policy` header tells the browser which sources of scripts and content are allowed to run at all. Even if output encoding fails somewhere and a script gets injected, the browser refuses to run it if it doesn't match the policy — a second layer that doesn't depend on every encoding decision in the codebase being correct.

---

## Why does marking a cookie HttpOnly limit XSS's impact even if it doesn't prevent the XSS itself?

Because it stops JavaScript — including an injected script — from reading that cookie via `document.cookie`, even after a successful attack. It blocks one of XSS's most damaging outcomes, session token theft, without touching the underlying script injection at all.

---

## Are modern frameworks like React or Django immune to XSS by default?

They cut the risk a lot through automatic escaping, but they're not unbreakable. Every one of them ships an explicit way to opt out (`dangerouslySetInnerHTML`, `|safe`) for cases where raw HTML rendering is actually intended — and that's exactly where real-world XSS tends to sneak back in.

---

# Common Mistakes

❌ Rendering user input into HTML without escaping.

The direct root cause of every XSS vulnerability — always rely on a framework's default output encoding, or explicit escaping if building HTML manually.

---

❌ Explicitly disabling a framework's default auto-escaping without a genuinely careful, deliberate reason.

`dangerouslySetInnerHTML` and `|safe` exist for legitimate cases, but reaching for them without properly sanitizing the underlying content first is a common, real source of XSS even in "safe by default" frameworks.

---

❌ Relying on a single layer of defense (output encoding alone) instead of layering CSP and HttpOnly cookies as well.

A single missed escaping decision anywhere in a large codebase can undo the entire protection if there's no additional, independent layer (CSP blocking unauthorized scripts, HttpOnly limiting cookie theft) to fall back on.

---

# Key Takeaways

- XSS happens when user-supplied data is rendered into a page without proper escaping, letting an attacker's script run with the site's own full privileges in victims' browsers.
- Stored, reflected, and DOM-based XSS differ in where the payload lives and how it reaches the victim, but share one root cause: unescaped, untrusted data reaching the page.
- Output encoding is the direct fix, and most frameworks apply it by default — but every framework's escape hatch for raw HTML is a real, recurring source of trouble when used carelessly.
- CSP is an independent second layer at the browser level, blocking unauthorized scripts even if output encoding fails somewhere in the codebase.
- HttpOnly doesn't prevent XSS, but it blocks one of its most damaging consequences — session token theft via JavaScript.
