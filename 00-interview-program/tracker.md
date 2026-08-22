# Tracker — three paths and a checklist

> **Priority:** Required
> **Est. time:** 10 min to choose a path
> **Track:** Both
> **HelloInterview:** none

Tick as you go. The full tagged inventory is in [curriculum.md](curriculum.md); this file is about
choosing how much of it to do.

---

## Choose a path

| Path | Time | Covers | Choose it if |
|---|---|---|---|
| **A — Minimum viable** | ~22 h | The gatekeeping risks only | The loop starts in under two weeks |
| **B — Default** | ~44 h | Everything marked Required | You have six weeks at 8–10 h/week |
| **C — Full** | ~87 h | Required + Recommended + relevant legacy | You have ten weeks, or want the material regardless of outcome |

Nothing here assumes the Web track. If the role is confirmed as Server + Web, add ~7 h for
[section 23](../23-web-and-frontend/).

---

## Path A — minimum viable (~22 h)

If you only do this much, do it in this order. It targets the three ways this loop most commonly ends
early: the gatekeeping screen, the I/O trap, and a Senior-shaped behavioural.

- [ ] **Rewrite the CV.** Add LotusFlare. Numbers in every bullet. — [transition-narrative.md](../22-behavioral-and-staff-scope/transition-narrative.md) · 2 h
- [ ] **Email the recruiter** — example problems, which req, level, environment, Server vs Web — [questions-to-ask-them.md](../22-behavioral-and-staff-scope/questions-to-ask-them.md) · 30 min
- [ ] **The I/O harness, until it is automatic** — [18-io-harness](../18-io-harness/) · 3 h
- [ ] **Python speed drills** — [speed-drills.md](../21-python-for-interviews/speed-drills.md) · 3 h
- [ ] **LC 76 Minimum Window Substring** until cold-solvable — [lc76](../09-coding-challenges/lyft/lc76-minimum-window-substring.md) · 1 h
- [ ] **Three laptop families**: paginated fetch, versioned KV, in-memory KV with transactions — [17](../17-lyft-laptop-round/) · 5 h
- [ ] **Laptop-round protocol** — [00-protocol.md](../17-lyft-laptop-round/00-protocol.md) · 30 min
- [ ] **Design round protocol + napkin math** — [design-round-protocol.md](../15-system-design/design-round-protocol.md), [napkin-math.md](../15-system-design/napkin-math.md) · 2 h
- [ ] **Real-time chat with delivery guarantees** — [realtime-chat](../15-system-design/realtime-chat-delivery-guarantees.md) · 1.5 h
- [ ] **Lyft's architecture** — [lyft-architecture.md](../15-system-design/lyft-architecture.md) · 1 h
- [ ] **Story bank + metrics** — [story-bank.md](../22-behavioral-and-staff-scope/story-bank.md), [metrics-for-stories.md](../22-behavioral-and-staff-scope/metrics-for-stories.md) · 2 h
- [ ] **Senior vs Staff framing** — [senior-vs-staff-framing.md](../22-behavioral-and-staff-scope/senior-vs-staff-framing.md) · 1 h
- [ ] **Read the playbook the night before** — [interview-playbook.md](interview-playbook.md) · 40 min

---

## Path B — the default six weeks (~44 h)

Everything marked **Required** in [curriculum.md](curriculum.md), sequenced.

### Week 0 — setup (4 h)
- [ ] Rewrite the CV, add LotusFlare, numbers in every bullet
- [ ] Email the recruiter with all five questions
- [ ] Read [README.md](README.md) and [interview-playbook.md](interview-playbook.md) end to end
- [ ] Skim [evidence.md](evidence.md) so you know what is actually reported
- [ ] Decide your path and block the calendar

### Week 1 — Python and I/O (9 h)
- [ ] [from-lua-and-scala-to-python.md](../21-python-for-interviews/from-lua-and-scala-to-python.md)
- [ ] [stdlib-for-interviews.md](../21-python-for-interviews/stdlib-for-interviews.md)
- [ ] [data-structures-and-idioms.md](../21-python-for-interviews/data-structures-and-idioms.md)
- [ ] [io-and-parsing.md](../21-python-for-interviews/io-and-parsing.md)
- [ ] [testing-with-unittest.md](../21-python-for-interviews/testing-with-unittest.md)
- [ ] [speed-drills.md](../21-python-for-interviews/speed-drills.md) — start; continue all six weeks
- [ ] [18-io-harness](../18-io-harness/) — clone, run, modify, until under three minutes from empty directory
- [ ] HI: Sliding Window (variable), Trie

### Week 2 — the laptop families (10 h)
- [ ] All seven families in [17-lyft-laptop-round](../17-lyft-laptop-round/), each timed at 60 min
- [ ] Each one twice: once cold, once as a clean class with tests
- [ ] Each one with **both** a stdin variant and a file variant
- [ ] Each one **multi-part** — add the harder layer after part 1 works
- [ ] [09-coding-challenges/lyft](../09-coding-challenges/lyft/) — the six evidence-backed LeetCode problems
- [ ] HI: Low-Level Design in a Hurry — framework plus two problems
- [ ] HI: Heap, Intervals, Stack (monotonic)

