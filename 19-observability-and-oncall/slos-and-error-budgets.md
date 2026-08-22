# SLOs and Error Budgets

> **Priority:** Required
> **Est. time:** 75 min
> **Track:** Both
> **HelloInterview:** none

Reliability targets are the only part of observability that a Staff engineer is expected to *set*, not
just *use*. Everything else in this section — alerts, on-call rotations, incident policy — is downstream
of a number that somebody negotiated with product. This file is about being the person who negotiates it.

---

## 1 · SLI, SLO, SLA — the distinctions, done precisely

| Term | What it is | Form | Audience | Consequence of breach |
|------|------------|------|----------|----------------------|
| **SLI** | Service Level *Indicator* — a measurement of one aspect of service quality | A ratio: `good events / valid events`, as a percentage | Engineering | None — it is just a number |
| **SLO** | Service Level *Objective* — a target for an SLI over a stated window | `SLI ≥ 99.9% over trailing 28 days` | Engineering + product | Internal policy fires (freeze, reprioritisation) |
| **SLA** | Service Level *Agreement* — a contract containing an objective and a penalty | `99.5% monthly uptime or 10% service credit` | Customers, legal | Money, credits, contractual remedy |
| **Error budget** | The permitted amount of unreliability: `1 − SLO` | `0.1%` → 43.2 min/30d, or *N* failed requests | Engineering + product | Spending it is the point; exhausting it triggers policy |

Three rules that separate people who have run this from people who have read about it:

1. **An SLO is always stricter than the SLA.** The SLA is what you promised the customer; the SLO is the
   internal line that gives you time to react before the promise breaks. A typical gap is one nine:
   SLA 99.5%, SLO 99.9%.
2. **An SLO without a window is meaningless.** "99.9% availability" is not an SLO. "99.9% of valid
   requests succeed, measured over a trailing 28-day window" is. The window determines the budget size,
   the alerting maths, and how long a bad day haunts you.
3. **Most services should have no SLA at all.** Internal services have SLOs. Adding an SLA to an internal
   service imports contract semantics and legal review for no benefit.

**Why 28 days and not "calendar month"?** A trailing 28-day window is always four full weeks, so it
contains the same number of weekends every time and the budget does not reset on the 1st. Calendar months
give you the "it's the 2nd, we have a fresh budget, ship everything" pathology. Use 28-day trailing for
alerting; calendar quarters for reporting to leadership if that is what they read.

---

## 2 · Choosing good SLIs

### 2.1 The two canonical forms

Almost every useful SLI reduces to one of two shapes. Both are ratios, deliberately.

**Availability / quality**

```
              count of valid requests that succeeded
SLI  =  ────────────────────────────────────────────────
                count of valid requests
```

**Latency**

```
        count of valid requests served faster than threshold T
SLI  =  ──────────────────────────────────────────────────────
                  count of valid requests
```

Note carefully what the latency SLI is **not**: it is not "p99 latency below 300 ms". It is
"99% of requests below 300 ms" — the same idea inverted so the output is a ratio, not a duration.

**Why the ratio form and not the percentile form?**

- **Percentiles do not compose.** You cannot average the p99 of ten shards to get the p99 of the service,
  and you cannot average yesterday's p99 with today's to get the two-day p99. Ratios add: good events and
  valid events are counters, and counters sum across shards and across time windows without error.
- **Error-budget arithmetic requires countable events.** "How much budget did that incident consume?" has
  an answer if the SLI is a ratio of counts and no answer if it is a percentile.
- **Burn-rate alerting is arithmetic on the ratio.** See §5. You cannot express "we are burning budget
  14× too fast" in terms of a percentile.
- **Implementation is cheaper.** A histogram bucket counter (`requests_bucket{le="0.3"}`) is a monotonic
  counter you can `rate()` and sum. A computed percentile is an estimate over a fixed window that has to
  be recomputed at every aggregation level.

The practical consequence: **instrument with histograms, define SLIs on bucket counters, keep percentiles
for dashboards and human intuition.** Pick your latency threshold *T* to land on a histogram bucket
boundary, or the SLI silently becomes an interpolation.

### 2.2 Multi-threshold latency

One threshold rarely captures the experience. A common pattern is a two-part latency SLO:

