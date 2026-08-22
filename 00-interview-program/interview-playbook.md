# Interview Playbook — how to run each round on the day

> **Priority:** Required
> **Est. time:** 40 min
> **Track:** Both
> **HelloInterview:** System Design in a Hurry → Delivery Framework; Behavioral → Decode / Select / Deliver

Study material is elsewhere. This is behaviour: what to do in the room, in what order, and what to say.

---

## 1 · Before anything

**Schedule deliberately.** Kyiv is 10 hours ahead of San Francisco. Ask for the 90-minute laptop round at
a time when you are sharp, not at 21:00. Ask to split the onsite across two days. Both are normal requests
and neither counts against you.

**Ask for the example laptop problems.** Confirmed to exist. Do them cold, timed, before the real one.

**Confirm the environment.** Reports conflict on whether the laptop round runs in your own IDE or in
CoderPad. They also conflict on whether the problem expects stdin/stdout or file I/O. Both must be settled
before you start coding.

**Expect a possibly-sloppy process.** 2025–26 reports describe repeated rescheduling and interviewers from
other teams. Do not read scheduling chaos as a signal about you.

---

## 2 · Recruiter screen (30 min)

Level gets provisionally set here. Say "Staff" and give one sentence of org-level evidence, not a list of
systems you built.

Have ready: why you are looking, why Lyft, a one-line non-negative reason for leaving LotusFlare after a
year (*"Ukraine hiring is frozen there and I want org-level scope"* is true and lands well — never
criticise them), and a compensation answer.

On compensation: your current base is ~$6,000/month gross. Do not anchor on it. Ask for their band first.
Lyft rarely goes above band and comp is set by a hiring committee rather than the manager, so the leverage
is on equity and level, not on base.

Ask your questions here — the full list is in
[../22-behavioral-and-staff-scope/questions-to-ask-them.md](../22-behavioral-and-staff-scope/questions-to-ask-them.md).

---

## 3 · Technical phone screen (60 min, CoderPad, gatekeeping)

One problem, essentially the whole hour. Medium to hard. Human-proctored — a Mexico City report says so
explicitly. Fail this and the loop ends.

**Language: use Python.** Lyft's own blog says to use your most fluent language, but a human grades
readability and idiomatic Scala with effect types is hard for a Python/Go engineer to read quickly. If
your Python is not ready by then, use C# — it is named in the job posting.

**The protocol:**

1. Restate the problem in your own words. Confirm you have it right before writing anything.
2. Ask about input size, ranges, duplicates, empty and null cases. Write the edge cases down where the
   interviewer can see them.
3. State a brute-force approach and its complexity out loud. Do not implement it.
4. State the intended approach and its complexity. Get a nod before coding.
5. Code. Narrate what you are doing, not what the syntax means.
6. Walk a concrete small example through your code by hand. Do not claim it works — show it.
7. State the final complexity and one thing you would change with more time.

**Highest-yield preparation:** sliding window. LC 76 Minimum Window Substring is Lyft's most-repeated
problem across four years — four independent reports. LC 480 sliding window median appeared in Oct 2025.
Both are in [../09-coding-challenges/lyft/](../09-coding-challenges/lyft/).

If you get stuck, say what you are considering and why. A verbatim interviewer note: *"we're more
interested in how you overcome mistakes rather than if you make them."*

---

## 4 · The laptop round (90 min) — the one to over-prepare

**Structure:** 15 min discussion, ~60 min coding, 15 min demo and questions. The interviewer stays on the
call with video and audio off and no screen share. Internet is allowed. You demo and email a zip.

**Graded 45% correctness, 35% clean code, 20% performance.**

### The first 15 minutes decide the round

Settle these before writing a line:

- **Where does input come from — stdin, a file, or arguments? Where does output go?** This is the single
  most common cause of failure. Ask explicitly. Do not assume.
- **How many parts are there?** These problems are multi-part. One candidate finished part 1 and was told
  *"we expect that part to be covered"* about part 2. Find out the shape up front so you can budget.
- What are the test cases? They usually give them.
- What is out of scope?

### Then

Clone your harness from [../18-io-harness/](../18-io-harness/). You should be able to go from empty
directory to a running, tested project in under three minutes.

Get part 1 correct and committed before starting part 2. A working part 1 plus a sketched part 2 beats two
half-finished parts. Leave comments where you knew what to do but ran out of time — that is explicitly
what saved one candidate.

**Do not** reach for a heavy framework. One report is explicit: no Spring, no Jersey. It is *"building a
small app with data structure implementation."*

**Do** write a few tests if time allows, but do not force TDD if it is not your normal practice.

In the last 10 minutes: stop coding, tidy names, add a short README explaining how to run it and what you
would do next, then zip and demo. The demo is part of the grade.

### What is actually asked

Seven recurring families, all worked in [../17-lyft-laptop-round/](../17-lyft-laptop-round/). The round has
recently drifted toward object-oriented design — a June 2026 report says *"the laptop round is basically
OOD"* — so practise designing a small class with clean method boundaries, not just an algorithm.

---

## 5 · Design rounds (60 min each, usually two)

This is where a Staff offer is won. Weight your preparation accordingly.

**Lyft's design round is not an abstract FAANG design round.** It includes real coding, code review,
library choices and testing strategy. One report warns that candidates from research backgrounds struggle
with its production focus.

### The protocol

1. **Clarify scope and scale first.** Who are the users, how many, what is the read/write ratio, what is
   the latency requirement, what is explicitly out of scope. Write it down.
