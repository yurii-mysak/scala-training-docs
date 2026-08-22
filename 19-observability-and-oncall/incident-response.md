# Incident Response

> **Priority:** Recommended
> **Est. time:** 50 min
> **Track:** Both
> **HelloInterview:** none

Incident response is a rehearsed process, not an improvisation. The distinguishing feature of an
organisation that handles incidents well is not that its engineers are smarter under pressure — it is that
the coordination is pre-decided, so the engineers get to spend their attention on the actual problem.

---

## 1 · Roles

Adapted from the Incident Command System. The point of separating roles is that **coordination and
debugging compete for the same attention**, and the person deepest in the debugging is the worst possible
choice to also be answering questions from executives.

| Role | Owns | Does **not** do |
|------|------|-----------------|
| **Incident Commander (IC)** | The response: who is doing what, what we try next, when we escalate, when we declare resolved. The single decision-maker | **Debug.** The moment the IC opens a terminal, the incident has no commander |
| **Operations lead** | Actually making changes: rollbacks, failovers, flags, scaling. The only person touching production | Communicate externally; take direction from anyone but the IC |
| **Communications lead** | Status page, stakeholder updates, executive channel, customer support liaison | Speculate on cause or ETA |
| **Scribe** | The timeline: what was observed, what was tried, what was decided, with timestamps | Anything else — this is a full-time job in a big incident |
| **Subject-matter experts** | Investigating specific hypotheses assigned by the IC | Make production changes without the ops lead |

### 1.1 Scaling the roles to the incident

| Severity | Roles |
|----------|-------|
| SEV3–4 | One person wears all hats. Formality would cost more than it saves |
| SEV2 | IC + ops lead. Scribe if it runs past 30 minutes |
| SEV1 | All roles filled, explicitly, by name, announced in the channel |

### 1.2 The rules that make it work

- **The IC is named out loud and acknowledged.** "I am taking IC" / "acknowledged". Ambiguity about who is
  in charge is the most expensive failure mode in incident response — it produces two people making
  contradictory production changes.
- **The IC is not the most senior person by default.** It is whoever is best placed to coordinate. A very
  senior engineer is often more valuable as an SME, and appointing them IC by reflex wastes them.
- **Handover is explicit.** "I am handing IC to Y" / "I have IC". Never implicit, never assumed — this
  matters enormously across a follow-the-sun handoff (see `oncall-health.md` §6.5).
- **One production change at a time, announced before it happens.** "I am rolling back the pricing service
  to a91f3c2 now" — because two simultaneous changes make the result uninterpretable, and if things
  improve you will not know which one did it.
- **Anyone can declare an incident. Only the IC declares it over.**

---

## 2 · Severity definitions

Severity must be defined by **user impact**, not by how alarming the internal symptom looks. Otherwise
everything becomes a SEV1 within six months and the scale stops carrying information.

| Sev | Definition | Examples | Response | Comms cadence | Postmortem |
|-----|-----------|----------|----------|---------------|------------|
| **SEV1** | Core journey broken for a large share of users; data loss; safety or security impact | Rides cannot be requested; payments double-charging; a safety-critical flow down; a data breach | Page immediately, all roles, exec notified | Every 30 min, even with no news | **Required**, within 5 working days |
| **SEV2** | Significant degradation, or a core journey broken for a subset; fast error-budget burn | One region down; p99 tripled; a specialist agent failing for one segment | Page, IC + ops lead | Every 60 min | Required |
| **SEV3** | Minor or contained impact; a workaround exists | A non-critical feature broken; elevated but sub-budget error rate | Ticket, same working day | On resolution | Optional — required if it repeats |
| **SEV4** | No current user impact; a latent risk | Redundancy lost but service healthy; a near miss | Ticket | None | Optional |

Two design points that keep the scale honest:

- **Declare early and downgrade freely.** Declaring a SEV2 that turns out to be a SEV3 costs a few minutes
  of a few people's time. Under-declaring a SEV1 costs an hour of user impact. Make downgrading explicitly
  blameless and routine, or people will hesitate to declare at all.
- **Include a "safety" clause.** For a team in Safety & Customer Care, an incident affecting a
  safety-reporting path is a SEV1 regardless of how few users it touches. Impact severity is not always
  proportional to user count, and the severity table must say so explicitly.

---

## 3 · The lifecycle

```
DETECT ──▶ TRIAGE ──▶ DECLARE ──▶ ASSEMBLE ──▶ MITIGATE ──▶ VERIFY ──▶ RESOLVE ──▶ REVIEW
   │          │          │            │            │           │          │           │
 alert /   is it real? severity   IC named,   stop the    confirm    root cause  postmortem,
 report    what is    assigned,   roles       user pain   with the   addressed,  action items
           the        channel     filled                 SLI, not    monitoring  tracked to
           impact?    opened                             a hunch     restored    completion
```

The two transitions people get wrong:

- **DETECT → DECLARE takes too long.** Somebody investigates alone for 40 minutes before telling anyone.
  Lower the bar to declare: declaring is cheap, and a declared SEV3 that gets downgraded costs nothing.
- **MITIGATE → VERIFY is skipped.** "I rolled it back, it should be fine" is not verification. Verify
  against the SLI, on the dashboard, for a sustained period. Incidents that get declared over and then
  re-open are almost always a skipped verify step.

---

## 4 · Mitigation vs resolution

The single most important operational distinction in this file.

| | Mitigation | Resolution |
|---|-----------|-----------|
| Goal | Stop the user pain | Ensure it cannot happen again |
| Timeframe | Minutes | Days to weeks |
| Examples | Roll back, disable a feature flag, fail over, shed load, scale up, route around a bad instance, serve stale from cache | Fix the bug, add the test, redesign the retry policy, add capacity headroom |
| Requires understanding the cause? | **No** | Yes |
| Who decides | IC, during the incident | Team, afterwards |

**Mitigate first. Understand later.** The instinct to find the root cause before acting is the most common
and most expensive error in incident response — every minute spent understanding is a minute of user
impact, and you can understand it just as well tomorrow from the logs.

The corollary: **your mitigations must be fast, rehearsed and safe to use without understanding.**

| Mitigation | Should take | Requires |
|-----------|-------------|----------|
| Roll back a deploy | < 5 min | One-command rollback, tested regularly, no manual steps |
| Disable a feature | < 1 min | Feature flags with a kill switch, and flags actually wired to the risky paths |
| Fail over a region/AZ | < 10 min | Rehearsed. An unrehearsed failover during an incident is a second incident |
| Shed load | < 2 min | Rate limiting configurable at runtime — at Lyft this exists at both the edge and the service mesh |
| Scale up | < 5 min | Headroom in quota, and a service that actually scales horizontally |

Rehearsal matters more than existence. A rollback procedure nobody has run in six months will fail on
its first use, at the worst possible moment.

### 4.1 Preserve evidence before you destroy it

The tension: mitigation often destroys the evidence. Restarting the pod fixes it *and* deletes the state
that would have explained it, which guarantees a repeat.

Before the bounce, if it costs less than a minute: capture a heap dump or goroutine/thread dump, snapshot
`/proc` and connection state, copy the logs off the node, note the exact instance IDs and the current
deploy SHA, and screenshot the dashboard state. Better still, script it — a single `capture-diagnostics`
command that the runbook invokes before the mitigation step. That is a small piece of tooling with an
outsized effect on how many incidents you actually learn from.

---

## 5 · Communication

### 5.1 Cadence

Fixed intervals, **whether or not there is news**. "No update, still investigating, next update in 30
minutes" is a valuable message: it tells everyone the response is alive and prevents the stream of "any
news?" messages that consume the IC's attention.

