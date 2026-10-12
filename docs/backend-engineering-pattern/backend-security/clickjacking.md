# Clickjacking

# Why Does Clickjacking Exist as a Vulnerability?

An attacker loads a legitimate site — yours — inside an invisible iframe on their own page, and lines it up so that whatever the victim thinks they're clicking is actually a real click on your site underneath. Your click-handling code sees a perfectly genuine click. It has no idea it was visually set up.

```
Attacker's page:

┌─────────────────────────────────┐
│                                  │
│   "Click here to win a prize!"   │  ← what the victim SEES
│         [   BUTTON   ]           │
│                                  │
└─────────────────────────────────┘

              ↕ (invisibly overlaid, exact same position)

┌─────────────────────────────────┐
│   your-bank.com (in a hidden      │  ← what's ACTUALLY there,
│   iframe, invisible to the        │     invisible to the victim
│   victim)                         │
│         [Delete My Account]       │
└─────────────────────────────────┘
```

```
Victim clicks the visible "win a prize" button

↓

The click ACTUALLY lands on the invisible iframe's "Delete My
Account" button, positioned exactly underneath

↓

your-bank.com sees a COMPLETELY GENUINE click on its own page —
there's no way for it to know the click was visually disguised
by a different site framing it
```

---

# Why This Isn't the Same Problem as CSRF

CSRF forges a request without the victim's browser ever loading the target site's page — the attacker constructs the request directly. Clickjacking works differently: the browser genuinely loads your real page, invisibly, inside an iframe, and the victim's actual click lands on it. It's a UI-level trick, not a forged request.

```
CSRF:          browser sends a request the victim never
               intentionally initiated at all

Clickjacking:  the victim's browser DOES load the real target
               page, and the victim genuinely DOES click on it —
               they're just tricked about WHAT they think they're
               clicking on
```

---

# The Fix: X-Frame-Options / CSP frame-ancestors

Stop your page from loading inside a foreign iframe at all, and the whole technique falls apart.

```http
X-Frame-Options: DENY
```

```
Tells the browser: NEVER render this page inside an iframe,
on ANY other origin, period
```

```http
X-Frame-Options: SAMEORIGIN
```

```
Tells the browser: this page CAN be framed, but ONLY by a page
on the SAME origin — blocking any third-party site from framing it
```

The more flexible modern equivalent is the Content-Security-Policy `frame-ancestors` directive:

```http
Content-Security-Policy: frame-ancestors 'self' https://trusted-partner.com
```

```
Provides the SAME core protection as X-Frame-Options, but with
more flexibility — you can specify EXACTLY which origins ARE
allowed to frame your page (useful if you have a legitimate
partner integration that needs to embed your content), rather
than a strict binary "never" or "same-origin only"
```

Apply either one to any page with a sensitive, single-click action, and the browser refuses to render that page inside a foreign iframe — no matter how the attacker tries to position or disguise it.

---

# Why a Legitimate Site Might Actually Want to Be Framed

Not every site should reach for `DENY` by default. Some genuinely need to allow framing — an embeddable widget meant to live on partner sites, for instance.

```
DENY:            never allow framing, from ANY origin — the
                 strictest, safest default for anything with
                 sensitive, clickable actions

SAMEORIGIN:       allow framing only from your OWN site — useful
                 if your own application legitimately frames its
                 own pages internally

An explicit allowlist (via CSP frame-ancestors):  allow specific,
                 trusted partner origins to frame your content,
                 while still blocking everyone else — appropriate
                 for a deliberately embeddable widget or integration
```

The right choice comes down to whether the page has a genuine reason to be embedded elsewhere at all. Default to `DENY` unless there's a real, considered reason not to.

---

# Real-World Examples

### Social Media "Like" and Share Button Attacks

A well-documented historical pattern: attackers overlaid invisible "like" or "share" buttons over disguised content, tricking victims into liking or sharing something — often to spread the malicious page further — with zero awareness they'd touched a social platform at all.

---

### Single-Click-Triggers-an-Action UI Elements as the General Target

Any UI where one click causes something consequential — a purchase, a permission grant, an account deletion — is a natural target if the page hosting it skips frame-protection headers. It's specifically dangerous for single-click flows, since a multi-step process is much harder to disguise and align invisibly.

---

### Modern Browsers and Frameworks Setting Frame Protection by Default

A lot of modern frameworks and security-conscious platforms now set `X-Frame-Options` or an equivalent CSP directive out of the box — this mitigation is well understood enough that it's become an expected default.

---

# Common Interview Questions

## How does clickjacking work? Walk through a concrete example.

An attacker overlays a legitimate site inside an invisible iframe on their own page, positioning a sensitive button — "Delete My Account," say — exactly under something enticing, like a "win a prize" button. The victim's click lands on the invisible, real button underneath, and the legitimate site sees a completely genuine click with no way to know it was visually staged.

---

## How does X-Frame-Options or CSP's frame-ancestors prevent clickjacking?

By telling the browser to refuse rendering the page inside a foreign iframe at all. `X-Frame-Options: DENY` blocks all framing; `SAMEORIGIN` allows only same-origin framing; CSP's `frame-ancestors` lets you specify exactly which origins are permitted, which is more flexible than the binary X-Frame-Options options.

---

## Why would a legitimate site ever want to allow itself to be framed?

For deliberately embeddable content — a widget meant to sit on partner sites. `SAMEORIGIN` or an explicit CSP `frame-ancestors` allowlist gives that flexibility while still blocking arbitrary, untrusted sites from framing the content.

---

## How is clickjacking different from CSRF?

CSRF forges a request the victim's browser sends without the victim seeing or interacting with the target site at all. Clickjacking is a UI-level trick — the browser genuinely loads the real target page, invisibly, and the victim's actual click lands on it. They're tricked about what they're clicking, not having a request forged with no interaction at all.

---

## What kind of pages are the highest-risk clickjacking targets?

Pages with a single click that triggers something consequential — a purchase confirmation, a permission grant, an account deletion. These are the easiest for an attacker to disguise and precisely align invisibly under bait content. Multi-step flows are much harder to pull off this way.

---

# Common Mistakes

❌ Not setting `X-Frame-Options` or the equivalent CSP `frame-ancestors` directive at all.

Leaves every page framable by default, exposing any single-click-triggers-an-action element to the clickjacking technique.

---

❌ Using `DENY` when `SAMEORIGIN` or an explicit partner allowlist would better fit a legitimate embedding use case.

An overly strict default can break intended functionality (an embeddable widget, for instance) — the right choice depends on whether the page genuinely needs to support being framed by someone.

---

❌ Assuming clickjacking and CSRF are solved by the same defense.

CSRF tokens and SameSite cookies don't touch clickjacking at all — the request itself is genuinely valid. Clickjacking needs its own, distinct defense: frame-blocking headers.

---

# Key Takeaways

- Clickjacking overlays a legitimate site inside an invisible iframe on a malicious page, tricking a victim's genuine click into landing on the real, hidden site's button instead of the visible bait.
- It's distinct from CSRF — the browser genuinely loads the real target page and the victim's actual click lands on it, rather than a request being forged with no interaction at all.
- `X-Frame-Options` (`DENY` or `SAMEORIGIN`) or the more flexible CSP `frame-ancestors` directive are the direct fix.
- Not every site should block all framing by default — legitimate embeddable widgets need a considered choice between `SAMEORIGIN` and an explicit, trusted-partner allowlist.
- Single-click pages are the highest-risk targets, since they're the easiest to disguise and align invisibly underneath bait content.
