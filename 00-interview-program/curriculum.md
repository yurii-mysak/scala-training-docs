# Curriculum — every item, tagged

> **Priority:** Required
> **Est. time:** 15 min to read
> **Track:** Both
> **HelloInterview:** none

Auto-generated from the front-matter of every file in this repo. Regenerate with
`python3 00-interview-program/build_curriculum.py`.

**Priority means:** *Required* — you cannot pass this loop without it. *Recommended* — materially
raises the odds. *Optional* — nice to have, or only relevant if the role turns out to include Web.

**New material:** 85 documents. Required only ≈ 43h 59m. Everything ≈ 62h 19m.
Existing repo material adds roughly 24 h more if you work all of it; see part 2.

---

## Part 1 — new material written for this loop

### 09 — Coding challenges (Lyft-evidence set)
*5 documents · ≈3h 10m*

| ✓ | Priority | Time | Track | Document |
|---|---|---|---|---|
| [ ] | **Required** | 40 min | Both | [LC 158 — Read N Characters Given Read4 II (Call Multiple Times)](../09-coding-challenges/lyft/lc158-read-n-chars-given-read4-ii.md) |
| [ ] | **Required** | 35 min | Both | [LC 716 — Max Stack](../09-coding-challenges/lyft/lc716-max-stack.md) |
| [ ] | **Required** | 30 min | Both | [LC 735 — Asteroid Collision](../09-coding-challenges/lyft/lc735-asteroid-collision.md) |
| [ ] | **Required** | 45 min | Both | [LC 76 — Minimum Window Substring](../09-coding-challenges/lyft/lc76-minimum-window-substring.md) |
| [ ] | **Required** | 40 min | Both | [LC 981 — Time Based Key-Value Store](../09-coding-challenges/lyft/lc981-time-based-key-value-store.md) |

### 14 — Cloud, containers & Kubernetes
*7 documents · ≈4h 15m*

| ✓ | Priority | Time | Track | Document |
|---|---|---|---|---|
| [ ] | **Required** | 40 min | Both | [Docker & Containers](../14-cloud-and-infrastructure/docker-and-containers.md) |
| [ ] | **Required** | 45 min | Both | [Kubernetes: The Object Model](../14-cloud-and-infrastructure/kubernetes-core.md) |
| [ ] | **Required** | 40 min | Both | [Kubernetes Debugging Playbook](../14-cloud-and-infrastructure/kubernetes-debugging-playbook.md) |
| [ ] | **Required** | 45 min | Both | [Kubernetes Operations: Keeping It Running](../14-cloud-and-infrastructure/kubernetes-operations.md) |
| [ ] | **Recommended** | 20 min | Both | [Container Runtimes & cri-o](../14-cloud-and-infrastructure/container-runtimes-cri-o.md) |
| [ ] | **Recommended** | 35 min | Server | [Deploying Python Services](../14-cloud-and-infrastructure/deploying-python-services.md) |
| [ ] | **Recommended** | 30 min | Both | [Service Mesh & Envoy](../14-cloud-and-infrastructure/service-mesh-and-envoy.md) |

### 15 — System design
*14 documents · ≈14h 0m*