| Audience | Channel | Cadence | Content |
|----------|---------|---------|---------|
| Responders | Incident channel | Continuous | Everything; this is the working surface |
| Internal stakeholders | Status channel | 30 min (SEV1) / 60 min (SEV2) | Impact, what is being done, next update time |
| Support / customer-facing teams | Their channel + the status page | On declare, on material change, on resolve | What to tell customers, and what *not* to say |
| Executives | A dedicated summary thread | 30–60 min | Impact, ETA confidence, decisions needed from them, nothing technical |
| Customers | Public status page | On declare (if externally visible), on material change, on resolve | Plain language, no internal names, no blame, no speculation |

### 5.2 The update template

```
[SEV2] Ride creation degraded — UPDATE 3 — 14:52 UTC

IMPACT     ~8% of ride requests failing in eu-central-1 since 14:05.
           Riders see "try again". No data loss. No other regions affected.
STATUS     Mitigating. Rolling back pricing-service to a91f3c2, ~10 min to complete.
CAUSE      Under investigation — correlates with the 14:03 pricing-service deploy.
NEXT       Update at 15:22 UTC or sooner if the situation changes.
IC         @yurii     COMMS @maria
```

Discipline points: state impact in **user terms** first, never speculate about cause in an external
update, always give the next update time, and never give an ETA you are not confident in — "we expect
recovery within 15 minutes of the rollback completing" is fine; "we should be back up soon" is not.

### 5.3 One voice

During an incident, exactly one person communicates externally. Multiple people posting updates produces
contradictory information, and contradictory information is what turns an outage into a trust problem.
Everyone else, including senior leaders, routes through the comms lead.

---

## 6 · Blameless postmortems

### 6.1 What blameless actually means

**It does not mean**: nobody is accountable, or that we do not discuss what people did.

**It means**: we assume everyone acted reasonably given the information, incentives, tooling and time
pressure they had, and we therefore ask *what made this action reasonable?* rather than *why did you do
that?* The engineer who ran the migration on the wrong cluster is not the cause; the tooling that made the
right cluster and the wrong cluster indistinguishable is.

The practical argument, which persuades sceptical managers: blame produces hiding, and hiding produces
repeat incidents. You are not being kind, you are protecting your information supply. The moment an
engineer believes a postmortem could damage them, you stop learning about near misses — and near misses
are the cheapest information you will ever get.

Accountability survives: people are accountable for *fixing* things, for writing the postmortem, and for
completing the action items. Nobody is punished for *causing* an incident.

### 6.2 Language to remove

| Counterfactual (remove) | Mechanistic (use) |
|------------------------|-------------------|
| "X should have noticed the alert" | "The alert was one of 40 that fired; it was 11th in the list" |
| "X failed to run the migration correctly" | "The migration tool defaults to the prod cluster and the confirmation prompt shows only the cluster's short name" |
| "The team could have tested this better" | "The test suite has no coverage for the empty-result path; that gap dates to the 2024 refactor" |
| "Human error" | Never a cause. It is a description of where the investigation stopped early |

"Should have", "could have", "failed to" and "didn't" are the marker words. If a postmortem contains them,
it has stopped investigating and started allocating fault.

### 6.3 The structure

1. **Summary** — three sentences: what broke, for whom, for how long.
2. **Impact** — quantified. Users affected, requests failed, revenue, error budget consumed, support
   contacts generated. Quantifying impact is what makes the follow-up work fundable.
3. **Timeline** — timestamped, from the first contributing change (not from the alert) to resolution.
   Include what people *believed* at each point, not just what was true. The false hypotheses are the most
   instructive part of the document.
4. **Contributing factors** — plural, deliberately. See §6.4.
5. **What went well** — genuinely, not as a courtesy. If the rollback took 90 seconds, that is a
   capability worth naming and protecting.
6. **The three questions** — §6.5.
7. **Action items** — §7.

### 6.4 "Root cause" is usually a fiction

