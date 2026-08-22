# Alert Design

> **Priority:** Required
> **Est. time:** 60 min
> **Track:** Both
> **HelloInterview:** none

Most organisations do not have an alerting problem, they have an alerting *inventory* problem: hundreds of
rules accumulated by people who have left, firing at people who cannot act on them, for conditions no user
would notice. This file is about the design principles and — more usefully for a Staff interview — about
running noise reduction as a measurable programme with a before/after table.

Prerequisite: `slos-and-error-budgets.md`, which supplies the burn-rate maths used throughout.

---

## 1 · Symptom-based vs cause-based alerting

| | Symptom-based | Cause-based |
|---|---------------|-------------|
| Example | "3% of checkout requests are failing" | "CPU on web-07 is at 91%" |
| Measures | What the user experiences | An internal condition that *might* cause it |
| Count grows with | Number of user journeys (a handful) | Number of components (thousands) |
| False negatives | Rare — if the user is hurt, it fires | Common — a failure mode you did not anticipate has no rule |
| False positives | Rare — the user really is hurt | Very common — high CPU is often completely fine |
| On-call action | Clear: something is broken, find it | Unclear: is this bad? |

**Page on symptoms. Use causes for diagnosis.**

The scaling argument is the one that convinces people. You have five user journeys and forty thousand
container instances. Symptom-based alerting needs on the order of twenty rules and covers failure modes
nobody has thought of yet, because any cause that hurts users produces the symptom. Cause-based alerting
needs a rule per resource per component and still misses the novel failure — the one where CPU, memory,
disk and queue depth are all green and the service is returning 500s because a certificate expired.

### 1.1 The legitimate exceptions

Some cause-based alerts are correct, and they share a property: **a certain future symptom with a long
lead time and a slow remedy.**

| Alert | Why it is legitimate | Severity |
|-------|---------------------|----------|
| Disk will be full in 4 hours (extrapolated) | Certain outage, and freeing disk takes time | Page if < 4 h, ticket if < 7 days |
| TLS certificate expires in 21 days | Certain total outage, renewal has lead time | Ticket at 21 days, page at 48 hours |
| Cloud quota / IP exhaustion approaching | Certain failure, quota increases take days | Ticket |
| Backup has not succeeded in 48 hours | The symptom only appears when you need it, at which point it is too late | Ticket, escalating |
| Replication lag growing without bound | Certain data-loss or failover risk | Page |
| Certificate/credential rotation failing | Silent until the outage | Ticket |

The test: *"if I ignore this, will a user definitely be hurt later, and would I need the lead time?"*
"Definitely" and "need the lead time" both have to be true. "CPU is at 90%" fails both.

### 1.2 Where saturation alerts belong

Saturation signals — CPU, memory, thread pool, connection pool, queue depth — are extremely valuable, and
they belong on **dashboards and in runbooks**, not on pagers. They are how you diagnose the symptom in
three minutes instead of thirty. Demoting them from pages to diagnostics does not throw them away; it
moves them to where they are actually useful.

The framing to remember: **RED for alerting, USE for diagnosis.**

- **RED** (Rate, Errors, Duration) — per service or endpoint. User-facing. This is where alerts come from.
- **USE** (Utilisation, Saturation, Errors) — per resource. Internal. This is where explanations come from.

---

## 2 · The properties of a good page

A page is an interrupt that may arrive at 03:00 and costs a human several hours of degraded capacity. It
has to earn that. Four tests, all of which must pass:

1. **Actionable.** There is something the recipient can do *right now*. Not "escalate to a team that is
   asleep", not "watch it".
2. **Urgent.** It cannot wait until morning without meaningful additional harm. If a four-hour delay
   changes nothing, it is a ticket.
3. **Novel.** It is not the fifth copy of an alert already firing for the same underlying cause, and it is
   not the same self-resolving flap as last Tuesday.
4. **User-relevant.** A user is being hurt now, or will certainly be hurt soon (§1.1).

Two more tests worth applying:

5. **Owned.** A named team owns the service and the alert. Unowned alerts always end up paging whoever is
   nearest, which is how alerting decays.
6. **Documented.** The alert links to a runbook that says what it means and what to check first. No
   runbook, no page — this should be enforced in code review.

### 2.1 The three-bucket policy

Every alert is exactly one of:

| Bucket | Delivery | Criteria | Response expectation |
|--------|----------|----------|---------------------|
| **Page** | Push + phone, escalates | All six tests pass | Acknowledge within 5 minutes, any hour |
| **Ticket** | Queue reviewed each working day | Needs human action, not urgent | Handled within the shift or the sprint |
| **Delete** | Nothing | Fails "actionable" or "user-relevant" | — |

There is a fourth thing people ask for — "just send it to a Slack channel so we can keep an eye on it".
That is the delete bucket with extra steps. A channel that receives 400 messages a day is read by nobody
and creates a false sense of coverage. If it matters, it is a ticket with an owner; if it does not, delete
it. The only legitimate use for a firehose channel is as an audit trail nobody is expected to read.

---

## 3 · Alerting on burn rate rather than utilisation

Resource utilisation is a *proxy* for user harm, and it is a bad one in both directions:

- **CPU at 90% with healthy latency and errors is fine.** It might even be the goal — you paid for that
  CPU. Paging on it means paging on efficiency.
- **CPU at 35% with a saturated connection pool is an outage.** The utilisation alert is silent while
  every request queues.

Burn-rate alerting inverts this: it alerts on the user-visible SLI, and the amount of error budget being
consumed determines the severity. That gives you a severity scale that is *derived* rather than guessed,
and it makes "is this worth waking someone up for" an arithmetic question. The full policy is in
`slos-and-error-budgets.md` §5; the summary:

| Severity | Long window | Short window | Burn rate | Budget consumed |
|----------|-------------|--------------|-----------|-----------------|
| Page | 1 h | 5 min | 14.4 | 2% |
| Page | 6 h | 30 min | 6 | 5% |
| Ticket | 24 h | 2 h | 3 | 10% |
| Ticket | 72 h | 6 h | 1 | 10% |

---

## 4 · Worked example: a noisy CPU alert becomes an SLO burn-rate alert

*Illustrative worked example. The numbers are invented to show the shape of the analysis, not drawn from
any real service.*

### 4.0 The starting point

```yaml
- alert: RidesApiHighCPU
  expr: |
    avg by (instance) (
      1 - rate(node_cpu_seconds_total{mode="idle", job="rides-api"}[5m])
    ) > 0.80
  for: 5m
  labels:
    severity: page
  annotations:
    summary: "CPU above 80% on {{ $labels.instance }}"
```

Pull the last 90 days of firing history out of the alert manager before touching anything:

| Measurement | Value |
|-------------|-------|
| Times fired (90 days) | 62 |
| Fired between 22:00 and 08:00 | 21 |
| Self-resolved within 10 minutes, no action taken | 51 |
| Correlated with any user-visible degradation | 4 |
| **Precision (actionable / total)** | **4 / 62 = 6.5%** |
| Median time to acknowledge | 11 min |
| Runbook linked | No |

Two conclusions. First, this alert is noise: 93.5% of its pages were wasted. Second — and this is the part
people miss — **the four real incidents are the reason nobody will let you simply delete it.** You need a
replacement that catches those four, not just a deletion.

Also note the 11-minute MTTA. That is not slowness; that is people having learned the alert is usually
nothing.

### 4.1 Step 1 — define what the user actually does

CUJ: *a rider requests a ride and gets a response.* The entry point is `POST /v1/rides`.

### 4.2 Step 2 — define the SLI

```
             requests to POST /v1/rides that returned non-5xx within 800 ms
SLI  =  ───────────────────────────────────────────────────────────────────────
             requests to POST /v1/rides excluding health checks and 400/422
```

Measured at the Envoy sidecar (not in the app) so that connection failures, timeouts and pods that died
mid-request are counted as failures rather than disappearing.

### 4.3 Step 3 — instrument

Histogram with bucket boundaries chosen so the SLO threshold lands exactly on a boundary — otherwise the
SLI is an interpolation:

```
le = 0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, +Inf
                        ^^^ the SLO threshold
```

Labels bounded to `{route, status_class}`. No `pod`, no `user_id`, no raw path.

### 4.4 Step 4 — set the SLO from measured data

Trailing 28-day measurement, before setting any target: **99.94%**.
Set the SLO at **99.9%** — just below observed, so there is a live budget without a permanent breach.

```
Traffic:  8,000,000 requests / 28 days
Budget:   8,000,000 × 0.001  =  8,000 failed-or-slow requests
          (equivalently 40.3 minutes of a 28-day window)
```

