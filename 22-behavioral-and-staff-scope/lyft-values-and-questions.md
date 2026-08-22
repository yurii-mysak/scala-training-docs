# Lyft Values and the Reported Question Bank

> **Priority:** Required
> **Est. time:** 60 min
> **Track:** Both
> **HelloInterview:** Behavioral — Decode / Select / Deliver; The Big Three Questions

Lyft runs the behavioural loop against **three** values, not a twelve-item leadership-principle list.
Everything an interviewer scores maps back to one of them. Knowing which value a question is fishing
for is the difference between answering the words and answering the intent.

---

## 1 · The three values, and the evidence each one wants

| Value | Surface reading | What the interviewer is actually collecting |
|-------|-----------------|---------------------------------------------|
| **Be yourself** | "Are you authentic?" | Self-awareness under pressure. Can you name a failure without deflecting, state a real opinion, and say "I was wrong" with specifics? Do you have a point of view that is yours rather than borrowed from a framework? |
| **Uplift others** | "Are you nice?" | Whether other engineers got measurably better because you were there. Mentoring with named outcomes, inclusion as practice not sentiment, disagreement handled so the other person stays engaged. |
| **Make it happen** | "Do you ship?" | Ownership through ambiguity and friction. Did you drive something to a measured outcome across organisational boundaries, including the parts nobody assigned you? |

### 1.1 Anti-patterns each value screens out

- **Be yourself** screens out the rehearsed candidate. A story that has no cost, no doubt and no
  moment of being wrong reads as marketing. So does a "failure" that is secretly a strength
  ("I cared too much about quality").
- **Uplift others** screens out the lone hero. If every story has exactly one named human in it —
  you — this value scores zero regardless of technical content. This is the single most common
  reason a strong Senior candidate fails a Staff bar.
- **Make it happen** screens out the passive narrator. "The team decided", "it was decided",
  "we were asked to" — three of those in a row and the interviewer cannot find the agency.

### 1.2 Value coverage is a budget

You will be asked roughly 6-9 questions in 45 minutes. Aim for a distribution of stories that covers
all three values at least twice each. Track coverage in
[story-bank.md](story-bank.md) — the grid there exists precisely so you notice that ten of your twelve
stories are **Make it happen** and none are **Uplift others**.

---

## 2 · The transcribed round (reported July 2026)

One Lyft behavioural round has been reported verbatim. Treat it as the canonical shape of the
45 minutes, not as a list to memorise answers for.

| # | Question as asked | Value | Notes |
|---|-------------------|-------|-------|
| 1 | Recent project you're proud of | Make it happen | Opener. Sets the depth for everything after. |
| 2 | What was your role? | Be yourself / Make it happen | Follow-up, immediate. Tests whether question 1 was honest about ownership. |
| 3 | What was impact? | Make it happen | Follow-up. |
| 4 | **How did you measure?** | Make it happen | Follow-up. Verbatim. See [metrics-for-stories.md](metrics-for-stories.md). |
| 5 | Tell me about failure | Be yourself | Topic switch. |
| 6 | Did you convince your colleague about your solution, and how? | Uplift others | Note "and how" — the mechanism is the answer, not the outcome. |
| 7 | What's inclusion for you? | Uplift others | Direct values probe. Wants a practice, not a definition. |

Read that sequence again: questions 2, 3 and 4 are all follow-ups on question 1. **One story
generated four questions.** That is the format signal in section 4 in its rawest form.

### 2.1 What each follow-up is really testing

- *What was your role?* — separating "I was on the team that did X" from "I did X". Answer with the
  decision you owned, not the tickets you closed.
- *What was impact?* — whether you know the number, or only the activity.
- *How did you measure?* — whether the number is real. A candidate who quotes an impact figure but
  cannot describe the instrument that produced it is worse off than one who never quoted a figure.

---

## 3 · Reported question bank, organised by value

All questions below are reported from real Lyft loops.

### 3.1 Be yourself