Serious incidents in distributed systems essentially never have one cause. They have a set of conditions
that were individually survivable:

> The retry policy had no backoff (2023) **and** the connection pool was sized for the old traffic pattern
> **and** the canary stage only ran for 3 minutes, shorter than the time for pool exhaustion to appear
> **and** the dashboard showing pool saturation was not on the on-call's default view.

Remove any one and the incident does not happen. Chasing a single root cause forces you to pick one of
these, which means you fix one and leave the other three in place. Use **contributing factors**, and
classify each so the action items distribute across the defence layers:

| Layer | Question |
|-------|----------|
| **Prevent** | What would have stopped this from being possible? |
| **Detect** | What would have told us sooner? |
| **Mitigate** | What would have let us stop the pain faster? |
| **Reduce impact** | What would have made the blast radius smaller? |

A postmortem whose action items are all in the "prevent" column is incomplete. You cannot prevent every
novel failure; you can always improve detection and mitigation, and those improvements generalise to
failures you have not imagined yet.

### 6.5 The three questions

For every incident, ask explicitly:

1. **What made this hard to detect?** (Detection latency: alert coverage, thresholds, missing SLI.)
2. **What made this hard to diagnose?** (Missing traces, no deploy markers, a stale runbook, a dashboard
   nobody knew about, an unowned service.)
3. **What made this hard to mitigate?** (No feature flag, a rollback that needed manual steps, an
   unrehearsed failover, needing someone who was asleep.)

Answering these three consistently across a quarter of incidents produces a much better prioritised
reliability backlog than any individual postmortem does — because the same answer keeps appearing, and the
repetition is the signal.

---

## 7 · Action items that are real

### 7.1 The test

| Bad action item | Why | Better |
|-----------------|-----|--------|
| "Add more monitoring" | Not specific, not owned, unfalsifiable | "Add a burn-rate alert on the checkout SLO at 14.4× — @a, 2 weeks" |
| "Be more careful with migrations" | Not a change to the system | "Migration tool requires typing the full cluster name to confirm — @b, 1 week" |
| "Improve documentation" | Nobody's job, no completion criterion | "Rewrite the pricing-service runbook's first three steps with copy-pasteable commands; verify in a game day — @c, 3 weeks" |
| "Consider moving to X" | Not an action, a wish | "Spike: evaluate X against the three failure modes in this incident; write a recommendation — @d, 2 weeks" |

Requirements for every item: **a named individual** (never a team, never "TBD"), **a due date**, **a size
estimate**, **a defence layer** (prevent / detect / mitigate / reduce impact), and **a ticket in the normal
backlog** — not a bullet in a document nobody reopens.

### 7.2 Fewer, and completed

**Three completed action items beat fifteen recorded ones.** A postmortem that generates fifteen items
produces a list nobody triages, and the presence of the list creates a false belief that the problem is
handled. Force the ranking during the review: which three of these, if done, would most change the outcome
of a repeat? Do those. Explicitly record the rest as "considered and not doing", with a reason — that is a
decision, and it is honest, and it is far better than a zombie backlog.

### 7.3 Tracking to completion

| Rule | Detail |
|------|--------|
| SEV1 action items due within 30 days | Tracked as a named metric |
| Overdue items escalate | To the owning manager at 30 days, automatically |
| Completion rate reported quarterly | At the on-call review (`oncall-health.md` §8) |
| **Below 70% completion** | The postmortem process is theatre. Fix the process — usually by generating fewer items — before writing another one |
| Repeat incidents flagged against their original postmortem | The strongest possible evidence that the item mattered |

That last row is the highest-leverage measurement in this file: when the same incident recurs, link it to
the earlier postmortem and the specific unfinished action item. Nothing else makes the cost of unfinished
follow-up so concrete, and it turns "we should do reliability work" into "this exact deferred item cost us
this exact outage".

---

## 8 · Error-budget-driven freeze policy