### 4.5 Step 5 — recording rules

Never put a 72-hour `rate()` in an alert expression.

```yaml
- record: sli:rides_create:bad_ratio:rate1h
  expr: |
    1 - (
      (
        sum(rate(envoy_http_request_duration_seconds_bucket{
              route="POST /v1/rides", le="0.8", status_class!~"5.."}[1h]))
      )
      /
      sum(rate(envoy_http_requests_total{
              route="POST /v1/rides", synthetic!="true", code!~"4(00|22)"}[1h]))
    )
# repeated for 5m, 30m, 2h, 6h, 24h, 72h
```

### 4.6 Step 6 — the alerts

```yaml
# PAGE — fast burn: 2% of the 28-day budget in one hour.
- alert: RidesCreateBudgetFastBurn
  expr: |
    sli:rides_create:bad_ratio:rate1h > (14.4 * 0.001)
      and
    sli:rides_create:bad_ratio:rate5m > (14.4 * 0.001)
  labels: { severity: page, slo: rides_create, team: rides }
  annotations:
    summary: "Ride creation burning error budget 14.4x (2% of the month in 1h)"
    impact:  "Riders are failing to request rides or waiting over 800 ms."
    runbook: "https://runbooks.internal/slo/rides_create#fast-burn"
    dashboard: "https://grafana.internal/d/rides-slo"

# PAGE — slower but substantial: 5% in six hours.
- alert: RidesCreateBudgetSlowBurn
  expr: |
    sli:rides_create:bad_ratio:rate6h  > (6 * 0.001)
      and
    sli:rides_create:bad_ratio:rate30m > (6 * 0.001)
  labels: { severity: page, slo: rides_create, team: rides }
  annotations: { runbook: "https://runbooks.internal/slo/rides_create#slow-burn" }

# TICKET — 10% in a day.
- alert: RidesCreateBudgetDrip
  expr: |
    sli:rides_create:bad_ratio:rate24h > (3 * 0.001)
      and
    sli:rides_create:bad_ratio:rate2h  > (3 * 0.001)
  labels: { severity: ticket, slo: rides_create, team: rides }

# TICKET — chronic: at nominal burn we exhaust exactly at window end.
- alert: RidesCreateBudgetChronic
  expr: |
    sli:rides_create:bad_ratio:rate72h > (1 * 0.001)
      and
    sli:rides_create:bad_ratio:rate6h  > (1 * 0.001)
  labels: { severity: ticket, slo: rides_create, team: rides }

# Suppress the quieter rules while the loud one is firing.
inhibit_rules:
  - source_matchers: [ severity="page",   slo="rides_create" ]
    target_matchers: [ severity="ticket", slo="rides_create" ]
    equal: [ slo ]
```

### 4.7 Step 7 — what happens to the CPU alert

It is **not deleted**. It is demoted and repurposed:

- A prominent panel on the service dashboard, next to the SLI panel and the deploy markers.
- A **ticket**-severity rule at a genuinely abnormal level with a long duration
  (`> 95% for 30m`), because sustained near-total saturation is worth a human look during working hours.
- Referenced from the runbook as **hypothesis #2** ("check CPU saturation and thread-pool queueing —
  historically the cause of ~4 ride-creation latency incidents").

That last line is the point. The knowledge encoded in the old alert survives; only the interrupt is gone.

### 4.8 The result

| Metric | Before (90 d) | After (next 90 d) |
|--------|---------------|-------------------|
| Pages from this rule family | 62 | 7 |
| Night pages (22:00–08:00) | 21 | 2 |
| Actionable | 4 (6.5%) | 6 of 7 (86%) |
| Real incidents caught | 4 | 6 — including two the CPU alert missed entirely |
| Median MTTA | 11 min | 4 min |
| Runbook linked | No | Yes |

The two extra incidents matter more than the noise reduction: a dependency timeout regression and a
certificate rotation failure, neither of which touched CPU at all. Symptom-based alerting catches failure
modes you did not enumerate — that is its whole advantage, and it is the sentence to say out loud in an
interview.

---

## 5 · Alert noise reduction as a measurable programme

This is the Staff-level version of the topic: not "we cleaned up some alerts" but a programme with a
baseline, a method, a governance mechanism, and a published result.

### 5.1 Build the inventory first

