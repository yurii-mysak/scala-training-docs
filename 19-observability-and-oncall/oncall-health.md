# On-Call Health

> **Priority:** Required
> **Est. time:** 75 min
> **Track:** Both
> **HelloInterview:** none

This is the Staff-scope file of the section. The role description carries a responsibility bullet on
establishing best practices for deployment, alerting and on-call health for an organisation — which means
the expected answer is not "I carried a pager and it was fine". It is: *on-call is a system, it has
measurable health, here is how I instrument it, here is how I changed the numbers, and here is the
mechanism that stopped it regressing.*

The difference between a Senior and a Staff answer here is almost entirely about whether the answer
contains a **measurement, a mechanism, and a scope beyond your own team.**

---

## 1 · On-call as a system with its own SLO

Treat the rotation exactly as you treat a service:

| Service concept | On-call equivalent |
|-----------------|--------------------|
| SLI | Pages per shift, percentage actionable, MTTA |
| SLO | "No more than 2 pages per 12-hour shift; ≥ 75% actionable" |
| Error budget | The page budget — pages above target are a debt |
| Burn | A service repeatedly over its page budget |
| Freeze policy | Exceeding the page budget two quarters running mandates reliability work |
| Postmortem | The quarterly on-call review |
| Users | The engineers on the rotation |

The widely-used target, and a defensible number to quote: **no more than two incidents per 12-hour
on-call shift.** Above that, the responder cannot do a proper job on any of them — no time to diagnose
properly, no time to write the postmortem, and the follow-up work never gets done, which guarantees the
same pages next week. The related Google SRE guidance is that **toil should be capped at 50%** of an
engineer's time, with the rest going to engineering that reduces future toil.

If you take one framing into an interview, take this: *an unhealthy rotation is not a morale problem, it
is a reliability problem, because the people who would fix the reliability are the people being
interrupted.*

---

## 2 · The metric set

### 2.1 Load metrics

| Metric | Definition | Healthy | Warning | Action threshold |
|--------|-----------|---------|---------|------------------|
| **Pages per shift** | Page-severity notifications delivered to the primary per 12 h | ≤ 2 | 3–4 | > 4 |
| **Pages per rotation-week** | Same, per person per week of primary duty | ≤ 5 | 6–15 | > 15 |
| **Night pages / week** | Delivered 22:00–08:00 responder-local | ≤ 1 | 2–3 | > 3 |
| **Weekend pages / week** | Sat/Sun | ≤ 1 | 2–3 | > 3 |
| **Sleep-disrupting pages** | Night pages that woke someone (survey or ack-latency proxy) | ≈ 0 | 1 | > 1 |
| **Interrupt load** | Non-page interrupts absorbed by the on-call: questions, tickets, escalations | ≤ 2 h/day | 2–4 h/day | > 4 h/day |

The **time-of-day distribution** matters more than the total. Twelve pages in a week that all arrive
between 10:00 and 17:00 is an annoying week. Four pages that all arrive between 02:00 and 05:00 is an
unsustainable rotation. Always plot the histogram by local hour, per person — not aggregated across
regions, which averages the pain into invisibility.

### 2.2 Quality metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| **Percentage actionable** | Pages where the responder changed the state of something | ≥ 75% |
| **Percentage self-resolving** | Resolved within 15 min with no action taken | ≤ 10% |
| **Repeat rate** | Pages from an alert that already fired in the same quarter | ≤ 25% |
| **Runbook coverage** | Page-severity alerts with a linked runbook | 100% |
| **Runbook accuracy** | Responders marking the runbook "accurate" at incident close | ≥ 80% |
| **Detection provenance** | Incidents detected by an alert before a human reported them | ≥ 85% |

**Repeat rate** is the most under-used metric in this list. A rotation with a 60% repeat rate is not
suffering from bad luck; it is suffering from postmortem action items that never get done. It converts
"we keep getting paged" into a specific, fixable claim.

### 2.3 Response metrics

| Metric | Definition | Note |
|--------|-----------|------|
| **MTTA** | Notification → acknowledgement | Track the median. A rising MTTA usually means the alerts have stopped being trusted, not that people got slower |
| **MTTR** | Detection → user impact ends | **Report median and p90, never the mean.** One 14-hour incident makes a mean meaningless |
| **Time to mitigation** | Detection → user pain stops | The number that actually matters; distinct from resolution |
| **Time to engage the right person** | Page → the person who could fix it is involved | Isolates escalation and ownership problems from technical difficulty |

Splitting MTTR into *detect → engage → diagnose → mitigate → resolve* is what makes it actionable. "MTTR
is 90 minutes" tells you nothing. "MTTR is 90 minutes, of which 40 is finding the right person" tells you
to fix the service catalogue, not the debugging tooling.

