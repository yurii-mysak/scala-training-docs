# Interview Program — Lyft Staff SWE, Global Support & Partnerships

> **Priority:** Required
> **Est. time:** 20 min to read
> **Track:** Both
> **HelloInterview:** none

Start here. This section is the program; sections 01–23 are the material it draws on.

The repo was originally a Scala interview knowledge base. Sections **17–23** and the extensions to
**09, 14 and 15** were written for one specific loop, from researched evidence about how that loop
actually runs — not from generic interview advice.

---

## 1 · The five files in this section

| File | What it is |
|---|---|
| [curriculum.md](curriculum.md) | Every document in the repo, tagged Required / Recommended / Optional with time estimates. **The full programme.** |
| [interview-playbook.md](interview-playbook.md) | How each round runs and how to behave in it, on the day. |
| [evidence.md](evidence.md) | The reported question bank, with what is verbatim and what is inference. |
| [hellointerview-map.md](hellointerview-map.md) | What to use your HelloInterview account for, mapped lesson by lesson. |
| [tracker.md](tracker.md) | A checkable progress tracker with three suggested paths. |

Plus [build_curriculum.py](build_curriculum.py), which regenerates the curriculum index from file
front-matter so it never drifts.

---

## 2 · Read the front-matter

Every document written for this program carries a block directly under its title:

```
> **Priority:** Required
> **Est. time:** 60 min
> **Track:** Server
> **HelloInterview:** System Design in a Hurry → Common Patterns → Real-time Updates
```

- **Required** — you cannot reasonably pass this loop without it.
- **Recommended** — materially raises the odds.
- **Optional** — nice to have, or only relevant if the role turns out to include Web.
- **Track** — `Server` applies always. `Server + Web` applies only if the role is confirmed as the
  full-stack variant; the recruiter's message said *"Server або Server + Web"*, so this is genuinely
  undecided. Ask before spending time on section 23.

Current totals: **86 tagged documents. Required only ≈ 44 h. Everything ≈ 63 h.** Existing repo material
adds roughly 24 h more. The programme is deliberately larger than any one person needs — pick from it.

---

## 3 · What this loop actually tests

Read this before choosing what to study, because it is what makes the priorities defensible.

**The loop.** Recruiter screen → 60-min CoderPad technical screen (gatekeeping — fail it and you are out)
→ **90-min laptop round in your own IDE** → **two design/architecture rounds** → 45-min behavioural,
sometimes a bar raiser → sometimes a domain-expertise round. You need roughly 3 of 4 technical rounds.

**Design carries the most weight.** Two design rounds against one coding round. If you have limited time,
sections 15 and 19 beat section 09.

**The laptop round is graded 45% correctness, 35% clean code, 20% performance.** Readable working code
beats complete-but-ugly. One offer recipient did not finish and passed anyway, on the strength of
comments and organisation.

**Candidates fail the laptop round on input/output handling, not algorithms.** This is the most
actionable single fact in the whole research, and it is why [section 18](../18-io-harness/) exists as a
runnable project rather than a document.

**The design round is not a FAANG design round.** It contains real coding, code review, library choices
and testing strategy. Named probes: NoSQL depth, and live napkin math on memory and CPU.

**Lyft's problem pool is narrow.** Seven recurring laptop families, all in [section 17](../17-lyft-laptop-round/).
Depth on those beats breadth across 300 LeetCode problems.

---

## 4 · The shape of a sensible six weeks

Three paths are laid out in [tracker.md](tracker.md). The default one:

| Week | Focus | Sections |
|---|---|---|
| 0 | Email the recruiter. Rewrite the CV. Set up the harness. | [18](../18-io-harness/), [22](../22-behavioral-and-staff-scope/transition-narrative.md) |
| 1 | Python muscle memory + the I/O harness until it is automatic | [21](../21-python-for-interviews/), [18](../18-io-harness/) |
| 2 | The seven laptop families, timed, multi-part | [17](../17-lyft-laptop-round/), [09/lyft](../09-coding-challenges/lyft/) |
| 3 | Design: chat first, then routing, crawler, geo | [15](../15-system-design/) |
| 4 | Behavioural, story bank, metrics for every story | [22](../22-behavioral-and-staff-scope/) |
| 5 | Observability, Kubernetes, LLM agent systems | [19](../19-observability-and-oncall/), [14](../14-cloud-and-infrastructure/), [20](../20-llm-agent-systems/) |
| 6 | Two full mock loops, then re-drill what broke | all |

Week 0 is not padding. The CV rewrite is the highest-priority item in the whole programme, because the
current one ends in April 2025 and omits the LotusFlare role entirely.

---

## 5 · Three things to do before studying anything

1. **Ask the recruiter which req you are being submitted to.** The PDF (Safety & Customer Care) and the
   DOU posting (Global Support & Partnerships) are different documents with different requirements. One
   says "lead a team of engineers"; the other says "serve as a dependable, high-bar interviewer."
2. **Ask for the example laptop problems.** They exist — a candidate confirmed being given them. Free,
   and worth more than any single document here.
3. **Confirm Server vs Server + Web.** It decides whether [section 23](../23-web-and-frontend/) is 7 hours
   of your life or zero.

Full list in [../22-behavioral-and-staff-scope/questions-to-ask-them.md](../22-behavioral-and-staff-scope/questions-to-ask-them.md).

---

## 6 · Honest limits of this material

- **No T6-specific loop description exists publicly.** Exactly one Staff-level report was found. The Staff
  loop shape here is inferred from Senior reports plus that single data point.
- **The 3-of-4 pass rule** comes from one Kyiv report and is corroborated only loosely. Treat as likely.
- **The AI-assistant policy for the laptop round is unknown for 2026.** The last confirmed statement is
  from 2023. Ask.
- **Reddit was inaccessible during research**, and 一亩三分地 thread bodies are paywalled. Both are real
  gaps in the corpus, not evidence of absence.
- **A Python guide shared by a friend could not be read** — the Evernote link is login-gated. If it turns
  out to contain material this programme lacks, section 21 is where it belongs.
- Priorities skew heavy on Required (56 of 86). That is a deliberate choice for a single named loop, but
  it means "Required" here is closer to "clearly relevant" than to "absolutely non-negotiable."

---

## Interview questions

This file is the programme index rather than a topic. The reported question bank is in
[evidence.md](evidence.md); per-round behaviour is in [interview-playbook.md](interview-playbook.md).