You cannot manage what you have not enumerated. Extract from the alert manager and the paging tool:

| Column | Source | Why |
|--------|--------|-----|
| Alert name | Rule definition | Identity |
| Owning team | Label — and if missing, that is finding #1 | Nothing improves without an owner |
| Severity | Label | Page / ticket split |
| Fires (90 d) | Paging tool history | Volume ranking |
| Night fires | Paging tool history | Human cost |
| Median duration | Paging tool history | Short duration ⇒ flapping/self-resolving |
| Acknowledged then no action | Incident records / survey | Actionability proxy |
| Linked to an incident | Incident tracker | The real precision numerator |
| Runbook link present | Annotations | Compliance |
| Tied to an SLO | Labels | Symptom vs cause |

The consistent finding: **a small number of alerts produce most of the pages.** Typically the top five to
ten rules account for the large majority of the volume. Fix those and you have most of the win in a week;
the long tail of rules that fired twice in a year is a different, lower-priority problem.

### 5.2 Baseline metrics — publish these before you change anything

| Metric | Definition |
|--------|-----------|
| Pages per rotation-week | Total page-severity notifications delivered to the primary |
| Night pages per rotation-week | Delivered 22:00–08:00 in the responder's local time |
| Percentage actionable | Pages that led to a human change of state, over total pages |
| Percentage self-resolving | Resolved with no action within 15 minutes |
| Top 5 alerts as a share of total volume | Concentration |
| MTTA (median) | Notification to acknowledgement |
| Runbook coverage | Share of page-severity alerts with a runbook link |
| SLO coverage | Share of page-severity alerts derived from an SLO burn rate |

Publishing the baseline is half the work. Most teams have never seen these numbers, and "we get 41 pages a
week, 68% of which resolve themselves" is an argument that does not need making.

### 5.3 The per-alert decision tree

For each alert, in descending order of volume:

```
Does a user notice when this fires?
├── No  → Is it a certain-future-symptom with lead time?   (§1.1)
│         ├── Yes → TICKET
│         └── No  → DELETE   (keep as a dashboard panel if it aids diagnosis)
└── Yes → Is it the same underlying condition as another firing alert?
          ├── Yes → group / inhibit; keep one page
          └── No  → Is it urgent (harm from a 4-hour delay)?
                    ├── No  → TICKET
                    └── Yes → Is it flapping?
                              ├── Yes → fix hysteresis: raise threshold, add `for:`,
                              │          widen the window, or fix the underlying flap
                              └── No  → PAGE — and it must have a runbook and an owner
```

### 5.4 The structural techniques

| Technique | What it fixes | Notes |
|-----------|--------------|-------|
| **Grouping** | 300 notifications for one condition | Group by cluster/service/alertname; one notification with a count |
| **Inhibition** | Downstream alerts during an upstream outage | If the shared database is down, suppress the 40 services alerting that the database is down |
| **Dependency suppression** | Same, generalised | Requires a service dependency graph — worth building |
| **`for:` duration** | Transient spikes | The cheapest single fix; most flapping alerts need `for: 10m` not `for: 0` |
| **Hysteresis / different fire and clear thresholds** | Oscillation around a boundary | Fire at 95%, clear at 85% |
| **Multi-window (burn rate)** | Precision and reset time simultaneously | See §3 |
| **Minimum-event guards** | Low-traffic ratio noise | `and sum(rate(...)) > 0.1` |
| **Maintenance windows / deploy silences** | Alerts caused by your own planned action | Must expire automatically; see the silence rule below |
| **Deduplication keys** | Repeated notifications for one incident | Group by a stable key, not by timestamp |

**The silence rule**: every silence has an owner, a linked reason, and a maximum expiry of 24 hours. An
open-ended silence is an alert deletion performed by someone who did not want to argue about it, and it is
how outages become invisible. Silences must appear in the shift handoff (`oncall-health.md` §5).

### 5.5 Governance — what stops it regressing

Cleanup without governance regresses within two quarters. Three mechanisms:

1. **Alerts as code, reviewed.** Alert rules live in version control with the service. A page-severity rule
   without `runbook`, `team`, and `severity` annotations fails CI. This is a ten-line lint rule and it is
   the highest-leverage thing in this file.
2. **A monthly automated report** per team: pages, night pages, percentage actionable, top offenders, and
   any alert with zero fires in six months (candidate for deletion) or under 20% actionability (candidate
   for demotion). Sent to the team, not to a manager — the goal is self-service, not surveillance.
