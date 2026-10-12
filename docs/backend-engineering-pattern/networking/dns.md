# DNS (Domain Name System)

# Why Does DNS Exist?

Machines talk in IP addresses — `142.250.183.78`. People remember `google.com`. DNS is the directory that turns one into the other, quietly, before a browser can open a single connection to anything.

```
Browser: user types "google.com"

↓

Somewhere, "google.com" needs to become "142.250.183.78"
before a TCP connection can even be attempted
```

Without it, every application would have to hardcode IP addresses. Move your traffic to a new server or data center, and every client still referencing the old IP breaks at once, with no way to redirect them.

---

# The Hierarchical Structure

DNS isn't one central database — it's a hierarchy of authorities, each responsible for a specific part of a domain name.

```
                              "." (root)

                                 ↓

                    .com  .org  .net  ...  (TLD servers)

                                 ↓

                    google.com  (authoritative nameserver
                                 for this specific domain)

                                 ↓

              www.google.com    mail.google.com   (specific records)
```

No single server answers every DNS query on Earth. Each level only needs to know the address of the next one down, and passes the question along.

---

# The Resolution Process

```
1. Browser checks its OWN cache → not found (first visit)

2. OS checks its cache → not found

3. Query sent to a RECURSIVE RESOLVER
   (your ISP's DNS server, or a public one like 8.8.8.8)

4. Recursive resolver checks ITS cache → not found

5. Resolver asks a ROOT server: "who handles .com?"
   → Root replies with the .com TLD server's address

6. Resolver asks the .com TLD server: "who handles google.com?"
   → TLD server replies with google.com's authoritative nameserver

7. Resolver asks google.com's authoritative nameserver:
   "what's the IP for www.google.com?"
   → Authoritative server replies with the actual IP

8. Resolver returns the IP to the browser, AND caches the answer
   for future queries (respecting the record's TTL)
```

```
Client → Recursive Resolver → Root → TLD → Authoritative → IP returned
                    ↓
              cached along the way, at every level, per its TTL
```

Every step in the chain caches its answer. That's why the next request for the same domain, from the same resolver, skips straight to the cached value instead of repeating the whole lookup.

---

# Record Types

```
A       →  maps a domain name to an IPv4 address
AAAA    →  maps a domain name to an IPv6 address
CNAME   →  an alias — "this name is really just another name,
            go look THAT one up instead"
MX      →  which mail servers handle email for this domain
TXT     →  arbitrary text data (commonly used for domain
            verification, SPF/DKIM email authentication records)
NS      →  which nameservers are authoritative for this domain
```

```
www.example.com     CNAME  example.com
example.com         A      93.184.216.34
```

A CNAME is just a pointer to another name. Resolving `www.example.com` here means following the CNAME to `example.com` first, then resolving *that* name's A record — one extra hop, worth remembering when you're tracing through a resolution chain.

---

# TTL and Caching — Why DNS Changes Aren't Instant

```
example.com    A    93.184.216.34    TTL: 3600  (1 hour)
```

Every DNS record carries a TTL, telling every resolver and cache along the chain how long it can keep using that answer before checking again. That's why changing a record doesn't take effect everywhere at once — any resolver still holding the old answer keeps serving it until its TTL runs out, no matter what the authoritative server says now.

```
You update your A record to point to a NEW server

↓

Resolvers that already cached the OLD record (TTL not yet expired)
keep sending traffic to the OLD server

↓

Only once each resolver's cached TTL expires does it re-query and
pick up the new value
```

This has real operational teeth. Teams planning a migration or failover lower a record's TTL well ahead of the change, so that once the cutover happens, stale cached answers expire quickly across the internet instead of lingering for the record's usual, longer TTL.

---

# DNS and Load Balancing / Failover

```
Round-robin DNS:   the same domain name resolves to DIFFERENT IPs
                    on different queries, cycling through a list —
                    a crude form of load distribution across
                    multiple servers

Health-check-aware DNS (e.g. Route53):  automatically stops
                    returning an unhealthy server's IP, redirecting
                    traffic only to servers currently passing
                    health checks
```

