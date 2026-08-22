# HelloInterview — what to use your account for

> **Priority:** Recommended
> **Est. time:** 15 min to read, then used throughout
> **Track:** Both
> **HelloInterview:** all of it

You already pay for HelloInterview and used it for your current role. It is stronger than this repo at
three things and weaker at one, so use it selectively rather than working through it end to end.

**HI is better than this repo at:** guided DSA practice with feedback, the standard system-design
vocabulary and delivery framework, and behavioural story structuring.

**HI cannot help you with:** anything Lyft-specific. It has no Lyft company page. The seven laptop
families, the reported question bank, and the Lyft architecture facts exist only here.

**Use both this way:** HI for reps and structure, this repo for what Lyft actually asks.

---

## 1 · DSA track — map to Lyft's real problem set

Lyft's pool is narrow. Only work the HI patterns that map onto reported Lyft problems.

| Priority | HI pattern | Why, for this loop |
|---|---|---|
| **Required** | **Sliding Window** — variable-length (Longest Substring Without Repeating, Longest Repeating Character Replacement) | LC 76 is Lyft's most-repeated problem, four independent reports. **HI does not have LC 76 itself** — do the HI patterns for the technique, then LC 76 from [../09-coding-challenges/lyft/lc76-minimum-window-substring.md](../09-coding-challenges/lyft/lc76-minimum-window-substring.md). |
| **Required** | **Trie** — Implement Trie Methods, Prefix Matching | Directly underlies the typeahead / autocomplete / T9 family, 5 independent reports. |
| **Required** | **Heap** — Merge K Sorted Lists, **Median from Data Stream** | Median from Data Stream is the two-heap technique behind LC 480, asked Oct 2025. Heaps also drive the job-scheduler family. |
| **Required** | **Intervals** — Can Attend Meetings, Merge Intervals, Employee Free Time | The job-scheduler / interval-to-worker family, 4 reports. A 2025 candidate failed this by hand-rolling a heap in Go. |
| **Required** | **Stack** — Monotonic Stack, Daily Temperatures | LC 735 Asteroid Collision sits at the top of the Lyft-tagged frequency list. |
| Recommended | **BFS — Graphs** (Rotting Oranges, 01-Matrix) and **DFS — Matrices** (Number of Islands, Flood Fill) | Grid/BFS spread was reported; crawler design leans on graph traversal. |
| Recommended | **Graphs** — topological sort, Course Schedule | DAG linearisation was a reported laptop problem. |
| Recommended | **Binary Search** — Search in Rotated Sorted Array, Koko Eating Bananas | General screen insurance. |
| Recommended | **Two Pointers** — Trapping Rain Water | In the Lyft-tagged set and already in your repo. |
| Optional | **Dynamic Programming**, Backtracking, Prefix Sum, Linked List, Matrices | Not absent from Lyft's set but not concentrated in it. Do only if time is left. |

**How to use it:** do the HI pattern overview and two problems per Required row for the technique, then
switch to the Lyft-specific problem in this repo. Do not grind HI's full 100+ problem list — the evidence
says Lyft's pool is small and specific.

---

## 2 · System Design in a Hurry — the highest-value part of your subscription

Two design rounds against one coding round. This is where the time goes.

| Priority | HI lesson | Maps to |
|---|---|---|
| **Required** | **Delivery Framework** | The protocol in [interview-playbook.md §5](interview-playbook.md). Use HI's framework; it is good and it is a habit worth having. |
| **Required** | Core Concepts → **Numbers to Know** | The live napkin-math probe. Pair with [../15-system-design/napkin-math.md](../15-system-design/napkin-math.md). |
| **Required** | Common Patterns → **Real-time Updates** | Chat with delivery guarantees — the strongest 2026 signal. Pair with [../15-system-design/realtime-chat-delivery-guarantees.md](../15-system-design/realtime-chat-delivery-guarantees.md). |
| **Required** | Common Patterns → **Dealing with Contention** | Idempotency, dedup, rate limiting. Pair with [../15-system-design/idempotency-and-deduplication.md](../15-system-design/idempotency-and-deduplication.md) and [rate-limiter.md](../15-system-design/rate-limiter.md). |
| **Required** | Key Technologies → **DynamoDB** | Lyft stores agent conversation state in DynamoDB via a custom checkpointer. Knowing its partition/sort key model and hot-partition behaviour is directly on-domain. |
| **Required** | Key Technologies → **Redis** | Lyft uses Redis Cluster sorted sets with ~30s expiry for driver discovery, and Redis for rate limiting at two layers. |
| **Required** | Core Concepts → Sharding, Consistent Hashing, CAP Theorem, Database Indexing | The NoSQL-depth probe. You already have strong material in [../06-databases-and-distributed-data/](../06-databases-and-distributed-data/) — use HI for the interview-shaped version. |
| **Required** | Advanced → **Proximity Search** | Driver–rider matching and the S2 geohashing discussion. |
| Recommended | Key Technologies → **Kafka**, Cassandra, PostgreSQL, Elasticsearch, API Gateway | Kafka you already know deeply; use HI only for the interview framing. |
| Recommended | Common Patterns → Multi-step Processes, Managing Long Running Tasks, Scaling Reads/Writes | Sagas, async integration, read scaling. |
| Recommended | Question Breakdowns → **Uber** | The closest published breakdown to Lyft's own domain. Do this one. |
| Recommended | Question Breakdowns → **Bitly** | Maps to the reported bit.ly/TinyURL question. |
| Recommended | Core Concepts → Networking Essentials, API Design, Data Modeling, Caching | Foundation; skim if solid. |
| Optional | Advanced → Time Series DBs, Vector Databases, Change Data Capture, Data Structures for Big Data | Only if time remains. Vector DBs connect loosely to the LLM work. |
| Optional | Key Technologies → Flink, ZooKeeper | Flink is Lyft's data platform, not this team. |