- 99% of requests faster than 300 ms (the "feels instant" line), **and**
- 99.9% of requests faster than 2,000 ms (the "gave up" line).

The first protects the median experience, the second protects the tail from becoming an availability
problem in disguise. A request that takes 45 seconds is a failed request even if it returns 200.

### 2.3 Defining "valid" and "good"

The denominator is where SLIs go wrong. Write down explicitly:

| Decision | Typical answer | Trap |
|----------|----------------|------|
| What is a *valid* event? | Requests to a real route, from a real client, that reached your system | Excluding too much until the SLI is always green |
| Do health checks count? | No — exclude by path or by a synthetic-traffic label | Health checks are 60% of your traffic and will hide a real outage |
| Do 4xx count as failures? | No for `400`/`404`/`422` (client's fault), **yes** for `429` if you caused the throttling, yes for `401` if your auth service is down | Blanket-excluding all 4xx hides broken clients you caused by shipping an incompatible API |
| Do bot/scraper requests count? | Usually excluded, but only if you can identify them stably | An exclusion rule you change during an incident is budget fraud |
| What about requests that never arrived? | Not measurable server-side — this is the argument for client-side or synthetic measurement | A total load-balancer failure gives you a *perfect* server-side SLI |

Last row is the important one and the one that catches people in interviews: **measure as close to the
user as you can afford to.** Ranked by fidelity:

1. **Client-side / RUM** — the truth, but noisy, unavailable during a total outage, and mixes in the
   user's bad Wi-Fi.
2. **Edge / load balancer / API gateway** — the usual right answer. Sees requests your service never saw.
3. **Service mesh sidecar** — at Lyft this is Envoy, which emits request metrics for free on both sides of
   every hop. Good fidelity, no application changes.
4. **Application middleware** — cheap and detailed, but blind to anything that failed before reaching the
   process (LB misconfiguration, TLS failure, connection exhaustion, OOM-killed pod).
5. **Synthetic probes / blackbox** — catches "the whole thing is down" when there is no traffic to measure.
   Complementary, not a substitute: a probe hitting one endpoint tells you nothing about the other ninety.

A mature setup uses (2) or (3) for the SLO and (5) as a floor so a zero-traffic outage still alerts.

### 2.4 The SLI menu by service type

| Service type | Availability SLI | Latency SLI | Other |
|--------------|------------------|-------------|-------|
| Request/response API | non-5xx / valid requests | fraction under T | correctness (spot-checked) |
| Async pipeline / streaming | records processed / records received | fraction processed within T of event time | **freshness**: age of newest processed record; **completeness**: records out / records in |
| Batch job | successful runs / scheduled runs | fraction finishing before deadline | coverage: fraction of input partitions processed |
| Storage | successful ops / ops | fraction under T, read and write separately | **durability**: separate concept, do not fold into availability |
| Long-running / conversational | sessions completed / sessions started | time-to-first-response | task success rate, escalation rate |

For the last row — an LLM agent platform — the tempting SLI is "conversations resolved without human
escalation". Be careful: that is a *product quality* metric, not a reliability SLI. Mixing them means an
LLM prompt regression and a database outage burn the same budget and trigger the same freeze, which is
wrong because the remediation paths are completely different. Keep two families:

- **Platform reliability SLO** — the pipeline responded at all, within a latency bound.
- **Agent quality SLO** — the answer was right / the task completed / no escalation.

They can both exist, both have budgets, and both have policies, but they should not share a budget.
See section 20 (LLM & agent systems) and `instrumenting-python-services.md` in this section.

### 2.5 SLOs go on journeys, not on microservices

This is the single most Staff-level thing in the file. If you put an SLO on every microservice you get:

- fifty SLOs nobody reads,
- no statement about whether a *user* can do anything, and
- an aggregation problem, because service SLOs do not compose into a journey SLO.

Instead, enumerate **critical user journeys** (CUJs) and put SLOs on those:

| CUJ | Spans | SLO |
|-----|-------|-----|
| Rider requests a ride and is matched | edge → matching → pricing → notification | 99.9% success, 99% under 2 s |
| Driver receives and accepts an offer | push → app → acceptance API | 99.95% success, 99% under 1 s |
| Support conversation gets a first response | edge → router → agent → LLM | 99.5% success, 95% first token under 3 s |

Three to five CUJs per product area. Individual services then get *derived* internal targets, or no SLO at
all — just enough dashboards to debug the CUJ they participate in.

---

## 3 · The arithmetic: what a number of nines actually buys

Time-based budget for common targets. A 30-day month is 43,200 minutes.

| SLO | Budget | Per 7 days | Per 30 days | Per 90 days | Per 365 days |
|-----|--------|-----------|-------------|-------------|--------------|
| 99% | 1% | 100.8 min | **7 h 12 m** | 21 h 36 m | 3 d 15 h |
| 99.5% | 0.5% | 50.4 min | **3 h 36 m** | 10 h 48 m | 43 h 48 m |
| 99.9% | 0.1% | 10.1 min | **43.2 min** | 2 h 10 m | 8 h 46 m |
| 99.95% | 0.05% | 5.0 min | **21.6 min** | 64.8 min | 4 h 23 m |
| 99.99% | 0.01% | 60.5 s | **4.32 min** | 12.96 min | 52.6 min |
| 99.999% | 0.001% | 6.0 s | **25.9 s** | 77.8 s | 5.3 min |

Read the 99.9% row again, because it is the row that changes behaviour:

> **99.9% over 30 days is 43 minutes.** One bad deploy that takes 45 minutes to roll back consumes the
> entire month. Two 20-minute incidents consume it. A single afternoon of a partially degraded dependency
> consumes it twice over.

This reframes every argument about deployment safety. "Why do we need automated rollback?" — because
manual rollback takes 25 minutes to notice plus 15 minutes to execute, and that is one incident per month
before you have spent anything on actual novel failures.

### 3.1 Event-based budgets are usually better

Time-based budgets require you to define what makes a minute "bad" (usually: error ratio in that minute
exceeds some threshold), and they weight 03:00 the same as 18:00. Event-based budgets do not:

```
Traffic:  1,000 req/s average  →  ~2.59 billion requests per 30-day month
SLO:      99.9%
Budget:   2,590,000,000 × 0.001  =  2,590,000 failed requests
```

At a smaller scale, and easier to hold in your head:

```
Traffic:  8,000,000 requests / 30 days
SLO:      99.9%
Budget:   8,000 failed requests
```

Now an incident is priced directly: "the bad deploy failed 3,100 requests, so it cost 39% of the month's
budget." No argument about whether a minute counted as down.

**When to prefer which:**

| | Time-based | Event-based |
|---|-----------|-------------|
| Uneven diurnal traffic | Overstates night incidents | Correct |
| Very low traffic services | Works | One failure = a big percentage; noisy |
| Total outage (no traffic at all) | Detects it | **Blind** — no valid events, so no failures |
| Explaining to executives | Familiar ("47 minutes down") | Needs a translation slide |

Common resolution: event-based budget for the SLO and burn-rate alerts, plus a synthetic-probe-based
availability check so a zero-traffic outage is still detected.

### 3.2 The dependency ceiling

Your SLO cannot exceed what your architecture supports. For *n* dependencies that must all work
(a serial chain, no fallbacks):

```
Achievable ≈ Π (dependency availability)

3 dependencies at 99.9%   →  0.999³   = 99.70%
5 dependencies at 99.9%   →  0.999⁵   = 99.50%
10 dependencies at 99.99% →  0.9999¹⁰ = 99.90%
```

So a service whose synchronous critical path touches five 99.9% dependencies **cannot** promise 99.9%,
and promising it anyway is how you get an SLO that is permanently in breach and therefore permanently
ignored. Your options are: reduce the number of synchronous dependencies, add fallbacks/caches so a
dependency failure degrades rather than fails, add redundancy so a dependency is not a single point, or
lower the SLO. Say this out loud in a design round — it is a strong, concrete signal.

Fallbacks change the maths in your favour. If a dependency at 99.9% has a cache fallback that serves stale
data successfully 95% of the time it is needed, the effective failure contribution drops from 0.1% to
0.1% × 5% = 0.005%.

---

## 4 · The error budget as a decision-making tool

### 4.1 The reframe

The budget is not an allowance for failure you should try to avoid using. It is **permission to take
risk**, denominated in a unit product and engineering both understand.

| Budget state | What it means | What you should do |
|--------------|---------------|--------------------|
| Consistently 90–100% remaining | Your SLO is too loose, or you are shipping too slowly / over-investing in reliability | Tighten the SLO or ship faster; reallocate reliability effort elsewhere |
| Healthy burn, ends the window at 10–40% remaining | The system is calibrated | Nothing — this is the goal |
| Repeatedly exhausted | Either the SLO is unrealistic for the architecture (see §3.2), or reliability work is genuinely underfunded | Force the choice: fund the work or move the number, in writing |

An unused error budget is a *cost*: it means you bought reliability the user did not ask for, with
engineering time that could have gone to features. That sentence is what makes product listen.

### 4.2 It converts an argument into arithmetic

Before SLOs, the conversation is: *"We need to slow down and fix reliability." / "No, we need this feature
by Q3."* Both positions are opinions and the louder person wins.

After SLOs: *"We have 12% of the budget left with 19 days to go, and the burn is 2.4× nominal. The
policy we agreed says we stop feature deploys at zero. We can spend the remaining budget on the Q3 feature
if we accept that any incident after that means a freeze — or we can spend two days on the retry storm
that is causing 60% of the burn and buy the budget back."*

Same disagreement, but now it has units, a forecast, and options. This is the sentence you want to be able
to produce in a behavioural round.

### 4.3 Getting the policy agreed *before* you need it

The most common failure of error budgets: the budget is exhausted, engineering invokes the freeze, the
VP of Product overrules it, and the budget is never mentioned again.

Prevent this by writing an **error budget policy** signed off at the level that would otherwise overrule
it, *before* the first breach:

- Who owns the SLO (a named product owner and a named engineering owner, not "the team").
- The exact thresholds and what happens at each (§6).
- Who can grant an exception, in what form, and for how long.
- How the SLO itself gets changed (only at the quarterly review, with data, never during an incident).
- What happens if the policy is overruled: it is *recorded* — the override is a documented decision with a
  name attached, not an unwritten reversal.

That last point is the real mechanism. You are usually not trying to stop a leader from overriding the
freeze; you are trying to make overriding it a visible, attributable act. That alone changes behaviour.

---

## 5 · Burn rate and multi-window multi-burn-rate alerting

### 5.1 Definition

**Burn rate** is how fast you are consuming the error budget, relative to the rate that would exactly
exhaust it at the end of the SLO window.

```
                observed error ratio
burn rate  =  ────────────────────────
                    1 − SLO
```

- Burn rate **1** → you finish the 30-day window with exactly zero budget left.
- Burn rate **2** → you run out in 15 days.
- Burn rate **1000** (a total outage against a 99.9% SLO: 100% errors / 0.1%) → you run out in 43 minutes.

| Burn rate | Error ratio at 99.9% SLO | Budget exhausted in |
|-----------|--------------------------|---------------------|
| 1 | 0.1% | 30 days |
| 3 | 0.3% | 10 days |
| 6 | 0.6% | 5 days |
| 14.4 | 1.44% | 50 hours |
| 100 | 10% | 7.2 hours |
| 1000 | 100% | 43.2 minutes |

### 5.2 Why single-window alerting fails

Suppose you alert on "error ratio over the last 5 minutes > 0.1%".

- **Terrible precision.** A 30-second blip crosses it. You page for 0.007% of the monthly budget.
- Now try "error ratio over the last 36 hours > 0.1%" to fix precision.
- **Terrible detection time.** A full outage has to run for a long time before a 36-hour average crosses
  the line.
- **Terrible reset time.** Once the incident ends, the long window keeps the alert firing for hours, so
  you cannot tell whether your fix worked and you start silencing things.

You cannot fix precision, recall, detection time and reset time with a single window. You need several.

### 5.3 The multi-window multi-burn-rate policy

The standard configuration (Google SRE Workbook), for a 30-day SLO window:

| Severity | Long window | Short window | Burn rate | Budget consumed when it fires | Time to exhaustion |
|----------|-------------|--------------|-----------|-------------------------------|--------------------|
| **Page** | 1 hour | 5 min | 14.4 | 2% | 50 hours |
| **Page** | 6 hours | 30 min | 6 | 5% | 5 days |
| **Ticket** | 24 hours | 2 hours | 3 | 10% | 10 days |
| **Ticket** | 72 hours | 6 hours | 1 | 10% | 30 days |

The arithmetic linking the columns:

```
budget consumed  =  burn rate × (long window / SLO window)

14.4 × (1 h / 720 h)  = 2%
 6   × (6 h / 720 h)  = 5%
 3   × (24 h / 720 h) = 10%
 1   × (72 h / 720 h) = 10%
```

**Both** conditions must hold — the long window *and* the short window must exceed the burn-rate
threshold. The short window (always long/12) is the "is it still happening right now?" gate. Without it,
the alert stays firing for a whole long-window duration after the incident ends. With it, the alert clears
within one short window of recovery.

**Detection time** for a given real burn rate *B*:

```
                    budget-consumed threshold × SLO window
detection time  =  ────────────────────────────────────────
                                    B
```

For the 1-hour / 14.4 page (2% threshold, 720-hour window):

| Real error ratio | Real burn rate | Detection time |
|------------------|----------------|----------------|
| 100% (total outage) | 1000 | **52 seconds** |
| 10% | 100 | 8.6 minutes |
| 5% | 50 | 17.3 minutes |
| 1.44% | 14.4 | 60 minutes (by construction) |
| 0.5% | 5 | never fires this rule — caught by the 6 h / burn-6 rule |

That table is the whole argument for burn-rate alerting in one place: a catastrophic failure pages in
under a minute, a slow leak becomes a ticket, and nothing in between pages you at 3 a.m. for something
that consumed 0.01% of the budget.

### 5.4 Implementation sketch

Precompute the ratios as recording rules — never evaluate a 72-hour `rate()` in an alert expression.

```promql
# Recording rules, one per window.
- record: job:slo_errors_ratio:rate1h
  expr: >
    sum(rate(http_requests_total{job="rides-api", code=~"5.."}[1h]))
      /
    sum(rate(http_requests_total{job="rides-api"}[1h]))

# ... repeated for 5m, 30m, 6h, 2h, 24h, 6h, 72h

# Page rule: fast burn.
- alert: RidesApiErrorBudgetFastBurn
  expr: >
    job:slo_errors_ratio:rate1h  > (14.4 * 0.001)
      and
    job:slo_errors_ratio:rate5m  > (14.4 * 0.001)
  labels:
    severity: page
  annotations:
    summary: "rides-api burning error budget 14.4x — 2% consumed in 1h"
    runbook: "https://runbooks.internal/rides-api/error-budget-burn"
```

For a **latency** SLO, the good-event count comes from histogram buckets, which are additive:

```promql
# "fraction of requests faster than 800 ms" over 1 hour
sum(rate(http_request_duration_seconds_bucket{job="rides-api", le="0.8"}[1h]))
  /
sum(rate(http_request_duration_seconds_count{job="rides-api"}[1h]))
```

Note this is a *fraction good*, so the burn-rate comparison inverts: alert when
`1 - fraction_good > burn_rate × (1 - SLO)`.

**Practical notes**

- Put the burn-rate multipliers and the SLO target in one place (a generator, or a template) so a single
  team cannot get the maths subtly wrong on their own copy.
- Low-traffic services produce a violently noisy ratio (one failure out of twelve requests is 8%). Either
  add a minimum-events guard (`and sum(rate(...[1h])) > 0.1`), lengthen the windows, or aggregate several
  low-traffic services into one SLO.
- Multiple burn-rate rules will fire simultaneously during a big incident. Use alert inhibition so the
  slow-burn ticket is suppressed while the fast-burn page is active.

---

## 6 · When the budget is exhausted

### 6.1 The staged policy

Do not have a single cliff at zero. Stage it, so the response is proportionate and starts early enough to
matter.

| Budget remaining | Policy |
|------------------|--------|
| **> 50%** | Normal operation. Ship. Take considered risks — this is what the budget is for. |
| **25–50%** | Advisory. The next planning session must include the top burn source. Risky changes (schema migrations, dependency upgrades, traffic shifts) go behind flags and staged rollouts. |
| **0–25%** | Every deploy needs a named approver and a tested rollback. No changes on Fridays or before a rotation handoff. Reliability items are pulled into the current sprint. |
| **Exhausted** | **Feature freeze.** Only reliability fixes, security fixes, and changes that reduce the burn. The team's default work item becomes the postmortem action list. |
| **Exhausted 2 windows running** | Escalate a level. A written plan from the owning manager: either funded reliability work with dates, or a formal proposal to change the SLO with data. |

### 6.2 What "freeze" must and must not mean

**Must include**: new user-facing features, non-essential dependency upgrades, non-essential
infrastructure changes, experiments.

**Must exclude** (these always ship): security patches, fixes for the ongoing burn, rollbacks, changes
that reduce risk, and anything with a legal or safety deadline. A freeze that blocks security patches will
be — correctly — ignored, and once ignored it never recovers authority.

**Time-box it.** "Frozen until the trailing 28-day budget recovers above 25%" is a condition that resolves
itself. "Frozen until further notice" becomes permanent and then becomes a joke.

### 6.3 Silver bullets

A useful pressure valve: give the product owner a small fixed number of **overrides per quarter**
(two is typical). Spending one un-freezes a release, is announced in the team channel, and is recorded
in the quarterly review.

This works because it makes the trade-off explicit and scarce without making it impossible. Product now
has a genuine reason to care about the burn rate: every incident makes their scarce override more likely
to be needed.

### 6.4 The anti-patterns

- **Relaxing the SLO to stop the alert.** If the SLO changes, it changes at a review, with data, with the
  product owner present, and the change is recorded. Never mid-incident, never by the person on call.
- **Excluding the incident from the budget retroactively.** "That was a cloud provider outage, it does not
  count." The user experienced it, so it counts. Track *attribution* separately — a column on the incident
  record, not an exemption from the maths. Attribution data is exactly what you need when negotiating
  a lower SLO or a multi-region investment.
- **Freezing the wrong team.** If service A's burn is caused by dependency B, freezing A's features is
  pure punishment. Budget policy needs an escalation path for "the burn source is not us", which routes to
  B's owner with the data attached.
- **Resetting the budget after a postmortem.** Budget consumption is a measurement, not a scoreboard you
  can clear by feeling bad about it.

---

## 7 · Negotiating SLOs with product

### 7.1 The sequence that works

1. **Start from the user, not the metric.** Ask: "what does the user do, and how do they know it broke?"
   That produces the CUJ list. Do not open by proposing a number.
2. **Measure what you have today.** Instrument the CUJ and watch it for two to four weeks with no target
   at all. Now you have a distribution, not a guess.
3. **Propose a target slightly below current performance.** If you are measured at 99.94%, propose 99.9%.
   Reason: an SLO you are already breaching produces alert fatigue and gets ignored in week two; an SLO
   you comfortably beat produces no signal. Just under current performance gives a live budget.
4. **Run it provisionally for a quarter.** Label it explicitly as provisional. No freeze policy yet, only
   reporting. This is what makes product willing to agree at all — it is reversible.
5. **Formalise at the quarterly review**, with the observed burn, the incidents that caused it, and a
   proposed policy.

### 7.2 The conversations you will actually have

**"Why not 100%?"**
Because 100% is not achievable and pursuing it is not free. Every nine costs roughly an order of magnitude
more: redundancy, multi-region, extra on-call, slower releases. Also, the user's own path to you is not
100% — mobile networks, DNS, their own device. Reliability far above the client's own reliability is
invisible to them and is money burnt.

**"Why not 99.99%?"**
Turn it into a price. "99.99% is 4.3 minutes a month. That means automated failover with no human in the
loop, multi-AZ everything, a doubled on-call rotation, and a release process with automated canary
analysis. Roughly *X* engineer-quarters and *Y* per month in infrastructure. Do we want to spend that here
or on the thing we discussed last week?" The point is not to refuse; it is to make the cost visible so the
decision is theirs and informed.

**"What does the user actually notice?"**
The best evidence is empirical: correlate historical latency and error rates against a business metric
(conversion, session abandonment, support contacts). If p95 latency above 1.5 s correlates with a
measurable drop-off and 1.0 s does not, your threshold is between them and you can defend it. This is the
single strongest move available and almost nobody does it.

**"The dependency is the problem, not us."**
See §3.2. Bring the composition arithmetic. It converts "we need the platform team to do better" from a
complaint into a specific number: "our ceiling is 99.7% while we make five serial calls; here are two
ways to raise it."

### 7.3 Rules for the number itself

- **Never set an SLO you cannot measure.** If the instrumentation does not exist, the first deliverable is
  the instrumentation, not the target.
- **Never set an SLO nobody will act on.** An SLO with no policy attached is a dashboard, and dashboards
  do not change behaviour.
- **Differentiate by tier.** A payment path and a recommendations widget do not deserve the same target.
  Publish a small tier table (Tier 1: 99.95%, Tier 2: 99.9%, Tier 3: 99.5%, best-effort: no SLO) so new
  services pick from a menu instead of inventing a number.
- **Fewer is better.** Three well-understood, well-defended SLOs beat forty auto-generated ones.

---

## 8 · Anti-patterns quick reference

| Anti-pattern | Why it is wrong | Fix |
|--------------|-----------------|-----|
| SLI defined as a percentile value | Percentiles do not aggregate or compose | Ratio of requests under a threshold |
| SLO per microservice | Says nothing about whether a user could do anything | SLOs on critical user journeys |
| SLO measured in the application only | Blind to LB, TLS, connection, and OOM failures | Measure at edge or mesh; add synthetic probes |
| Health-check traffic in the denominator | Hides real failures under a mountain of green | Exclude by route or synthetic-traffic label |
| Budget policy written after the first breach | Gets overruled and never recovers authority | Sign it off in advance, at the level that would overrule it |
| Single-window alert threshold | Noisy, or slow, or both | Multi-window multi-burn-rate |
| 100% SLO / "five nines" by default | Unachievable and unpriced | Tier table with justified targets |
| Retroactive exclusions | Turns the budget into a negotiation | Attribute causes, never exempt |
| Setting the SLO to match current performance exactly | Zero budget from day one; permanent freeze | Slightly below observed |

---

## 9 · Staff framing: rolling SLOs out across an organisation

If asked "how would you introduce SLOs at Lyft-scale?", the wrong answer is a definition of SLI/SLO/SLA.
The right answer is a rollout plan with a stopping condition.

1. **Pick one team with a real problem.** Not the healthiest team, not the worst — a team with visible
   pager pain and a cooperative product partner. Success needs to be legible.
2. **Two or three CUJs, not thirty.** Instrument, observe for a month, no targets.
3. **Build the paved road while you do it**: an SLO definition format in code, a generator that produces
   the recording rules and the four burn-rate alerts, a dashboard template, and a budget report. The point
   is that team two spends a day on this, not a month.
4. **Publish the pilot's before/after numbers**: pages per week, percentage actionable, budget consumed,
   incidents caught by burn-rate alerts before a customer reported them.
5. **Expand by pull, not push.** Teams adopt because the pilot team's on-call is visibly better. If nobody
   pulls, the pilot did not produce a good enough result and pushing will not fix that.
6. **Then make it policy** for tier-1 services only, with a defined owner, a review cadence, and a
   template. Never mandate before the paved road exists — a mandate without tooling produces forty bad
   SLOs and permanent cynicism.
7. **Stopping condition**: SLOs that nobody looks at get deleted at the quarterly review. Coverage is not
   the goal; behaviour change is.

Cross-links: `alert-design.md` (turning the burn rate into pages), `oncall-health.md` (measuring whether
the result was actually better), `incident-response.md` (the freeze policy in practice).

---

## Interview questions

**1. What is the difference between an SLI, an SLO, and an SLA?**
An SLI is a measurement — a ratio of good events to valid events. An SLO is a target for that ratio over a
stated window, used internally to drive engineering decisions. An SLA is a contract with a customer
containing an objective and a financial or contractual penalty. The SLO should always be stricter than the
SLA so you have room to react before the contract breaks, and most internal services should have an SLO
and no SLA at all.

**2. A team proposes "p99 latency under 300 ms" as their SLI. What is wrong with it?**
It is a percentile, not a ratio, so it does not compose: you cannot aggregate p99s across shards or across
time windows, and you cannot express error-budget consumption or burn rate in terms of it. Rewrite it as
"99% of valid requests complete in under 300 ms" — the same intent, but now the SLI is a count of good
events over valid events, which sums correctly, is cheap to compute from histogram buckets, and supports
burn-rate alerting.

**3. What does a 99.9% monthly SLO actually allow, and why does that matter?**
43.2 minutes of budget in a 30-day month, or equivalently 0.1% of requests — 8,000 failed requests if you
serve 8 million a month. It matters because it prices deployment safety: a single bad deploy that takes 45
minutes to detect and roll back consumes the entire month. That turns "should we invest in automated
rollback and canary analysis" from a preference into arithmetic.

**4. Explain burn-rate alerting and why you would use multiple windows.**
Burn rate is the observed error ratio divided by the error budget, so burn rate 1 exhausts the budget
exactly at the end of the SLO window. A single window forces a bad trade-off: short windows are noisy,
long windows detect slowly and reset slowly. A multi-window multi-burn-rate policy runs several rules —
typically 1 h at 14.4× and 6 h at 6× as pages, 24 h at 3× and 72 h at 1× as tickets — each paired with a
short window at one twelfth the length to confirm the burn is still happening. A total outage then pages
in about 52 seconds while a slow leak becomes a ticket instead of a 3 a.m. page.

**5. How would you decide between a time-based and a request-based error budget?**
Request-based, unless there is a reason not to. Time-based budgets weight a 03:00 outage the same as an
18:00 one and require an arbitrary definition of what makes a minute "bad". Request-based budgets price
incidents directly in failed user requests. The exception is very low traffic, where a handful of failures
produces a wild ratio, and total outages, where there is no traffic to measure — so pair the request-based
SLO with a synthetic probe so a zero-traffic outage still alerts.

**6. Product wants 99.99% availability. How do you handle that conversation?**
First check whether it is achievable: if the critical path makes five serial calls to 99.9% dependencies,
the ceiling is 99.5% and no amount of effort in my service changes it. Then price it — 99.99% is 4.3
minutes a month, which implies automated failover, multi-region, canary analysis, and a bigger on-call
rotation — and put the cost next to what else that investment could buy. The decision is theirs; my job is
to make sure it is informed rather than aspirational. Best case, I bring data correlating latency and
errors with an actual business metric so the target is empirical.

**7. Your error budget is exhausted with two weeks left in the window. What happens?**
Whatever the pre-agreed error budget policy says — which is the important part, because the policy has to
exist before the breach or it gets overruled. Typically: feature deploys stop, reliability fixes and
security patches continue, the postmortem action list becomes the team's default work, and the freeze
lifts when the trailing budget recovers above a threshold. If product needs an exception there is a small
quarterly allowance of overrides, spent visibly. What I would not do is relax the SLO or retroactively
exclude the incident.

**8. How do you avoid SLO sprawl in a large organisation?**
Put SLOs on critical user journeys rather than on every microservice — three to five per product area —
and give services a tier table to pick from rather than letting each team invent a number. Build the paved
road first: a definition format in code that generates the recording rules, burn-rate alerts, dashboard,
and budget report. Then delete SLOs nobody looks at during the quarterly review. Coverage is not the goal;
the goal is a small number of targets that actually change decisions.

**9. Should a dependency's outage count against your error budget?**
Yes, because the user experienced the failure regardless of whose fault it was, and an SLO that excuses
dependency failures stops describing the user's experience. But record the attribution on the incident, so
you can show at the quarterly review that, say, 60% of the burn came from one dependency. That is the
evidence for either a fallback, a cache, a redundancy investment, or a renegotiated SLO — all of which are
better outcomes than an exemption clause.

**10. Your service has an SLO but nobody has ever been paged by it. Good or bad?**
Suspicious. Either the SLO is far looser than actual performance, in which case it provides no signal and
should be tightened, or the alerting is not actually wired to the burn rate, or the service genuinely has
no traffic. A healthy SLO ends its window with some budget consumed but not exhausted. Consistently
finishing at 100% remaining means you bought reliability nobody asked for, which is a real cost paid in
engineering time.
