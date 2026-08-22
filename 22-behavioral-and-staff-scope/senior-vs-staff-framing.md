# Senior vs Staff Framing — The Downlevelling File

> **Priority:** Required
> **Est. time:** 90 min
> **Track:** Both
> **HelloInterview:** Behavioral — Adapting to Big Tech; The Big Three Questions

This is the file that decides T5 or T6. Everything else in section 22 feeds it.

The problem, stated plainly: **thirteen years, real breadth, long tenures — and stories about systems
you personally built.** That is a strong Senior profile. At Staff the protagonist of the story is the
organisation, and you are the person who changed its direction. Same events, different protagonist.

---

## 1 · Why the framing carries the whole decision

| Mechanism | Consequence for you |
|-----------|---------------------|
| Level is set by a **hiring committee** reading written interviewer feedback, not by the people who liked you in the room | Your stories are re-told second-hand by someone who was not there. Whatever scope signal did not survive into the interviewer's notes does not exist. Make the scope claim explicit enough to be transcribed. |
| Lyft runs a **lagging-promotion model** — internal promotion follows demonstrated operation at the level | External candidates are levelled the same way: on evidence you have *already* been operating at Staff, not on potential. "I'm ready to step up" is a Senior answer. |
| Behavioural round is often the **only** round that carries organisational evidence | The technical rounds establish that you can build. Nothing else in the loop can establish that you change how a group of teams works. If it is not in the behavioural round, it is not in the packet. |
| A **bar raiser** is typically added at Staff | Their explicit brief is to test level rather than fit. They probe the organisational half of every story hardest. |

The asymmetry that matters: a Staff-scope story that is technically modest still reads Staff.
A technically brilliant story with one human in it reads Senior. Depth is not the axis being measured.

---

## 2 · The five dimensions that separate T5 from T6

| Dimension | Senior (T5) | Staff (T6) |
|-----------|-------------|------------|
| **Blast radius** | One service, one team | Several teams, a platform, or a policy everyone follows |
| **Origin of work** | Assigned, then executed well | Identified by you, then made into someone's roadmap |
| **Durability** | The system works | The standard survived you leaving |
| **Humans** | You unblocked yourself | Named people changed what they do |
| **Cost** | Delivered on time | You said no to something specific, and paid for it |

Every story in [story-bank.md](story-bank.md) should be checkable against all five. Three out of five
is usually enough; zero out of five is a Senior story regardless of the technology in it.

---

## 3 · Same story, two scopes

Below, the left column is the natural telling — accurate, competent, and levelled at Senior. The
right column is the same events with the organisation as protagonist. These are **shape examples**,
not your history: fill them with your own facts from the bank.

### 3.1 A migration

| | |
|---|---|
| **Senior** | "I migrated our billing service off the legacy queue onto Kafka. I designed the topic layout, wrote the consumers, and ran the cutover over a weekend. Zero data loss." |
| **Staff** | "Four teams were each building their own retry logic on top of the legacy queue, and two of them had already shipped subtly different at-least-once semantics. I wrote up the failure modes, took it to the platform group, and got the migration onto their quarter instead of ours. I did the billing service first as the reference implementation and then reviewed the other three teams' cutovers. The delivery-semantics decision is still the default in the service template two years later. It cost us a quarter of feature work, which I argued for explicitly with the product lead." |

The technical content is identical. What changed: the problem is now organisational (four teams,
divergent semantics), the work was *created* rather than assigned, other teams appear by name-of-role,
the artefact outlived the project, and there is a stated cost.

### 3.2 An incident

| | |
|---|---|
| **Senior** | "We had an outage when the cache filled up. I found it from the alert, rolled back the deploy, and added a memory guard plus an alert on eviction rate. It hasn't recurred." |
| **Staff** | "The outage was a symptom: three services had each been given a cache with no eviction policy because our service template didn't have one. I ran the review, and instead of closing it on the one service I proposed we treat the template as the fix. That was unpopular — it meant two other teams re-deploying for a problem they hadn't hit yet. I took the argument to the weekly architecture forum with the eviction-rate data from all three, and we changed the template and backfilled. MTTR on that class went from about 40 minutes to under 10 because the alert now exists everywhere by default." |

The move: from *this incident* to *this class of incident*, from your service to the template
everyone inherits, and through a forum rather than a pull request.

### 3.3 A disagreement with a peer

| | |
|---|---|
| **Senior** | "A colleague wanted to use a document store; I thought a relational schema fit better. I built a prototype showing the query patterns we actually had, and he agreed." |
| **Staff** | "A colleague wanted a document store and I wanted relational. We were about to make that decision twice more in the same quarter on two other services, so I stopped arguing about this one and proposed we write down the choice criteria — access patterns, consistency needs, operational load — as a one-page decision guide. Building it changed my own position on his service: his access pattern genuinely was document-shaped and we shipped his design. The guide got used for the next two decisions without me in the room. What I gave up was being right on the original argument, which was the correct trade." |

The move: from winning an argument to removing the argument, and conceding the specific case.
Note the reversal — Staff stories are more credible when you lose something.

