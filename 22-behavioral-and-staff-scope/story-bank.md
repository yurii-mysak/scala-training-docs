# Story Bank — 12-Slot Working Template

> **Priority:** Required
> **Est. time:** 4 h (fill-in, across several sessions)
> **Track:** Both
> **HelloInterview:** Behavioral — Story Builder; Decode / Select / Deliver

This is a **template, not content**. Nothing below is filled in for you on purpose — invented
experiences collapse on the second follow-up, and Lyft's round is built from follow-ups.

Twelve slots, because the round is breadth over depth: 6-9 questions in 45 minutes, and reusing one
story three times reads as a thin career. Each slot holds one 90-second story plus the material to
expand it to five minutes.

---

## 1 · How to use this file

1. Draft each slot in HelloInterview's **Story Builder** — it produces well-formed but long stories.
2. Compress to 90 seconds using [carl-and-star.md](carl-and-star.md) section 3.
3. Run the **Staff-scope check** on the slot. If it fails, re-frame rather than swapping in a bigger
   project — see [senior-vs-staff-framing.md](senior-vs-staff-framing.md) section 5.
4. Fill the **numbers you need** line. Recovery techniques in
   [metrics-for-stories.md](metrics-for-stories.md).
5. Write four probes and answer them aloud.
6. Mark the slot done only when it survives four consecutive probes without invention.

Rules while filling:

- Different employers across slots. Four stories from one job reads as one job.
- Different **decades of scale** where possible: a two-person decision and a four-team decision are
  different evidence.
- At least two slots where you were wrong, and one where you reversed yourself publicly.
- No slot may be blank on the day. An empty slot is a question you cannot answer.

---

## 2 · Coverage grid

Fill the right-hand columns as you complete slots. The audit is in section 4.

| # | Slot | Primary value | Also serves | Employer | Done |
|---|------|---------------|-------------|----------|------|
| 1 | Proudest project with measured impact | Make it happen | Be yourself | ____ | [ ] |
| 2 | A production bug you caused | Be yourself | Make it happen | ____ | [ ] |
| 3 | Convincing a peer who disagreed | Uplift others | Be yourself | ____ | [ ] |
| 4 | Mentoring someone concretely | Uplift others | Make it happen | ____ | [ ] |
| 5 | A failure and what changed after | Be yourself | Uplift others | ____ | [ ] |
| 6 | A cross-functional conflict | Uplift others | Make it happen | ____ | [ ] |
| 7 | Setting technical direction | Make it happen | Uplift others | ____ | [ ] |
| 8 | A trade-off made deliberately | Make it happen | Be yourself | ____ | [ ] |
| 9 | On-call / reliability improvement | Make it happen | Uplift others | ____ | [ ] |
| 10 | Inclusion | Uplift others | Be yourself | ____ | [ ] |
| 11 | Driving adoption of something new | Make it happen | Uplift others | ____ | [ ] |
| 12 | A decision you later reversed | Be yourself | Make it happen | ____ | [ ] |

---

## 3 · The slots

Each slot uses the same shape. `____` means fill it in; do not delete the prompt.

---

### Slot 1 — Proudest project with measured impact

**Answers:** "Recent project you're proud of. What was your role? What was impact? How did you measure?" **[Reported at Lyft]**

- **Context** (system, scale, stakes, your position): ____
- **The organisational problem** (not the technical one): ____
- **Decision 1** and the alternative rejected: ____
- **Decision 2** and the alternative rejected: ____
- **Result**, before → after, with time window: ____
- **What it cost**: ____
- **Learning / what the org kept**: ____
- **One-sentence non-technical framing** (for the PM interviewer): ____

**Numbers you need:** primary impact metric before and after · time window · team size · traffic or
data volume · the instrument that produced the number.

**Staff-scope check:** does the result section name a team other than yours, or a standard that
outlived the project? If the whole story is "the system I built worked", this is a Senior telling.

**Four probes to rehearse:** What was your role specifically? · How did you measure? · Who disagreed?
· Is it still running, and who owns it?

---

### Slot 2 — A production bug you caused

**Answers:** "Tell me about how you handled a production bug you caused." **[Reported at Lyft]**

