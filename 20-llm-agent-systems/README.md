# LLM Agent Systems

> **Priority:** Required
> **Est. time:** 20 min
> **Track:** Both
> **HelloInterview:** Behavioral → Answering AI Questions

---

## Why this section exists for this role

This is the largest gap between the candidate and the job, and it is not close.

Two of the nine responsibility bullets in the posting are about driving AI adoption. The target team's
flagship product **is** a production multi-agent platform: LangGraph and LangSmith, Claude via Amazon
Bedrock, 7 production agents, ~270k interactions/month, a meta agent acting as a stateful router, a
custom `DynamoDBSaver`, safety checks fanned out in parallel before any LLM reasoning. And Lyft has a
named Anthropic partnership that includes Anthropic training Lyft engineers on AI-assisted development.
An interview loop for this team will touch this material, and the behavioural round has a reported
question — "Tell me some experience related to ML or Gen AI" — that lands directly on it.

The framing throughout is deliberate: **agents are distributed systems with unusual failure modes.**
That is not a rhetorical device, it is the accurate description, and it is the framing that converts 13
years of JVM/Akka distributed-systems work into credibility on this stack rather than leaving it on the
other side of a gap. Supervision hierarchies, actor-per-conversation, at-least-once delivery with
idempotent side effects, backpressure, event sourcing and snapshotting, single-writer discipline,
scatter-gather — every one has a direct counterpart here, and each file says so explicitly where it
applies.

What is genuinely new is a short list, and knowing it is short is itself the point: non-determinism in
the control path, a finite context window that behaves like memory pressure, cost as a first-class
resource, prompt injection as an untrusted-input channel with no escaping primitive, silent
provider-side capability drift, and correlated failure between an agent and the instruments used to
evaluate it.

**If time is short**, the highest-return order is: `evaluating-agents.md`, then
`lyft-scc-case-study.md`, then `agent-state-and-checkpointing.md`. Evaluation is where most candidates
are weakest and where Lyft has published a genuinely interesting failure of their own; the case study
is the team's actual system; the checkpointing file doubles as NoSQL depth practice, which is a named
probe in the design rounds.

---

## Files

| # | File | Priority | Est. time | Description |
|---|------|----------|-----------|-------------|
| 1 | [agent-architectures.md](agent-architectures.md) | Required | 60 min | Model/tools/memory/loop decomposition, tool schemas, single vs router vs handoff vs hierarchical, ReAct and plan-execute, and when an agent is the wrong answer |
| 2 | [langgraph-patterns.md](langgraph-patterns.md) | Required | 75 min | Graph as state machine, reducers, conditional routing, `Command(goto=...)`, supervisor pattern, parallel fan-out, interrupts, streaming — each mapped to its Akka analogue |
| 3 | [agent-state-and-checkpointing.md](agent-state-and-checkpointing.md) | Required | 60 min | Conversation state as a durability problem; designing a `DynamoDBSaver`: keys, item limits, conditional writes, TTL; the Akka Persistence parallel |
| 4 | [evaluating-agents.md](evaluating-agents.md) | Required | 90 min | Offline eval sets, golden trajectories, trajectory vs outcome, CI regression gates, online A/B and shadow — and the Lyft simulator distribution-shift case study generalised into eval validity |
| 5 | [llm-as-judge.md](llm-as-judge.md) | Recommended | 40 min | Rubric design, position and verbosity bias, pairwise vs pointwise, calibrating against human labels, where a judge quietly fails |
| 6 | [production-llmops.md](production-llmops.md) | Recommended | 60 min | Tracing, prompt registry and versioning, cost and token budgets, latency and streaming UX, caching, rate limits and failover, guardrails, PII |
| 7 | [rag-and-retrieval.md](rag-and-retrieval.md) | Recommended | 40 min | Chunking, embeddings, vector indexes, hybrid search, reranking, retrieval evaluation. Background, kept tight |
| 8 | [lyft-scc-case-study.md](lyft-scc-case-study.md) | Required | 45 min | Focused reconstruction of the target team's platform from published facts, plus questions to ask the interviewers |
| 9 | [ai-dev-tools-adoption.md](ai-dev-tools-adoption.md) | Required | 45 min | The position to argue on responsible adoption of AI development tools: where they help, review standards, security and IP, test discipline, measurement, rollout — with the honest counter-arguments |

