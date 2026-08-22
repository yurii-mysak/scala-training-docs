# Evidence — the reported question bank, and how much to trust it

> **Priority:** Required
> **Est. time:** 30 min
> **Track:** Both
> **HelloInterview:** none

Everything below comes from first-hand candidate reports: Glassdoor, Blind, Taro, LeetCode Discuss, the
Ukrainian DOU forum, and 一亩三分地. Aggregator sites that fabricate plausible-sounding questions were
discarded — see §7 for which and why.

**Notation:** `[V]` verbatim as the candidate wrote it. `[P]` paraphrased from a first-hand report.
`[INF]` inference, clearly labelled as such.

---

## 1 · The loop

`[P]` Senior/Staff, 2026: recruiter screen 30 min → technical phone screen 60 min on CoderPad, gatekeeping
→ laptop coding 90 min → design/architecture 60 min → second design or domain-expertise round 60 min →
experience/behavioural 45 min, sometimes a bar raiser.

`[V]` Blind, 8 YOE candidate: *"1 coding round (1.5 hours), 2 design rounds (1 hour each), and 1 behavioral
round (45 minutes)"* — coding described as *"Not leetcode."*

`[V]` Blind, on variation: *"It can be different depending on the level and position… Different orgs have
different interview formats for SWE… even within LOBs there is a lot of nuance."*

`[P]` The only Staff-level report found anywhere (Apr 2026, **accepted offer**, difficulty rated
"Average"): technical screen was *"one of the most commonly asked hard leetcode questions… on the blind57
list"*; onsite was laptop coding with test cases, system design, a **bar-raiser** behavioural, and a
**domain-knowledge round** on cloud security.

`[V]` Kyiv, Aug 2022, six stages: intro 30 min → live coding 60 min (*batch reading from a file*) → laptop
90 min (*word analyzer, T9*) → CS fundamentals 60 min (*LC 76 with minor adjustments*) → system design 60
min (*"a malware software that copies the whole Wikipedia"*) → behavioural 45 min **with a product
manager**. Scoring rule `[V]`: *"must pass at least 3 out of 4 to get the offer."* The live-coding round is
gatekeeping — fail it and you are out.

`[INF]` The 3-of-4 rule appears in one report and is only loosely corroborated. Treat as likely, not certain.

---

## 2 · The laptop round

`[V]` *"15 minutes for question review/approach discussion, approximately 60 minutes for coding, and
remaining time for submission and follow-up questions, totaling around 90 minutes."*

`[V]` Interviewer present but *"video/audio off, no screen sharing."*

`[P]` You work in your own environment, they provide the problem statement and test cases, you demo and
**submit a zip by email**.

`[P]` Grading: **correctness 45% / clean code 35% / performance 20%.** Appears in two independent places —
a US interview guide, and a Ukrainian DOU forum thread where Kyiv candidates discuss the loop in Russian.
Two unrelated communities quoting the same numbers implies Lyft communicates them.

`[V]` *"Reading stuff from input, doing some processing, and writing to output. Can be somewhat
leetcodeish, but not intended to be typical leetcode."*

`[V]` *"It will be around building a small app with data structure implementation to support the
functionality requested."* — explicitly do not use Spring or Jersey.

`[V]` *"be ready to code very fast. I'd say you should be able to finish the example laptop interviews they
give you in 20 minutes or less if you hope to finish the real one. It's open book, but you don't have time
to look anything up (besides simple documentation)."* — **confirms Lyft sends example problems in advance.**

`[V]` June 2026, SF Senior: *"the laptop round is basically OOD."* Same report: *"you may or may not meet
the manager of the team you are interviewing for during the onsite behavioral."*

`[V]` *"Legacy name as it was done on the laptop when other companies still used a white board."*

### The I/O trap — the dominant failure mode