- **What you shipped and why it seemed right**: ____
- **How you found out** (alert, customer, colleague): ____
- **Blast radius** (users, revenue, duration): ____
- **First action, in the first ten minutes**: ____
- **Who you told, and when**: ____
- **Mitigation vs fix** — separate them: ____
- **Systemic change that removes the class**: ____ — did it ship? ____
- **Learning**: ____

**Numbers you need:** detection time · time to mitigation · time to fix · users or requests affected ·
money or SLA impact if any · recurrence count since.

**Staff-scope check:** did the fix change something beyond your own service — a template, a review
gate, an alert everyone inherits? A bug fixed only in your service is a Senior story.

**Four probes to rehearse:** Why didn't testing catch it? · What did you tell the customer? · Would
your change have caught it? · Has anything similar happened since?

---

### Slot 3 — Convincing a peer who disagreed

**Answers:** "Did you convince your colleague about your solution, and how?" **[Reported at Lyft]**

- **The two positions**, stated fairly — theirs first: ____
- **Their strongest argument**: ____
- **The artefact you built to make it checkable** (benchmark, spike, failure-mode table): ____
- **What you conceded or changed in your own position**: ____
- **How the decision was actually made** (who decided, in what forum): ____
- **Relationship afterwards**: ____
- **Learning**: ____

**Numbers you need:** whatever the artefact produced — latency, cost, error rate, lines of code, hours
of operational load. The point of the artefact is that it produced a number.

**Staff-scope check:** did you remove the need to have this argument again — criteria written down, a
default set, a guide others used without you? Winning once is Senior; settling the class is Staff.

**Four probes to rehearse:** What if they'd still disagreed? · Were you right? · Who made the final
call? · Have you used that approach since?

---

### Slot 4 — Mentoring someone concretely

**Answers:** "What experience do you have with mentoring and creating systems?" **[Reported at Lyft]**

- **Who** (role and level, no name needed): ____
- **Where they started** — a specific gap, not "junior": ____
- **What you actually did**, week by week: ____
- **Where they got to** — scope they now own: ____
- **The system you built from it** (onboarding path, rotation, review standard): ____
- **How many people have been through it**: ____
- **Who runs it now**: ____
- **Friction you absorbed** to standardise it: ____

**Numbers you need:** time to first meaningful PR · time to on-call readiness · number of people
through the system · number of seniors whose ad-hoc effort it replaced.

**Staff-scope check:** the question has two halves and most candidates answer one. If there is no
mechanism that runs without you, this slot is unfinished.

**Four probes to rehearse:** What did you change in how you mentor? · What if someone doesn't want
mentoring? · How do you know it worked? · Who else contributed to it?

---

### Slot 5 — A failure and what changed after

**Answers:** "Tell me about failure." / "Time you failed at something." **[Reported at Lyft]**

- **What you believed at the time and why it was reasonable**: ____
- **The decision that was yours**: ____
- **What the world did instead**: ____
- **The real cost** — do not soften: ____
- **Who else paid for it**: ____
- **What you changed** — a mechanism, not a feeling: ____
- **Did the change stick**: ____

**Numbers you need:** time or money lost · people affected · how long before it was caught.

**Staff-scope check:** is the blast radius organisational? At Staff a failure story should be
*larger*, not safer. Advice other teams followed, a standard you set that was wrong, a hire or a
roadmap call. No rescue at the end.

**Four probes to rehearse:** What was the earliest signal you missed? · What did your manager say? ·
Would you make the same call with the same information? · What stops it now?

---

### Slot 6 — A cross-functional conflict

**Answers:** "How do you manage a difficult partnership?" **[Reported at Lyft]**

- **The other function** (PM, data, security, another eng team) and what they were measured on: ____
- **The friction, from their point of view**: ____
- **What you changed first**: ____
- **What you gave up**: ____
- **The working agreement that replaced the friction**: ____
- **Escalation** — did you, when, and did you tell them first: ____
- **Outcome and current state**: ____

**Numbers you need:** how long the block lasted · cost of the block (engineer-weeks, delayed launch) ·
what improved after, measured.

**Staff-scope check:** does the story diagnose the other side's constraint rather than their
behaviour? "They were slow" is Senior. "They had three teams asking for variants of the same thing
and no prioritisation" is Staff.

**Four probes to rehearse:** What was their incentive? · What would they say about you? · When did you
escalate and why then? · What would you do earlier next time?