The mechanics live in `slos-and-error-budgets.md` §6. What matters in the incident context:

- **The freeze is automatic, not a judgement call.** It follows from the budget arithmetic, which is why
  it has to be pre-agreed. If invoking it requires winning an argument each time, it will never be
  invoked when it matters.
- **What continues during a freeze**: security patches, fixes for the ongoing burn, rollbacks, and
  anything that reduces risk. A freeze that blocks security patches will be ignored, and once ignored it
  never regains authority.
- **The un-freeze condition is a measurement**, not a meeting: the trailing budget recovering above a
  threshold. "Frozen until further notice" becomes permanent and then becomes a joke.
- **A small quarterly allowance of overrides** for the product owner, spent visibly and recorded, keeps
  the policy from being either ignored or absolute.
- **Freezing the wrong team is punishment, not policy.** If the burn came from a dependency, the escalation
  routes to that dependency's owner with the attribution data attached.

---

## 9 · Practising

Process that is only exercised during real incidents will fail during real incidents.

| Practice | What it tests | Cadence |
|----------|--------------|---------|
| **Game day** | A specific failure injected in a controlled environment; the on-call responds for real using the runbook | Monthly |
| **Wheel of Misfortune** | A tabletop exercise: someone describes symptoms, the responder talks through the investigation | Fortnightly, 30 min |
| **Escalation test** | A deliberate test page at a random hour; does it reach a human, how fast | Quarterly |
| **Rollback drill** | Actually roll back a production service | Monthly |
| **Failover drill** | Actually fail over a region or an AZ | Quarterly |
| **Runbook walkthrough** | Someone who did not write it follows it | On each runbook, twice a year |

The tabletop exercise is dramatically under-used: it costs half an hour, needs no infrastructure, surfaces
gaps in the runbook and in shared mental models, and is the single best onboarding tool for a new on-call.

---

## Interview questions

**1. Walk me through how you would run a SEV1.**
Declare it immediately and name an incident commander out loud, with acknowledgement, so there is no
ambiguity about who decides. The IC coordinates and does not debug — the moment they open a terminal the
incident has no commander. Assign an ops lead who is the only person making production changes, one at a
time and announced before they happen, plus a comms lead and a scribe. Then mitigate before understanding:
roll back, flip the flag, fail over, shed load — stop the user pain first, diagnose afterwards from the
logs. Communicate on a fixed cadence whether or not there is news, verify recovery against the SLI rather
than a hunch before declaring it over, and schedule the postmortem while everyone still remembers.

**2. What is the difference between mitigation and resolution, and why does it matter?**
Mitigation stops the user's pain and does not require understanding the cause — rollback, kill switch,
failover, load shedding. Resolution fixes the underlying defect and does require understanding. It matters
because the instinct to find the cause before acting is the most expensive habit in incident response:
every minute spent understanding is a minute of user impact, and the understanding is equally available
tomorrow. The corollary is an engineering requirement, not just a process one — your mitigations have to
be fast, rehearsed and safe to invoke blind, which means one-command rollbacks, flags actually wired to
the risky paths, and failover drills that happen on a schedule rather than for the first time during an
incident.

**3. Tell me about how you handled a production bug you caused. [Reported at Lyft]**
Structure it as: what I shipped, how it was detected and how long that took, what I did first — which
should be mitigate, not investigate — what the user impact was in numbers, and then what I changed about
the system so that class of mistake becomes impossible or harmless. The last part is what separates a
Senior from a Staff answer: not "I was more careful afterwards", but a specific systemic change — a
missing test, a canary stage that was too short to catch it, a rollback that took too long, a flag that
should have existed. And I would say plainly that I wrote the postmortem myself and that it was blameless
in the technical sense: the interesting question was not why I made the mistake, but why the system let
the mistake reach users.

