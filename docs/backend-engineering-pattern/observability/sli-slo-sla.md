# SLI, SLO, SLA, and Error Budgets

# Why Do SLIs, SLOs, and SLAs Exist?

"Make the system reliable" is meaningless as an engineering goal — it can't be measured, can't be argued about with data, and gives no basis for deciding whether a specific incident actually mattered or whether a risky deploy is acceptable this week. SLIs, SLOs, and SLAs exist to turn a vague aspiration into something precise, measurable, and directly actionable — the vocabulary that lets "reliable" mean something specific enough to make real engineering trade-off decisions around.

```
Vague:     "the payment service should be reliable"

Precise:   "99.9% of payment requests should complete successfully
            within 300ms, measured over a rolling 30-day window"
```

---

# SLI — Service Level Indicator

An actual, concrete **measurement** of some aspect of the service's behavior — built directly from the metrics covered in the Metrics chapter.

```
SLI examples:

- The percentage of requests that complete successfully
- The percentage of requests that complete within 300ms (p99 latency threshold)
- The percentage of time the service was available at all
```

```promql
# A concrete SLI, expressed as a PromQL query:
sum(rate(http_requests_total{status!~"5.."}[30d]))
/
sum(rate(http_requests_total[30d]))
```

An SLI is just a number, computed from real, observed data — it makes no judgment about whether that number is good or acceptable; it's purely a measurement of reality as it actually is.

---

# SLO — Service Level Objective

A **target** for an SLI — the internal goal an engineering team holds itself to.

```
SLO: "99.9% of requests will complete successfully,
      measured over a rolling 30-day window"
```

This is an internal commitment, set by the team that owns the service, based on what's actually achievable and what the business genuinely needs — not an external promise made to a customer (that's the SLA, covered next). An SLO is where "reliable" gets a precise, agreed-upon definition that the team can be held accountable to, and that engineering decisions can be measured against.

---

# SLA — Service Level Agreement

An SLO that's been turned into an **external, often contractual promise** to customers — typically with real consequences (a service credit, a refund, a penalty) if it's violated.

```
Internal SLO:     99.9% success rate

External SLA:     99.5% success rate (deliberately LOOSER than
                    the internal SLO)
```

```
SLI  →  measures reality (the actual, observed number)
SLO  →  the internal target the team holds itself to
SLA  →  the external, contractual promise — deliberately set
         LOOSER than the SLO, giving a safety margin
```

The SLA is almost always set with more slack than the internal SLO, and this is deliberate, not sloppy — it gives the team room to notice a problem and fix it *before* actually breaching the external, often costly, contractual commitment. If the internal SLO and external SLA were set to the exact same number, the team would have zero buffer between "we're starting to see a problem internally" and "we've now broken a paying customer's contractual guarantee."

---

# Error Budgets — The Concept That Makes This Practical Rather Than Abstract

This is arguably the single most valuable, most frequently cited idea from Google's SRE practice, precisely because it turns an abstract reliability target into a concrete, everyday engineering decision-making tool.

```
SLO: 99.9% success rate

↓

Error Budget = the remaining 0.1% — a concrete, SPENDABLE
               allowance for acceptable failure
```

```
If the SLO is 99.9% over 30 days, and the service has been running
at 99.95% (better than the target) so far this period:

↓

There's error budget REMAINING — the team has room to take on some
additional risk: ship a riskier feature, run a more aggressive
experiment, or accept a brief planned maintenance window

If the service has been running at 99.85% (worse than the target):

↓

The error budget is EXHAUSTED — the team should shift focus toward
stability and reliability work, and be far more conservative about
shipping new, risky changes until performance recovers back within budget
```

This reframes reliability work from a vague, ongoing tension ("ship fast" vs "be careful") into a concrete, data-driven decision: **is there error budget left, or not?** A team with budget to spare has genuine, deliberate license to take calculated risks; a team that's blown through its budget has a clear, objective signal to pump the brakes on risky changes and prioritize stability instead — removing the need for that decision to be an argument based on gut feeling or organizational politics.

---

# Real-World Examples

### Google's SRE Book

The original, formalized source of error budgets as a deliberate engineering practice — Google's Site Reliability Engineering discipline uses error budgets explicitly to balance the tension between feature velocity and reliability, giving teams an objective, shared metric to base release decisions on rather than an ongoing subjective negotiation between product and engineering priorities.

---

### Cloud Provider SLAs