3. **A page budget per service**, treated exactly like an error budget: exceed it two quarters running and
   reliability work becomes mandatory in the next planning cycle. See `oncall-health.md` §8.

### 5.6 The before/after table you will be asked for

The behavioural round asks "how did you measure?" verbatim. Have this table:

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Pages / week / rotation | 41 | 9 | −78% |
| Night pages / week | 12 | 1.5 | −87% |
| Actionable | 22% | 81% | +59 pp |
| Self-resolving with no action | 61% | 8% | −53 pp |
| Median MTTA | 9 min | 3 min | −67% |
| Alerts with a runbook | 31% | 100% (enforced in CI) | — |
| Incidents detected by alert before a customer reported | 64% | 91% | +27 pp |
| Alert rules total | 340 | 96 | −72% |

Two rows carry the argument. **Percentage actionable** shows you improved quality, not just volume — you
can always reduce pages by turning alerting off. **Incidents detected before a customer reported** proves
you did not lose coverage while doing it. Without that second row, a good interviewer will ask "so what
did you break?" and you need the answer ready.

Record it in `staff-scope-stories.md` with your own real numbers.

---

## 6 · Runbooks

### 6.1 The contract

Every page-severity alert carries a `runbook` annotation. Enforced in CI. Non-negotiable, because the
alternative is the on-call reading someone else's alert expression at 03:00 to guess what it means.

### 6.2 What a runbook contains

| Section | Content |
|---------|---------|
| **What this means** | One sentence in plain language |
| **User impact** | What is broken for whom, and how severe |
| **Is it real?** | The one dashboard link or query that confirms or refutes it in 30 seconds |
| **First three checks** | Actual copy-pasteable queries and commands, in order, with what each answer implies |
| **Known mitigations** | Concrete commands: the rollback, the feature flag, the scale-up, the failover — with their risks |
| **Escalation** | Who to call, in what order, and at what point |
| **Links** | Dashboard, recent deploys, dependency status, the last three incidents from this alert |

**What a runbook is not**: a design document, a description of the architecture, or a page of prose. It is
a decision aid for a tired person. If it is longer than a screen and a half, the useful part is buried.

### 6.3 Runbook rot and how to measure it

Runbooks decay silently — the commands stop working, the dashboards move, the mitigation stopped applying
three refactors ago. Countermeasures:

- **Confirm-or-edit at incident close.** The responder ticks "runbook was accurate" or edits it. That is a
  30-second obligation attached to a moment when the knowledge is fresh, and it produces a measurable
  accuracy rate.
- **Track last-verified date.** A runbook not confirmed in the last two firings is flagged.
- **Game-day testing.** Deliberately trigger the condition in a staging environment and have someone who
  did not write the runbook follow it. Everything wrong with it surfaces in fifteen minutes.

### 6.4 Runbooks are a queue of automation candidates

If the first three steps of a runbook are always the same three commands, that is a script. If the script
always works, that is auto-remediation — with two guardrails: a **rate limit** (auto-remediate at most N
times per hour, then page, so you cannot mask a worsening problem indefinitely) and a **ticket on every
automated action**, so the underlying problem stays visible instead of being quietly papered over forever.

The progression is: manual page → documented runbook → script referenced by the runbook → automated
remediation with a ticket → the underlying defect fixed and the alert deleted. Every alert should be
somewhere on that path, and an alert that has been at step one for a year is a finding.

---

## 7 · Escalation policy design

### 7.1 The chain

```
Alert fires
  └─ Primary on-call        — notified immediately (push, then SMS, then phone)
       └─ unacked after N   — Secondary on-call
            └─ unacked      — Team lead / manager
                 └─ unacked — Incident commander on duty / central SRE
                      └─ unacked — a phone that is always answered (last resort must be a human)
```

Tune *N* by severity: 5 minutes for SEV1, 15 for SEV2, next business day for SEV3. The last hop must
terminate at a human being; an escalation chain whose final step is an unmonitored mailbox is a chain with
no end.

### 7.2 Design rules

- **Primary and secondary are different people, and the secondary is not a second pager.** The secondary
  exists to catch unacknowledged pages and to be a second pair of hands on a big incident — not to receive
  every notification, which just doubles the fatigue.