| ✓ | Priority | Time | Track | Document |
|---|---|---|---|---|
| [ ] | **Required** | 10 min | Both | [System Design](../15-system-design/README.md) |
| [ ] | **Required** | 45 min | Both | [Design Round Protocol — a repeatable 60-minute structure](../15-system-design/design-round-protocol.md) |
| [ ] | **Required** | 75 min | Server | [Distributed Web Crawler — full worked design](../15-system-design/distributed-web-crawler.md) |
| [ ] | **Required** | 75 min | Server | [Driver Location Matching — full worked design](../15-system-design/driver-location-matching.md) |
| [ ] | **Required** | 60 min | Server | [Idempotency & Deduplication — and why exactly-once is a fiction](../15-system-design/idempotency-and-deduplication.md) |
| [ ] | **Required** | 45 min | Both | [Lyft's Real Architecture — free Staff-instinct points](../15-system-design/lyft-architecture.md) |
| [ ] | **Required** | 60 min | Both | [Napkin Math — latency, storage, QPS, cores, and memory, out loud](../15-system-design/napkin-math.md) |
| [ ] | **Required** | 60 min | Server | [Rate Limiter — full worked design](../15-system-design/rate-limiter.md) |
| [ ] | **Required** | 120 min | Both | [Real-Time Chat with Delivery Guarantees — full worked design](../15-system-design/realtime-chat-delivery-guarantees.md) |
| [ ] | **Required** | 90 min | Server | [Support Case Routing — full worked design](../15-system-design/support-case-routing.md) |
| [ ] | **Required** | 60 min | Server | [Third-Party Dependency Failure Modes — full worked design](../15-system-design/third-party-failure-modes.md) |
| [ ] | **Recommended** | 45 min | Server | [Demand Heatmap and Surge Signal — full worked design](../15-system-design/demand-heatmap-and-surge.md) |
| [ ] | **Recommended** | 50 min | Server | [Multi-Channel Notification System — full worked design](../15-system-design/notification-system.md) |
| [ ] | **Recommended** | 45 min | Server | [URL Shortener — full worked design](../15-system-design/url-shortener.md) |

### 17 — The Lyft laptop round
*10 documents · ≈6h 35m*

| ✓ | Priority | Time | Track | Document |
|---|---|---|---|---|
| [ ] | **Required** | 30 min read (+ 90 min per timed drill) | Both | [The 90-Minute Laptop Round Protocol](../17-lyft-laptop-round/00-protocol.md) |
| [ ] | **Required** | 45 min | Both | [Stateful Paginated Fetch (fetchN over a page-at-a-time upstream)](../17-lyft-laptop-round/01-stateful-paginated-fetch.md) |
| [ ] | **Required** | 40 min | Both | [Versioned (Temporal) Key-Value Store](../17-lyft-laptop-round/02-versioned-kv-store.md) |
| [ ] | **Required** | 60 min | Both | [In-Memory KV Store with Transactions (BEGIN / COMMIT / ROLLBACK)](../17-lyft-laptop-round/03-inmemory-kv-transactions.md) |
| [ ] | **Required** | 50 min | Both | [Trie Typeahead / Autocomplete / T9](../17-lyft-laptop-round/04-trie-typeahead-t9.md) |
| [ ] | **Recommended** | 45 min | Both | [Job Scheduler / Interval-to-Worker Assignment](../17-lyft-laptop-round/05-job-scheduler-workers.md) |
| [ ] | **Recommended** | 45 min | Both | [File / Log / CSV Parsing](../17-lyft-laptop-round/06-file-log-csv-parsing.md) |
| [ ] | **Recommended** | 30 min | Both | [One-Offs: Lower-Frequency Reported Patterns](../17-lyft-laptop-round/08-oneoffs.md) |
| [ ] | **Optional** | 40 min | Both | [Nested Dot-Path Key-Value Store](../17-lyft-laptop-round/07-nested-path-kv.md) |
| [ ] | **Optional** | 10 min | Both | [Timed Drill Log](../17-lyft-laptop-round/09-timed-drill-log.md) |

### 18 — I/O harness (runnable project)
*5 documents · ≈1h 5m*

| ✓ | Priority | Time | Track | Document |
|---|---|---|---|---|
| [ ] | **Required** | 10 min | Both | [I/O Harness for the Laptop Round](../18-io-harness/README.md) |
| [ ] | **Required** | 5 min | Both | [Laptop Round Runbook](../18-io-harness/RUNBOOK.md) |
| [ ] | **Required** | 10 min | Both | [Using the I/O Harness](../18-io-harness/USAGE.md) |
| [ ] | **Recommended** | 20 min | Both | [Scala Fallback Skeleton](../18-io-harness/SCALA.md) |
| [ ] | **Optional** | 20 min | Both | [C# Fallback Skeleton](../18-io-harness/CSHARP.md) |

### 19 — Observability & on-call
*9 documents · ≈7h 55m*

| ✓ | Priority | Time | Track | Document |
|---|---|---|---|---|
| [ ] | **Required** | 10 min | Both | [Observability and On-Call](../19-observability-and-oncall/README.md) |
| [ ] | **Required** | 60 min | Both | [Alert Design](../19-observability-and-oncall/alert-design.md) |
| [ ] | **Required** | 60 min | Server | [Metrics, Logs and Traces](../19-observability-and-oncall/metrics-logs-traces.md) |
| [ ] | **Required** | 75 min | Both | [On-Call Health](../19-observability-and-oncall/oncall-health.md) |
| [ ] | **Required** | 75 min | Both | [SLOs and Error Budgets](../19-observability-and-oncall/slos-and-error-budgets.md) |
| [ ] | **Required** | 25 min | Both | [Staff-Scope Stories from DevOps and On-Call Work](../19-observability-and-oncall/staff-scope-stories.md) |
| [ ] | **Recommended** | 60 min | Server | [Debugging Distributed Systems](../19-observability-and-oncall/debugging-distributed-systems.md) |
| [ ] | **Recommended** | 50 min | Both | [Incident Response](../19-observability-and-oncall/incident-response.md) |
| [ ] | **Recommended** | 60 min | Server | [Instrumenting Python Services](../19-observability-and-oncall/instrumenting-python-services.md) |

### 20 — LLM & agent systems
*10 documents · ≈8h 55m*

| ✓ | Priority | Time | Track | Document |
|---|---|---|---|---|
| [ ] | **Required** | 20 min | Both | [LLM Agent Systems](../20-llm-agent-systems/README.md) |
| [ ] | **Required** | 60 min | Server | [LLM Agent Architectures](../20-llm-agent-systems/agent-architectures.md) |
| [ ] | **Required** | 60 min | Server | [Agent State and Checkpointing](../20-llm-agent-systems/agent-state-and-checkpointing.md) |
| [ ] | **Required** | 45 min | Both | [Driving Responsible Adoption of AI Development Tools](../20-llm-agent-systems/ai-dev-tools-adoption.md) |
| [ ] | **Required** | 90 min | Server | [Evaluating Agents](../20-llm-agent-systems/evaluating-agents.md) |
| [ ] | **Required** | 75 min | Server | [LangGraph Patterns](../20-llm-agent-systems/langgraph-patterns.md) |
| [ ] | **Required** | 45 min | Both | [Case Study: Lyft's Safety & Customer Care Agent Platform](../20-llm-agent-systems/lyft-scc-case-study.md) |
| [ ] | **Recommended** | 40 min | Server | [LLM as Judge](../20-llm-agent-systems/llm-as-judge.md) |
| [ ] | **Recommended** | 60 min | Both | [Production LLMOps](../20-llm-agent-systems/production-llmops.md) |
| [ ] | **Recommended** | 40 min | Server | [RAG and Retrieval](../20-llm-agent-systems/rag-and-retrieval.md) |

### 21 — Python for interviews
*8 documents · ≈5h 10m*

| ✓ | Priority | Time | Track | Document |
|---|---|---|---|---|
| [ ] | **Required** | 10 min | Both | [Python for Interviews](../21-python-for-interviews/README.md) |
| [ ] | **Required** | 45 min | Both | [Data Structures & Idioms](../21-python-for-interviews/data-structures-and-idioms.md) |
| [ ] | **Required** | 45 min | Both | [From Lua & Scala to Python](../21-python-for-interviews/from-lua-and-scala-to-python.md) |
| [ ] | **Required** | 40 min | Both | [I/O and Parsing](../21-python-for-interviews/io-and-parsing.md) |
| [ ] | **Required** | 60 min | Both | [OOP & Design in Python](../21-python-for-interviews/oop-and-design-in-python.md) |
| [ ] | **Required** | 10 min to read; ~5-6 h spread over 2-3 weeks to run the drills | Both | [Speed Drills — Python Muscle Memory](../21-python-for-interviews/speed-drills.md) |
| [ ] | **Required** | 60 min | Both | [Standard Library for Interviews](../21-python-for-interviews/stdlib-for-interviews.md) |
| [ ] | **Required** | 40 min | Both | [Testing with `unittest`](../21-python-for-interviews/testing-with-unittest.md) |

### 22 — Behavioural & Staff scope
*10 documents · ≈6h 59m*

| ✓ | Priority | Time | Track | Document |
|---|---|---|---|---|
| [ ] | **Required** | 15 min (this file); ~10 h for the section | Both | [Behavioural & Staff Scope](../22-behavioral-and-staff-scope/README.md) |
| [ ] | **Required** | 45 min | Both | [CARL and STAR — Structuring Behavioural Answers](../22-behavioral-and-staff-scope/carl-and-star.md) |
| [ ] | **Required** | 60 min | Both | [Lyft Values and the Reported Question Bank](../22-behavioral-and-staff-scope/lyft-values-and-questions.md) |
| [ ] | **Required** | 45 min | Both | [Metrics for Stories — Recovering Numbers You Did Not Record](../22-behavioral-and-staff-scope/metrics-for-stories.md) |
| [ ] | **Required** | 90 min | Both | [Senior vs Staff Framing — The Downlevelling File](../22-behavioral-and-staff-scope/senior-vs-staff-framing.md) |
| [ ] | **Required** | 4 h (fill-in, across several sessions) | Both | [Story Bank — 12-Slot Working Template](../22-behavioral-and-staff-scope/story-bank.md) |
| [ ] | **Required** | 60 min | Both | [Transition Narrative — The Awkward Questions](../22-behavioral-and-staff-scope/transition-narrative.md) |
| [ ] | **Recommended** | 40 min | Both | [AI and GenAI Behavioural Questions](../22-behavioral-and-staff-scope/ai-and-genai-questions.md) |
| [ ] | **Recommended** | 30 min to read, then ~6 h of practice | Both | [Mock Rehearsal Plan](../22-behavioral-and-staff-scope/mock-rehearsal-plan.md) |
| [ ] | **Recommended** | 30 min | Both | [Questions to Ask Them](../22-behavioral-and-staff-scope/questions-to-ask-them.md) |

### 23 — Web & frontend (conditional track)
*7 documents · ≈4h 15m*

| ✓ | Priority | Time | Track | Document |
|---|---|---|---|---|
| [ ] | **Recommended** | 5 min | Server + Web | [Web & Frontend – Conditional Track](../23-web-and-frontend/README.md) |
| [ ] | **Recommended** | 60 min | Server + Web | [Frontend System Design](../23-web-and-frontend/frontend-system-design.md) |
| [ ] | **Optional** | 20 min | Server + Web | [Accessibility & Quality](../23-web-and-frontend/accessibility-and-quality.md) |
| [ ] | **Optional** | 40 min | Server + Web | [API Integration Patterns](../23-web-and-frontend/api-integration-patterns.md) |
| [ ] | **Optional** | 30 min | Server + Web | [Frontend Testing](../23-web-and-frontend/frontend-testing.md) |
| [ ] | **Optional** | 60 min | Server + Web | [React & TypeScript Refresher](../23-web-and-frontend/react-typescript-refresher.md) |
| [ ] | **Optional** | 40 min | Server + Web | [Web Performance](../23-web-and-frontend/web-performance.md) |

---

## Part 2 — existing repo material, re-tagged for this loop

The 186 documents already in this repo were written for Scala interviews. Most still earn their
place; some do not. Section-level guidance rather than per-file, because the judgement is the same
across each section.

| ✓ | Priority | Time | Section | Why |
|---|---|---|---|---|
| [ ] | **Required** | ~6 h | [06-databases-and-distributed-data](../06-databases-and-distributed-data/) | Your strongest existing asset. CAP, linearizability vs serializability, partitioning & rebalancing, distributed transactions, DynamoDB, Cassandra LSM, event sourcing. Feeds the design rounds directly — DynamoDB is what Lyft uses for agent state. |
| [ ] | **Required** | ~5 h | [07-messaging-and-streaming](../07-messaging-and-streaming/) | Kafka fundamentals and advanced, delivery QoS/DLQ/HA, backpressure, high-throughput/low-latency systems. Directly reusable in every design round. |
| [ ] | **Required** | ~4 h | [08-algorithms-and-data-structures](../08-algorithms-and-data-structures/) | Foundation for the CoderPad screen. Re-read Sorting/Searching, Trees & Graphs, Traversal, Recursion & DP, binary heap, hashset/hashmap. |
| [ ] | **Recommended** | ~2 h | [10-networking](../10-networking/) | HTTP/TLS, load balancing, reverse proxies. Feeds the Envoy and API-design parts of design rounds. |
| [ ] | **Recommended** | ~1.5 h | [12-testing](../12-testing/) | Testing strategy is explicitly probed in Lyft's design round ('library preferences and testing strategies'). Skim for vocabulary. |
| [ ] | **Recommended** | ~1.5 h | [11-security](../11-security/) | One Staff report included a cloud-security domain round. Worth a skim, not a deep dive, unless the recruiter names security. |
| [ ] | **Recommended** | ~3 h | [03-akka-ecosystem](../03-akka-ecosystem/) | Do not present as Akka knowledge. Re-read cluster, streams and backpressure as transferable distributed-systems concepts: actor-per-conversation maps onto agent session state, supervision onto escalation. |
| [ ] | **Optional** | ~0 h | [05-jvm-internals](../05-jvm-internals/) | Deep and excellent, but Lyft runs Python and Go. Only relevant if an interviewer asks about your background. |
| [ ] | **Optional** | ~0 h | [13-data-engineering](../13-data-engineering/) | Lakehouse/Delta/Parquet. Relevant only to Lyft's data-platform org, which is not this team. |
| [ ] | **Optional** | ~0 h | [01-scala-language](../01-scala-language/) | Skip for this loop. Retain for LotusFlare and for the fallback plan. |
| [ ] | **Optional** | ~0 h | [02-functional-programming](../02-functional-programming/) | Skip for this loop. |
| [ ] | **Optional** | ~0.5 h | [04-concurrency-and-async](../04-concurrency-and-async/) | Concepts transfer, syntax does not. Skim only the Cats Effect concurrency file for vocabulary. |
| [ ] | **Optional** | ~0 h | [16-adtech](../16-adtech/) | Not relevant to Lyft. Skip. |

---

## Interview questions

This file is an index, not a topic. See [interview-playbook.md](interview-playbook.md) for how
each round runs and [evidence.md](evidence.md) for the reported question bank.
