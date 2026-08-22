# AI and GenAI Behavioural Questions

> **Priority:** Recommended
> **Est. time:** 40 min
> **Track:** Both
> **HelloInterview:** Behavioral — Answering AI Questions

**"Tell me some experience related to ML or Gen AI"** is a newer reported Lyft question. On this team
it is not small talk: they run a LangGraph multi-agent customer-support platform with seven
production agents at roughly 270k interactions a month.

The trap is obvious once stated. You have no ML background, and the team does. Overclaim and you are
caught in the first follow-up by someone who does this daily. Underclaim and you look uninterested in
the thing the team actually builds.

---

## 1 · What the question is really asking

| Surface reading | What is being tested |
|-----------------|----------------------|
| "Have you done ML?" | Rarely. They are not hiring an ML engineer for a platform team. |
| "Can you talk about this without being useless?" | Yes. Can you hold a technical conversation about agent systems at the systems level. |
| "Are you honest about what you don't know?" | Yes, and heavily — this is a **Be yourself** probe wearing a technical costume. |
| "Will you engage with the domain or resent it?" | Yes. A candidate who treats LLM work as not-real-engineering is a bad fit for this specific team. |

The strongest answer available to you is: **the hard parts of their platform are distributed-systems
problems you have thirteen years in, the LLM layer is genuinely new to you, and you are already
using the tooling seriously.** All three clauses are true, which is why it holds up under drilling.

---

## 2 · The credibility ladder

Claim only from the rungs you actually stand on, and say which rung you are on.

| Rung | Claim | Can you say it |
|------|-------|----------------|
| 5 | I have trained or fine-tuned models in production | No. Never claim this. |
| 4 | I have shipped LLM-backed features to production users | Only if literally true. If not, do not imply it. |
| 3 | I have built with LLM APIs and agent frameworks non-trivially | Only if you have. Be ready to name the framework and a failure mode you hit. |
| 2 | I use AI dev tooling seriously and have opinions on where it fails | **Yes** — and this is a legitimate, current, checkable answer. See section 4. |
| 1 | I have read their engineering write-ups and can reason about the architecture | **Yes** — and it is worth more than most candidates realise. |
| 0 | I have no exposure | Do not say this. It is not true and it forecloses the conversation. |

Answer from rungs 1 and 2, and say explicitly that you are not on rungs 4 and 5. The explicit
disclaimer is what makes the rest credible.

### 2.1 The one sentence that does the most work

> "I'm not an ML engineer and I won't pretend to be — what I've got is the systems half of it, and
> I've been using the tooling hard enough to have opinions about where it breaks."

Say it early. It converts the whole answer from a claim into an assessment, and assessments survive
follow-ups that claims do not.

---

## 3 · The systems bridge — where your actual depth lands

This is the substance of the answer. Their published architecture is a distributed state machine, and
each component maps to something you have shipped.

| Their component | The distributed-systems problem underneath | Your ground |
|-----------------|-------------------------------------------|-------------|
| Meta agent as a **stateful router** dispatching via `Command(goto=...)` | Routing with persistent per-conversation state; classification as a dispatch decision | Actor supervision and message routing; state machines per entity |
| Custom **`DynamoDBSaver`** implementing `BaseCheckpointSaver` | Checkpointing a long-running workflow; recovery after failure; write patterns and item-size limits | Event sourcing, snapshots, projection rebuild — see [Event Sourcing](../06-databases-and-distributed-data/Event-Sourcing-Guide.md), [DynamoDB](../06-databases-and-distributed-data/dynamodb_refresher.md) |
| **Safety checks fanned out in parallel** before any LLM reasoning | Parallel fan-out with a hard ordering barrier; fail-closed semantics; latency budget across a scatter-gather | Akka Streams fan-out/fan-in, backpressure, [Delivery, QoS, DLQ](../07-messaging-and-streaming/Messaging-delivery_qos_dlq_ha.md) |
| Separate rider and driver routers | Domain partitioning of a shared platform; per-tenant divergence without forking | Microservice boundaries, bounded contexts |
| **JSON-configured self-serve agents** pulling prompts from a prompt hub | Config-as-data platform with internal customers; versioning and rollback of behaviour | Platform work, schema evolution, [gRPC & Protobuf](../15-system-design/grpc_protobuf_schema_design.md) |
| Retries against a non-deterministic, expensive, slow dependency | Idempotency, timeouts, budget-aware retry, partial failure | Exactly-once semantics, idempotency keys, saga compensation |

### 3.1 The question underneath the question

If they want to see whether you can *think* about this domain, the highest-value thing you can say is
about **evaluation and non-determinism**: an LLM call is a dependency that is slow, costly,
occasionally wrong, and not reproducible. Everything hard about the platform follows from that —
you cannot write a deterministic integration test, you cannot bound tail latency the usual way, and
your correctness signal is statistical rather than binary.

That framing is available to you from first principles and it is the actual engineering content of
their domain.

---

## 4 · Answering from rung 2 — AI dev tools

Your strongest honest experiential answer is adoption of AI development tooling, which is also
organisational evidence and therefore Staff-shaped rather than merely technical.

Structure it as Slot 11 in [story-bank.md](story-bank.md) — driving adoption of something new:

- What you introduced, and what people did before.
- Why the status quo held (usually a legitimate concern: review load, correctness, IP, or trust).
- What you measured. Adoption count, review turnaround, defect rate, time-to-first-PR for new joiners.
- **Where it fails.** This is the differentiating half. Opinions on where AI tooling produces
  plausible-but-wrong output, and what guardrails you put around it, are worth more than enthusiasm.