---

## 3 · Low-Level Design in a Hurry — do not skip this

A June 2026 report says **"the laptop round is basically OOD."** HI's Low-Level Design track is the best
available preparation for that drift, and this repo does not duplicate it.

**Required.** Work the framework and two or three worked problems, then apply the same structure to the
seven families in [../17-lyft-laptop-round/](../17-lyft-laptop-round/) — designing the class boundaries
before writing the algorithm.

---

## 4 · Behavioral track

| Priority | HI lesson | Note |
|---|---|---|
| **Required** | **CARL framework** (Context, Actions, Results, Learnings) | Use CARL rather than STAR. The Results step forces the number, and *"How did you measure?"* is a verbatim reported Lyft question. |
| **Required** | **Story Builder** | Build the bank here, store it in [../22-behavioral-and-staff-scope/story-bank.md](../22-behavioral-and-staff-scope/story-bank.md). Aim for many short stories — Lyft's round is breadth, not depth. |
| **Required** | **Answering AI Questions** | *"Tell me some experience related to ML or Gen AI"* is a reported Lyft question, and two JD bullets are about AI adoption. |
| Recommended | The Big Three Questions | Tell me about yourself / a conflict / a failure. All reported at Lyft. |
| Recommended | Adapting to Big Tech | Relevant: you are moving from outsourcing and product-services work to a US product company. |
| Recommended | Decode / Select / Deliver | Useful for the heavy follow-ups Lyft reports. |

**One adjustment to make.** HI's behavioural material is calibrated to generic big-tech values. Lyft has
exactly three — Be yourself, Uplift others, Make it happen. Re-tag your HI-built stories against those.

---

## 5 · Guided Practice and mocks

Use HI's guided practice with feedback for **design rounds specifically**, in week 3 and week 6. It is the
closest available proxy for the real thing and this repo cannot replicate feedback.

Two caveats. HI's design practice is calibrated to the abstract FAANG design round; Lyft's includes real
coding, code review and testing strategy, so the feedback will not cover that dimension. And HI has no
Lyft company page, so its "company-specific" prompts do not apply here — use the ranked list in
[interview-playbook.md §5](interview-playbook.md) instead.

---

## 6 · What to ignore

- **HI's ML System Design track.** The team uses LLM agents but you are not being hired as an MLE, and the
  reported loop has no ML design round. [Section 20](../20-llm-agent-systems/) covers what you actually need.
- **The full DSA problem list.** Lyft's pool is narrow. Depth on the mapped patterns beats breadth.
- **Company-specific question sets for Meta, Amazon, Google, OpenAI, Anthropic.** Different loops.

---

## Interview questions

**1. Why use CARL rather than STAR here?**
Both structure a story, but CARL's explicit Results and Learnings steps force a measured outcome and a
reflection. *"How did you measure?"* is a verbatim reported Lyft follow-up, so a framework that makes you
answer it unprompted is the safer default.

**2. HI teaches a delivery framework for design. Does it apply at Lyft?**
The opening does — clarify, scope, estimate, API, data model, architecture. The back half needs adapting,
because Lyft's design round includes real coding, code review and testing strategy rather than staying
abstract. Use HI's structure, then go deeper into implementation than HI's rubric expects.

**3. You have ten hours and both HI and this repo. How do you split them?**
Roughly: three hours on HI system design (Delivery Framework, Numbers to Know, Real-time Updates, Dealing
with Contention, DynamoDB), two on HI Low-Level Design, and five on this repo's laptop families and the
I/O harness. The repo has what is Lyft-specific; HI has the reps and the feedback.
