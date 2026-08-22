# Metrics for Stories — Recovering Numbers You Did Not Record

> **Priority:** Required
> **Est. time:** 45 min
> **Track:** Both
> **HelloInterview:** Behavioral — CARL Framework

**"How did you measure?"** is asked verbatim in a transcribed Lyft behavioural round, immediately
after "what was impact?". It is not a formality. It separates people who were close to the outcome
from people who were close to the code.

Short file. The work is not reading it, it is spending two hours reconstructing your numbers.

---

## 1 · What the question is testing

| Reading | Signal |
|---------|--------|
| "Do you know the number?" | Basic. Half of candidates fail here. |
| "Do you know the **instrument**?" | The real probe. A number without a source is a number you were told, not one you owned. |
| "Do you know its **limits**?" | Staff signal. Sampling windows, confounders, what the metric does not capture. |
| "Did you set the measurement up **before** the change?" | Strongest signal available. Baseline-then-change is engineering; after-the-fact justification is storytelling. |

Answer in that order: **instrument → number → confidence.** "It was on the service's Grafana board
off Prometheus; p99 went from about 400 ms to about 180 ms over the two weeks after cutover; the
before-figure is solid, the after-figure I'm quoting from memory."

---

## 2 · Metric families, and where each hides

You almost certainly have more numbers than you think. They are in artefacts, not in your memory.

| Family | Typical metrics | Where to find it retroactively |
|--------|-----------------|-------------------------------|
| **Latency** | p50/p95/p99, tail behaviour under load | Old dashboards, SLO docs, load-test reports, performance tickets, the alert thresholds you set |
| **Throughput** | requests/sec, events/sec, messages/day, peak vs mean | Kafka topic sizing decisions, partition counts, autoscaling configs, capacity-planning docs |
| **Cost** | monthly cloud spend, cost per request, instance counts | Terraform state and instance types, reserved-instance discussions, any "we need to cut spend" thread |
| **Deployment** | deploys per week, lead time, change-failure rate, rollback count | CI history, release notes, changelog, the pipeline config you wrote |
| **Reliability** | incidents/quarter, MTTR, pages/week, actionable-page ratio, uptime | Postmortems, on-call handover notes, alert rules, SLA/SLO documents |
| **Team velocity** | cycle time, review turnaround, onboarding time, flake rate | Sprint boards, retro notes, CI flake reports, onboarding docs |
| **Adoption** | teams on the standard, services migrated, users of the tool | Repo counts, service registry, the migration tracker spreadsheet |
| **Business** | revenue, conversion, applications processed, churn, compliance findings | Product review decks, audit reports, the reason the project was funded |

### 2.1 The funding question

If you cannot find a number, ask: **why did someone pay for this work?** Every funded project had a
justification, and that justification contained a number — a cost, a risk, a deadline, a competitor,
a regulator. That number is your Results line even if you never measured the outcome.

---

## 3 · Mining your own background

Applied to the four bodies of work you actually have. These are prompts, not answers.

### 3.1 Event-driven mortgage platform

Regulated, transactional, high-value-per-unit domain — the richest source of business numbers you own.

- **Volume**: applications or originations per month; peak day; total loan value passing through.
- **Latency that mattered to a human**: time from application submission to decision; how much of it
  was your system versus waiting on people.
- **Correctness**: reconciliation discrepancies per month, before and after event sourcing. Event
  sourcing exists partly to make this number zero — if it went to zero, that is your headline.
- **Replay and recovery**: how long a full projection rebuild took; how often you had to do one; what
  it would have cost without the event log.
- **Compliance**: audit findings, evidence-production time, retention requirements met. "The auditors
  could answer their own questions from the event log" is a compliance outcome with organisational
  reach.
- **Cost of a defect**: in this domain a wrong decision has a per-case monetary value. Ask what one
  bad case was worth.

Cross-reference [Event Sourcing](../06-databases-and-distributed-data/Event-Sourcing-Guide.md) and
[Event Sourcing, CQRS & Sagas](../15-system-design/event_sourcing_cqrs_sagas_guide.md) when the
follow-up goes technical.

### 3.2 AWS / Terraform DevOps

The easiest place to find hard numbers, because infrastructure work is measured by definition.

- **Before/after of manual → codified**: environment provisioning time (days to minutes is the
  classic, and it is checkable), number of environments, drift incidents.
- **Deployment frequency and lead time**: the two DORA metrics you can usually reconstruct from CI
  history alone.
- **Cost**: monthly spend before and after right-sizing; percentage saved; what you did with the
  saving.
- **Blast radius of a config error**: how many services shared the module you wrote; that count is
  your adoption metric and your scope metric simultaneously.
- **Toil**: engineer-hours per week spent on environment work before and after.

See [Terraform & AWS](../14-cloud-and-infrastructure/terraform_aws_overview.md).

### 3.3 Scandinavian media microservices

Consumer traffic, so latency and traffic-shape numbers exist and are usually memorable.

- **Traffic**: requests/sec at peak, ratio of peak to trough, the event that caused the peak (a live
  broadcast, a news spike). Peak-to-mean ratio is a strong Staff detail because it implies you did
  capacity planning.
- **Latency**: p99 on the read path; cache hit rate; CDN offload percentage.
- **Service count and coupling**: how many services, how many you owned, how many depended on yours.
- **Availability**: uptime, incidents per quarter, the worst outage and its duration.
- **Content or catalogue scale**: items, users, concurrent streams — whatever the domain unit was.

### 3.4 Current LotusFlare work

Recent, so the numbers are still recoverable — go and get them before you leave.