Public cloud SLAs (a specific uptime percentage with a defined service credit for violations) are a direct, visible real-world instance of the SLA concept — deliberately set looser than whatever the provider's actual internal SLO and observed performance typically are, giving the provider a real operational safety margin before an external, contractual commitment is ever at risk.

---

### Release Freezes Triggered by Budget Exhaustion

Companies practicing SRE seriously will explicitly freeze non-critical feature releases once a service's error budget for the period is exhausted, resuming normal release velocity only once performance recovers back within budget — a direct, practical, observable consequence of taking the error budget concept seriously rather than treating it as a purely theoretical framework.

---

# Common Interview Questions

## Explain the difference between an SLI, an SLO, and an SLA.

An SLI is an actual measurement of the service's behavior (the percentage of requests that succeeded). An SLO is an internal target for that measurement, that the engineering team holds itself to. An SLA is that target turned into an external, often contractual promise to customers, typically with consequences for violation, and deliberately set looser than the internal SLO to leave a safety margin.

---

## Why is an SLA usually looser than the internal SLO?

To give the team room to notice and fix a developing problem before actually breaching an external, often costly, contractual commitment. If the SLA and SLO were identical, there'd be zero buffer between "we're starting to see trouble internally" and "we've now broken a customer-facing guarantee" — the gap between them is a deliberate safety margin, not an oversight.

---

## What is an error budget, and how does it actually change day-to-day engineering decisions?

The allowed amount of failure implied by an SLO — if the SLO is 99.9%, the error budget is the remaining 0.1%. It's a concrete, spendable allowance: if the budget has room remaining, a team has genuine license to take on calculated risk (ship a riskier feature, run an experiment); if the budget is exhausted, the team should shift focus to stability and be far more conservative about further risky changes until performance recovers. It turns "should we ship this risky thing" from a subjective argument into an objective, data-driven decision.

---

## How would you define an SLI for a checkout service?

Something like "the percentage of checkout requests that complete successfully within 500ms," computed directly from request metrics (success/failure counts and latency histograms, from the Metrics chapter) — the specific measurement should reflect what actually matters to the user's real experience of that flow, not an arbitrary internal system metric with no direct connection to what the customer actually experiences.

---

## What's wrong with setting an SLO at 100%?

It's both unrealistic (no real system achieves perfect reliability indefinitely) and removes the entire error budget concept — with zero allowed failure, there's no room for legitimate risk-taking, routine maintenance, or planned deployments at all, since literally any failure at all would violate the target. A well-chosen SLO deliberately leaves room for the kind of normal operational activity every real system needs to perform.

---

# Common Mistakes

❌ Conflating SLI, SLO, and SLA as if they're interchangeable terms for the same thing.

Each plays a distinct role — a measurement, an internal target, and an external contractual promise — and confusing them muddles both how they're set and how they're used in actual engineering decisions.

---

❌ Setting an SLO at 100%.

Unrealistic, and eliminates any error budget at all — leaving no room for legitimate risk-taking, routine maintenance, or planned deployments without technically violating the target.

---

❌ Setting an external SLA equal to (or tighter than) the internal SLO.

Removes the safety margin the gap between them is supposed to provide, meaning any developing internal problem immediately risks breaching an external, potentially costly commitment with no buffer to notice and fix it first.

---

❌ Treating an SLO as a purely reporting/compliance exercise rather than an actual decision-making tool.

The real value of an SLO (via its error budget) is in actively shaping day-to-day engineering priorities — release pace, risk tolerance — not just producing a number for a quarterly report nobody actually acts on.

---

# Key Takeaways

- SLIs, SLOs, and SLAs exist to turn a vague aspiration ("be reliable") into a precise, measurable, actionable target — an SLI measures reality, an SLO is the internal goal, and an SLA is that goal turned into an external, contractual promise.
- An SLA is deliberately set looser than the internal SLO, giving the team a genuine safety margin to notice and address a developing problem before an external commitment is actually breached.
- An error budget — the allowed amount of failure implied by an SLO — turns reliability from an abstract goal into a concrete, spendable allowance that directly informs real engineering decisions about release pace and risk tolerance.
- A team with error budget remaining has genuine license to take on calculated risk; a team that's exhausted its budget has a clear, objective signal to prioritize stability over new, risky changes.
- Setting an SLO at 100% is a common mistake — it's unrealistic and removes any error budget at all, leaving no room for the routine risk every real system needs to be able to take.