### 2.4 Sustainability metrics

| Metric | Definition | Note |
|--------|-----------|------|
| **Toil ratio** | Fraction of the on-call's time on manual, repetitive, automatable, reactive work | Cap at 50% |
| **Follow-up completion** | Incident action items closed within 30 days | Below ~70% and postmortems are theatre |
| **Rotation depth** | People who can take primary for this service | ≥ 6 for 24/7 |
| **Bus factor per runbook** | People who have actually executed the mitigation | ≥ 2 |
| **Handoff compliance** | Shifts with a written handoff | ≥ 95% |
| **Survey** | "Would you be comfortable if this rotation stayed as-is for another year?" per quarter | The only metric that catches slow-burn misery |

That last one is not soft. Every quantitative metric can look acceptable while the rotation is quietly
grinding people down — because the expensive part is often not the page count but the *anticipation*: not
sleeping properly, not being able to leave the house, not being able to plan a week. A one-question
quarterly survey catches it and gives you something to put next to the numbers.

### 2.5 Where the data comes from

If you cannot answer "how many pages did we get last week", the first project is not fixing on-call, it is
**getting the data**. Typical sources:

| Source | Provides |
|--------|----------|
| Paging tool API (PagerDuty, Opsgenie) | Notifications, timestamps, ack times, escalations, who was on call |
| Alert manager | Rule definitions, labels, annotations, silences |
| Incident tracker | Severity, duration, mitigation time, postmortem link, action items |
| Ticket system | Action-item completion, ages |
| Version control | Alert rules as code, runbook edit history |
| Chat | Incident channel timestamps; a rough proxy for engagement time |

Derived fields you have to compute yourself, since no tool gives them to you: *actionable* (needs either
a responder tick at incident close or a heuristic like "an incident record or a change was created"),
*night page* (needs the responder's local timezone, not UTC and not the company's headquarters timezone),
and *repeat* (needs stable alert identity across rule edits).

Build this as a weekly job that writes a small table, not as a dashboard someone has to remember to open.
The report should arrive in the team's channel every Monday with last week's numbers and the trend.

---

## 3 · Rotation design

### 3.1 Size

| Rotation size | Weeks on primary per year | Verdict |
|---------------|--------------------------|---------|
| 3 | ~17 | Unsustainable. One holiday or one departure and it collapses |
| 4 | 13 | Punitive for 24/7; workable for business-hours-only |
| 6 | ~9 | The practical minimum for 24/7 primary |
| 8 | ~6.5 | Comfortable; leaves room for holidays and departures |
| 12+ | ~4 | Too infrequent — people lose familiarity and every shift is a relearning exercise |

There is a floor *and* a ceiling. Below six, the rotation is fragile and every absence is a crisis. Above
roughly twelve, people go so long between shifts that they no longer know the systems, the tooling, or
where the runbooks are — and a rotation of strangers has a worse MTTR than a rotation of five tired
people. If you have thirty engineers, run three rotations of eight or ten by domain rather than one
rotation of thirty.

### 3.2 Shift shape

| Shape | Pros | Cons | Fits |
|-------|------|------|------|
| **Weekly, 24/7** | Best continuity; one context transfer per week | Nights are on the same person all week; brutal if page volume is high | Low page volume, single region |
| **Split day/night** | Nobody's sleep is destroyed twice | Two handoffs a day; needs twice the people | High volume, single region |
| **Follow-the-sun, 2–3 regions** | No night pages at all, in principle | Handoff overhead; hard timezone arithmetic; needs real regional depth | Genuinely distributed teams (§6) |
| **Business hours + best-effort nights** | Cheap and humane | Only honest if the SLO permits overnight degradation | Internal tools, tier-3 services |

That last row is worth taking seriously rather than treating as a failure. If a service's SLO genuinely
permits a four-hour overnight recovery, then paging on it overnight is a cost with no benefit. Aligning
the pager policy to the SLO tier is a legitimate — and cheap — way to reduce night pages: **only tier-1
services page overnight.** Getting that written down is often a bigger win than any technical change.

### 3.3 Primary, secondary, and the interrupt shield

- **Primary** takes the pages.
- **Secondary** exists for two things: catching unacknowledged pages, and being a second pair of hands on
  a large incident. The secondary should *not* receive every notification — a "shadow pager" doubles the
  fatigue and halves the accountability, because each person assumes the other has it.
- **Interrupt shield** (sometimes "support" or "batman"): a separate daytime role that absorbs questions,
  ad-hoc requests, escalations from other teams and the ticket queue. Splitting this from the pager is one
  of the highest-value changes available, because the two loads have different urgency and combining them
  means the on-call is shredded during the day and exhausted at night.

### 3.4 Onboarding — nobody goes straight to primary

