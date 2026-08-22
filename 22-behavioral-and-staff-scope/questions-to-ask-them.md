# Questions to Ask Them

> **Priority:** Recommended
> **Est. time:** 30 min
> **Track:** Both
> **HelloInterview:** none

Every round ends with 5-10 minutes for your questions, and at Staff those minutes are scored. The
hiring committee reads interviewer notes; "asked good questions about X" appears in them.

The difference between a Senior and a Staff question is not depth — it is **what the question implies
you would do with the answer.** A Senior question gathers information about the job. A Staff question
probes how the organisation makes decisions, and implies you are already thinking about operating
inside it.

---

## 1 · The test for a good question

| Check | Fail | Pass |
|-------|------|------|
| Could it be answered from the careers page? | "What's the tech stack?" | "What made you write your own checkpointer instead of using the built-in one?" |
| Does it imply you would act on the answer? | "Is there good work-life balance?" | "What does the on-call rotation look like in a bad week, and what's the last thing you fixed because of it?" |
| Does it assume the answer is good? | "Is the codebase well tested?" | "Where is the testing weakest right now, and is anyone funded to fix it?" |
| Is it about you or about them? | "What's the promotion process?" | "What would a Staff engineer here have changed by the end of their first year?" |
| Does it survive a short answer? | Yes/no questions | Questions that require an example |

**Ask questions you actually want answered.** A performed question is detectable and it fails
**Be yourself** in the same round where you were assessed on authenticity.

Budget: **two to three questions per round**, prepared, plus one improvised from something the
interviewer said. Do not bring a list of ten and work through it.

---

## 2 · The strongest single question

On their published agent simulator finding — offline pass rates around 90%, production revealing a
distribution shift because off-the-shelf LLM user simulators behave like nice, helpful assistants
while real users send brief impatient messages, fixed by fine-tuning simulators on real customer
verbatims.

> "You published the simulator distribution-shift finding — 90% offline that didn't survive contact
> with real users. Once you'd fine-tuned the simulators on real verbatims, how do you know the new
> distribution is right? What's the feedback loop that catches the next shift, and does it run
> automatically or does someone have to notice?"

**Why this is the best question you can ask:**

| Property | Effect |
|----------|--------|
| Proves you read their engineering writing, specifically | Almost no candidate does this at the level of a named finding |
| Engages their *failure*, not their success | Peer behaviour, not flattery |
| The question is harder than the finding | You are asking about the second-order problem, which is genuinely open |
| Framed as a systems question — feedback loop, automation, ownership | Staff framing without claiming ML expertise |
| Connects to "how did you measure?" | Same thread as the behavioural round |

Ask it of an engineer or the hiring manager. Keep it to the length above; a longer version becomes a
statement. Do not ask it of a recruiter.

Supporting context in [ai-and-genai-questions.md](ai-and-genai-questions.md) section 5.

---

## 3 · By interviewer type

### 3.1 Recruiter

Practical only. Save judgement questions for people who can answer them.

- What does the loop look like end to end, and what is the level being assessed?
- Is the behavioural round with the team or with someone outside it?
- For the 90-minute laptop round — is the expected I/O channel stdin/stdout or files? (Genuinely
  useful: the dominant failure mode in that round is I/O handling, not algorithms.)
- What's the timeline, and is there anything about my background you'd want me to address up front?

The last one is quietly valuable — it surfaces the CV items in
[transition-narrative.md](transition-narrative.md) early, with the person whose job it is to
pre-empt them.

### 3.2 Hiring manager

Where the scope questions belong.

- **"What would a Staff engineer here have changed by the end of their first year — not shipped,
  changed?"** The single best level-calibration question available. If the answer is a list of
  features, the role is a Senior role with a Staff title. If it is about standards, direction or how
  teams work together, it is real.
- What decisions are currently being made twice because nobody owns them?
- Where does the team's scope end and another team's begin, and where is that boundary painful?
- Who are the internal customers of the platform, and what do they complain about?
- What did the team try in the last year that didn't work?
- How does a technical decision that affects three teams actually get made here?

### 3.3 Engineers on the team

Concrete and operational. These also tell you whether you want the job.

- **On-call:** how many people in the rotation, how many pages in a normal week, and what was the
  last page that woke someone at 3am? Follow up with: was it fixed, or is it still there?
- What is the noisiest alert you have, and why has nobody deleted it?
- What breaks most often, and does anyone own it?
- How long does it take a new engineer to ship something to production, and what is the slowest part?
- Which part of the system would you rewrite if you were given a quarter?
- What is the test story for the non-deterministic parts of the platform?
- How do the self-serve JSON-configured agents get validated before they go live, and who is
  accountable when one behaves badly?

The on-call pair — pages per week *and* the last 3am page — is worth more than any question about
culture. Nobody can misrepresent a specific 3am page.

### 3.4 Bar raiser or cross-team interviewer

They are outside your prospective team, so ask about the organisation.

