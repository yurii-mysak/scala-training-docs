# System Design

> **Priority:** Required
> **Est. time:** 10 min
> **Track:** Both
> **HelloInterview:** none

Two of the four technical rounds in this loop are design rounds, and they are not abstract FAANG-style
design rounds — they include real coding, code review, library choices, and testing strategy, with two
named probes: **NoSQL depth** (say the partition key, not just the database name) and **live napkin math
on memory and CPU**. Read [design-round-protocol.md](design-round-protocol.md) before any worked design
in this folder; it is the structure every other file in here is written to fit.

---

## Read in this order

### The method — read this first

| # | File | Priority | Est. time | Description |
|---|------|----------|-----------|-------------|
| 1 | [design-round-protocol.md](design-round-protocol.md) | Required | 45 min | A repeatable 60-minute structure for the round: phases, timing, the scoping/API/data-model/scale/failure-mode/trade-off sequence, what to do when the interviewer drills into implementation, and "full working design" vs "good design" |
| 2 | [napkin-math.md](napkin-math.md) | Required | 60 min | Live back-of-envelope math on latency, storage, QPS, cores, and memory — a named probe. Includes the worked support-chat sizing example this section's designs reuse |
| 3 | [lyft-architecture.md](lyft-architecture.md) | Required | 45 min | Lyft's actual stack — Envoy, protobuf/gRPC, the Redis sorted-set driver index, S2 cells, DynamoDB, edge/mesh rate limiting, the 30-second batching window, the target team's agent platform — each fact framed as an opinion with a stated cost, not trivia to recite |
| 4 | [idempotency-and-deduplication.md](idempotency-and-deduplication.md) | Required | 60 min | Why exactly-once is a fiction, the idempotency-key protocol, dedup windows, the donation-platform worked example. The argument every "at-least-once" design in this section applies rather than re-derives |

### Worked full designs — same depth and structure throughout

| # | File | Priority | Est. time | Description |
|---|------|----------|-----------|-------------|
| 5 | [realtime-chat-delivery-guarantees.md](realtime-chat-delivery-guarantees.md) | Required | 120 min | The single highest-value design in this loop — reported at Lyft in four variants. Delivery semantics, ordering, backpressure, presence, storage partition-key reasoning |
| 6 | [distributed-web-crawler.md](distributed-web-crawler.md) | Required | 75 min | Reported as "copy the whole of Wikipedia." Politeness-bound frontier design, dedup at three layers, the 24-hour-outage recovery follow-up |
| 7 | [support-case-routing.md](support-case-routing.md) | Required | 90 min | Not a verbatim report, but the highest-probability design for this specific team: intake, classification, SLA tiers, skill-based queueing, the AI-agent-first path with confidence thresholds, and what happens when the LLM is slow or down |
| 8 | [driver-location-matching.md](driver-location-matching.md) | Required | 75 min | Real-time location ingestion, geohash/S2/H3 compared, the Redis sorted-set index, radius-query candidate generation, the batching window, and offer/accept/cascade dispatch |
| 9 | [rate-limiter.md](rate-limiter.md) | Required | 60 min | Fixed window, sliding log, sliding window counter, token bucket, and leaky bucket compared; atomic Redis enforcement; edge vs mesh; client behaviour on 429; the retry-storm failure mode |
| 10 | [demand-heatmap-and-surge.md](demand-heatmap-and-surge.md) | Recommended | 45 min | Reported near-verbatim. Builds on file 8: demand/supply aggregation, the staleness-vs-cost trade-off, and the feedback loop where showing the signal changes it |
| 11 | [url-shortener.md](url-shortener.md) | Recommended | 45 min | Reported as `bit.ly/TinyURL`. Key-generation strategies compared, the read-heavy cache path, and the 301-vs-302 decision most candidates get wrong |
| 12 | [notification-system.md](notification-system.md) | Recommended | 50 min | Multi-channel fan-out, template/preference management, coalescing vs deduplication, quiet hours, retry with backoff, and the cross-channel at-least-once asymmetry |

### Background reference — already in the repo, cross-linked rather than duplicated

| # | File | Priority | Est. time | Description |
|---|------|----------|-----------|-------------|
| 13 | [grpc_protobuf_schema_design.md](grpc_protobuf_schema_design.md) | Recommended | 30 min | gRPC/HTTP2 primer, protobuf wire format and schema design, versioning and compatibility — the schema referenced directly by the chat design's protobuf sketch |
| 14 | [event_sourcing_cqrs_sagas_guide.md](event_sourcing_cqrs_sagas_guide.md) | Recommended | 40 min | Event sourcing/CQRS, microservice patterns, distributed transactions, Saga vs. 2PC — background for exactly-once-payment-style prompts and long-running workflows |
| 15 | [Architecture-Dev-Process.md](Architecture-Dev-Process.md) | Optional | 30 min | General SWE reference: algorithms/Big-O cheat sheet, OOD glossary, refactoring catalogue, estimation, SDLC/Kanban, UML, code quality metrics |
| 16 | [payments_interview_prep_expanded.md](payments_interview_prep_expanded.md) | Optional | 30 min | Card-network flows (authorization/capture/settlement), tokenization and PCI-DSS, 3-D Secure and fraud prevention — background for the donation-platform exactly-once-payment prompt |