```
Shadow          → receives notifications alongside the primary, takes no action,
                  attends the incidents.        (1–2 shifts)
Reverse shadow  → drives the response with the experienced person watching
                  and available to take over.   (1–2 shifts)
Primary         → with a named, briefed backup for the first shift.
```

Attach an onboarding checklist: access to every system (verified by actually using it, not by a ticket
saying it was granted), the paging app installed and tested with a real test page, the escalation policy
read, three runbooks executed in staging, and a walkthrough of the top five historical incidents for
this service.

The access point is where this most often fails. The classic 03:00 disaster is discovering that the new
on-call's production credentials were never provisioned, or that their VPN certificate expired. **Test
access, do not assume it** — a scripted pre-shift check that verifies the responder can reach every system
they might need takes an afternoon to build and eliminates an entire class of incident.

### 3.5 Fairness

- **Published at least a month ahead** so people can plan their lives. A schedule that changes with two
  days' notice is worse than a heavier but predictable one.
- **Frictionless swaps** — a self-service swap that does not need a manager's approval. High swap friction
  means people take shifts they should not.
- **Holiday equity**: local public holidays differ across Ukraine, Germany and Mexico, so a naive
  round-robin systematically punishes whoever has the most holidays overlapping their slots. Track
  holiday-shift counts per person across the year and rebalance explicitly.
- **Accommodations** for medical, caring and parental circumstances, arranged privately and without
  requiring an explanation to the team.
- **Everyone who ships is on the rotation**, including the most senior people. A rotation that excludes
  the people who make the architectural decisions removes the feedback loop that makes systems operable —
  this is the single strongest cultural argument for on-call, and it is worth making explicitly.

---

## 4 · Toil, and reducing it

Toil is work that is manual, repetitive, automatable, tactical, devoid of enduring value, and scales
linearly with service growth. It is not "work I dislike" and it is not all operational work — a genuinely
novel incident investigation is not toil.

Measuring it: have the on-call classify each interrupt at close into a small fixed taxonomy —
*genuine incident / automatable repeat / question that a doc would answer / access or permission request /
manual process step / false alarm*. Two weeks of that data tells you exactly where the automation budget
should go, and it costs the responder ten seconds per interrupt.

The predictable distribution: a large share is access requests and questions that documentation would
answer. Those are not glamorous to fix, and they are usually the cheapest wins available.

---

## 5 · Handoff quality

### 5.1 Why it is where incidents are lost

The two highest-risk moments in on-call are the start of a shift and the handoff. A degraded system that
the outgoing person understood and the incoming person has never heard of is exactly the setup for a small
problem becoming a long one.

### 5.2 The handoff template

```
SHIFT HANDOFF — <service/rotation> — <from> → <to> — <timestamp + timezone>

OPEN INCIDENTS
  <id> <sev> <one line> — current state, who else is involved, next step

DEGRADED / WATCHING
  <system> — what is off, since when, why we have not fixed it, what would make it urgent

SILENCES ACTIVE                      ← the most commonly lost item
  <alert> — silenced by <who>, until <when>, reason, linked ticket

IN-FLIGHT CHANGES
  deploys, migrations, traffic shifts, freezes, planned maintenance in the next 24 h

SUSPICIONS
  anything odd I noticed and did not chase. No obligation to act; you should just know.

ENVIRONMENT
  anything unusual: a dependency's maintenance window, a partner's incident,
  a public event driving traffic
```

The **silences** section is the one that matters most and is most often skipped. An alert silenced at
Friday 16:00 "just for an hour" that nobody removed is how outages become invisible for a weekend. The
enforcing rule: every silence has an owner, a linked reason, and an expiry of at most 24 hours, and active
silences appear automatically in the handoff — generate that section from the alert manager API rather
than trusting anyone to remember.

The **suspicions** section is the one people find odd and is disproportionately valuable. "The p99 on the
pricing service looked slightly worse yesterday afternoon and I could not tie it to anything" is exactly
the information that turns a four-hour investigation into a twenty-minute one, and it will never be
written down unless the template asks for it explicitly.

### 5.3 Live vs asynchronous

- **Asynchronous document** is the default: written, posted in the channel, cheap.
- **A 15-minute live handoff** is worth it when the shift was busy, when an incident is open, or when the
  handoff crosses regions and the two people rarely talk. The written document is still produced — the
  call is in addition, not instead.
- **Always in writing**, because handoffs are the source material for the quarterly review. A verbal
  handoff leaves no evidence of what was known when.

---

## 6 · Follow-the-sun for a Ukraine / Germany / Mexico team

This is a specific structural question, and it deserves specific arithmetic rather than a generic
"follow-the-sun is nice".

### 6.1 The actual offsets