This is the same idea as the Service Discovery chapter, just running at the DNS layer — steering traffic only to healthy instances. It pays the same caching tax, though: a health-check-aware DNS failover still isn't instant everywhere, because of the TTL behavior above.

---

# Real-World Examples

### AWS Route53

A managed DNS service that does health-check-based failover and geographic routing at the DNS layer itself, sending users to the nearest healthy region. Teams reach for it specifically because it can stop returning a dead endpoint without any application-level load balancer getting involved.

---

### Cloudflare DNS

A widely used public resolver, alongside Google's 8.8.8.8 — people pick it for speed and privacy. A good reminder that the "recursive resolver" in the chain above isn't some abstraction; it's a real service you can choose.

---

### The "DNS Propagation" Support Ticket

A classic one: someone changes a record and reports "it's not working yet" ten minutes later. Nothing's actually broken — resolvers around the world are just still serving the old, cached answer until their TTLs expire.

---

# Common Interview Questions

## Walk me through what happens between typing a URL and a page loading.

DNS resolution comes first. The browser and OS check their own caches, then ask a recursive resolver, which — if it has no cached answer either — walks the hierarchy from the root server to the relevant TLD to the domain's authoritative nameserver, and finally gets an IP back. Only then can the browser open a TCP connection (and, for HTTPS, do a TLS handshake) and actually send the request.

---

## Why does DNS rely so heavily on caching and TTLs?

Because walking the full hierarchy — root, then TLD, then authoritative server — for every single request would be slow and would hammer a small number of root and TLD servers with repetitive load. Caching the answer at every level, for as long as the TTL allows, means only the very first lookup for a given domain, per resolver, ever needs the full multi-step resolution.

---

## Why doesn't a DNS record change take effect everywhere instantly?

Because resolvers around the world may already have the old answer cached, and they'll keep serving it until that copy's TTL expires. DNS has no way to push an update out to every resolver holding the old value — each one just re-queries independently once its own TTL runs out.

---

## What's the difference between an A record and a CNAME record?

An A record maps a name straight to an IPv4 address. A CNAME is an alias pointing to another name instead of an IP — resolving it takes an extra step, since you then have to resolve whatever domain the CNAME points to.

---

## How does DNS enable geographic load balancing?

A provider like Route53 can return different IPs for the same domain depending on where the query is coming from, routing users to a nearby data center or region. Paired with health checks, it can also skip an unhealthy region's IP entirely and send traffic to a healthy one instead.

---

# Common Mistakes

❌ Setting a record's TTL too high right before a planned migration or failover.

Any resolver holding the old value keeps using it for the full TTL. Set a long TTL right before a cutover, and you get a long tail of clients still hitting the old server well after the "official" change.

---

❌ Assuming a DNS change propagates instantly everywhere.

Resolvers around the world cache independently and expire on their own schedules — there's no way to force an immediate, universal update once a record's been cached elsewhere.

---

❌ Setting TTLs excessively low as a default, "just to be safe."

Very low TTLs mean resolvers re-query far more often, adding avoidable load to authoritative nameservers and a bit of extra lookup latency for every client. Match the TTL to how often the record is actually expected to change — don't minimize it reflexively.

---

# Key Takeaways

- DNS translates human-readable domain names into IP addresses via a hierarchical system of authorities (root, TLD, authoritative nameservers), not one central database.
- The resolution process caches its answer at every level it passes through — that's why repeat lookups for the same domain are fast, and why a record change doesn't land everywhere instantly.
- A record's TTL controls how long resolvers are allowed to cache its answer — lowering it ahead of a planned change is the usual way to shrink how long stale answers linger after a cutover.
- Different record types (A, AAAA, CNAME, MX, TXT, NS) serve different purposes — CNAME is the odd one out, requiring an extra resolution step since it points to a name rather than an IP.
- DNS itself can double as a load-balancing and failover mechanism (round-robin, or health-check-aware routing like Route53) — the same goal as Service Discovery, just running at the DNS layer.