- **Acknowledgement is not resolution.** Acknowledging means "a human is on it". Track the two separately
  (MTTA and MTTR); conflating them hides the case where pages are acked instantly by reflex and then
  nothing happens.
- **Test the chain quarterly.** Send a deliberate test page at a random hour and measure whether it
  reached someone and how fast. Escalation policies rot: people leave, phone numbers change, an override
  gets set and never removed. You do not want to discover that during a SEV1.
- **Route by service, not by person.** The escalation target is a *schedule* attached to a service in a
  service catalogue. Alerts routed to individuals break when that person is on holiday.
- **Cross-team escalation needs a directory.** A service catalogue with owner, tier, SLO, runbook and
  escalation schedule per service. Without it, cross-team escalation is "ask in a channel and hope",
  which at 03:00 does not work.
- **Match the channel to the severity.** Do not page a channel nobody watches; do not phone-call a
  ticket-severity condition. The aggressiveness of the notification should scale with the severity, and
  the recipient should be able to trust that mapping.

### 7.3 Severity mapping

| Severity | Definition | Delivery | Ack SLA | Escalates after |
|----------|-----------|----------|---------|-----------------|
| SEV1 | Major user-facing outage or safety impact | Push + SMS + phone, repeating | 5 min | 5 min |
| SEV2 | Significant degradation, or fast budget burn | Push + SMS | 15 min | 15 min |
| SEV3 | Needs action today, no immediate user harm | Ticket queue + one push during working hours | Same working day | — |
| SEV4 | Needs action eventually | Ticket queue | Sprint | — |

Keep the severity definitions identical to the incident severities in `incident-response.md` §2. Two
different severity scales in one organisation is a reliable source of confusion during exactly the moments
you cannot afford it.

---

## 8 · Anti-patterns

| Anti-pattern | Consequence | Fix |
|--------------|-------------|-----|
| Paging on CPU / memory / disk utilisation | Noise, and it misses real failures | Page on SLO burn; keep resources on dashboards |
| Alert with no runbook | 20 extra minutes of MTTR, every time | Enforce in CI |
| Alert with no owner | Pages whoever is nearest; nobody fixes it | Ownership label required; unowned alerts get deleted |
| Alerting from log queries at scale | Slow, expensive, breaks on format changes | Emit a metric; alert on the metric |
| A Slack channel of alerts | Read by nobody, creates false confidence | Ticket with an owner, or delete |
| Indefinite silences | Invisible outages | Max 24 h, owner, linked reason, appears in handoff |
| Static thresholds on a metric with strong seasonality | Fires every Monday morning | Ratio-based SLIs, or compare against the same time last week |
| One alert per instance | 300 notifications for one condition | Aggregate first, then alert; group notifications |
| Duplicating alerts across two systems | Double pages, disagreement about state | One source of truth for paging |
| Severity chosen by the alert's author, by feel | Everything becomes SEV1 | Severity derived from budget burn |
| Adding an alert as a postmortem action item, reflexively | The inventory grows every incident, forever | An action item that adds a page must say which one it replaces |

That last row is worth dwelling on. "Add monitoring for X" is the most common postmortem action item in
the world and it is how a 340-rule inventory happens. The discipline: a new page-severity alert must
identify the SLO it protects, or the alert it replaces.

---

## Interview questions

**1. What makes a good page?**
It must be actionable, urgent, novel, and about user-visible harm — plus owned by a named team and linked
to a runbook. The practical test I use is: if this fires at 3 a.m. and I do nothing until morning, is a
user meaningfully worse off? If no, it is a ticket. If there is nothing the recipient can do, it is not a
page regardless of how bad the condition is. Everything that fails those tests should be a ticket, a
dashboard panel, or deleted.

**2. Symptom-based or cause-based alerting — why?**
Symptom-based for paging, cause-based for diagnosis. The scaling argument is decisive: symptom alerts
scale with the number of user journeys, which is small, and they catch failure modes nobody enumerated,
because any cause that hurts users produces the symptom. Cause-based alerts scale with the number of
components, produce constant false positives, and still miss the novel failure where every resource metric
is green and the service is down. The exception is a certain future symptom with long lead time —
certificate expiry, disk filling, quota exhaustion — where you genuinely need the warning.

