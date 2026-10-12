# SSRF (Server-Side Request Forgery)

# Why Does SSRF Exist as a Vulnerability?

A server that takes a URL from user input and fetches it on its own behalf — a preview image, a webhook check, link metadata — will fetch whatever URL it's given. Point it at an internal address the server can reach but an outside attacker never could, and the server becomes an unwitting proxy straight into your own infrastructure.

```
App feature: "paste a URL and we'll show you a preview of the page"

↓

Legitimate use:  user submits https://news-site.com/article

↓

The SERVER fetches this URL, extracts a preview image/title,
and shows it to the user
```

```
Malicious use:  attacker submits http://169.254.169.254/latest/
                 meta-data/iam/security-credentials/

↓

The SERVER, trusting it's "just fetching a webpage," makes THIS
request instead — from WITHIN the cloud environment where this
address IS reachable — and returns whatever comes back directly
to the attacker
```

The server isn't doing anything wrong by fetching a URL — that's its whole job here. The mistake is never checking whether the destination was actually appropriate for it to reach on the user's behalf.

---

# Why This Is Especially Dangerous in Cloud Environments

`169.254.169.254` isn't a random address. It's the internal-only IP for the cloud provider's metadata service — AWS, GCP, and Azure all run some version of it — and it hands out live credentials for whatever IAM role the server itself is running as.

```
GET http://169.254.169.254/latest/meta-data/iam/security-credentials/some-role

↓

Response:  {
    "AccessKeyId": "...",
    "SecretAccessKey": "...",
    "Token": "...",
    "Expiration": "..."
}
```

Get an attacker in front of that endpoint, and they walk away with live credentials scoped to the server's own permissions — not just this one endpoint, but whatever that IAM role is allowed to touch. A "we let users make our server fetch arbitrary URLs" bug can turn into a full account compromise, depending on how broad that role is.

---

# The Fix

## Strict Allowlisting, Not a Denylist

```
Denylist approach (WEAK):  block known-bad patterns
                          ("no 169.254.x.x", "no localhost")

↓

Easily bypassed — alternate IP encodings (decimal, octal, or IPv6
forms of the same address), a URL that initially resolves to an
allowed address but REDIRECTS to a blocked one, DNS rebinding
(a domain that resolves to a safe IP at validation time, then a
DIFFERENT, internal IP at actual request time)
```

```
Allowlist approach (STRONG):  explicitly define exactly which
                              domains/IP ranges are PERMITTED,
                              and reject everything else by default
```

A denylist means guessing every way an attacker might disguise a forbidden destination, and there's always one more encoding trick you didn't think of. An allowlist flips that: only what's explicitly permitted is reachable, full stop.

## Validate the Resolved IP, Not Just the Hostname

```
Checking ONLY the hostname the user submitted is insufficient —
a hostname can resolve to a DIFFERENT IP than expected, or the
server could follow a REDIRECT to an entirely different address
after the initial check already passed

↓

The FIX: resolve the URL's actual IP address FIRST, validate
THAT resolved IP is not in a private/internal range (169.254.x.x,
10.x.x.x, 127.0.0.1, and other reserved ranges), and disable
automatically following redirects blindly — re-validate any
redirect target before following it too
```

## Network-Level Segmentation as Defense in Depth

Beyond the application layer, restrict what the fetching server can actually reach on the network — firewall rules, security groups blocking the metadata endpoint and other sensitive internal services. That's the backstop that holds even if an application-level check has a gap.

---

# Real-World Examples

### The 2019 Capital One Breach

The most-cited real-world SSRF incident. An SSRF bug reached the AWS metadata service, pulled credentials for an IAM role with overly broad permissions, and those credentials were then used to exfiltrate a massive amount of customer data. It's the case study everyone reaches for because it shows the exact chain: an SSRF bug hits the metadata endpoint, and that alone escalates into a full breach.

---

### URL Preview / "Unfurling" Features

Any feature that fetches and previews a user-submitted URL — a chat app's link preview, an "import from URL" button — is a natural SSRF candidate if the destination isn't checked against a strict allowlist.

---

### Webhook Registration Endpoints

Letting users register a webhook URL your server will call later is the same problem wearing a different hat: the server makes a request, on the user's behalf, to a destination the user controls. Same allowlist and IP-validation discipline applies.

---

# Common Interview Questions

## What is SSRF, and how does it work? Walk through a concrete example.

A server-side application takes a URL from user input and fetches it on its own behalf, without validating the destination. An attacker supplies an internal address the server can reach but they couldn't reach directly — the AWS metadata service's internal-only address, say, submitted to a "preview this webpage" feature — tricking the server into fetching and returning sensitive internal data.

---

## Why is SSRF especially dangerous in cloud environments specifically?

Because cloud providers expose a well-known, internal-only metadata endpoint (`169.254.169.254` on AWS) handing out live credentials for whatever IAM role the server runs as. An SSRF bug that reaches it can hand an attacker the server's own cloud credentials, escalating well past the original vulnerable endpoint.

---

## How would you prevent SSRF?

A strict allowlist of permitted destinations rather than a denylist, since denylists are easy to bypass via redirects or alternate IP encodings. Resolve the URL's actual IP and validate that directly, not just the hostname string, and never follow a redirect without re-validating where it goes. Network-level segmentation is a necessary backstop on top of all that.

---

## Explain the Capital One breach at a high level.

An SSRF bug let an attacker make the affected server fetch data from the AWS metadata service, pulling temporary credentials tied to an overly broad IAM role. Those credentials were then used to access and exfiltrate a huge amount of customer data elsewhere in AWS — a direct illustration of an SSRF bug plus the metadata endpoint plus loose IAM permissions adding up to a full breach.

---

## Why is a denylist approach considered weak for preventing SSRF?

It requires anticipating every way an attacker might disguise a forbidden destination — alternate encodings, a redirect after the check passes, DNS rebinding. An allowlist sidesteps all of that by only permitting explicitly-approved destinations in the first place.

---

# Common Mistakes

❌ Using a denylist of "forbidden" domains or IPs instead of a strict allowlist.

Denylists are notoriously easy to bypass via redirects, alternate IP address encodings, or DNS rebinding tricks — an allowlist is the structurally sound approach.

---

❌ Validating only the originally-submitted hostname without checking what IP address it actually resolves to.

A hostname's resolved IP can differ from what was expected, and a URL that initially resolves to an allowed address can still redirect to a blocked, internal one after the check has already passed.

---

❌ Blindly following redirects without re-validating the redirect target.

A URL that passes initial validation can redirect to an entirely different, internal address — each redirect needs the same validation applied as the original URL.

---

❌ Relying solely on application-level checks without any network-level restriction as a backstop.

If the application-level validation has a gap or bug, network-level segmentation (restricting what the server can actually reach) is what prevents that single point of failure from becoming a full compromise.

---

# Key Takeaways

- SSRF happens when a server fetches a user-supplied URL on its own behalf without checking the destination, letting an attacker use it as a proxy into internal infrastructure.
- It's especially dangerous in cloud environments because of the metadata service endpoint, which hands out live credentials for the server's own IAM role — the Capital One breach is the canonical real-world case.
- A strict allowlist beats a denylist — denylists are easy to bypass through redirects, encoding tricks, or DNS rebinding.
- Validate the resolved IP, not just the submitted hostname, and never follow a redirect without re-validating it.
- Network-level segmentation is a necessary backstop beyond application-level validation alone.