Suggested reading order: 1 → 2 → 3 → 4 → 8, then 5, 6, 7 as needed, with 9 read before the behavioural
round.

---

## Related material already in this repo

| Topic | Where | Why it matters here |
|---|---|---|
| DynamoDB modelling | [dynamodb_refresher.md](../06-databases-and-distributed-data/dynamodb_refresher.md) | Prerequisite for the `DynamoDBSaver` design exercise |
| Event sourcing | [Event-Sourcing-Guide.md](../06-databases-and-distributed-data/Event-Sourcing-Guide.md) | Checkpointing is a snapshot store; the comparison is the point |
| Actor supervision | [AkkaActorsCore.md](../03-akka-ecosystem/AkkaActorsCore.md), [AkkaAdvanced.md](../03-akka-ecosystem/AkkaAdvanced.md) | Supervisors, routers, stash, restart strategies |
| Cluster sharding | [Akka_Cluster.md](../03-akka-ecosystem/Akka_Cluster.md) | Single-writer-per-conversation is exactly entity sharding |
| Backpressure | [akka_streaming_and_backpressure_detailed_guide.md](../03-akka-ecosystem/akka_streaming_and_backpressure_detailed_guide.md) | Contrast with push-only token streaming |
| Delivery guarantees | [Messaging-delivery_qos_dlq_ha.md](../07-messaging-and-streaming/Messaging-delivery_qos_dlq_ha.md) | At-least-once node execution, idempotency keys |
| Sagas and long-running workflows | [event_sourcing_cqrs_sagas_guide.md](../15-system-design/event_sourcing_cqrs_sagas_guide.md) | Human-in-the-loop interrupts are sagas with durable timers |
| Testing practice | [12-testing](../12-testing/README.md) | Trajectory invariants, mocks, property-based assertions |
| Security | [Security-threats.md](../11-security/Security-threats.md) | Prompt injection, egress, supply chain |

---

## Interview questions

**1. What experience do you have with LLM agent systems?** **[Reported at Lyft]** *(asked as "Tell me some experience related to ML or Gen AI")*
Answer from the systems side and be honest about the shape of the experience. An agent is a loop around
a stateless, non-deterministic RPC, and the hard parts are durable conversation state, supervision and
routing, at-least-once execution with idempotent side effects, and evaluation as a measurement problem
— all of which are 13 years of familiar work in new clothes. Then demonstrate depth on one concrete
thing rather than gesturing broadly.

**2. What is genuinely new about agents versus systems you have built before?**
A short list, and knowing it is short matters. Non-determinism in the control path, so you assert on
invariants and distributions instead of outputs. A finite context window that behaves like memory
pressure and needs an eviction policy. Cost as a first-class resource, so a retry storm is a budget
incident. Prompt injection, where all text reaching the context is untrusted with no escaping
primitive. And correlated failure between the agent and the instruments used to evaluate it.

**3. Why is "an agent is a distributed system" more than a metaphor?**
Because the operational problems are literally the same ones. Partial failure between a tool executing
and its result reaching the model is at-least-once delivery. A conversation pinned to one writer is
entity sharding. Checkpoint-per-superstep is snapshotting. Parallel tool calls are scatter-gather with
a join deadline. Node retry policies are supervision strategies. If you already have the reflexes, the
transfer is mostly vocabulary.

**4. Which of these files would you read first if you had one evening?**
`evaluating-agents.md`, because evaluation is where LLM systems stop being demos, it is where most
engineers are weakest, and Lyft has published a failure of their own that generalises into a genuinely
interesting statement about measurement validity. Then the case study, because knowing the team's
actual architecture changes the quality of every conversation in the loop.

**5. What is the single most transferable idea in this section?**
That an eval suite is a measurement instrument, and an instrument must not share a failure domain with
the thing it measures. Lyft's simulator reported 90% pass rates while production disagreed, because
LLM-generated users behave like helpful assistants and real customers are terse and impatient. That is
the same rule as never monitoring a service with something that depends on it — a rule any
infrastructure engineer already holds, applied somewhere new.
