# Staff-Scope Stories from DevOps and On-Call Work

> **Priority:** Required
> **Est. time:** 25 min
> **Track:** Both
> **HelloInterview:** Behavioral → CARL Framework; The Big Three Questions

**"How did you measure?"** is asked verbatim in a transcribed Lyft behavioural round, immediately after
"what was impact?" This file's only job is making sure the numbers are ready before that question lands,
specifically for the body of work most likely to survive four consecutive probes: alerting, on-call, and
deployment practice.

This file does **not** re-teach story structure or general number-recovery — that is
[carl-and-star.md](../22-behavioral-and-staff-scope/carl-and-star.md) and
[metrics-for-stories.md](../22-behavioral-and-staff-scope/metrics-for-stories.md). It feeds directly into
**Slot 9 — On-call / reliability improvement** in
[story-bank.md](../22-behavioral-and-staff-scope/story-bank.md), and it uses the five Staff-vs-Senior
dimensions from [senior-vs-staff-framing.md §2](../22-behavioral-and-staff-scope/senior-vs-staff-framing.md)
without repeating them — go read that table first if it is not already familiar.

---

## 1 · The five numbers to have ready

| Number | What it is | Why it is a Staff signal, specifically |
|--------|------------|-------------------------------------------|
| **Alert-noise reduction** | Actionable pages as a percentage of all pages, before and after an audit | Directly answers "did the org page less for the same reliability" — see [alert-design.md §5](alert-design.md) |
| **MTTR change** | Detect-to-resolve time, before and after a change to tooling, runbooks, or rotation | Shows the change held under real incidents, not just in a retro | 
| **Pages/week, before and after** | Raw on-call load per rotation | The rawest, most checkable number you own — see [oncall-health.md §2](oncall-health.md) |
| **Deployment frequency** | Deploys per week/day, before and after a pipeline change | A DORA metric almost always reconstructable from CI history alone |
| **Change failure rate** | Percentage of deploys causing a rollback or an incident | The number that proves faster deploys did not trade away safety — pair it with frequency, never quote one without the other |

Reconstruction technique is the same for all five: bound it, anchor it on an artefact (a dashboard, a
postmortem, CI history, the rotation tool), or count what never decays — see
[metrics-for-stories.md §4](../22-behavioral-and-staff-scope/metrics-for-stories.md) for the full
technique set. Do not re-derive it here; just run it against these five specifically before the loop.

---

## 2 · Mining prompts, one per sibling file

Each file in this section maps to a question worth asking yourself now, while the numbers are still
recoverable:

| Source | Prompt |
|--------|--------|
| [alert-design.md](alert-design.md) | Did you ever audit a noisy alert set? What fraction were actionable before, what fraction after, and what did you do with the rules that did not survive the audit? |
| [oncall-health.md](oncall-health.md) | What was pages/week for your rotation at its worst, and what changed it? Did you touch rotation design, follow-the-sun coverage, or compensation — any of which is a bigger story than "I fixed alerts" |
| [slos-and-error-budgets.md](slos-and-error-budgets.md) | Did you ever set or renegotiate an SLO with product? That is a story where you were the person setting the target, not just meeting it — a specifically Staff-shaped claim |
| [incident-response.md](incident-response.md) | Pick one incident you ran or contributed a fix to. What was MTTR for that class of incident before and after your change, and how many incidents of that class happened afterward? |
| [debugging-distributed-systems.md](debugging-distributed-systems.md) | What is the hardest bug you found using traces or correlation rather than guessing? That is a Mechanism layer for almost any story — see [carl-and-star.md §4](../22-behavioral-and-staff-scope/carl-and-star.md) |
| [metrics-logs-traces.md](metrics-logs-traces.md) | Did you ever fix a cardinality explosion or a logging-cost problem? Cost-of-observability numbers are memorable and checkable against a cloud bill |
| [instrumenting-python-services.md](instrumenting-python-services.md) | Did you introduce instrumentation somewhere that had none? "Zero visibility to full RED dashboards" is a clean before/after even without a precise number |

---

## 3 · The rewrite drill, worked

**Weak — reads Senior:**

> "I noticed our on-call rotation was getting a lot of pages, so I looked into the alerts and cleaned some
> up. Things got quieter after that."

No number, no instrument, one person, no organisational consequence, no cost paid. Every tell from
[senior-vs-staff-framing.md §4](../22-behavioral-and-staff-scope/senior-vs-staff-framing.md) is present.

**Strong — same underlying work, reframed:**

> "I was on-call for [service] at about 35 pages a week, most of them not actionable. I audited every
> rule against one question — would a human do something different because of this page — cut or
> demoted the ones that failed it, and rewrote the survivors against burn rate instead of raw
> utilisation. Pages dropped to about 8 a week, a roughly 77% reduction, and MTTR on the ones that
> remained fell too, because the signal-to-noise on a page finally matched what a responder needed. I
> wrote the audit method up as a template, and two other teams adopted it the following quarter without
> me driving it. What I do differently now is write every new alert against its burn-rate threshold
> before it ships, not after the first bad week."

Same work. What changed: a primary number with a before/after and an instrument (the audit), a second
number that shows the fix held under real conditions (MTTR), blast radius widened from one rotation to
two other teams, durability (the method outlived the initial push), and a Learning that is a standing
practice, not a platitude.

---

## 4 · Quick instrument reference for these five numbers

| Number | Typical instrument |
|--------|----------------------|
| Alert-noise reduction | The alert-rule audit itself — a before/after count of rules and their actionable-page ratio |
| MTTR | Incident-management tool timestamps (detect, ack, mitigate, resolve) |
| Pages/week | PagerDuty/Opsgenie (or equivalent) rotation history |
| Deployment frequency | CI/CD pipeline history — count of production deploys over a fixed window |
| Change failure rate | Postmortems or incident tags cross-referenced against the same deploy count |

State the instrument before the number, every time — see
[metrics-for-stories.md §1](../22-behavioral-and-staff-scope/metrics-for-stories.md) for why that
ordering is the one that scores.

---

## Interview questions

**1. How did you measure?** **[Reported at Lyft]**
Instrument first, number second, confidence third. For an on-call story: "pages/week from the rotation
tool's history — about 35 before, about 8 after the audit, and I'm confident in that ratio even if the
exact endpoints are from memory."

**2. What was impact?** **[Reported at Lyft]**
One primary number with a before, an after, and a time window — pages/week or MTTR, not both at once.
Let the follow-up ask for the second number rather than leading with a list.

**3. Tell me about an on-call or reliability improvement you made.**
This is Slot 9. Lead with the number, not the activity: state the pages/week or MTTR change before
describing what you actually did to cause it.

**4. Did deployment frequency and change failure rate move together or trade off?**
The honest, Staff-shaped answer names both numbers and states the relationship plainly — either they
improved together (the strongest version, meaning the pipeline change was a genuine win) or frequency
rose while failure rate briefly rose too, with what you did about the second half.

**5. How do you know the alert-noise reduction actually held, rather than regressing after you left?**
Durability, not a one-time fix: point to the audit becoming a template, a review step in a runbook, or
another team adopting it — anything that shows the practice outlived the initial push, not just the
count on the day you measured it.

**6. What would you check if you didn't have the exact number in front of you?**
Name the artefact — the rotation tool's history, the incident tool's timestamps, the CI pipeline log —
and give a bounded range from memory rather than refusing to estimate or inventing false precision.