`[V]` *"It is usually a LC-Hard problem with some changes. The best advice I can give is to prepare some
functions to read and write in STDIN and STDOUT, files and console, this will save you a lot of time and
will let you focus on solving the actual problem."*

`[V]` *"you can not write your code to accept input from a file… you have to stick to whatever they expect"*

`[V]` *"input handling was tricky — they couldn't use file input and had to follow the expected stdin
format precisely."*

`[INF]` Note the contradiction between the first and second quotes: **the expected channel varies by
problem.** Have both ready and confirm which in the first 15 minutes.

### Multi-part structure

`[V]` A candidate who finished part 1 including stdin/stdout but ran out of time on part 2 (transactions)
was told: *"We expect that part to be covered. Only thing that can save is strong yes from one of the
other rounds."*

`[P]` An offer recipient who **did not finish all tasks** attributed passing to having *"commented my code
and organized your solution well."*

### Problem families, by independent report count

| Family | Reports | Representative wording |
|---|---|---|
| Stateful paginated fetch / read-N (LC 158) | **7** (3 in 2025) | `[V]` *"Implement wrapper handling N API calls returning M results with exception handling"*; `[V]` *"GetPage API implementation returning integer lists and next-page tokens"*; `[V]` *"They asked me to program a solution to resolve the issue with pagination"* |
| Versioned / temporal KV store (LC 981) | **6** | `[V]` *"Versioned Key-Value Store… If the version does not exist, return the latest that is smaller than the given version."* |
| Trie typeahead / autocomplete / T9 | **5** | `[V]` *"Code autocomplete (type a word, comes up with suggestions)"*; `[V]` Kyiv: *"Word analyzer (T9)"* |
| In-memory KV with begin/commit/rollback | **4** (2026) | `[V]` *"a KV in-memory database problem requiring support for rollback/commit/begin transaction"* |
| Job scheduler / interval→worker (LC 253, 1094) | **4** (2026) | `[V]` *"Job scheduler with workers: Use SortedSet/SortedDictionary. it is not hard, but need to deal with standard inputs."* |
| File / log / CSV parsing | **4** | `[V]` *"Print the K-th non-empty line of a large UTF-8 file without loading it into memory"* |
| Nested / hierarchical dot-path KV | 2 | `set(path, value)` / `get` / `delete` with auto-created intermediates |
| LRU variants | 2 | `[V]` *"Implement LRU cache but the backing data structure is an Arraylist"* |

`[V]` One-offs, single report each: Max Stack (LC 716) · union-find with same-set queries · DAG
linearisation · iterator design pattern over sorted arrays · grid/BFS spread · *"implement class with
attack method; game over when health reaches zero"* · *"match shopping list items with promotion codes"*.

`[P]` Languages candidates reported using: **Go** (Toronto Sep 2025 — ran out of time hand-rolling a heap;
the interviewer *"was unaware of Go's standard library limitations"*), **C#** (2016, got the offer),
Python and Java implied elsewhere. `[V]` *"VSCode or similar IDE, no package/library restrictions."*

---

## 3 · Coding screen and CS fundamentals

`[INF]` **LC 76 Minimum Window Substring is Lyft's single most-repeated problem** — four independent
reports across 2022–2026 and three continents.

| Problem | LC | Context |
|---|---|---|
| Minimum Window Substring | 76 | `[V]` Kyiv Aug 2022 *"with minor adjustments"* (CS fundamentals slot); `[V]` CDMX Jun 2026 Senior, and *"esta protectorado con un humano"* — **human-proctored**; `[P]` 2026 Senior, passed; `[V]` Jul 2026 *"Find the smallest window in a string containing all target characters"* |
| Find the median in a sliding window | 480 | `[V]` Oct 2025 Toronto. Told to expect *"medium LeetCode questions"*, got this Hard, no offer |
| Asteroid Collision | 735 | `[V]` *"with follow-up variations"*; top of the Lyft-tagged frequency list |
| Water and Jug Problem | 365 | `[V]` noted specifically as a **staff-level** phone screen |
| Word Ladder — BFS | 127 | `[V]` SF Senior SWE |
| Binary tree iterator | 173 | `[V]` SF Senior SWE |
| Implement pagination on an API endpoint | — | `[V]` SF Senior SWE |
| Product of Array Except Self | 238 | Top of the Lyft-tagged frequency list |
| — | — | `[V]` *"HashMap and state management related question"*, Jul 2026, Difficult, no offer |
| — | — | `[V]` *"One question - leetcode hard with a slight variation. Second one - implement methods in a class"* + *"you need be super fluent with coding to complete the code in 60 min."* |