- What you would not use it for.

Full treatment of the adoption position, including the Anthropic-partnership context:
[../20-llm-agent-systems/ai-dev-tools-adoption.md](../20-llm-agent-systems/ai-dev-tools-adoption.md).

The relevance is direct: Lyft's Anthropic partnership includes Anthropic training Lyft engineers on
AI-assisted development. A candidate who has already driven that adoption at their own company is
answering a question the team is actively working on.

---

## 5 · The distribution-shift story as shared ground

Lyft published an honest failure: their offline agent simulator showed roughly 90% pass rates, but
production revealed a **distribution shift** — off-the-shelf LLM user simulators behave like nice,
helpful assistants, while real users send brief, impatient messages. They fixed it by fine-tuning
simulators on real customer verbatims.

This is the most useful single fact you have, for three reasons:

1. **It is a testing problem, not an ML problem.** Your test distribution did not match production.
   That is a bug class you have hit in load testing, in synthetic data, in staging environments that
   were too clean. You can speak about it from experience without claiming any ML knowledge —
   see [Load Testing](../12-testing/Testing-load_testing.md) and
   [Property-Based Testing](../12-testing/Testing-property_based.md).
2. **It is a measurement problem**, which connects to the "how did you measure?" thread running
   through the whole round: a metric that looked good and was measuring the wrong population.
3. **It is a legitimate question to ask them.** See
   [questions-to-ask-them.md](questions-to-ask-them.md).

Use it as *analogy*, not as flattery. "That's the same failure mode as a load test built from a
synthetic traffic profile that doesn't match the real request mix" is a peer-level observation.
"I loved your blog post" is not.

---

## 6 · Answer template, 90 seconds

1. **Position yourself honestly** (10s): not an ML engineer, have the systems half, using the tooling
   seriously.
2. **Rung-2 experience** (30s): the AI-dev-tools adoption story, with an adoption number and a
   failure mode you found.
3. **Systems bridge** (30s): one concrete mapping from section 3 — the checkpointer or the parallel
   safety fan-out is the best one, because it is unambiguously a distributed-systems problem.
4. **What you would need to learn** (10s): name it specifically — evaluation methodology, prompt
   versioning discipline, cost-per-interaction budgeting — rather than saying "the AI side".
5. **Hand it back** (10s): a question about how they evaluate, or how the self-serve agents are
   validated before they go live.

Ending on a question is deliberate. It converts a weakness-shaped question into a technical
conversation between peers, which is the outcome you want.

---

## 7 · Failure modes

| Anti-pattern | Why it fails |
|--------------|--------------|
| Reciting LLM vocabulary (RAG, embeddings, vector DBs, temperature) with no experience behind it | The interviewer builds these daily. One follow-up exposes it, and you have now also failed **Be yourself**. |
| Claiming a side project as production experience | Say "side project" if it is one. The word costs nothing and buys credibility. |
| "AI is just calling an API" | Dismissive of the team's work, and factually wrong about the hard parts. Disqualifying on fit. |
| Long enthusiasm with no engineering content | Reads as a candidate who has read headlines. |
| Ignoring the question and pivoting to distributed systems | The bridge must be explicit — connect *their* component to *your* experience, do not just change subject. |
| Overstating the AI-tools adoption number | It is checkable in principle and it is a small claim. State the real count. |

---

## Interview questions

**1. Tell me some experience related to ML or Gen AI.** **[Reported at Lyft]**
Position honestly first: not an ML engineer, strong on the systems half, using the tooling seriously
enough to have opinions about its failure modes. Then one rung-2 story with a number, then one
explicit mapping from their architecture to something you have built. Finish with what you would need
to learn, named specifically.

**2. What do you think is hard about running agents in production?**
Non-determinism turns every familiar guarantee into a statistical one: no deterministic integration
tests, unbounded tail latency on an external dependency, cost per request that varies with input, and
retries that are not idempotent by default. Then state persistence and recovery mid-conversation.

**3. How would you test a multi-agent system?**
Separate the deterministic scaffolding — routing, checkpointing, safety fan-out, retries — which you
test conventionally, from the model behaviour, which needs an evaluation set drawn from real traffic.
Name the distribution-shift risk explicitly: a synthetic evaluation population that does not match
production is a measurement bug, not a model bug.

**4. Have you used LangGraph or similar frameworks?**
Answer literally. If not, say so, then describe what you understand the shape to be — a graph of
nodes over shared state with a checkpointer for durability — and ask what forced them to write a
custom `BaseCheckpointSaver` rather than use an off-the-shelf one. Honest plus curious beats vague
plus confident.

**5. How have you used AI tools in your own development work?**
Rung 2, and answer it as an adoption story rather than a personal-productivity story: what you rolled
out, what people did before, the adoption count, and the guardrail you added after finding where it
produced plausible-but-wrong output.

**6. Where do you think AI coding tools shouldn't be used?**
Have a real answer. Typical ground: anything where a plausible-looking wrong result is expensive and
hard to detect — security-sensitive code, data migrations, concurrency primitives — and anywhere the
reviewer would not have caught the error unaided.

**7. Our offline evaluation looked good but production didn't match. What would you check?**
The population, first: how the evaluation inputs were generated and whether that distribution matches
real traffic. Then the metric definition, the sampling window, and whether the offline harness shares
the production code path. This is their published simulator problem, and it is a testing question.