---

### Slot 7 — Setting technical direction

**Answers:** "How do you set technical direction for people who don't report to you?"

- **The decision that kept recurring**: ____
- **Who owned the decision before you got involved** (often nobody): ____
- **The mechanism you used** (criteria doc, reference implementation, forum, template): ____
- **How you got buy-in without authority**: ____
- **Teams that adopted it**: ____
- **Someone who did not adopt it** — and what you did: ____
- **How long it held**: ____

**Numbers you need:** teams adopting · services on the standard · decisions it settled · time saved
per decision.

**Staff-scope check:** this slot is pure Staff signal, so it must not degrade into "I wrote a good
design doc". Direction means other people changed what they build.

**Four probes to rehearse:** Who could have overruled you? · What did you do about the holdout? · Has
it aged well? · How did you know it was the right direction?

---

### Slot 8 — A trade-off made deliberately

**Answers:** "Tell me about a time you decided not to do something."

- **The two things you could not both have**: ____
- **How you costed each side** — the actual arithmetic: ____
- **Who you took the decision to** (peers and PM, not just your manager): ____
- **What you chose and what you killed**: ____
- **Who was unhappy**: ____
- **How you defended it afterwards**: ____
- **Whether it was right, in hindsight**: ____

**Numbers you need:** the cost you computed (engineer-hours, latency budget, dollars) · the delay you
accepted · the improvement you bought.

**Staff-scope check:** something must have been genuinely lost — a feature deferred, a customer
commitment moved, a colleague's preferred design overruled. A trade-off that cost nothing was a
preference.

**Four probes to rehearse:** How did you get that number? · What did the PM say? · What if you'd
chosen the other way? · Did anyone escalate over your head?

---

### Slot 9 — On-call / reliability improvement

**Answers:** general Make-it-happen probes; also strong for a Safety & Customer Care team.

- **Baseline pain** — pages per week, noisiest alert, worst hour: ____
- **What you measured first**: ____
- **The change** (alert quality, runbook, ownership, architecture): ____
- **What you deleted** — alerts removed matter as much as alerts added: ____
- **Effect on the humans**, not just the metrics: ____
- **How it held over 6-12 months**: ____

**Numbers you need:** pages per week before/after · MTTR before/after · percentage of pages that were
actionable · incidents per quarter · number of engineers in the rotation.

**Staff-scope check:** did the rotation as a whole get healthier, or did you personally get better at
being paged? The first is Staff; the second is Senior.

**Four probes to rehearse:** Which alert did you delete and how did you decide? · What did the rest of
the rotation think? · What broke that you didn't have an alert for? · How is it now?

---

### Slot 10 — Inclusion

**Answers:** "What's inclusion for you?" **[Reported at Lyft]**

- **The practice you personally run** — one sentence: ____
- **Where it came from** (something you noticed, not something you read): ____
- **One instance where it changed an outcome**: ____
- **What it cost** (time, comfort, a decision that took longer): ____
- **Whether anyone else adopted it**: ____

**Numbers you need:** usually none, and forcing one here is worse than none. If the practice is about
review participation, meeting airtime or distributed-team fairness, a rough count is fine
("in a team of nine, three people never spoke in design reviews").

**Staff-scope check:** does it operate at the level of how the team works, rather than how you behave?
For a fully remote engineer in Kyiv working with a distributed org, timezone fairness and
written-first decision-making are legitimate, concrete, and directly relevant to this role.

**Four probes to rehearse:** What if it slows the meeting down? · Has anyone pushed back? · How do you
know it worked? · What have you got wrong here?

---

### Slot 11 — Driving adoption of something new

**Answers:** "Tell me about a time you introduced a new technology or practice."

- **What you introduced and what it replaced**: ____
- **Why the status quo held** — the real reason, usually not ignorance: ____
- **The first adopter and how you got them**: ____
- **What you did to make adoption cheap** (migration tooling, docs, doing it for them): ____
- **Adoption curve**: ____
- **Who never adopted and why that was acceptable**: ____
- **What you would not introduce again**: ____

**Numbers you need:** teams or services adopting, over what period · effort saved per team · the
before/after on whatever it was meant to improve.