| Location | Winter | Summer | DST? |
|----------|--------|--------|------|
| Kyiv, Ukraine | UTC+2 (EET) | UTC+3 (EEST) | Yes, EU dates |
| Germany | UTC+1 (CET) | UTC+2 (CEST) | Yes, EU dates |
| Mexico City | UTC−6 | UTC−6 | **No** — Mexico abolished nationwide DST in 2022 (a northern border strip still follows US DST) |

| Pair | Winter gap | Summer gap |
|------|-----------|------------|
| Kyiv ↔ Germany | 1 h | 1 h |
| Germany ↔ Mexico City | 7 h | 8 h |
| Kyiv ↔ Mexico City | **8 h** | **9 h** |

Two immediate consequences:

1. **Kyiv and Germany are effectively one timezone.** For coverage purposes they are a single shard. This
   is good news — it gives that shard real depth — but it means you have two coverage regions, not three.
2. **The Europe–Mexico gap changes by an hour twice a year**, because Europe still observes DST and
   Mexico does not. Every schedule, every "coverage from X to Y" statement, and every recurring handoff
   meeting must be defined **in UTC** with local times derived, or it silently breaks in late March and
   late October. Write schedules in UTC. This is a small, concrete, credible detail to raise.

### 6.2 The overlap window is small

Business-hours overlap between the EU shard and Mexico City:

| Season | Mexico City 09:00–11:00 is... | Usable overlap |
|--------|------------------------------|----------------|
| Winter | Kyiv 17:00–19:00 / Germany 16:00–18:00 | ~2 hours, at the end of the EU day |
| Summer | Kyiv 18:00–20:00 / Germany 17:00–19:00 | ~1 hour, and it is EU evening |

So the handoff window is real but narrow, it sits at the uncomfortable end of the European day, and it
shrinks in summer. Design for it deliberately: **a fixed handoff slot defined in UTC, scheduled inside the
winter overlap so it survives the summer shift**, with a written handoff document that does not depend on
the call happening.

### 6.3 The coverage arithmetic, and the hole

Two regions eight hours apart cannot cover 24 hours with 12-hour shifts. The union of two 12-hour windows
offset by 8 hours is 20 hours.

```
UTC   00  02  04  06  08  10  12  14  16  18  20  22  00
EU    ..  ..  ..  ████████████████████████  ..  ..  ..     06:00–18:00 UTC  (Kyiv 08–20 winter)
MX    ██  ..  ..  ..  ..  ..  ..  ████████████████████     14:00–02:00 UTC  (MX 08–20)
                      ^^^^^^^^^^^^ overlap (14:00–18:00 UTC)
      ^^^^^^^^^^^^^^^^ GAP: 02:00–06:00 UTC
                       = Kyiv 04:00–08:00 winter
                       = Mexico City 20:00–00:00
```

**A four-hour hole, and four hours of redundant overlap.** Pretending otherwise is the classic
follow-the-sun mistake. The honest options:

| Option | Mechanism | Cost |
|--------|-----------|------|
| **Stretch Mexico's evening** | MX takes 10:00–22:00 local (16:00–04:00 UTC); EU takes 06:00–18:00 UTC | Gap shrinks to 2 h (04:00–06:00 UTC). MX has a late-evening shift |
| **Stretch the EU morning** | EU shard starts 05:00 UTC (Kyiv 07:00) | An early start, but not a night page |
| **Accept a small night window** | One region carries a pager for the residual 2–4 h with a documented expectation (e.g. ~0.3 pages/week) | Honest and often correct — but only if the page rate is genuinely that low |
| **Add a third region** | An APAC or US-West presence | The only structurally clean fix; a hiring decision, not an engineering one |
| **Tier the pager** | Only tier-1 SLO breaches page in the gap window; everything else queues | Cheap, and usually the right first move |
| **Automate the gap** | Auto-remediation with rate limits for known conditions in that window | Reduces, does not eliminate |

### 6.4 The geography is mostly an advantage — say so

If the product's traffic is US-centric, then **US night is 06:00–14:00 UTC, which is exactly the European
working day.** The EU shard covers the riskiest low-staffing window with no night pages at all, and Mexico
covers US business hours in its own daytime. The genuinely awkward window is US late evening
(02:00–06:00 UTC), which is low traffic.

Frame it that way in an interview. "This team's geography gives near-24-hour coverage without night pages
for the majority of the load; the residual is a four-hour window at the lowest-traffic time of day, and
here are the four ways to close it" is a much stronger answer than a generic description of
follow-the-sun.

### 6.5 The costs nobody budgets for

- **Every handoff loses context.** Two handoffs a day is the practical maximum; three regions with
  eight-hour shifts sounds elegant and produces a game of telephone. Prefer two regions with 12-hour
  shifts and a strong written handoff.