`[P]` **Byteboard is still in use** for interns and some full-time reqs as of Feb 2026 (Mexico City) — part
1 is reading a design document and adding comments, part 2 is implementing a related program. Unlikely in
a Staff loop, but recognise the name.

---

## 4 · System design

| Prompt | Evidence |
|---|---|
| *"Design a scalable real-time chat system with delivery guarantees"* | `[V]` Jul 2026 |
| *"Design 1:1 chat, system design"* | `[V]` Jul 2026, Difficult. `[V]` *"Time passed too quickly if you're new to it"* |
| *"Design whatsapp like service"* | `[V]` |
| *"Design a malware software that copies the whole Wikipedia"* | `[V]` Kyiv Aug 2022. `[INF]` a crawler, framed adversarially |
| Web crawler | `[P]` *"API design, data schema, HTML parsing, real-time considerations. Interviewer wanted trade-offs rather than a complete solution"* |
| *"How would you design a feature that tells Lyft drivers where in the city has highest demand, and therefore higher fares?"* | `[V]`. Community answer `[V]`: *"Broken into server API design and client architecture. Most importantly show the pro and con of your design. Provide more than one design consideration."* |
| *"How would you design at ETA system for Lyft drivers?"* | `[V]` |
| *"Design the system for text completion"* | `[V]` Kyiv, MLE, Nov 2021, Difficult |
| *"Design bit.ly"* / TinyURL | `[V]` recurring |
| *"Design Twitter — REST APIs, data models, tweets, follows, news feeds"* | `[V]` |
| Donation platform with exactly-once payment guarantees | `[V]` recurring |
| *"Idempotency Key in Systems — request deduplication"* | `[V]` |
| *"a web application that has a lot of 3rd party dependencies that have a variety of failure modes"* | `[V]` T4 loop |

### Probes and the bar

`[V]` *"emphasis on NoSQL concepts"* plus *"light napkin math about how much memory/CPU is needed"* — two
independent sources.

`[P]` The design round *"incorporates significant coding implementation aspects,"* includes code review,
covers production concerns, and emphasises *"library preferences and testing strategies"* while
de-emphasising abstract problem solving. Candidates from research backgrounds reportedly struggle with the
production focus.

`[V]` An interviewer explaining a rejection: *"having a full working design is not the same as having a
good design. Answering all questions the interviewer has does not mean that you gave satisfactory
answers."*

`[V]` *"Questions scaled to billions of users."* `[V]` *"Interviewer emphasized 'attention to detail'."*

---

## 5 · Behavioural

`[V]` One whole round transcribed, Jul 2026: *"Recent project you're proud of, What was your role?, What
was impact?, **How did you measure?**, Tell me about failure, Did you convince your colleague about your
solution and how?, What's inclusion for you"*

| Question | Evidence |
|---|---|
| *"Tell me about how you handled a production bug you caused."* | `[V]` Sep 2025 |
| *"What experience do you have with mentoring and creating systems?"* | `[V]` Sep 2025, Senior |
| *"Tell me some experience related to ML or Gen AI"* | `[V]` Oct 2025 — a newer theme |
| *"Why did you choose Lyft? Your project-related experience. You cross-functional experience"* | `[V]` |
| *"How do you manage a difficult partnership?"* | `[V]` |
| *"Time you failed at something"* / *"The project that is the most challenging"* | `[V]` |
| *"How would you go about fixing x mistake?"* | `[V]` |