### Week 3 — design (10 h)
- [ ] [design-round-protocol.md](../15-system-design/design-round-protocol.md) and [napkin-math.md](../15-system-design/napkin-math.md) first
- [ ] [realtime-chat-delivery-guarantees.md](../15-system-design/realtime-chat-delivery-guarantees.md)
- [ ] [support-case-routing.md](../15-system-design/support-case-routing.md)
- [ ] [third-party-failure-modes.md](../15-system-design/third-party-failure-modes.md)
- [ ] [distributed-web-crawler.md](../15-system-design/distributed-web-crawler.md)
- [ ] [driver-location-matching.md](../15-system-design/driver-location-matching.md)
- [ ] [rate-limiter.md](../15-system-design/rate-limiter.md) and [idempotency-and-deduplication.md](../15-system-design/idempotency-and-deduplication.md)
- [ ] [lyft-architecture.md](../15-system-design/lyft-architecture.md)
- [ ] Each design done **out loud, timed at 60 min**, before reading the write-up
- [ ] HI: Delivery Framework, Numbers to Know, Real-time Updates, Dealing with Contention, DynamoDB, Proximity Search

### Week 4 — behavioural (7 h)
- [ ] [lyft-values-and-questions.md](../22-behavioral-and-staff-scope/lyft-values-and-questions.md)
- [ ] [carl-and-star.md](../22-behavioral-and-staff-scope/carl-and-star.md)
- [ ] [story-bank.md](../22-behavioral-and-staff-scope/story-bank.md) — write the stories, many and short
- [ ] [metrics-for-stories.md](../22-behavioral-and-staff-scope/metrics-for-stories.md) — a number on every one
- [ ] [staff-scope-stories.md](../19-observability-and-oncall/staff-scope-stories.md) — mine the DevOps history
- [ ] [senior-vs-staff-framing.md](../22-behavioral-and-staff-scope/senior-vs-staff-framing.md)
- [ ] [ai-and-genai-questions.md](../22-behavioral-and-staff-scope/ai-and-genai-questions.md)
- [ ] [transition-narrative.md](../22-behavioral-and-staff-scope/transition-narrative.md) — the one-year answer
- [ ] HI: CARL, Story Builder, Answering AI Questions

### Week 5 — operations and AI platform (8 h)
- [ ] [slos-and-error-budgets.md](../19-observability-and-oncall/slos-and-error-budgets.md)
- [ ] [metrics-logs-traces.md](../19-observability-and-oncall/metrics-logs-traces.md)
- [ ] [alert-design.md](../19-observability-and-oncall/alert-design.md)
- [ ] [oncall-health.md](../19-observability-and-oncall/oncall-health.md)
- [ ] [kubernetes-core.md](../14-cloud-and-infrastructure/kubernetes-core.md) and [kubernetes-operations.md](../14-cloud-and-infrastructure/kubernetes-operations.md)
- [ ] [docker-and-containers.md](../14-cloud-and-infrastructure/docker-and-containers.md)
- [ ] [service-mesh-and-envoy.md](../14-cloud-and-infrastructure/service-mesh-and-envoy.md)
- [ ] [lyft-scc-case-study.md](../20-llm-agent-systems/lyft-scc-case-study.md)
- [ ] [agent-architectures.md](../20-llm-agent-systems/agent-architectures.md) and [langgraph-patterns.md](../20-llm-agent-systems/langgraph-patterns.md)
- [ ] [evaluating-agents.md](../20-llm-agent-systems/evaluating-agents.md)
- [ ] [ai-dev-tools-adoption.md](../20-llm-agent-systems/ai-dev-tools-adoption.md)

### Week 6 — rehearsal (6 h)
- [ ] One full mock: 60-min coding + two 60-min designs + 45-min behavioural
- [ ] [mock-rehearsal-plan.md](../22-behavioral-and-staff-scope/mock-rehearsal-plan.md)
- [ ] HI guided practice, design rounds, with feedback
- [ ] Re-drill whatever broke
- [ ] Re-read [interview-playbook.md](interview-playbook.md) the night before each round

---

## Path C — full (~87 h)

Path B, plus everything marked **Recommended**, plus the legacy sections tagged Required or Recommended
in [curriculum.md §Part 2](curriculum.md) — principally
[06-databases-and-distributed-data](../06-databases-and-distributed-data/) (~6 h),
[07-messaging-and-streaming](../07-messaging-and-streaming/) (~5 h) and
[08-algorithms-and-data-structures](../08-algorithms-and-data-structures/) (~4 h).

Those three are the strongest material you already had, and they feed the design rounds directly. If your
timeline allows Path C, they are better value than more LeetCode.

---

## Ongoing, every week regardless of path

- [ ] Speed drills, 15 min a day — [speed-drills.md](../21-python-for-interviews/speed-drills.md)
- [ ] One timed 60-min laptop problem
- [ ] One 60-min design, out loud, before reading the write-up
- [ ] Add one story to the bank, with a number

---

## Interview questions

This file is a planning tool rather than a topic. Reported questions are in [evidence.md](evidence.md).