- **Incidents that span a handoff need an explicit incident-commander transfer**, not an implicit one: a
  stated current hypothesis, what has been ruled out, what is in flight, who has been told what, and an
  explicit "you are now IC" acknowledgement. Without that, the new region restarts the investigation from
  scratch — the single largest MTTR cost in a distributed rotation.
- **Regional depth must be real.** A region that cannot resolve an incident without waking someone in
  another region is not providing coverage; it is providing a delay. This constrains hiring and knowledge
  distribution, not just scheduling. Track "incidents where a region had to escalate cross-region" as a
  metric — it is the honest measure of whether follow-the-sun is working.
- **Language and comms.** Incident channels, runbooks and postmortems in one shared language, with a
  norm that people write plainly and ask clarifying questions freely. Under pressure, a non-native speaker
  reading a runbook full of idiom is a real, avoidable source of delay.
- **Public holidays do not align.** Ukrainian, German and Mexican holiday calendars barely overlap. Build
  the combined calendar into the scheduler, and treat a date where two of three regions are on holiday as
  a coverage risk to plan for in advance.

---

## 7 · Compensation and sustainability

### 7.1 Models

| Model | Description | Note |
|-------|-------------|------|
| **Standby stipend** | A flat payment per shift regardless of pages | The clearest signal that the availability itself has value |
| **Per-incident payment** | Payment per page handled | Creates a perverse incentive against fixing the noise |
| **Time off in lieu** | Compensating rest for out-of-hours work | Only works if the culture actually lets people take it |
| **Written recovery rule** | "Paged after 22:00 → you start after midday, no questions, no approval" | Cheap, immediate, and highly visible |
| **Comp days per rotation** | A day off after a heavy shift | Simple; needs enough rotation depth to absorb |

The **written recovery rule** is the highest value-per-effort item on this list. It costs nothing, it is
enforceable, and it changes how the rotation feels immediately. The critical word is *written*: an
informal "of course, take the morning" is not usable by the people most likely to need it, because they
are the people least likely to ask.

Whatever the model, **avoid per-incident payment as the primary mechanism.** Paying people per page pays
them to keep the pages, which is the opposite of what you want. Pay for the constraint on their life, not
for the interrupt.

### 7.2 Legal and regulatory — get help, do not improvise

On-call is regulated employment in several jurisdictions, and this team spans three of them.

- **Germany** distinguishes *Rufbereitschaft* (standby: free to be elsewhere, on call) from
  *Bereitschaftsdienst* (on-site standby), and the two are treated differently for working-time and pay
  purposes. Daily rest-period requirements interact directly with night pages: an interruption can reset
  or break a required rest period, which has consequences for the following day's schedule. Where a works
  council (*Betriebsrat*) exists, the on-call arrangement is typically a matter for co-determination.
- **Ukraine** and **Mexico** have their own working-time, overtime and rest rules.

Two practical rules: **involve HR and local employment counsel before designing a rotation that spans
jurisdictions**, and **do not assume a policy that is legal in one country is legal in another.** In an
interview, showing awareness that this is a legal and not just a cultural question is a strong Staff
signal — the specific statute is not what is being tested; knowing to ask is.

### 7.3 Making the case for investment

Managers fund on-call improvements when the cost is quantified. The shape of the argument:

```
Rotation cost per quarter
  = (pages × average interrupt cost in engineer-hours)
  + (night pages × next-day productivity loss)
  + standby compensation
  + recruiting/backfill risk attributable to rotation burnout

Fix cost
  = engineer-weeks to eliminate the top 3 page sources
```

Even with rough numbers, this is usually a lopsided comparison, and it is far more persuasive than
"people are unhappy". A worked example: 40 pages a week across a rotation, at a conservative two hours of
lost productive time per page including the recovery, is 80 engineer-hours a week — two full-time
engineers spent on interrupts. If three weeks of work removes 70% of them, the payback is under a month.

Do the arithmetic honestly, label the assumptions clearly, and present the range rather than a single
number. This is exactly the kind of reasoning the behavioural round's "how did you measure?" probe is
looking for.

### 7.4 Burnout signals

Watch for: rising MTTA (people have stopped trusting the pager), swap requests concentrating on a few
people, postmortem action items consistently unfinished, a drop in voluntary participation in the
rotation, quiet exclusions ("don't page X, they're busy"), and — the clearest early signal — the survey
question in §2.4 trending down while all the quantitative metrics look fine.

---

## 8 · The quarterly on-call review that actually changes things

Most on-call reviews are a slide deck of charts that everyone nods at and nothing happens. The difference
between a review that changes things and one that does not is entirely structural.

### 8.1 Inputs, prepared in advance

Circulate 48 hours before, so the meeting is for decisions and not for reading:

1. **The metric pack** — every metric from §2, this quarter vs last, per rotation.
2. **Top 10 alerts by page volume**, with actionability and owner.
3. **Every incident** by severity, with mitigation time and postmortem link.
4. **Action-item completion rate** from last quarter's incidents, and the list of overdue ones by name.
5. **Last quarter's commitments**, each marked done / not done / abandoned.
6. **The anonymous survey results** (the one question from §2.4, plus a free-text box).

### 8.2 The agenda

| Time | Item | Output |
|------|------|--------|
| 0–10 | **Read last quarter's commitments aloud, one by one, with the owner's name and status** | Accountability, publicly |
| 10–20 | Metric pack: what moved, what did not | Shared understanding |
| 20–35 | Top page sources: for each, decide fix / demote / delete / accept | Decisions, with owners |
| 35–45 | Action-item completion; any overdue item is re-committed with a name and date, or explicitly killed | No zombie items |
| 45–55 | Rotation and policy changes: size, shape, coverage, compensation | Decisions |
| 55–60 | Commit to **three to five** changes for next quarter, each with an owner and a date | The output |

### 8.3 The four mechanisms that make it stick

Everything in the agenda above is ordinary. These four are what separate it from theatre:

1. **Open by reading last quarter's commitments aloud with names attached.** Nothing else produces
   follow-through like knowing that in twelve weeks your name will be read out next to "not done". It
   costs ten minutes and it is the single most effective element.
2. **Commitments enter the normal backlog**, sized and prioritised alongside feature work, owned by an
   individual and not by "the team". Reliability work in a separate list that is never scheduled is
   reliability work that does not happen.
3. **Cap the output at three to five changes.** A review that produces twenty action items produces zero
   completed ones. Choosing three is the hard, valuable part of the meeting, and the discipline of
   choosing forces the ranking conversation you actually need to have.
4. **An automatic escalation with teeth.** A service over its page budget for two consecutive quarters
   triggers a written plan from the owning manager: funded reliability work with dates, or a formal
   proposal to change the SLO with data, or the service is reclassified to a lower support tier with the
   pager policy relaxed accordingly. The point is not punishment — it is that the situation cannot simply
   persist unexamined for a third quarter.

### 8.4 The page budget

Give each service a page budget, exactly parallel to its error budget:

| Service tier | Pages / quarter | Night pages / quarter |
|--------------|-----------------|----------------------|
| Tier 1 | ≤ 20 | ≤ 4 |
| Tier 2 | ≤ 12 | ≤ 2 |
| Tier 3 | ≤ 6 | 0 (does not page overnight) |

Over budget in one quarter is a discussion. Over budget in two is the §8.3.4 escalation. This makes
on-call load a *managed* quantity with a policy attached rather than a thing that happens to people, and
it is the mechanism that lets you say "this is a system, not a complaint" in an interview.

### 8.5 What the output looks like

A good review produces something like:

- Delete 14 alerts, demote 9 to tickets — owner: A, by week 3.
- Fund the retry-storm fix in the pricing client, which caused 31% of last quarter's pages — owner: B,
  two engineer-weeks, by week 8.
- Change the night-page policy: only tier-1 SLO burn pages between 22:00 and 08:00 — owner: C, by week 2.
- Move Mexico's shift to 10:00–22:00 local to shrink the coverage gap from 4 h to 2 h — owner: D, next
  schedule cycle.
- Add the written "paged after 22:00 → start after midday" rule to the team handbook — owner: E, week 1.

Five items, five names, five dates. Next quarter opens by reading them out.

---

## 9 · Staff scope: a 90-day plan for taking this on

If asked "you join and the on-call is a mess — what do you do in your first quarter?":

| Weeks | Focus | Deliverable |
|-------|-------|-------------|
| 1–2 | **Measure.** Pull 90 days of paging and incident history. Do not change anything yet | The baseline, published |
| 2–3 | **Listen.** Talk to everyone on the rotation individually. Ride along on a shift | The qualitative half of the picture |
| 3–4 | **The top five.** Identify the alerts producing most of the pages | A ranked list with owners |
| 4–6 | **Quick wins.** Delete and demote the obviously-unactionable; add `for:` durations; write the missing runbooks for the top five; add the written recovery rule | Visible improvement inside a month |
| 6–10 | **Structural.** One SLO on the most important journey, with burn-rate alerts replacing the worst cause-based rules. Fix the single biggest page source properly | The pilot, with before/after numbers |
| 8–12 | **Mechanism.** CI check for runbook + owner on page-severity rules. Weekly automated report. The quarterly review, scheduled and with an agenda | The thing that outlives you |
| 12 | **Publish.** Before/after, what worked, what did not, what is next | The credibility to do it for the next team |