### 3.4 Mentoring

| | |
|---|---|
| **Senior** | "I mentored a junior on our team. We paired twice a week for a few months and he got a lot more confident with the codebase. He's doing well now." |
| **Staff** | "We were onboarding four people in one quarter and every one of them was consuming a different senior engineer ad hoc, which was invisible and unevenly good. I took one of them myself, wrote down what I actually did with him week by week, and turned it into a four-week onboarding path with a first-PR target and a named buddy. Eleven people have gone through it since. The person I took now runs the payments on-call rotation and reviews the same onboarding docs. The unglamorous part is that I had to get two other seniors to stop doing it their own way." |

The move: from one relationship to a mechanism, with a count of people through it and evidence the
mentee now operates independently. The friction line ("stop doing it their own way") is what makes it
credible.

### 3.5 A bad technical decision

| | |
|---|---|
| **Senior** | "I chose an event-sourced model for a service that didn't need it. The complexity slowed us down and eventually we simplified it. I learned to match the pattern to the problem." |
| **Staff** | "I pushed event sourcing as the house pattern after it worked well on the origination platform. Two teams adopted it on my recommendation, and on one of them it was clearly wrong — a low-volume CRUD service that got a projection pipeline it did not need. That cost them roughly a quarter. I called it in the architecture forum rather than letting it quietly rot, wrote the criteria for when the pattern earns its complexity, and helped them unwind it. The lasting change is that we stopped recommending patterns and started recommending criteria. I am much slower now to generalise from one success." |

The move: the blast radius of the mistake is organisational, you retracted it publicly, and the
correction became a standard. A Staff-level failure story is *larger*, not safer.

### 3.6 A cross-team dependency

| | |
|---|---|
| **Senior** | "We were blocked on the identity team's API for six weeks. I escalated to my manager, and meanwhile built a temporary stub so we could keep going." |
| **Staff** | "We were blocked on identity, and when I looked into it they were blocked too — they had three teams asking for variations of the same endpoint and no way to prioritise. I went and sat with their tech lead, and we found that two of the three requests collapsed into one shape. I wrote the joint spec, gave up the field we wanted most because it was the expensive one, and their team shipped one endpoint instead of three. The stub we'd built got deleted. The part I'd do differently is that I waited five weeks to go and ask why — I treated it as their queue problem for far too long." |

The move: diagnosing the other team's constraint instead of escalating, absorbing cost to unblock a
shared path, and an honest self-criticism about latency to act.

### 3.7 A roadmap trade-off

| | |
|---|---|
| **Senior** | "We had to choose between adding the reporting feature and paying down test-suite flakiness. I made the case for the tests, and we did those first." |
| **Staff** | "Our test suite was at about 8% flake and three teams shared it, so every one of them was paying a tax they'd stopped noticing. I costed it — roughly 40 engineer-hours a week across the three teams in re-runs and false triage — and took that number to the three leads and the PM rather than to my own manager. We agreed to defer the reporting feature by six weeks, which was a real commitment to a customer and I was in the room when we told them. Flake went to under 1% and we put a hard gate in CI so it couldn't drift back. Reporting shipped late and that was my call to defend." |

The move: quantified organisational tax, the decision taken to the group that owned it rather than
upward, an explicit cost paid in front of a customer, and a mechanism that prevents regression.

---

## 4 · The tells that get you downlevelled

Interviewers rarely think "this is a Senior candidate" as a conclusion. They notice patterns and the
level falls out of the write-up. These are the patterns.

### 4.1 "I built"

The single most common tell. Thirteen years of building produces a vocabulary of construction:
*I built, I designed, I wrote, I implemented, I refactored.* All accurate. All Senior.

| Verb you reach for | Verb that carries scope |
|--------------------|-------------------------|
| I built / I implemented | I decided / I proposed / I got it onto the roadmap |
| I fixed | I stopped it recurring across the fleet |
| I designed the schema | I set the schema standard the other teams adopted |
| I did the migration | I sequenced the migration across four teams |
| I helped out | I unblocked / I reviewed / I reversed my position |

Caveat: do not overcorrect into pure management language. A Staff engineer still has hands on the
system, and an answer with no technical substance fails a different way — it reads as a manager
applying for an IC role. The target is **decision verbs wrapped around real technical detail**.

### 4.2 No other humans in the story

If you can tell the whole story without naming another role — a PM, a tech lead, a peer who
disagreed, the person who inherited it — the story has one participant and it is not an
organisational story. Test every slot in the bank: **how many humans appear, and does at least one of
them disagree with you?**

Related tell: humans appear only as beneficiaries ("the team was happy", "it helped everyone"). They
must appear as agents — people who changed what they do, or who pushed back.

### 4.3 No organisational consequence

The story ends when the system works. At Staff it should end at one of:

- another team adopted it,
- a standard, template or process changed,
- a decision that would otherwise recur got settled,
- someone's roadmap changed,
- a person's scope grew.

If none of those is true, ask whether the story is the right one for a Staff round at all. Some are
not — keep them for technical rounds and pick a different bank slot here.

### 4.4 No measurement

