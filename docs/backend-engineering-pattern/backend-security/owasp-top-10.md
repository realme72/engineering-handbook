# OWASP Top 10

# Why Does the OWASP Top 10 Exist?

Every vulnerability in this section is real and worth understanding deeply — but a team facing limited time and limited security expertise needs a way to prioritize: what actually matters most, based on real-world prevalence and impact, not just what sounds most technically interesting? The OWASP (Open Web Application Security Project) Top 10 exists to answer exactly this — a periodically updated, industry-standard, data-informed ranking of the most critical web application security risks, giving the industry a shared vocabulary and a practical checklist grounded in actual breach data and broad practitioner surveys, rather than everyone independently guessing at what matters most.

```
Without a shared standard:  every team, every security review
                             independently guesses at what to
                             prioritize checking for

With the OWASP Top 10:       a common, prioritized, evidence-based
                             baseline — informed by real breach
                             data and industry-wide surveys — that
                             security reviews, secure coding
                             guidelines, and compliance checklists
                             can all reference consistently
```

This chapter walks through the 2021 OWASP Top 10 categories, explicitly cross-referencing the chapters in this handbook that already cover several of them in depth, and giving full treatment to the ones that don't yet have a dedicated home elsewhere.

---

# The Ten Categories

## 1. Broken Access Control (Now #1)

The category that moved to the top of the list in the 2021 update — and it deserves the attention, since it's arguably the single most common real-world vulnerability class, more so than the more "exciting"-sounding categories like injection. Its most common concrete form is **IDOR (Insecure Direct Object Reference)**:

```
GET /api/orders/123

↓

The endpoint checks: does order 123 EXIST? Yes → return it

↓

It does NOT check: does the CURRENT, requesting user actually
                    OWN order 123?

↓

Any authenticated user can view (or, worse, modify) ANY order,
simply by changing the number in the URL
```