- **Scale of the platform**: subscribers, transactions, tenants, regions.
- **What your component does per day**: the throughput number for the thing you own.
- **Release cadence and incident load** for your service.
- **Anything you changed**: performance, cost, defect rate, onboarding time for a new tenant.
- **Lua-specific**: if you introduced or standardised anything in a Lua codebase — testing approach,
  module structure, review standard — the adoption count is a metric.

Practical note: recent-employer numbers are the ones an interviewer probes hardest, because they
assume your memory is good. Collect them now rather than reconstructing them under pressure.

---

## 4 · Reconstruction techniques

When the dashboard is gone and the company is behind you.

| Technique | Method | Example phrasing |
|-----------|--------|------------------|
| **Bound it** | Give a range you are confident contains the truth | "Somewhere between 2,000 and 5,000 requests a second at peak — I'd have to check, but that order." |
| **Anchor on an artefact** | Derive from something structural you remember | "We ran 12 instances of it, and we sized those for about 300 rps each, so call it low thousands." |
| **Anchor on a decision** | Recover the number from the threshold that triggered work | "We started the migration because the p99 crossed 500 ms, which was the SLO." |
| **Anchor on money** | Recover from budget conversations | "It was the second-largest line in our AWS bill, around a third of it." |
| **Anchor on people** | Convert time into engineer-hours | "Three people were spending most of a day a week on it — call it 20 hours a week." |
| **Ratio instead of absolute** | Give the change, not the level | "It roughly halved. I'm more confident in the ratio than in either endpoint." |
| **Count the countable** | Some numbers never decay: teams, services, people, repos | "Four teams adopted it; that one I'm sure of." |

Counting things is underrated. Team counts, service counts, adoption counts and incident counts are
exactly the metrics that carry Staff scope, and they are the ones you can still state precisely years
later.

---

## 5 · Stating an estimate honestly

The failure mode is not vagueness. It is **false precision that collapses under a probe**.

### 5.1 The pattern

1. Flag it as an estimate, once, briefly. *"From memory, so treat it as approximate —"*
2. Give the figure with appropriate granularity. Round to the precision you actually have: "about
   400 ms", not "412 ms".
3. Say what you are confident in. *"The direction and the rough magnitude I'm sure of; the exact p99
   I'd want to check."*
4. Name the instrument that produced it.

Do not apologise past step 1. One hedge is candour; three hedges is a lack of ownership.

### 5.2 What not to do

| Anti-pattern | Why it fails |
|--------------|--------------|
| Inventing a precise figure | Follow-up drilling is deep at Lyft; two probes and the arithmetic stops working. |
| "It improved significantly" | Answers nothing and signals distance from the outcome. |
| Percentages with no baseline | "40% faster" is meaningless without the starting point. Always give one endpoint. |
| Quoting a company-level number as yours | "We processed a billion events" when your component saw a fraction. State your component's share. |
| Refusing to estimate | "I don't have numbers" is worse than a bounded range. Engineers estimate; that is part of the job. |

### 5.3 Arithmetic that must survive

If you say 300 rps per instance and 12 instances, the interviewer may say "so 3,600 a second?" —
and your earlier "low thousands" must agree. Before the loop, do the napkin math on each story once,
on paper, and make the numbers consistent with each other. This is the same skill the design rounds
probe with live memory and CPU estimation, so the practice transfers.

---

## 6 · Two-hour recovery exercise

Do this once, before filling [story-bank.md](story-bank.md).

1. For each of the four bodies of work in section 3, write every number you can recall in ten
   minutes, without checking anything. Include ones you are unsure of.
2. Mark each `solid` / `bounded` / `guess`.
3. For the guesses, apply one anchoring technique from section 4 and rewrite as a bounded range.
4. For each story slot, pick **one primary number** — the one you lead with — and two supporting ones.
5. Write the instrument next to each primary number. Any primary number with no instrument gets
   demoted to supporting.
6. Check the arithmetic across numbers within each story.

Output: twelve primary numbers with sources. That is the whole deliverable.

---

## Interview questions

**1. How did you measure?** **[Reported at Lyft]**
Instrument, number, confidence — in that order. "It was a Grafana board on the service's Prometheus
metrics; p99 went from roughly 400 ms to roughly 180 ms in the two weeks after cutover; I'm confident
in the ratio, less so in the exact endpoints."

**2. What was impact?** **[Reported at Lyft]**
One primary number with a before, an after and a time window, then the business consequence in one
clause. Resist listing four metrics — pick the one that mattered and let the follow-up ask for more.

**3. Was that metric the right one to optimise?**
A Staff probe. Name what the metric did not capture and what you watched alongside it as a guardrail —
error rate next to latency, cost next to throughput, review turnaround next to deploy frequency.

**4. How do you know the improvement came from your change?**
Describe the controls: a baseline taken before, a staged rollout, a period with no other releases, or
a comparison service left unchanged. If you had none of those, say so and give the reason you still
believe the attribution.

**5. That number seems high — walk me through it.**
Do the arithmetic out loud from a structural anchor: instances, per-instance capacity, peak factor.
If it does not reconcile, say so and correct yourself. Visible correction is a better signal than a
defended wrong figure.

**6. You said you don't remember exactly — what would you check?**
Name the concrete artefact: the dashboard, the postmortem, the capacity doc, the CI history. Knowing
where the number lives proves you owned it even when the value itself is gone.

**7. What did you measure before you started?**
The strongest version of this whole topic. If you took a baseline, lead with it. If you did not, say
so plainly and describe how you now instrument first — that is a legitimate Learning.