**3. Walk me through converting a noisy CPU alert into something useful. [Reported at Lyft — adjacent to the "how did you measure?" probe]**
First I pull the firing history: how many times in 90 days, how many at night, how many self-resolved,
how many correlated with real user impact. Say 62 fires, 4 real — 6.5% precision. Then I define what the
user actually does, write an SLI as the ratio of requests that succeeded within a latency threshold,
measure current performance, set an SLO just below it, and replace the CPU rule with multi-window
burn-rate alerts. Crucially I do not delete the CPU signal — it becomes a dashboard panel and hypothesis
number two in the runbook, plus a ticket-level rule at a genuinely abnormal threshold. Then I measure
again, and I report both the noise reduction and the detection coverage, because reducing pages is trivial
if you are allowed to lose coverage.

**4. How do you run alert noise reduction as a programme rather than a cleanup?**
Inventory, baseline, method, governance, published result. Inventory every rule with its owner, severity,
90-day fire count, night fires, actionability and runbook status. Baseline the team metrics — pages per
week, percentage actionable, MTTA — and publish them before changing anything. Work top-down by volume,
because a handful of rules is usually most of the pages. Then governance so it does not regress: alerts as
code with a CI check that page-severity rules have an owner and a runbook, a monthly automated report per
team, and a page budget per service that triggers mandatory reliability work when exceeded twice.

**5. How do you show that reducing alerts did not reduce coverage?**
Track detection provenance: the share of incidents that were detected by an alert before a customer or
another team reported them. If pages drop 78% and that number goes up, you removed noise. If it goes down,
you removed signal. I would also track incidents with no corresponding alert at all as a separate count.
Noise reduction that is not paired with a coverage metric is unfalsifiable, and an interviewer should
push on exactly that.

**6. Forty services page simultaneously because a shared database is down. What is wrong and how do you fix it?**
Two things. Structurally, those are cause-based alerts on a dependency rather than symptom alerts on each
service's own SLI — but even with symptom alerts, forty journeys really are broken, so the fix is
notification-level, not rule-level. I would add inhibition rules driven by a service dependency graph so
an upstream alert suppresses its downstream consumers, group notifications by incident rather than by
service, and make sure the database has its own high-severity alert that is the one that actually pages.
The on-call should receive one page that says "shared database down, 40 dependent services affected".

**7. Where do resource-utilisation metrics belong if not on pagers?**
On dashboards, next to the SLI panel, and in runbooks as named hypotheses. They are how you go from "ride
creation is failing" to "the connection pool is saturated" in three minutes. The framing I use is RED for
alerting — rate, errors, duration, which are user-facing — and USE for diagnosis — utilisation,
saturation, errors per resource. Demoting a saturation alert from a page does not discard the knowledge in
it; it moves that knowledge to the runbook where it is actually useful.

**8. Should every alert have a runbook, and how do you stop runbooks going stale?**
Every page-severity alert, yes, enforced by a CI check on the annotation rather than by good intentions.
For staleness: the responder confirms or edits the runbook at incident close, which is a 30-second
obligation at the moment the knowledge is freshest and gives you a measurable accuracy rate; flag any
runbook not confirmed in its last two firings; and periodically have someone who did not write it follow
it in a game day. I also treat runbooks as an automation queue — if the first three steps are always the
same commands, that is a script, and if the script always works, that is auto-remediation with a rate
limit and a ticket so the underlying problem stays visible.

**9. How do you design an escalation policy?**
Route to a schedule attached to a service, never to an individual. Primary, then secondary after an
unacknowledged interval tuned by severity — five minutes for SEV1 — then lead, then a final hop that
always terminates at a human. The secondary catches unacknowledged pages and is a second pair of hands,
not a duplicate pager. Then two things people skip: a service catalogue so cross-team escalation is
lookup rather than shouting in a channel, and a quarterly test page at a random hour to prove the chain
still works, because escalation policies rot silently as people leave and overrides are forgotten.

**10. A postmortem action item says "add monitoring so we catch this sooner". What is your response?**
Push back and make it specific, because that phrasing is how a 340-rule alert inventory happens. I would
ask which SLI would have moved during this incident, and whether the existing burn-rate alerts would have
caught it more slowly or not at all. Usually the answer is that the SLO alert *would* have fired but ten
minutes later than a targeted rule, in which case the honest action item is about detection latency, not a
new page. If a new page-severity alert is genuinely required, it has to name its owner, its runbook, and
either the SLO it protects or the alert it replaces.
