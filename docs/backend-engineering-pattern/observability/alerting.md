# Alerting

# Why Does Alerting Exist?

A dashboard, however well-designed, only helps if a human happens to be looking at it at the exact moment something goes wrong — and real incidents don't schedule themselves around business hours. Alerting exists to flip this around: instead of relying on someone noticing a problem on a dashboard, the system itself actively notifies a human (or triggers automated action) the instant a monitored condition crosses a concerning threshold.

```
Dashboard:  requires a human to be ACTIVELY WATCHING, at the
             right moment, to notice a problem

Alerting:    the SYSTEM notices the problem, and actively
             notifies a human — no one needs to be watching
             at that exact moment for it to work
```

---

# Alert on Symptoms, Not Causes

This is one of the most important, most quoted principles in this entire chapter, and it's a genuinely common interview topic on its own.

```
CAUSE-based alerting:    "CPU usage is at 85%"

SYMPTOM-based alerting:  "p99 latency has exceeded 500ms" or
                          "error rate has exceeded 2%"
```

High CPU alone doesn't necessarily mean users are actually having a bad experience — the service might be handling that load perfectly fine, well within its actual capacity. Alerting on every possible internal cause, rather than on what users actually experience, produces alerts that fire even when nothing is genuinely wrong from the user's perspective — which is exactly the seed of the next problem, alert fatigue.

```
The practical principle:  alert on the things that DIRECTLY
                          reflect user-facing impact (the four
                          golden signals from the Metrics chapter
                          — latency, traffic, errors, saturation
                          measured as an actual limit being hit,
                          not just "CPU is somewhat elevated")

                          Use internal-cause metrics for
                          INVESTIGATION and DASHBOARDS, once an
                          alert has already fired — not as the
                          alert trigger itself
```

This directly sets up the SLI/SLO chapter — a symptom-based alert is, in practice, usually built directly from the same SLIs that define what "healthy" means for a service in the first place.

---

# Alert Fatigue — A Real, Well-Documented Operational Failure Mode

```
Too many alerts, too many of them low-value or non-actionable

↓

On-call engineers start treating alerts as background noise
rather than something requiring immediate attention

↓

A GENUINE, serious incident's alert gets the same reduced
attention as the dozens of noisy, unimportant ones before it

↓

The entire purpose of alerting — getting a human's attention
FAST when something actually matters — is undermined
```

This is exactly the "boy who cried wolf" problem, and it's a well-documented, real cause of missed or delayed incident response at organizations that don't actively manage their alert volume and quality. The fix isn't more alerts, or more sensitive thresholds — it's the opposite: being deliberate and disciplined about which conditions actually deserve to interrupt a human, and aggressively pruning or tuning anything that fires often without being genuinely actionable.

```
A useful test for any alert:  "if this fires, does someone
                                need to DO something right now?"

If the answer is no → it probably shouldn't be a page/alert at
                       all — maybe a dashboard panel, or a lower-
                       urgency notification instead
```

---

# Alertmanager

Prometheus's companion component specifically for handling what happens *after* an alert condition is detected — deduplication, grouping, routing, and silencing.

```
Deduplication:  the SAME underlying issue triggering multiple,
                 nearly-identical alert instances (e.g. from many
                 replicas of the same service) gets collapsed into
                 ONE notification instead of a flood of duplicates

Grouping:       related alerts (e.g. every service in one data
                 center reporting problems during a single
                 regional outage) get bundled into one coherent
                 notification instead of dozens of separate,
                 disconentected pages

Routing:        different alerts get sent to the right team/channel
                 based on their labels — a database alert goes to
                 the database team, not the whole engineering org

Silencing:       during a KNOWN maintenance window or an already-
                 acknowledged, in-progress incident, related alerts
                 can be deliberately suppressed instead of continuing
                 to page on something already being actively handled
```

Without this layer, a single underlying incident (say, one data center losing power) could generate hundreds of individual, disconnected alerts — one per affected service, per replica — completely burying the actual, single root cause under a flood of noise at exactly the moment clarity matters most.

---

# Runbooks

Every alert should be paired with a documented, actionable response procedure — precisely because the person responding to a 3am page is very often not the engineer who originally wrote the alerting rule or built the underlying system.

```
Alert fires: "Payment Service error rate > 5%"

↓

WITHOUT a runbook:  the on-call engineer has to figure out, from
                     scratch, under time pressure, what this
                     service even does and what might be wrong

WITH a runbook:      a documented procedure — check X dashboard,
                      look for Y specific failure pattern, here's
                      how to safely restart/rollback if needed,
                      here's who to escalate to if this specific
                      step doesn't resolve it
```

