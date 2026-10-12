# API Versioning

# Why Does API Versioning Exist?

Once an API has real clients — a mobile app in the app store, a third-party integration, another team's service calling yours — you lose the ability to just change it.

```
Day 1:  You ship  GET /users/42  →  { "name": "Alice" }

Day 90: You need to split "name" into first_name / last_name

Day 90: Every client that reads response.name just broke
```

The problem isn't that you changed something. It's that you have no way of knowing who's calling you, on what version of your contract, or what breaks when you change it. A mobile app is especially brutal here — you can ship a backend change in a minute, but the old app version is sitting on millions of phones for months because users don't update immediately, and some never will.

Versioning exists to give you a way to change the contract **without breaking the clients who already depend on the old one** — either by running both shapes simultaneously, or by making the change in a way that old clients simply don't notice.

---

# What Problem It Actually Solves

- **Client lifecycle mismatch** — your backend deploys in minutes, your mobile clients deploy over months. Versioning bridges that gap.
- **Third-party integrations** — you don't control when (or if) an external developer updates their integration against your API.
- **Internal team boundaries** — even inside one company, Team A's service consuming Team B's API is still a contract neither side can silently break.
- **Confidence to actually improve the API** — without a versioning story, teams get scared to fix bad early design decisions, and the API calcifies around its first mistakes forever.

---

# What Counts as a Breaking Change

This is the part interviewers actually probe — most people know versioning exists, fewer can correctly classify a change.

## Safe (Non-Breaking) Changes

```
Adding a new optional field to a response
Adding a new optional query parameter
Adding a new endpoint
Adding a new enum value the client doesn't have to handle yet
```

A client that ignores unknown fields (which any well-written client should) doesn't notice these.

## Breaking Changes

```
Removing a field
Renaming a field
Changing a field's type (string → number)
Changing a field from optional to required
Changing the meaning of an existing status code
Changing default/implicit behavior a client silently relied on
```

```json
// Before
{ "amount": "500" }

// After — looks like an improvement, is actually a breaking change
{ "amount": 500 }
```

Any client doing `amount.startsWith(...)` or concatenating it into a string just broke. The type changed — that's breaking, full stop, no matter how small it looks in a diff.

---

# Versioning Strategies

## URI Versioning

```http
GET /v1/users/42
GET /v2/users/42
```

The version lives directly in the path. Simple, visible in every log line, trivially cacheable (different URL = different cache entry), and the most common approach in practice — Twitter, most public REST APIs.

The purist objection: the resource `/users/42` is conceptually the same entity in v1 and v2, so its identity shouldn't change based on version. In practice, almost nobody cares about this objection — operational simplicity wins.

## Header Versioning

```http
GET /users/42
Accept: application/vnd.myapi.v2+json
```

The URL stays stable; the version is negotiated via a header. This is "more correct" REST, since the resource's identity doesn't change. The cost: it's invisible in access logs unless you specifically log headers, harder to test by pasting a URL into a browser, and clients can forget to send it and silently get a default version they didn't intend.

## Query Parameter Versioning

```http
GET /users/42?version=2
```

Rare in serious APIs — it mixes versioning concerns into the same namespace as actual query filters, and is easy to strip out accidentally by tooling that normalizes query strings.

## Date-Based Versioning (Stripe's Approach)

```http
GET /v1/charges/ch_123
Stripe-Version: 2023-10-16
```

Instead of `v1`/`v2`/`v3`, Stripe versions by the *date the contract changed*, and every account is pinned to whatever version was current when the account was created — permanently, unless they explicitly opt into a newer one.

```
Account created 2021-03-01  →  pinned to the 2021-03-01 contract forever

Account explicitly upgrades →  pinned to the new date's contract
```

Internally, Stripe maintains a chain of small, additive transformations between consecutive dated versions, so a request from an old-pinned account gets transformed forward to the current internal shape, and the response gets transformed backward to what that old version expects. This means Stripe's actual database and business logic only ever deal with *one* current shape — the transformation layer absorbs all the version differences at the edge.

It's the most operationally sophisticated approach here, and no coincidence it comes from the company where breaking a client's integration means breaking someone's revenue.

## No Explicit Versioning — Additive-Only Evolution