2. **Do the napkin math out loud.** Two independent sources name live memory and CPU estimation as a probe.
   Storage per record × records per day. QPS from DAU × actions. Memory for the hot set. Do not skip this —
   see [../15-system-design/napkin-math.md](../15-system-design/napkin-math.md).
3. **API first, then data model, then architecture.** Not boxes first.
4. **Name the trade-off at every decision, and give the alternative you rejected and why.** The one
   substantive community answer to a reported Lyft design question says exactly this: *"most importantly
   show the pro and con of your design. Provide more than one design consideration."*
5. **Go deep where they push.** Expect NoSQL depth specifically — partitioning, consistency, hot keys.
6. **Cover failure modes and operations.** What breaks, what alerts, what the on-call sees. This is where
   Staff separates from Senior and where [section 19](../19-observability-and-oncall/) pays off.

### The bar, verbatim from an interviewer explaining a rejection

> *"Having a full working design is not the same as having a good design. Answering all questions the
> interviewer has does not mean that you gave satisfactory answers."*

Read that as: completeness is not the target, judgement is. A smaller design with sharp reasoning beats a
larger one recited.

### Free credibility — know Lyft's own architecture

Envoy service mesh with a sidecar per app server, which Lyft built and donated to CNCF. Protocol Buffers
between services. Redis Cluster with sorted sets keyed by timestamp and ~30s expiry for active driver
discovery. **Google S2 hierarchical geohashing at level 5, chosen deliberately to avoid hot shards.**
DynamoDB for serialised map data and agent state. Rate limiting at both edge and service-mesh layers.

Saying *"I would shard by S2 cell rather than raw geohash to avoid hot cells"* in a Lyft design round is
exactly the experience-grounded instinct that reads as Staff. Details in
[../15-system-design/lyft-architecture.md](../15-system-design/lyft-architecture.md).

### Most likely prompts, ranked

1. Real-time chat with delivery guarantees — two verbatim 2026 reports, and it fits the support domain.
2. Support case routing — inference, but the most on-domain design for this team.
3. Distributed web crawler — two reports including Kyiv 2022.
4. Driver–rider matching with live location indexing.
5. Demand heatmap / surge — verbatim reported.
6. A web app with many third-party dependencies with varied failure modes — verbatim reported, and the
   best fit for an "integration platform" team.

---

## 6 · Behavioural (45 min)

**Breadth, not depth.** A June 2026 report: *"behavioral has bunch of questions instead of talking about
one specific project."* Prepare many short stories, not three long ones. Expect heavy follow-ups on each.

**Lyft has exactly three values: Be yourself · Uplift others · Make it happen.** Ignore any guide citing
Amazon-style leadership principles for Lyft.

**Attach a number to every story.** *"How did you measure?"* appears verbatim in a transcribed round, and
it is the exact axis on which Senior stories get downlevelled. See
[../19-observability-and-oncall/staff-scope-stories.md](../19-observability-and-oncall/staff-scope-stories.md).

**At Staff, the protagonist is the organisation.** "I built a large system" is a Senior story. "I changed
how three teams build systems, and here is the metric" is a Staff story. This is the single most common
way strong candidates get downlevelled.

In Kyiv in 2022 this round was run by a product manager rather than an engineer. At Staff, expect a bar
raiser. Full question bank in
[../22-behavioral-and-staff-scope/lyft-values-and-questions.md](../22-behavioral-and-staff-scope/lyft-values-and-questions.md).

---

## 7 · The question that will make you memorable

Lyft published an honest account of a hard problem: their offline agent simulator showed **90% pass rates
while production revealed a distribution shift** — off-the-shelf LLM user simulators behave like nice,
helpful assistants, while real Lyft users send brief, impatient messages. They fixed it by fine-tuning
simulators on real customer verbatims.

Asking about this proves you read their engineering output and that you think about evaluation realism.
Almost no other candidate will do it. Background in
[../20-llm-agent-systems/lyft-scc-case-study.md](../20-llm-agent-systems/lyft-scc-case-study.md).

---

## 8 · After

Timeline is 4–6 weeks end to end, with a 5–21 day gap after the onsite while the hiring committee meets.
**Lyft is more likely to ghost on rejections than on offers, so silence is not necessarily a no — follow up.**

If the offer comes in at Senior rather than Staff, note that internal T5 → T6 is quoted at 3–5 years.
Negotiate level at offer rather than planning to prove it later.

---

## Interview questions

**1. How do you open a design round?**
Clarify users, scale, read/write ratio, latency target and explicit non-goals, write them down, then do the
napkin math out loud before drawing anything. Only then API, data model, architecture.

**2. What do you do in the first 15 minutes of the laptop round?**
Settle the I/O channel and format, find out how many parts there are, read the provided test cases, and
confirm scope. Then clone the harness. Coding starts after that, not before.

**3. You are 20 minutes from the end with part 2 half-written. What do you do?**
Stop adding functionality. Make part 1 unambiguously correct and clean, comment what part 2 would do and
how, write the README, then demo. Readable working code beats broken complete code at 45/35/20.

**4. The interviewer says your design is fine but does not seem satisfied. What is happening?**
Probably completeness without judgement. Go back and state trade-offs explicitly, name the alternative you
rejected and why, and cover failure modes and operational behaviour. That is the gap between a working
design and a good one.

**5. How do you answer "tell me about a project you're proud of" at Staff level?**
Make the organisation the protagonist and attach a measured outcome. Not "I built X" but "our teams kept
hitting Y, I changed Z across three of them, and here is the number that moved."