Two things to say out loud about this plan. First, **measure before changing** — not out of caution, but
because without a baseline you cannot prove the improvement, and an unprovable improvement does not get
you funding for the next one. Second, **the mechanism is the deliverable.** Deleting 200 alerts is a
Senior contribution; the CI check and the review cadence that stop them coming back is the Staff one.

Cross-links: `alert-design.md` (the alert-level work), `slos-and-error-budgets.md` (the budgets both
policies rest on), `incident-response.md` (postmortems and action items),
`staff-scope-stories.md` (turning this into interview stories with numbers).

---

## Interview questions

**1. How do you know whether an on-call rotation is healthy? [Reported at Lyft — "How did you measure?"]**
I measure it like a service. Load: pages per 12-hour shift against a target of two or fewer, night pages
per week, and the time-of-day histogram in each responder's local time rather than aggregated. Quality:
percentage actionable — target 75% or better — percentage self-resolving, and repeat rate, which is the
share of pages from an alert that already fired this quarter. Response: MTTA, and MTTR reported as median
and p90 rather than mean because one long incident destroys a mean. Sustainability: toil ratio, follow-up
completion within 30 days, rotation depth, and one anonymous quarterly survey question — "would you be
comfortable if this rotation stayed as-is for another year?" — because every quantitative metric can look
fine while the anticipation of being paged is quietly grinding people down.

**2. What experience do you have with mentoring and creating systems? [Reported at Lyft]**
The clearest example of both together is treating on-call as a system rather than a rota. Creating the
system means the measurement pipeline, the page budget per service with an escalation when it is exceeded
twice, the CI check that refuses a page-severity alert without an owner and a runbook, and a quarterly
review whose first agenda item is reading last quarter's commitments aloud with names attached. The
mentoring half is inseparable from it: a shadow-then-reverse-shadow onboarding path so nobody goes to
primary cold, runbooks written so that the second person to hit a problem does not repeat the first
person's investigation, and a deliberate policy that senior engineers stay on the rotation so operability
feedback reaches the people making architectural decisions. The measure of both is whether the system
still works after I stop attending the review.

**3. You take over a rotation getting 40 pages a week. Walk me through your first quarter.**
Measure before changing anything: 90 days of paging history, per alert, with night fires, self-resolution
rate and whether each led to any action — and I publish that baseline, because without it no later
improvement is provable. Then talk to every person on the rotation individually and ride along on a shift,
because the numbers will not tell me that people have stopped trusting the pager. Then the top five alerts,
which are usually most of the volume: delete the unactionable, demote the non-urgent, add hysteresis to
the flapping, and write the missing runbooks. Around week six I would move to structural work — one SLO on
the most important user journey with burn-rate alerts replacing the worst cause-based rules — and by the
end of the quarter the mechanism: a CI check, a weekly automated report, and a scheduled quarterly review.
Then publish before-and-after, including a coverage metric, because reducing pages is trivial if you are
allowed to lose detection.

**4. How do you design on-call for a team split across Ukraine, Germany and Mexico?**
First the arithmetic, because it constrains everything. Kyiv and Germany are one hour apart, so they are
effectively a single coverage shard; Mexico City is eight hours behind Kyiv in winter and nine in summer,
because Europe observes DST and Mexico abolished it. Two regions eight hours apart with 12-hour shifts
cover 20 hours, not 24 — there is a four-hour hole around 02:00 to 06:00 UTC, plus four hours of redundant
overlap. So I would stretch the Mexico shift later to shrink the gap to about two hours, tier the pager so
only tier-1 SLO burn pages in that window, and be explicit that the residual is accepted rather than
pretending it is covered. I would also define every schedule in UTC, because a schedule written in local
time silently breaks twice a year. And I would point out the upside: if traffic is US-centric, the
European shard covers US night during its own working day, which is the whole benefit of this geography.

**5. What makes a good shift handoff, and what usually goes wrong?**
A written handoff every shift, covering open incidents, systems that are degraded and being watched,
in-flight changes and freezes, and — the two that get skipped — active silences and unexplained
suspicions. Active silences are where incidents get lost: an alert muted "just for an hour" on a Friday
that nobody removed can hide an outage for a weekend, so every silence needs an owner, a reason, and a
maximum 24-hour expiry, and the handoff section should be generated from the alert manager rather than
relying on memory. The suspicions section — "the pricing p99 looked slightly off yesterday and I could not
tie it to anything" — feels unnecessary and is repeatedly the thing that turns a four-hour investigation
into a twenty-minute one. And when an incident spans a handoff, the incident-commander transfer has to be
explicit, with the current hypothesis and what has been ruled out, or the new region restarts from zero.