| Question | What a strong answer contains |
|----------|-------------------------------|
| Tell me about a failure. / Time you failed at something. | A decision that was yours, a consequence that was real, and a specific mechanism you changed afterwards. No rescue at the end. |
| Tell me about how you handled a production bug you caused. | Detection, blast radius, your first action, comms to affected humans, the fix, and the systemic change that stops the class of bug. Ownership language throughout. |
| Why did you choose Lyft? | A specific, checkable reason tied to their published work. See [transition-narrative.md](transition-narrative.md#7--why-lyft). |

### 3.2 Uplift others

| Question | What a strong answer contains |
|----------|-------------------------------|
| Did you convince your colleague about your solution, and how? | The mechanism of persuasion: what evidence you produced, what you conceded, what changed in your own position. A story where you simply won is a weak answer. |
| What experience do you have with mentoring and creating systems? | Note the conjunction — they want mentoring that became a *system* (a rotation, a review standard, an onboarding path), not one-off pairing. |
| What's inclusion for you? | A concrete practice you personally run, and one time it changed an outcome. Definitions score nothing. |
| How do you manage a difficult partnership? | Diagnosis of the other side's incentives, a change you made first, and an escalation path you used deliberately rather than emotionally. |

### 3.3 Make it happen

| Question | What a strong answer contains |
|----------|-------------------------------|
| Recent project you're proud of. What was your role? What was impact? How did you measure? | See section 2. Prepare this as a four-layer story, not one paragraph. |
| Tell me some experience related to ML or Gen AI. | Newer question. See [ai-and-genai-questions.md](ai-and-genai-questions.md). Credible adjacency beats claimed expertise. |

---

## 4 · Two format signals that change how you prepare

### 4.1 Breadth over depth — many short stories, not three long ones

Most candidates prepare three deep stories and try to route every question into one of them. Lyft's
round punishes this: with 6-9 questions in 45 minutes, reusing one story three times reads as a thin
career. The budget per question is roughly **90 seconds of opening answer**, then follow-ups.

Practical consequence: prepare **12 distinct situations at 90-second depth** rather than 3 at
10-minute depth. Each must also be *expandable* to 5 minutes if the interviewer keeps pulling.
[carl-and-star.md](carl-and-star.md) covers the compress/expand mechanics;
[story-bank.md](story-bank.md) is the 12-slot template.

### 4.2 Heavy follow-ups on every answer

Assume every answer is followed by two to four probes. The reported round shows a 1:3 ratio of
opening questions to follow-ups. This means:

- Never put your best detail in the opening answer. Leave headroom the follow-up can find.
- Every claim you make is a door the interviewer can open. Do not claim a number you cannot
  source, a design you cannot draw, or a teammate's growth you cannot describe.
- "I don't remember the exact figure, but the shape was..." is an acceptable answer.
  A fabricated precise figure that collapses under one probe is a failed round.

Drill this specifically — see [mock-rehearsal-plan.md](mock-rehearsal-plan.md#3--follow-up-drilling).

---

## 5 · Who is in the room

| Signal | Implication |
|--------|-------------|
| In Kyiv this round has been run by a **product manager**, not an engineer | Stories must survive without shared technical vocabulary. Lead with the user/business consequence, then the mechanism. A story that only lands if the listener knows what an Akka Stream is will not land. |
| At Staff, expect a **bar raiser** | An interviewer outside the hiring team whose job is to check the level, not the fit. Bar raisers probe the *organisational* half of every story hardest: who else was affected, who disagreed, what it cost. |
| Round is 45 minutes | Tight. An interviewer who has to cut you off to get through their list will score you lower on communication regardless of content. |

Practical translation for the PM interviewer: rehearse a one-sentence non-technical framing for each
of the twelve stories. "We were losing applications because the system forgot state after a restart"
travels; "we lacked idempotent event replay" does not.

---

## 6 · Warning: do not prepare from Amazon material

A large fraction of the online "Lyft behavioural prep" content is recycled Amazon Leadership
Principle material — Customer Obsession, Ownership, Dive Deep, Disagree and Commit, Bias for Action,
and so on. **Lyft does not use leadership principles.** Any guide that names them is not describing
this company's rubric.

Concrete risks if you prepare from that material:

| Amazon habit | Why it hurts at Lyft |
|--------------|----------------------|
| One deep story per principle, 5-8 minutes each | Directly opposed to Lyft's breadth-over-depth format. You will cover a third of the question list. |
| Heavy STAR-with-metrics recital | Reads rehearsed against **Be yourself**, which is explicitly screening for authenticity. |
| "Dive Deep" style exhaustive detail dumps | With a PM interviewer, unparsed technical depth is noise, not signal. |
| Mapping answers to principle names out loud | Naming a rubric that this company does not have signals you prepared for a different interview. |

The correct mapping target is the three values in section 1. If a prep resource cannot name those
three, discard it.

---

## 7 · Preparation checklist for this file

- [ ] Can name the three values without looking, and one piece of evidence each fishes for.
- [ ] The "proud project" story survives four consecutive follow-ups including "how did you measure".
- [ ] Have a concrete inclusion *practice*, not a definition.
- [ ] Have a persuasion story where you changed your own position partway through.
- [ ] Have a mentoring story that produced a repeatable system, not just a grateful junior.
- [ ] Every story has a one-sentence non-technical framing for the PM interviewer.
- [ ] Deleted or ignored every Amazon-LP-based prep note.

---

## Interview questions

**1. Recent project you're proud of. What was your role? What was impact? How did you measure?** **[Reported at Lyft]**
Open with the organisational problem and the outcome number, in one sentence. State your role as the
decision you owned and the people you moved, not the code you wrote. Give impact as a before/after
pair with a time window. For measurement, name the instrument — dashboard, query, incident log,
finance report — and admit precision limits rather than rounding into confidence.

**2. Tell me about a failure. / Time you failed at something.** **[Reported at Lyft]**
Pick a failure where the decision was clearly yours and the cost was real. Describe what you believed
at the time and why it was reasonable, then what the world did instead. End on the mechanism you
changed — a review gate, a test, a rollout policy — not on a feeling. Do not add a rescue where the
project succeeded anyway.

**3. Tell me about how you handled a production bug you caused.** **[Reported at Lyft]**
Sequence it: how you found out, what the blast radius was, what you did in the first ten minutes, who
you told and when. Separate mitigation from fix. Close with the systemic change that removes the
class of bug, and be honest about whether it shipped.

**4. Did you convince your colleague about your solution, and how?** **[Reported at Lyft]**
The "how" is the answer. Describe the evidence you built — a benchmark, a spike, a failure-mode table —
and the part of their position you adopted. A story where you were right and they eventually agreed
scores lower than one where the joint decision was better than either starting point.

**5. What's inclusion for you?** **[Reported at Lyft]**
Answer with a practice you run, then an instance. For example: making sure the quietest person in a
design review is asked directly for their objection before the decision closes, and a time that
surfaced a constraint the room had missed. Avoid definitions and avoid speaking for groups you are
not in.

**6. What experience do you have with mentoring and creating systems?** **[Reported at Lyft]**
Answer both halves. Name a person and what changed for them measurably — scope they now own, a review
they now run. Then name the system: an onboarding path, a rotation, a design-review standard, and how
many people it has passed through since.

**7. How do you manage a difficult partnership?** **[Reported at Lyft]**
Diagnose the other side's incentives out loud — what were they being measured on that made them
behave that way. Describe the concession or change you made first, the working agreement you
established, and the point at which you escalated deliberately with the other party informed.

**8. Why did you choose Lyft?** **[Reported at Lyft]**
Be specific and checkable. Reference their published multi-agent support platform and the honest
write-up of the simulator distribution shift, and connect it to what you want to do next at
organisational scope. Avoid generic mission language. Full treatment in
[transition-narrative.md](transition-narrative.md).

**9. Which of our values do you find hardest?**
A legitimate probe against **Be yourself**. Pick one honestly and give evidence you are working on
it. Claiming all three come naturally is the wrong answer to a question designed to test candour.

**10. How do you like to receive feedback?**
Short, concrete, with an example of feedback that changed how you work. This is an **Uplift others**
question in disguise — the interviewer is checking whether feedback flows both directions around you.