**Staff-scope check:** adoption by others is the entire measurement. If the story ends with you using
the new thing well, it belongs in a technical round, not here. Note also this is the natural bridge
to [ai-and-genai-questions.md](ai-and-genai-questions.md) and the AI-dev-tools position in
[../20-llm-agent-systems/ai-dev-tools-adoption.md](../20-llm-agent-systems/ai-dev-tools-adoption.md).

**Four probes to rehearse:** Who resisted? · How did you handle the team that said no? · What did it
cost to maintain? · Was it worth it?

---

### Slot 12 — A decision you later reversed

**Answers:** "What would you do differently?" and as a second failure story.

- **The original decision and the case for it**: ____
- **The evidence that changed your mind**: ____
- **How long you held on after the first contrary signal**: ____
- **How you announced the reversal, and to whom**: ____
- **Cost of the reversal**: ____
- **What replaced it**: ____
- **What you now do earlier**: ____

**Numbers you need:** time between first contrary signal and reversal · cost of the wrong path ·
improvement after.

**Staff-scope check:** the reversal must have been *public* — announced in a forum, retracted advice,
told the teams who followed you. A quiet private change of mind is not organisational evidence.

**Four probes to rehearse:** What was the signal you ignored? · How did the people who'd adopted it
react? · What do you do now to catch this earlier? · Have you reversed anything since?

---

## 4 · Coverage audit

Run this once all twelve are drafted, and again a week before the loop.

| Check | Target | Actual |
|-------|--------|--------|
| Slots complete | 12 | ____ |
| Stories per value: Be yourself | ≥ 4 | ____ |
| Stories per value: Uplift others | ≥ 4 | ____ |
| Stories per value: Make it happen | ≥ 4 | ____ |
| Distinct employers represented | ≥ 3 | ____ |
| Stories where you were wrong | ≥ 2 | ____ |
| Stories with a named cost | 12 | ____ |
| Stories with a real number | ≥ 10 | ____ |
| Stories with ≥ 2 humans with agency | 12 | ____ |
| Stories affecting more than one team | ≥ 6 | ____ |
| Stories with a one-line non-technical framing | 12 | ____ |

Any row under target is a specific evening of work, not a general worry.

### 4.1 Live tracking during the round

Keep a mental tally of which slots you have spent. If the interviewer says "you've mentioned that
project a few times", you have already lost coverage. Selecting a fresh slot per question is the
**Select** discipline from HelloInterview's Decode / Select / Deliver track.

---

## Interview questions

**1. Recent project you're proud of. What was your role? What was impact? How did you measure?** **[Reported at Lyft]**
Slot 1. Deliver the 90-second core holding two details back; answer role as decisions owned versus
decisions others owned; give one number with a time window and name the instrument behind it.

**2. Tell me about how you handled a production bug you caused.** **[Reported at Lyft]**
Slot 2. Sequence detection, blast radius, first action, comms, mitigation, fix, systemic change. Be
explicit about which of those you owned personally and whether the systemic change actually shipped.

**3. Did you convince your colleague about your solution, and how?** **[Reported at Lyft]**
Slot 3. State their position first and fairly, then the artefact that made the disagreement
checkable, then what you conceded. Finish on what stops the same argument recurring.

**4. What experience do you have with mentoring and creating systems?** **[Reported at Lyft]**
Slot 4. One person with a concrete before/after in scope, then the mechanism, then the count of
people through it and who owns it now.

**5. Tell me about failure. / Time you failed at something.** **[Reported at Lyft]**
Slot 5, with Slot 12 held in reserve if they ask for a second. Real cost, no rescue, mechanism
changed, and honesty about whether the mechanism stuck.

**6. What's inclusion for you?** **[Reported at Lyft]**
Slot 10. A practice you run, an instance where it changed an outcome, and what it cost. No
definitions, no speaking for groups you are not in.

**7. How do you manage a difficult partnership?** **[Reported at Lyft]**
Slot 6. Diagnose their incentives, name what you changed first and what you gave up, then the working
agreement and any deliberate escalation.

**8. Do you have another example of that?**
This is why the bank has twelve slots and not five. Switch employer and value simultaneously — it
demonstrates breadth in one move.

**9. Which of these projects would you say most changed how your organisation worked?**
A direct Staff-scope probe. Have a designated answer: usually Slot 7 or Slot 11, and it should not be
the same story as Slot 1.