A runbook turns "an alert fired, now what" into a concrete, followable procedure — dramatically reducing both the time to resolution and the cognitive load on whoever happens to be on-call, especially for a system they didn't personally build.

---

# Real-World Examples

### PagerDuty / Opsgenie

Widely used tools specifically for on-call scheduling, alert routing, and escalation — if the primary on-call engineer doesn't acknowledge an alert within a configured time window, it automatically escalates to a secondary responder, ensuring a genuinely critical alert doesn't go unanswered just because one specific person happened to be unreachable.

---

### Prometheus + Alertmanager

The standard open-source pairing in cloud-native stacks — Prometheus evaluates alerting rules against its collected metrics, and Alertmanager handles the deduplication, grouping, routing, and silencing described above before a notification ever reaches a human.

---

### A Real Regional Outage

A directly illustrative case for why grouping matters — dozens of individual services all reporting elevated error rates simultaneously during one regional infrastructure failure should ideally surface as one clear, grouped "region X is down" notification, not fifty separate, seemingly-unrelated pages arriving at once.

---

# Common Interview Questions

## Why should you alert on symptoms rather than causes?

Because an internal cause (elevated CPU, for instance) doesn't necessarily mean users are actually experiencing a problem — a service might handle that load perfectly fine within its actual capacity. Alerting on symptoms (elevated latency, error rate) ties alerts directly to genuine user-facing impact, avoiding alerts that fire even when nothing is actually wrong from the user's perspective, which directly reduces alert fatigue.

---

## What is alert fatigue, and how do you prevent it?

The phenomenon where too many low-value, non-actionable alerts train on-call engineers to start ignoring alerts as background noise — meaning a genuinely serious incident's alert can receive the same reduced attention as the noise preceding it. Preventing it means being deliberate about which conditions genuinely warrant interrupting a human, and aggressively pruning or tuning any alert that fires often without requiring real action.

---

## What does Alertmanager actually do?

Deduplication (collapsing many near-identical alert instances into one notification), grouping (bundling related alerts from a single root cause into one coherent notification instead of a flood of separate ones), routing (sending different alerts to the right team based on labels), and silencing (suppressing alerts during known maintenance windows or an already-acknowledged incident).

---

## Why should every alert have an associated runbook?

Because the person responding to an alert — especially outside business hours — is very often not the engineer who wrote the alerting rule or built the system it's monitoring. A runbook turns "an alert fired, now what" into a concrete, followable procedure, dramatically reducing both time to resolution and the cognitive burden on whoever happens to be on-call for a system they may not have deep familiarity with.

---

## How does alerting relate to the SLIs/SLOs a team defines?

Symptom-based alerts are, in practice, usually built directly from the same SLIs used to define a service's reliability targets — an alert firing when latency exceeds a threshold is typically tied to the exact SLI (and its associated SLO) the team has already committed to, rather than an arbitrary, disconnected number.

---

# Common Mistakes

❌ Alerting on every possible internal metric instead of user-facing symptoms.

Produces alerts that fire even when users aren't actually experiencing a problem, directly feeding alert fatigue and training responders to start ignoring notifications.

---

❌ Having no runbook attached to an alert.

Leaves whoever's on-call to figure out an unfamiliar system from scratch under time pressure, dramatically increasing both stress and time to resolution.

---

❌ Not deduplicating or grouping related alerts.

A single root cause can generate a flood of separate, seemingly-unrelated pages, burying the actual underlying issue under noise exactly when clarity matters most.

---

❌ Treating alert thresholds as a "set once and forget" configuration.

Alert thresholds need periodic review as a service's traffic patterns and baseline behavior change over time — a threshold that made sense a year ago can become either too noisy or too insensitive as the system evolves.

---

# Key Takeaways

- Alerting exists to proactively notify a human the instant a concerning condition is detected, rather than relying on someone happening to be watching a dashboard at the right moment.
- Alerting on symptoms (user-facing impact — latency, error rate) rather than every possible internal cause (CPU, memory) ties alerts directly to what actually matters, and is a direct defense against alert fatigue.
- Alert fatigue — too many low-value alerts training responders to start ignoring notifications — is a real, well-documented failure mode that undermines the entire purpose of alerting; the fix is disciplined pruning, not more sensitive thresholds.
- Alertmanager's deduplication, grouping, routing, and silencing exist specifically to prevent a single root cause from generating an overwhelming flood of disconnected, individually-fired alerts.
- Every alert should be paired with a runbook, since the person responding is very often not the engineer who built the system or wrote the alert — a documented procedure turns "now what" into a concrete, followable response.