"It was much faster" is a Senior answer. "How did you measure?" is asked verbatim at Lyft. Absence of
numbers reads two ways, both bad: either the impact was not real, or you were not close enough to the
business to know. See [metrics-for-stories.md](metrics-for-stories.md), including how to state an
estimate honestly when the exact figure is gone.

### 4.5 No trade-off that cost something

Every Staff story should contain a sentence beginning roughly *"which cost..."* or *"what we gave up
was..."*. Reasons:

- Decisions without cost are not decisions, they are preferences.
- Staff engineers are trusted to spend other people's time. Evidence you have spent it deliberately
  is exactly what the level is about.
- It is the fastest available proof against rehearsal, satisfying **Be yourself** at the same time.

Costs that count: a feature deferred, a quarter spent, a customer commitment moved, a person's
preferred design overruled, your own position abandoned, technical debt taken on knowingly.

### 4.6 Quick diagnostic

Read a story back and count:

| Check | Fail signal |
|-------|-------------|
| Verbs of decision vs verbs of construction | Construction verbs outnumber decision verbs |
| Number of humans with agency | Fewer than two |
| Teams affected | One |
| Numbers present | Zero |
| Explicit cost | Absent |
| Lifetime after you | Not mentioned |

Four or more fail signals and the story will be written up as Senior.

---

## 5 · The rewrite drill

For each of the twelve slots in [story-bank.md](story-bank.md), do this once, on paper:

1. Write the story the way you would naturally tell it. Do not sanitise it.
2. Underline every first-person verb. Count construction vs decision.
3. List every human in it. If fewer than two, find the ones you edited out — they existed.
4. Answer in one line: **what did the organisation do differently afterwards?** If you cannot, the
   story needs a different frame or a different slot.
5. Add the number and the instrument that produced it.
6. Add the cost sentence.
7. Re-compress to 90 seconds using [carl-and-star.md](carl-and-star.md) section 3.

Steps 3, 4 and 6 are the ones that actually move the level. Steps 1-2 are diagnosis.

---

## 6 · Two honesty constraints

This file is about framing, not inflation. Two hard limits:

- **Do not claim scope you did not have.** Lyft's follow-up drilling is deep, and a fabricated
  cross-team story dies on the second probe ("who was the tech lead on the other team?"). The
  reframe works because the organisational content was genuinely there and you were leaving it out —
  not because you are adding it.
- **Do not erase your collaborators.** Overclaiming is a worse failure than underclaiming at Staff;
  it fails **Uplift others** directly. The Staff telling names more people than the Senior telling,
  not fewer.

The honest version of this file's thesis: you have been operating at more than one-service scope for
years, and describing it at one-service scope. Fix the description.

---

## Interview questions

**1. Recent project you're proud of. What was your role? What was impact? How did you measure?** **[Reported at Lyft]**
Pick the story with the widest blast radius, not the most technically interesting one. State the
organisational problem first, your decision second, the code third. Answer "role" with the decision
you owned plus what your collaborators owned by name-of-role. Close on the standard or system that
outlived the project.

**2. Tell me about a failure.** **[Reported at Lyft]**
At Staff, choose a failure whose blast radius was organisational — advice you gave that other teams
followed, a standard you set that was wrong. Retract it explicitly, say what it cost the other teams,
and name the criteria you replaced it with.

**3. Did you convince your colleague about your solution, and how?** **[Reported at Lyft]**
Better answer: describe how you removed the need to have the argument again — a decision guide, a
benchmark, a written criteria doc — and name the case where you conceded. Winning is a Senior
outcome; settling the class of decision is a Staff outcome.

**4. What experience do you have with mentoring and creating systems?** **[Reported at Lyft]**
Answer the "creating systems" half deliberately. One person you mentored, with what they now own, and
one mechanism — onboarding path, rotation, review standard — with a count of people through it and
who runs it now that you do not.

**5. How do you manage a difficult partnership?** **[Reported at Lyft]**
Lead with the other team's constraint rather than their behaviour. Describe what you changed first,
what you gave up to collapse the conflict, and the working agreement that replaced the friction.
Escalation should appear as a deliberate, announced step, not a complaint.

**6. What's the largest scope of technical decision you've owned?**
Answer with the decision's reach, not its difficulty: how many teams inherited it, how long it held,
who could have overruled you. Include the one you got wrong at that scope — a candidate who has only
made correct large decisions has not made many.

**7. How do you set technical direction for people who don't report to you?**
Name the mechanism you actually use: written criteria, reference implementation, an architecture
forum, a service template. Then a concrete instance where it worked and one where it did not, and
what you did when someone simply disagreed and shipped their own way.

**8. Tell me about a time you decided not to do something.**
A direct Staff probe. Use the roadmap trade-off slot: the quantified tax, who you took it to, the
commitment that moved, and how you defended it afterwards. The cost must be specific and someone
must have been unhappy.

**9. What would the engineers around you say changed after you joined?**
This is the lagging-promotion question in disguise. Answer with durable artefacts — a template, a
rotation, a review standard, a class of incident that stopped — and be able to say who owns each one
now.