---

## If you only have an hour

Read [design-round-protocol.md](design-round-protocol.md), then
[realtime-chat-delivery-guarantees.md](realtime-chat-delivery-guarantees.md) end to end, then skim
[support-case-routing.md](support-case-routing.md)'s section headings. That combination covers the
structure every design round is graded against, the single most-reported prompt worked in full, and the
design this specific team would actually ask for.

## A pattern that repeats across this whole folder

The same handful of mechanisms reappear as the answer to unrelated-looking questions, and naming the
reuse is itself a signal worth giving in the room:

| Pattern | First full treatment | Reused in |
|---------|------------------------|-----------|
| TTL as a self-healing failure detector | [lyft-architecture.md §5](lyft-architecture.md) (driver discovery) | Chat's connection registry and presence; agent availability in support-case-routing |
| Full-jitter exponential backoff | [realtime-chat-delivery-guarantees.md §5.4](realtime-chat-delivery-guarantees.md) (reconnect storms) | Rate limiter client behaviour; notification retry |
| A batching window converts greedy-online into offline-optimal | [lyft-architecture.md §8.3](lyft-architecture.md) (ride matching) | Driver-matching's dispatch loop; named and priced (then declined) for support-case assignment |
| Circuit breaker: open → cooldown → half-open probe | [distributed-web-crawler.md §10.2](distributed-web-crawler.md) (a dead host) | The LLM call guard in support-case-routing; the rate-limiter-store guard; notification provider failures |
| A signal that changes the thing it measures | [lyft-architecture.md §10](lyft-architecture.md) (the agent-eval distribution shift) | The demand-heatmap feedback loop; the retry-storm mechanism in rate-limiter.md |
| Bounded partition key via time-bucketing | Chat's `conversation_id#yyyymm` | Driver-location history, url-shortener's storage note, notification delivery history |

## Interview questions

**1. This folder has sixteen files. If the round is tomorrow, what do you actually read?**
[design-round-protocol.md](design-round-protocol.md) for the structure, then
[realtime-chat-delivery-guarantees.md](realtime-chat-delivery-guarantees.md) end to end — it is the
highest-value single file in the loop — then skim every other worked design's §1 (the one-sentence
frame) and failure-mode table, which is enough to not be caught flat-footed if the prompt lands elsewhere.

**2. Why does almost every file in this folder end up talking about napkin math, TTLs, and backpressure?**
Because the same handful of mechanisms are the right answer to most of Lyft's actual constraints, and
repeating them across unrelated-looking prompts is the point, not a coincidence — see the pattern table
above. Naming the reuse explicitly in the room ("this is the same TTL-as-failure-detector idea as the
driver index") is itself a Staff-level signal, not just an efficient way to prepare.

**3. How do the worked designs in this folder differ from a typical FAANG system-design guide?**
Two ways: they include the coding sub-question the round pivots to, with tested Python, and they are
grounded in Lyft's actual published architecture wherever that architecture is a defensible answer,
rather than a generic reference architecture. [lyft-architecture.md](lyft-architecture.md) is what makes
that grounding possible — its facts are cited, not invented.

**4. What is the named "NoSQL depth" probe, concretely?**
The interviewer wants the partition key stated and defended before a database name is even mentioned —
"`conversation_id` as the key because it makes the two most common access patterns single-item
operations" is the shape of a good answer. Every worked design in this folder has a storage-model section
built around exactly that move.

**5. What is the named "napkin math" probe, concretely?**
Live, out-loud back-of-envelope arithmetic on scale, memory, and CPU — not a memorised number. Every
worked design states its scale assumptions explicitly and derives a small number of consequences from
them, which is the format to reproduce live: assumption, arithmetic, conclusion, in that order.

**6. Two files were built by generalising a fact from lyft-architecture.md into a full design. Which, and
why does that matter?**
Driver-location-matching.md builds out the Redis-sorted-set-plus-S2 fact from §5-6, and
demand-heatmap-and-surge.md builds on top of that again. It matters because an interviewer can ask "why"
at any depth on either topic, and the answer is always available by walking one file back toward the
sourced fact rather than running out of material.

**7. What is the single biggest mistake candidates make across every design in this folder?**
Treating "a full working design" as the goal. An interviewer explaining a real rejection put it exactly
this way: having a full working design is not the same as having a good one, and answering every question
asked does not mean the answers were satisfactory. The trade-off tables and "working vs good" tables in
every file exist specifically to close that gap.