**4. What does "blameless" mean, and what does it not mean?**
It means assuming everyone acted reasonably given the information, tooling, incentives and time pressure
they had, so the question becomes "what made that action look right at the time?" rather than "why did you
do that?" It does not mean nobody is accountable — people are accountable for writing the postmortem and
completing the action items; they are just not punished for having been at the keyboard. The practical
argument that convinces sceptics is not about kindness: blame produces hiding, hiding kills your supply of
near-miss information, and near misses are the cheapest reliability data you will ever get.

**5. Why do you avoid the phrase "root cause"?**
Because serious distributed-systems incidents almost never have one. They have several individually
survivable conditions that lined up — a retry policy with no backoff, a pool sized for old traffic, a
canary stage too short to expose it, a saturation dashboard not on the on-call's default view. Remove any
one and there is no incident. Insisting on a single root cause forces you to pick one and fix it while
leaving the others in place. I prefer contributing factors classified by defence layer — prevent, detect,
mitigate, reduce impact — because a postmortem whose actions are all in the "prevent" column is
incomplete: you cannot prevent novel failures, but better detection and mitigation generalise to failures
you have not imagined.

**6. How do you make sure postmortem action items actually get done?**
Generate fewer of them. Three completed items beat fifteen recorded ones, and a long list creates a false
belief that the problem is handled. Every item needs a named individual — never a team — a due date, a
size, and a ticket in the same backlog as feature work rather than in a document nobody reopens. Then
measure completion within 30 days and report it at the quarterly review; below about 70% the postmortem
process is theatre and the process needs fixing before another one is written. The most powerful
mechanism is linking repeat incidents back to the specific unfinished action item from the earlier
postmortem — that turns "we should invest in reliability" into "this deferred item cost us this outage".

**7. How do you set severity levels so they stay meaningful?**
Define them by user impact rather than by how alarming the internal symptom looks, or everything becomes a
SEV1 within six months and the scale stops carrying information. Then make declaring cheap and downgrading
routine and explicitly blameless, because the expensive error is under-declaring, not over-declaring. I
would also include an explicit clause that impact is not always proportional to user count — for a safety
or customer-care domain, an incident affecting a safety-reporting path is top severity regardless of how
few users hit it, and the table has to say that or people will do the arithmetic and get it wrong.

**8. Your mitigation is to restart the pods, which fixes it and destroys the evidence. What do you do?**
Capture first if it costs under a minute — thread or heap dump, connection and socket state, logs copied
off the node, the exact instance IDs and deploy SHA, a screenshot of the dashboard — then restart. Better,
script it as a single `capture-diagnostics` command invoked as an explicit step in the runbook before the
mitigation step, so it happens under pressure without anyone having to remember it. If capture genuinely
conflicts with speed, mitigation wins and you note in the postmortem that you have a repeat waiting for
you — but that trade-off should be rare, because it is cheap engineering to make it unnecessary.

**9. How do you communicate during an incident?**
One voice externally — exactly one person posts updates, and everyone else including senior leaders routes
through them, because contradictory updates turn an outage into a trust problem. Fixed cadence regardless
of news: "no update, still investigating, next update in 30 minutes" is a valuable message because it
stops the stream of "any news?" that consumes the IC's attention. Every update leads with impact in user
terms, states what is being done, and gives the time of the next update. Externally I never speculate
about cause and never give an ETA I am not confident in — "recovery expected within 15 minutes of the
rollback completing" is fine, "should be back soon" is not.

**10. How do you practise incident response?**
Regularly and cheaply. The highest value-per-hour is a fortnightly half-hour tabletop — someone describes
symptoms and the responder talks through their investigation out loud — which needs no infrastructure and
immediately exposes gaps in runbooks and in shared mental models. Beyond that: monthly game days injecting
a real failure in a controlled environment, monthly rollback drills and quarterly failover drills, because
an unrehearsed failover during an incident is just a second incident, and a quarterly test page at a
random hour to prove the escalation chain still reaches a human. The rule underneath all of it is that any
process only exercised during real incidents will fail during real incidents.