**6. How would you convince leadership to fund reliability work to reduce pager load?**
Quantify the current cost and put it next to the fix cost. Forty pages a week at a conservative two hours
of lost productive time each, counting recovery, is eighty engineer-hours a week — the equivalent of two
full-time engineers spent on interrupts, before counting the next-day productivity loss from night pages
or the attrition risk. If three engineer-weeks removes 70% of them, the payback is under a month. I would
present it as a range with the assumptions labelled rather than a single confident number, because the
first question will be about the assumptions. The other lever is making the load a *managed* quantity: a
page budget per service, so that being over budget triggers a written plan rather than persisting
unexamined for another quarter.

**7. Is on-call compensation necessary, and what model would you pick?**
Yes, because on-call constrains someone's life whether or not it pages, and unpaid constraint is where
resentment and quiet exclusions start. I would pay a standby stipend for the shift rather than per
incident, because paying per page pays people to keep the pages, which is exactly backwards. The
highest-value item costs nothing: a *written* rule that anyone paged after 22:00 starts after midday the
next day with no approval needed. Written matters, because an informal "of course, take the morning" is
not usable by the people most likely to need it. And for a team spanning Germany, Ukraine and Mexico, I
would involve HR and local counsel before designing anything — German law distinguishes standby from
on-site duty and has rest-period rules that night pages interact with, and a policy that is fine in one
country may not be in another.

**8. How do you run a quarterly on-call review that actually changes something?**
Four structural things, none of them about the charts. Open by reading last quarter's commitments aloud
with the owner's name and status — nothing else produces follow-through like knowing your name will be
read next to "not done" in twelve weeks. Cap the output at three to five changes, because a review that
produces twenty items completes zero and the act of choosing three forces the ranking conversation you
need anyway. Put those commitments into the normal backlog, sized and owned by a named individual, not
into a separate reliability list that never gets scheduled. And have an automatic escalation with teeth: a
service over its page budget two quarters running requires a written plan from the owning manager —
funded work with dates, a data-backed proposal to change the SLO, or reclassification to a lower support
tier. Circulate the metric pack 48 hours ahead so the hour is spent deciding, not reading.

**9. Your MTTR is 90 minutes. How do you improve it?**
First I refuse to treat it as one number. I split it into detect, engage, diagnose, mitigate, resolve, and
report the median and p90 rather than the mean, because one 14-hour incident makes a mean meaningless.
Usually the split reveals something structural: if forty of those minutes are "engage", the problem is
service ownership and the escalation directory, not debugging tooling. If detection is slow, that is
alerting coverage. If diagnosis is slow, that is missing runbooks, missing deploy markers on dashboards,
or missing trace coverage. And I separate time-to-mitigation from time-to-resolution, because they need
different fixes — mitigation is about rollbacks, feature flags and failover being fast and rehearsed,
while resolution is about the underlying defect. Optimising the wrong one is the common mistake.

**10. Someone on the rotation is clearly burning out. What do you do?**
Immediately and individually: take them off the rotation, without requiring an explanation or making it a
performance conversation, and cover the shift myself or with a volunteer. That is the short-term action
and it should not need approval. Then the systemic question, because one person burning out on a healthy
rotation is unusual and usually means the rotation is not healthy for anyone — I would check whether the
load is concentrated (swap requests clustering on a few people, or a bus factor of one on a critical
runbook), whether the metrics were showing it and nobody was looking, and whether the survey signal was
trending down while the page count looked fine. The failure I would own is not having noticed from the
data: if the only way I learn the rotation is unsustainable is by someone breaking, my measurement is
inadequate, and that is a fixable gap.

**11. How do you decide who should be on the rotation?**
Everyone who ships code to the service, explicitly including the most senior engineers, because a rotation
that excludes the people making architectural decisions removes the feedback loop that makes systems
operable — that is the strongest argument for on-call and worth stating directly. The practical floor is
about six people for 24/7 primary; below that a single holiday or departure collapses the schedule. There
is also a ceiling around twelve, because people who are on call once a quarter no longer know the systems
or the tooling, and a rotation of strangers has a worse MTTR than a smaller tired one. With thirty
engineers I would run three rotations of eight to ten split by domain rather than one of thirty. And
nobody goes to primary cold: shadow, then reverse shadow, then primary with a named backup, with access
verified by actually using it rather than by a ticket claiming it was granted.

**12. What is toil and how do you reduce it?**
Toil is manual, repetitive, automatable, tactical work with no enduring value that scales linearly with
the service — not simply work people dislike, and a genuinely novel investigation is not toil. The
standard guidance caps it at 50% of an engineer's time. I measure it cheaply: the on-call classifies every
interrupt at close into a small fixed taxonomy — real incident, automatable repeat, question a doc would
answer, access request, manual process step, false alarm — which takes ten seconds and after two weeks
tells you exactly where the automation budget should go. The distribution is predictably unglamorous:
usually a large share is access requests and questions documentation would answer, which are the cheapest
things to fix and the least likely to be prioritised without the data.