- How does technical direction propagate between teams here? Is there a forum, a standard, a document?
- What is the last thing an engineer changed that affected teams beyond their own?
- Where do you see the biggest gap between how the org thinks it works and how it works?
- What would make you regret this hire in a year?

The last one is direct and lands well with someone whose job is calibration. Be ready for it to be
turned around.

### 3.5 Product manager (the Kyiv behavioural round has been run by a PM)

Ask what a PM uniquely knows, and ask about the engineering-product interface.

- How do engineering trade-offs get communicated when a decision moves a commitment you have made
  externally?
- What is the last time engineering told you no, and how did that go?
- Which metric does the team actually steer by day to day?
- What do customers of the support platform complain about that the metrics do not capture?

That last one connects directly to the distribution-shift theme and to "how did you measure?".

---

## 4 · Three areas worth covering across the loop

You will not get all of these into one round. Spread them.

### 4.1 On-call health

Ask for: rotation size, pages per week, actionable-page ratio, and one specific recent page. What you
are diagnosing is whether reliability work is funded or merely admired. A team that cannot name its
page count does not look at it.

If the answers are bad, that is information — and it is also an opening: reliability improvement is
Slot 9 in [story-bank.md](story-bank.md), and offering a concrete first-90-days idea in response is a
legitimate Staff signal.

### 4.2 Team scope and boundaries

Ask where the team's ownership ends. The interesting answer is always about the boundary that is
currently painful — a shared dependency, an unowned service, a decision that keeps getting relitigated.
Those boundaries are exactly where Staff work exists, and asking about them signals you know that.

### 4.3 What Staff impact looks like in year one

Ask it of the hiring manager, and listen for whether the answer involves other teams. Useful
follow-ups:

- Who was the last person to do that here, and what did they do?
- What stopped the previous attempt?
- What would you need from me in the first 90 days for this to have been a good hire?

The 90-days question gives you material for a strong close, and it gives the hiring manager a concrete
picture of you in the role — which is what you want them carrying into the committee discussion.

---

## 5 · Questions to avoid

| Question | Problem |
|----------|---------|
| "What's the promotion process?" / "How fast can I get to T7?" | Reads as levelling anxiety in the round where levelling is decided. |
| "Is there a lot of on-call?" | Sounds like avoidance. Ask for the numbers instead — same information, opposite signal. |
| "What's the culture like?" | Unanswerable, and gets you a rehearsed answer. |
| "Do you use microservices?" | Answerable from public writing. Signals you did not read it. |
| Anything about compensation, in a technical or behavioural round | Recruiter conversation. |
| "What's your biggest weakness as a team?" framed as a gotcha | Cute reversal, reads as adversarial. Ask "what didn't work last year?" instead. |
| Three questions in one breath | Wastes the slot; the interviewer answers the easiest one. |

---

## 6 · Prepared set

Carry six, use two or three per round, and always keep one improvised from the conversation.

1. What would a Staff engineer here have changed by the end of their first year — not shipped, changed?
2. Once you'd fine-tuned the simulators on real verbatims, what catches the next distribution shift?
3. How many people are in the on-call rotation, and what was the last page that woke someone at 3am?
4. What decisions are currently being made twice because nobody owns them?
5. Where does this team's scope end, and where is that boundary painful right now?
6. What did the team try in the last year that didn't work?

Improvised questions score higher than prepared ones because they prove you were listening. Note one
thing the interviewer says in the first ten minutes and come back to it at the end.

---

## Interview questions

**1. Do you have any questions for us?**
Two or three, not ten. Lead with the one that implies you are already thinking about operating in the
role — the year-one change question with a hiring manager, the on-call specifics with an engineer,
the distribution-shift follow-up with anyone on the platform.

**2. What are you looking for in your next role?**
Organisational scope: setting direction other teams build against, on a platform with internal
customers. Keep it consistent with the answer in
[transition-narrative.md](transition-narrative.md) — the two get compared.

**3. What would make you turn down an offer from us?**
Answer honestly and specifically: a role where the scope turned out to be one team and one service,
or where reliability work is unfunded. Naming a real condition is more credible than "nothing".

**4. Why did you choose Lyft?** **[Reported at Lyft]**
Frequently asked just before "any questions for us?", and the two should chain. Be specific:
multi-agent support platform on LangGraph, meta agent as stateful router, custom DynamoDB
checkpointer, safety checks fanned out ahead of LLM reasoning. Then say which part you find hardest,
and let your prepared question in section 2 come straight out of it.

**5. Is there anything we haven't asked that you think we should have?**
Use it to fill a coverage gap from [story-bank.md](story-bank.md) — usually the Staff-scope slot
(setting direction, or driving adoption) if the round stayed on individual delivery. Thirty seconds,
not three minutes.

**6. What would you want to work on first?**
Do not commit to a redesign you cannot justify from outside. Say what you would want to understand
first — the boundary that is painful, the on-call load, the evaluation loop — and name the kind of
change you would expect to make once you had. Humility about specifics plus clarity about method.