`[V]` Format signal, Jun 2026 Senior: *"behavioral has bunch of questions instead of talking about one
specific projects"* — **breadth over depth.** `[V]` *"Lots of follow ups for each answer."*

`[P]` Kyiv 2022: the 45-min behavioural was run by a **product manager**, covering past experience, tasks,
technologies, values and soft skills.

Lyft's values: **Be yourself · Uplift others · Make it happen.** Any guide citing Amazon-style leadership
principles for Lyft is aggregator contamination.

---

## 6 · Warning signals worth weighing

`[P]` Taro pass rates by location: Toronto 0% across 9 SWE reports, New York 22% across 9, Kyiv 0% across 3.
`[INF]` Small samples, and rejected candidates self-select into reporting. Not a rate, but not nothing.

`[V]` Sep 2025 Senior: *"This is by far the worst interview experience I have ever had"* — postponed
roughly five times, then a quick rejection. `[V]` *"Hiring manager was from another group"*; `[V]` *"they
weren't truly recruiting for the role."*

`[V]` 2026 T4 who failed: *"Lyft's bar seems quite high."* `[V]` 2026 Senior who passed: *"the interview
quality wasn't very high, with sketchy elements. Multiple team members showed signs of burnout, and the
team morale seemed low"* and *"Lyft's hiring bar may have dropped."*

`[V]` Blind, undated: *"A lot of open roles are being terminated or repurposed at Lyft right now. Not the
best time to interview."* One candidate declined an offer because *"they have significantly reduced TC."*

`[P]` Down-levelling is documented: a Senior Infra candidate received an offer at **T4** and declined over
compensation.

`[P]` Lyft asks permission to contact your current employer for references.

---

## 7 · Sources discarded, and why

Fabricated or generic question lists with no candidate attribution: **prepfully** (its "onsite coding"
list includes *"check whether a string is a palindrome"* — no company asks that at onsite; it also
astroturfs Glassdoor answer sections with ads for its own service), **codinginterview.com**,
**interviewkickstart** (templated: *"Create Lyft for deaf drivers"*), **vervecopilot**.

**interviewquery** is mixed — it correctly names Minimum Window Substring and the real-time chat design,
both independently confirmed, but its 30-item question table is its own generic bank, not Lyft questions.

**prachub** — topics are corroborated by independent first-hand reports, but its problem statements are
AI-elaborated into tidy specs with invented constraints. Use as practice specs; do not quote as reports.

**Exponent** and **techprep** invent nothing and are honest about round structure, but are useless for
questions. **igotanoffer** and **hellointerview** have **no Lyft SWE page at all**, despite search results
suggesting otherwise.

### Gaps in this corpus

Reddit was entirely inaccessible during research (403 on both domains). 一亩三分地 thread bodies are
paywalled — titles, previews and replies produced most of the laptop-round material above, but the detailed
write-ups behind the paywall are almost certainly the richest untapped source. Glassdoor pagination is
blocked by robots.txt, capping direct access at roughly the three most recent reports per filtered view
against a claimed 143–157 total.

---

## Interview questions

**1. How much of this should you believe?**
The multi-source items — the 45/35/20 rubric, the I/O trap, LC 76, the two-design-round shape, the laptop
families with 4+ reports — are solid. Single-report items are directional. Anything marked `[INF]` is
reasoning, not evidence.

**2. What is the single most actionable fact here?**
That candidates fail the laptop round on input/output handling rather than on algorithms. It is cheap to
fix and it is the most common named cause of failure.

**3. What does the evidence say you should prepare least?**
Broad LeetCode grinding. Lyft's pool is narrow and the same families recur across seven years. Depth on
those beats breadth.
