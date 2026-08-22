# Observability and On-Call

> **Priority:** Required
> **Est. time:** 10 min
> **Track:** Both
> **HelloInterview:** none

The job posting carries a responsibility bullet on establishing best practices for deployment, alerting,
and on-call health for an organisation — a system-design responsibility, not a "I carried a pager"
anecdote. This section covers the practice (metrics/logs/traces, alerting, debugging, incidents,
instrumentation) and the Staff-scope framing of it (on-call as a system with its own SLO, and turning
that experience into behavioural stories with real numbers attached).

---

## Read in this order

| # | File | Priority | Est. time | Description |
|---|------|----------|-----------|-------------|
| 1 | [slos-and-error-budgets.md](slos-and-error-budgets.md) | Required | 75 min | SLI/SLO/SLA precisely defined, choosing good SLIs, what a number of nines actually buys, the error budget as a decision tool, multi-window multi-burn-rate alerting, negotiating an SLO with product |
| 2 | [metrics-logs-traces.md](metrics-logs-traces.md) | Required | 60 min | The three signals reframed as encodings of the same events, not a "pillars" checklist — which one answers which question, cardinality as the failure mode that kills metrics systems, sampling, OpenTelemetry, a cost model |
| 3 | [alert-design.md](alert-design.md) | Required | 60 min | Symptom-based vs. cause-based alerting, the properties of a good page, burn-rate alerting, a worked noisy-CPU-alert-to-SLO-burn-rate rewrite, alert-noise reduction as a measurable programme, runbooks, escalation policy |
| 4 | [debugging-distributed-systems.md](debugging-distributed-systems.md) | Recommended | 60 min | A method, not a checklist: correlating deploys with regressions, using traces to find the slow hop, tail latency and coordinated omission, thundering herds and metastable failures |
| 5 | [incident-response.md](incident-response.md) | Recommended | 50 min | Roles, severity definitions, the lifecycle, mitigation vs. resolution, communication, blameless postmortems, real action items, error-budget-driven freeze policy |
| 6 | [oncall-health.md](oncall-health.md) | Required | 75 min | The Staff-scope file of the section: on-call as a system with its own SLO, the metric set, rotation design, toil reduction, handoff quality, follow-the-sun across time zones, compensation, a 90-day plan for taking this on |
| 7 | [instrumenting-python-services.md](instrumenting-python-services.md) | Recommended | 60 min | Practical Python instrumentation ending in what to measure in an LLM-agent pipeline; doubles as Python practice — the SDK-shaped code is worth typing out |
| 8 | [staff-scope-stories.md](staff-scope-stories.md) | Required | 25 min | Turns this section's practice into behavioural-round material: the five numbers to have ready (alert-noise reduction, MTTR, pages/week, deployment frequency, change failure rate), a mining prompt per sibling file, and a worked weak-to-strong story rewrite |

---

## If you only have an hour

Read [slos-and-error-budgets.md](slos-and-error-budgets.md) and [oncall-health.md](oncall-health.md).
Together they are the two files most likely to produce a design-round or behavioural-round answer that
reads as "has run this," rather than "has read about this" — an SLO you can defend the choice of, and an
on-call system you can describe the shape of, not just a rotation you were in.

## How this section connects to the rest of the program

[design-round-protocol.md](../15-system-design/design-round-protocol.md)'s failure-modes phase and every
worked design's own failure-mode table draw directly on this section's vocabulary — burn rate, MTTR,
blast radius, runbooks. [staff-scope-stories.md](staff-scope-stories.md) is this section's bridge into
[22-behavioral-and-staff-scope](../22-behavioral-and-staff-scope/README.md), specifically **Slot 9** of
[story-bank.md](../22-behavioral-and-staff-scope/story-bank.md) — read the two together once the numbers
are recovered.

## Interview questions

**1. Where should someone with real DevOps experience but no formal observability vocabulary start in
this section?**
[slos-and-error-budgets.md](slos-and-error-budgets.md), because it supplies the vocabulary — SLI, SLO,
error budget, burn rate — that the rest of the section and most of the design rounds' failure-mode
discussions assume. Reading it first turns "I carried a pager" into a system with a defensible target.

**2. What is the difference between an SLI, an SLO, and an SLA?**
An SLI is the measured indicator (e.g. the fraction of requests under 300 ms); an SLO is the internal
target on that indicator (99.9% of requests under 300 ms over 28 days); an SLA is the external, usually
contractual promise, typically set looser than the SLO to leave margin. Confusing the three is a common
and noticeable imprecision.

**3. What are metrics, logs, and traces each actually for?**
Three encodings of the same underlying events, not independent pillars: metrics answer "how much/how
often" cheaply at any cardinality that stays low; logs answer "what exactly happened, in this one case";
traces answer "where did the time go, across services." Picking the wrong one for a question — logs for a
trend, metrics for a single request's story — is the tell that someone has not run this in production.

**4. How would you design an alert so it pages less and means more?**
Alert on symptom, not cause, and on SLO burn rate rather than raw utilisation, so a page means "the error
budget is draining fast enough to matter" rather than "a number crossed an arbitrary line." See the
worked CPU-alert-to-burn-rate rewrite in [alert-design.md §4](alert-design.md).

**5. Walk through your incident-response process.**
Roles assigned before the incident, not during it; a severity definition everyone already agrees on;
mitigation prioritised over root-cause resolution while the incident is live; a blameless postmortem with
action items that are tracked, not aspirational. [incident-response.md](incident-response.md) has the
full lifecycle.

**6. How would you establish on-call best practices across an organisation, not just your own service?**
Treat on-call itself as a system with an SLO — pages/week, actionable-page ratio, MTTR, toil hours — and
run a quarterly review against those numbers the same way a product SLO gets reviewed.
[oncall-health.md §9](oncall-health.md) has a 90-day plan for taking this on as new scope, which is the
shape of a Staff-level answer to this question, not a description of a rotation you were in.

**7. How did you measure the improvement, and how do you know it held?** **[Reported at Lyft]**
Name the instrument before the number — the rotation tool's history, the incident tool's timestamps —
and point to something that shows durability: the practice becoming a template, another team adopting it,
or a metric still holding a quarter later. [staff-scope-stories.md](staff-scope-stories.md) is built
entirely around getting this specific answer ready.