Some APIs (Slack's, for stretches of its history) skip a version number entirely and commit to a discipline instead: only add, never remove or change existing behavior. Old fields stay forever, deprecated but present; new functionality shows up as additional fields or endpoints.

This only works if the team actually holds the line and never makes a breaking change — a cultural commitment as much as a technical one, and it gets harder to sustain the older and larger an API gets.

---

# Deprecating an Old Version

Shipping v2 doesn't mean v1 disappears the next day. A responsible deprecation communicates intent before removing anything.

```http
GET /v1/users/42

HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 31 Dec 2026 23:59:59 GMT
Link: <https://api.example.com/v2/users/42>; rel="successor-version"
```

- **`Deprecation`** — tells the client this version is on its way out.
- **`Sunset`** — an actual date after which it stops working, giving clients a concrete deadline instead of an open-ended warning they'll ignore.
- **`Link` (successor-version)** — points directly at the replacement, so a client's tooling can discover the migration path programmatically instead of a human having to go read changelog docs.

Pair this with actual usage monitoring — track which API keys or clients are still calling the deprecated version, and reach out to the stragglers as the sunset date approaches. A deprecation notice nobody reads isn't a deprecation strategy.

---

# Python Implementation

A simplified version of Stripe's date-pinning approach — storing a version per account and transforming the response at the edge, so business logic only deals with one internal shape:

```python
from datetime import date

# Each transform maps the CURRENT internal shape backward to an older
# version's shape. Applied in reverse chronological order.
VERSION_TRANSFORMS = {
    date(2024, 1, 1): lambda data: {**data, "amount": str(data["amount"])},  # int -> str
}

CURRENT_VERSION = date(2025, 6, 1)


def serialize_for_version(data: dict, account_version: date) -> dict:
    result = data
    for version_date in sorted(VERSION_TRANSFORMS, reverse=True):
        if account_version < version_date:
            result = VERSION_TRANSFORMS[version_date](result)
    return result


def handle_get_charge(charge_id: str, account_version: date) -> dict:
    charge = {"id": charge_id, "amount": 500}  # current internal shape: amount is an int
    return serialize_for_version(charge, account_version)


# An account pinned to a version before the int->str change gets the old shape
handle_get_charge("ch_123", account_version=date(2023, 1, 1))
# {"id": "ch_123", "amount": "500"}

# A newer account gets the current shape untouched
handle_get_charge("ch_123", account_version=date(2025, 1, 1))
# {"id": "ch_123", "amount": 500}
```

Notice what the code doesn't do: `handle_get_charge` never branches on version at all. Every version-specific difference lives in one isolated transform layer, which is what keeps this from turning into a spaghetti of `if version == "v1"` checks scattered across application code as versions pile up over the years.

---

# Real-World Examples

### Stripe

Date-based versioning, pinned per account, with an internal chain of additive transforms — described in detail above. Explicitly documented, including the exact list of what changed between every consecutive version pair.

---

### GitHub

```http
GET /users/octocat
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
```

GitHub moved from implicit versioning (media-type based, easy to get wrong) to an explicit `X-GitHub-Api-Version` header with a defined support window, after learning that "invisible" header versioning led to too many integrations silently depending on undocumented behavior of whatever version happened to be current when they wrote the integration.

---

### Twitter/X

```
/1.1/statuses/update.json
/2/tweets
```

Classic URI versioning. The jump from v1.1 to v2 was also used as an opportunity for a significant redesign of the resource model itself, not just a version bump — a reminder that a major version bump is often really about "we're changing the whole model," not a single field.

---

# Common Interview Questions

## URI versioning vs header versioning — which do you pick and why?

URI versioning for visibility, cacheability, and ease of testing/debugging — you can see exactly what version a request hit just from the URL in a log line. Header versioning for architectural purity (the resource's identity doesn't change across versions) at the cost of that visibility. Most teams pick URI versioning; the operational win outweighs the theoretical objection.

---

## How do you decide if a change is breaking?

Ask: would an existing client, written against the current contract, behave differently or crash if this change shipped without their code changing? Adding an optional field — no. Removing a field, renaming one, or changing a type — yes, every time, regardless of how small the change looks in a diff.

---

## How does Stripe avoid maintaining N copies of its entire codebase for N versions?

By keeping only one current internal shape and business logic, and pushing all version differences into a thin transformation layer at the API edge — a chain of small, additive request/response transforms between consecutive dated versions. The database and core logic never know or care what version the caller is pinned to.

---

## How do you actually get clients off a deprecated version?

Communicate a concrete `Sunset` date (not an open-ended warning), expose `Deprecation` and `Link` headers so tooling can detect it automatically, and — critically — actively monitor which specific clients/API keys are still hitting the old version and reach out to them directly as the deadline approaches. A deprecation notice nobody's watching isn't a real migration plan.

---

## Can you avoid versioning altogether?

Yes, if the team commits to strict additive-only evolution — never remove or repurpose an existing field or endpoint, only add new ones, and use deprecation markers for old fields you intend to eventually retire slowly. This is a real strategy (Slack has leaned on it), but it's a cultural discipline as much as a technical one, and it gets harder to sustain the older and larger the API gets.

---

# Common Mistakes

❌ Treating a type change as "just a small tweak."

`"500"` → `500` looks tiny in a diff and breaks every client that was doing string operations on that field.

---

❌ Versioning the whole API when only one endpoint actually changed.

Forces every client to migrate everything at once, even the 95% of the contract that didn't change. Fine-grained versioning (or additive evolution) avoids this.

---

❌ Deprecating a version with no concrete removal date.

An open-ended "this is deprecated, please migrate eventually" gets ignored indefinitely. A `Sunset` date creates actual urgency.

---

❌ Letting version-specific logic leak into business logic.

`if version == "v1": ... elif version == "v2": ...` scattered across handlers ages terribly. Isolate version differences into a dedicated transformation layer at the edge, like Stripe's approach.

---

❌ Not tracking which clients are on which version.

Without usage data per version, you have no way to know if it's actually safe to sunset an old version, or who to warn before you do.

---

# Key Takeaways

- Versioning exists to bridge the gap between how fast your backend can change and how slowly your clients actually update.
- Only additions (new optional fields, new endpoints) are safe by default — removals, renames, and type changes are breaking, no matter how small they look.
- URI versioning wins on operational simplicity and visibility; header versioning wins on architectural purity — most real systems pick URI versioning.
- Stripe's date-pinned versioning with a chain of additive transforms is the most sophisticated real-world pattern — one internal shape, version differences isolated entirely at the edge.
- A deprecation without a concrete `Sunset` date and active usage monitoring isn't a real migration strategy — it's a suggestion clients will ignore.