This directly connects to the Authorization chapter in the Authentication section, which covers the general principle (authentication proves *who* you are; authorization determines *what* you're allowed to do) — IDOR is exactly what happens when that authorization check is silently skipped for a specific resource, checking only "does this exist" instead of "does this belong to the requester."

## 2. Cryptographic Failures (Previously "Sensitive Data Exposure")

Not encrypting sensitive data at rest or in transit, using weak or outdated cryptographic algorithms, or storing passwords insecurely. This connects directly to the TLS chapter for data in transit — and worth adding here specifically, since it wasn't covered elsewhere: **passwords should never be stored in plaintext, or with a fast, general-purpose hash (like plain SHA-256) alone**. Use a purpose-built, deliberately slow password-hashing algorithm — bcrypt or Argon2 — combined with a unique salt per password, specifically because these algorithms are designed to make brute-forcing a stolen password database computationally expensive, unlike a fast general-purpose hash that an attacker can try billions of guesses against per second.

## 3. Injection

**Covered in full depth in this section's own SQL Injection, Command Injection, and Insecure Deserialization chapters** — the common thread across all of them is untrusted input being interpreted as executable syntax (SQL, shell commands, or arbitrary object-reconstruction instructions) instead of pure data.

## 4. Insecure Design

A genuinely important, broader category added distinctly in the 2021 update — security flaws baked into the **architecture** itself, not just an implementation bug in otherwise-sound code. A password reset endpoint with no rate limiting **by design** (nobody ever intended to add it, it was simply never part of the design) is a design flaw, distinct from a coding mistake in an endpoint that was *supposed* to have rate limiting but implemented it incorrectly. Directly connects to the Rate Limiting chapter, and to the general principle that security needs to be a design consideration from the start, not a bug-fixing exercise applied after the fact.

## 5. Security Misconfiguration

Default credentials left unchanged, verbose error messages leaking stack traces or internal implementation details directly to users, unnecessary features or ports left enabled, and missing security headers — directly connects to the CSP and X-Frame-Options headers covered in the XSS and Clickjacking chapters, both of which are common, real examples of a security misconfiguration when simply left unset by default.

## 6. Vulnerable and Outdated Components

Using a dependency or library with a known, publicly disclosed vulnerability (a CVE) without patching it — the entire reason automated dependency-scanning tools (Dependabot, Snyk) exist as standard, expected parts of a modern CI/CD pipeline, flagging outdated or vulnerable dependencies automatically rather than relying on a team to manually track every dependency's security advisories.

## 7. Identification and Authentication Failures

**Covered extensively across the entire Authentication section** (Identity & Authentication, Sessions, Cookies, JWT, Access/Refresh Tokens, Authentication System Design) plus this section's own **Session Hijacking** chapter — weak password policies, session tokens that aren't properly protected or rotated, and missing multi-factor authentication all fall under this broad category.

## 8. Software and Data Integrity Failures

Includes **Insecure Deserialization** (covered in its own chapter in this section) plus a broader, related concern worth introducing here: **supply chain integrity** — not verifying that a downloaded package, a CI/CD pipeline dependency, or an auto-update mechanism hasn't been tampered with somewhere along the way. A compromised, widely-used open-source package (or a compromised CI pipeline step) can silently inject malicious code into thousands of downstream applications that trusted it without verification — a category of risk that's grown significantly more prominent as software supply chains have become more complex and interconnected.

## 9. Security Logging and Monitoring Failures

Not logging security-relevant events (failed login attempts, permission changes, access to sensitive data) or not actively alerting on suspicious patterns — directly connects to the **Logging** and **Alerting** chapters in the Observability section. A breach that goes undetected for months, purely because nobody was logging or watching for the relevant signals, is often a far more damaging outcome than the initial vulnerability itself.

## 10. Server-Side Request Forgery (SSRF)

**Covered in full depth in this section's own SSRF chapter** — including the Capital One breach case study and the specific danger of cloud metadata endpoints.

---

# Real-World Examples

### OWASP's Own Data-Driven Methodology

The Top 10 list itself is compiled from a combination of real, contributed breach and vulnerability data alongside a broad industry practitioner survey — a genuine, evidence-informed ranking, not a list of whatever vulnerabilities happen to sound most alarming or technically interesting.

---

### Security Audits and Secure Code Review Checklists

Widely used directly as a baseline checklist by companies conducting security audits, penetration tests, and secure code reviews — its broad, standardized adoption is precisely why being fluent in all ten categories (and knowing which of your own systems' vulnerabilities map to which category) is such a common, practical interview expectation.

---

### Broken Access Control's Rise to #1

A genuinely significant, real shift in the 2021 update, reflecting actual observed trends — access control failures (and IDOR specifically) have become the most commonly identified vulnerability class across real-world applications, overtaking injection, which had dominated earlier versions of the list.

---

# Common Interview Questions

## What is OWASP, and why does its Top 10 list matter?

The Open Web Application Security Project maintains a periodically updated, data-informed ranking of the most critical web application security risks, based on real breach data and broad practitioner surveys. It matters because it gives the industry a shared, prioritized, evidence-based vocabulary and checklist, rather than every team independently guessing at what to prioritize checking for.

---

## Explain Broken Access Control / IDOR with a concrete example.

An endpoint like `GET /api/orders/123` checks whether order 123 exists, but fails to check whether the currently authenticated user actually owns that order — letting any authenticated user view or modify any order simply by changing the ID in the URL. It's the most common real-world form of Broken Access Control, and became the #1 OWASP category in the 2021 update.

---

## What changed in the 2021 OWASP Top 10 update?

Broken Access Control moved to the #1 position, reflecting its rise as the most commonly identified real-world vulnerability class, and Insecure Design was added as a new, distinct category — recognizing that some vulnerabilities are architectural flaws baked into a system's design from the start, not just implementation bugs in otherwise well-designed code.

---

## How would you use the OWASP Top 10 as a practical checklist in a code review?

Walk through each category and ask whether the code under review has adequately addressed it — does every resource-fetching endpoint verify ownership, not just existence (Broken Access Control); are passwords hashed with bcrypt/Argon2, not a fast general-purpose hash (Cryptographic Failures); are dependencies current and free of known CVEs (Vulnerable Components); are security-relevant events logged and alerted on (Logging and Monitoring Failures) — treating it as a structured, prioritized set of questions rather than a vague, generic "is this secure" check.

---

## Is the OWASP Top 10 a complete, exhaustive list of every possible vulnerability?

No — it's a prioritized baseline of the most common, highest-impact risks based on real-world data, not an exhaustive catalog of every conceivable vulnerability. Treating it as a complete checklist that guarantees security once fully addressed misses that it's specifically meant to prioritize the risks most likely to matter, not enumerate every theoretically possible one.

---

# Common Mistakes

❌ Treating the OWASP Top 10 as a complete, exhaustive checklist that guarantees security once fully checked off.

It's a prioritized baseline of the most common, highest-impact risks based on real-world data — not an exhaustive list of every possible vulnerability a system could have.

---

❌ Under-prioritizing Broken Access Control / IDOR relative to more "exciting"-sounding vulnerabilities like SQL injection.

It's now the single most commonly identified real-world vulnerability class, and deserves at least as much attention as injection-family vulnerabilities in any real security review.

---

❌ Storing passwords with a fast, general-purpose hash instead of a purpose-built, deliberately slow algorithm.

A fast hash (even SHA-256 alone) lets an attacker who obtains a stolen password database try billions of guesses per second — bcrypt and Argon2 are specifically designed to make this computationally expensive, which is exactly the property password storage needs.

---

# Key Takeaways

- The OWASP Top 10 is a periodically updated, data-informed ranking of the most critical web application security risks, giving the industry a shared, prioritized vocabulary rather than everyone independently guessing at what matters most.
- Broken Access Control (and its most common form, IDOR) is now the #1 category as of the 2021 update — checking that resources verify ownership, not just existence, is one of the highest-value checks in any security review.
- Several categories (Injection, SSRF, parts of Authentication Failures and Software Integrity Failures) are covered in full depth elsewhere in this handbook — this chapter's value is in the categories not yet given dedicated treatment: password hashing specifics, Insecure Design as an architectural concern, Security Misconfiguration, Vulnerable Components, and supply chain integrity.
- It's a prioritized baseline informed by real breach data, not an exhaustive checklist that guarantees complete security once fully addressed.
- Passwords should always be hashed with a purpose-built, deliberately slow algorithm (bcrypt or Argon2) with a unique salt per password — never a fast, general-purpose hash alone.
