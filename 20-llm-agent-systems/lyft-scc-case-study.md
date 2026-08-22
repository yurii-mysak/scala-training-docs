# Case Study: Lyft's Safety & Customer Care Agent Platform

> **Priority:** Required
> **Est. time:** 45 min
> **Track:** Both
> **HelloInterview:** Behavioral → Answering AI Questions

This is the flagship product of the team hiring. Walking in able to describe its architecture, name
the design decisions, and ask sharp questions about it is worth more than any amount of generic
AI knowledge. This file reconstructs the platform **from published facts only**, and marks clearly
where reconstruction becomes inference.

> **Discipline for the interview:** state the facts as facts, and label your reconstruction as
> reconstruction. "From what's public, it looks like X — is that right?" invites a conversation.
> Asserting an invented detail about their own system as fact ends one.

---

## 1 · The facts

Everything in this table is from public material. Nothing here is inferred.

| Fact | |
|---|---|
| **Scale** | 7 production agents, ~270,000 interactions/month |
| **Headline result** | 87% reduction in average resolution time |
| **Model** | Claude, accessed via **Amazon Bedrock** |
| **Orchestration** | **LangGraph** |
| **Observability / prompts** | **LangSmith**, including **Prompt Hub** |
| **Router** | A **meta agent acting as a stateful router**: classifies incoming requests and dispatches to specialist subagents via `Command(goto=...)` |
| **Segmentation** | **Separate rider and driver routers** |
| **Safety** | **Safety checks fanned out in parallel before any LLM reasoning** |
| **State** | A **custom `DynamoDBSaver` implementing LangGraph's `BaseCheckpointSaver`** |
| **Agent mix** | Hand-built specialist agents alongside **JSON-configured self-serve agents pulling prompts from LangSmith Prompt Hub** |
| **Published failure** | Their offline agent simulator showed **90% pass rates**, but production revealed a **distribution shift** — off-the-shelf LLM user simulators behave like "nice, helpful assistants" while real users send **brief, impatient messages**. Fixed by **fine-tuning simulators on real customer verbatims** |
| **Partnership** | A named Anthropic partnership that includes **Anthropic training Lyft engineers on AI-assisted development** |

Wider Lyft engineering context that bears on this system: Python is the primary backend language
(with Go), services talk over **Protocol Buffers / gRPC** through an **Envoy** service mesh, Flask for
Python APIs, AWS with Kubernetes, and DynamoDB is already used elsewhere in the estate.

---

## 2 · The architecture, reconstructed

```
                 rider / driver support entry point
                                │
                                ▼
        ┌──────── parallel safety checks (deterministic) ────────┐
        │   pii / abuse / incident classification, fanned out    │
        └───────────────────────┬───────────────────────────────┘
                                │  (implicit join before any LLM call)
                                ▼
                        meta agent — stateful router
                        classify intent, Command(goto=...)
                                │
              ┌─────────────────┴──────────────────┐
              ▼                                    ▼
        rider router                         driver router
              │                                    │
   ┌──────────┼──────────┐              ┌──────────┼──────────┐
   ▼          ▼          ▼              ▼          ▼          ▼
 specialist  specialist  self-serve   specialist  specialist  self-serve
 (hand-built)            (JSON cfg,   (hand-built)            (JSON cfg)
                          Prompt Hub)
              │                                    │
              └──────────► back to meta agent ◄────┘
                                │
                    resolve  |  escalate to human
                                │
                                ▼
                  DynamoDBSaver — checkpoint per superstep
                  LangSmith — traces, prompts, evals
```

**Which parts are stated and which are inferred:** the safety fan-out, the meta-agent router with
`Command(goto=...)`, the split rider/driver routers, the two flavours of specialist, the
`DynamoDBSaver`, and the LangSmith/Bedrock/LangGraph stack are all published. The specific specialist
agents, the exact safety checks, the return-to-router edge, and the escalation path are reasonable
reconstruction — say so if you draw this.

---

## 3 · The design decisions worth understanding

### 3.1 Meta agent as a *stateful* router

The word "stateful" is doing real work. A one-shot classifier hands the conversation off and
disappears; a stateful router stays in the loop, receives control back from the specialist, and can
re-classify mid-conversation. A user who opens with a billing question and then mentions a safety
incident gets re-routed.

* It also concentrates risk: router accuracy bounds system accuracy, since a misrouted request cannot
  be rescued by a perfect specialist. It is the first thing you would evaluate and the first thing you
  would alert on.
* Akka analogue: a parent that keeps the conversation and forwards to children, rather than handing the
  client a direct reference to a child. The parent stays in the supervision path.
* Mechanics in [langgraph-patterns.md](langgraph-patterns.md).

### 3.2 Safety checks in parallel, before any LLM reasoning

Two separable properties, and both are good:

* **Before** — an unsafe request never reaches a model at all. Compare with the weaker
  "generate then moderate", which pays for generation and relies on a second stochastic component to
  catch the first. The guard gates the model's *turn* rather than reviewing its *output*.
* **In parallel** — the checks cost `max(latency)` rather than `sum(latency)`, so safety is nearly free
  in the latency budget. That is what makes "always run them" affordable, and "always" is what makes a
  safety control real.

For a Safety & Customer Care org this is the load-bearing decision in the whole design: the invariant
is enforced by deterministic code, positioned upstream of the non-deterministic component.

### 3.3 Separate rider and driver routers

Two populations with different intents, different entitlements, different policies and different tool
sets. Splitting them gives each a smaller prompt and a smaller tool set — both direct accuracy wins —
plus independent evaluation, independent deploys, and blast-radius isolation: a rider-side prompt
change cannot regress driver support. It is bounded contexts applied to prompts.

### 3.4 A custom `DynamoDBSaver`

They implemented LangGraph's `BaseCheckpointSaver` against DynamoDB rather than using a stock backend.
Reasonable reading: DynamoDB is already in the estate, it fits the access pattern (everything is keyed
by conversation), and it gives managed durability, TTL and streams without new operational surface.

The interesting engineering is in what that implementation must get right — key design, the 400 KB item
limit against a growing conversation, conditional writes for concurrency, TTL versus real deletion.
That is worked through in
[agent-state-and-checkpointing.md](agent-state-and-checkpointing.md), and it is the most likely place
for this case study to turn into a design-round conversation.

### 3.5 Hand-built plus JSON-configured self-serve agents

The platform decision. Hand-built agents where the logic is intricate; configuration-driven agents,
pulling prompts from Prompt Hub, for the long tail. The marginal cost of the twentieth agent has to
approach zero or a platform team becomes a bottleneck.

The trade-off to name: **configuration is a deployment channel**. A prompt edit changes production
behaviour, so the self-serve path needs the same gates as the code path — versioning, staged rollout,
an eval gate, one-click rollback — or it is a way to bypass every control you placed on code. See
[production-llmops.md](production-llmops.md#3--prompt-versioning-and-a-prompt-registry).

### 3.6 Claude via Bedrock

Going through a cloud provider's model service rather than a vendor API directly is usually a
governance and procurement decision as much as a technical one: existing AWS controls, IAM, VPC
endpoints, data-handling terms and regional routing. It also constrains you — model version
availability and region coverage are the provider's schedule, not yours.

---

## 4 · Reading the numbers

Public figures: 7 agents, ~270k interactions/month, 87% reduction in average resolution time.
The arithmetic below is your own inference from those figures — present it that way.

* **Rate**: 270,000 / (30 x 86,400) ≈ **0.1 interactions/s** average. Even a 20x peak is ~2/s. So
  throughput is not the engineering challenge; **state size, latency, correctness and safety are.**
  Noticing that is a better signal than being impressed by the number.
* **Per agent**: ~38k interactions/month each if evenly spread, which they will not be — support
  volume is heavily skewed by intent. Worth asking about.
* **87% reduction in average resolution time** is a *latency* metric. The natural engineering
  questions: what happened to resolution *quality*, to repeat-contact rate, and to the *distribution*
  rather than the average? An average can improve 87% while a tail gets much worse. Asking this shows
  you read metrics like an engineer rather than like a press release.

---

## 5 · The published failure, and why it matters

They published that their offline simulator reported **90% pass rates** while production revealed a
**distribution shift**: off-the-shelf LLM user simulators behave like nice, helpful assistants; real
customers send brief, impatient messages. They fixed it by fine-tuning simulators on real customer
verbatims.

Three things to take from it:

1. **It is a measurement-validity failure, not a model failure.** The harness worked; the population it
   sampled was wrong. Sampling error shrinks with more examples; validity error does not shrink at all.
2. **The specific mechanism is instructive.** An agent whose recovery strategy is "ask a clarifying
   question" scores well against a cooperative simulator and collapses against a user who answers
   clarification with "just fix it". The failing case was never in the test population.
3. **A team that publishes this is a team worth joining, and worth engaging on.** Complimenting the
   write-up and then asking what they instrumented afterwards is a much better conversation than
   reciting it back.

Full treatment, including how to detect this class of failure before production and the general
statement about correlated instruments, is in
[evaluating-agents.md](evaluating-agents.md#9--case-study-the-simulator-that-lied). That generalisation
is the differentiating material; this file is the facts it rests on.

---

## 6 · Where 13 years of distributed systems maps onto this

Useful to have rehearsed, because "why you" for this specific team is a question with a good answer.

| Their problem | Your prior art |
|---|---|
| Stateful router dispatching to specialists | Actor supervision hierarchies, routers, `become`-driven FSMs |
| Conversation state, durable, resumable | Akka Persistence, event sourcing, CQRS, snapshotting |
| `DynamoDBSaver` key design, item limits, conditional writes | Distributed data modelling, partition-key design, optimistic concurrency |
| Parallel fan-out and joins before reasoning | Akka Streams graph DSL, scatter-gather, `Future.sequence` |
| At-least-once node execution with side effects | Idempotency keys, exactly-once semantics work, delivery guarantees |
| Human-in-the-loop interrupts that resume hours later | Sagas, durable timers, long-running workflow orchestration |
| Rate limits, provider failover, degraded paths | Circuit breakers, bulkheads, backpressure, load shedding |
| Evaluation as a measurement instrument | Monitoring that does not share a failure domain with the thing it monitors |
| Multi-team platform with self-serve configuration | Platform and API design, schema evolution, blast-radius control |

The honest gap is Python fluency and hands-on LangGraph, not the systems thinking. Say that plainly if
asked — a Staff candidate who can name their own gap precisely reads as more senior than one who
cannot.

---

## 7 · Questions to ask your interviewers

These are questions *you* ask *them* — distinct from the `## Interview questions` section below, which
is what they may ask you. Pick four or five; they signal more than any answer you give.

**Architecture**

1. Is the meta agent's classification a single model call, or has it grown into its own graph?
2. When a specialist can't resolve something, does control return to the meta agent, or does the
   specialist escalate directly? How do you avoid ping-ponging between agents?
3. How much state does a specialist subagent get — the full conversation, or a projection the router
   builds for it?
4. Did splitting rider and driver routers come from prompt accuracy, from team ownership, or from
   authorisation boundaries?
5. What is in the parallel safety fan-out today, and how has that set changed since launch?

**State and durability**

6. How do you handle checkpoint growth against DynamoDB's item-size limit on long conversations —
   summarisation, externalising the blob, or capping conversation length?
7. What happens when a user double-sends, or when a human support agent takes over a thread the bot is
   mid-turn on? Is there a single-writer guarantee per `thread_id`?
8. How do you deal with state-schema changes while conversations are in flight?

**Evaluation**

9. After the simulator distribution-shift finding, what did you put in place to detect that class of
   problem earlier? Is anything monitoring the correlation between offline scores and online outcomes?
10. What is blocking in CI versus reported-only, and how did you pick the thresholds?
11. The 87% figure is an average — how did the distribution and the repeat-contact rate move?

**Platform and organisation**

12. What does the self-serve path look like end to end for a team that wants a new agent, and what gates
    does a prompt change pass before it reaches production?
13. What is the split of your time between building agents and building the platform, and where is that
    heading?
14. Where does the platform team's ownership stop and the requesting team's begin — who is on call when
    a self-serve agent misbehaves?
15. What does the Anthropic partnership look like day to day for an engineer on this team?

**Roadmap**

16. What is the hardest unsolved problem on this platform right now?
17. What would agent number 20 need that agent number 7 did not?

---

## 8 · Cross-references

* [agent-architectures.md](agent-architectures.md) — router and hierarchical topologies.
* [langgraph-patterns.md](langgraph-patterns.md) — the graph mechanics, with this platform as the example.
* [agent-state-and-checkpointing.md](agent-state-and-checkpointing.md) — the `DynamoDBSaver` design exercise.
* [evaluating-agents.md](evaluating-agents.md) — the simulator case study, generalised.
* [ai-dev-tools-adoption.md](ai-dev-tools-adoption.md) — the other half of the AI-related job description.

---

## Interview questions

**1. Tell me some experience related to ML or Gen AI.** **[Reported at Lyft]**
Lead with systems, not models: durable conversation state, supervision and routing, at-least-once
execution with idempotent side effects, evaluation as a measurement problem. Be explicit that you have
built distributed systems for 13 years and have been going deep on agent systems specifically — naming
the gap is stronger than papering over it. Then show the depth is real by discussing something concrete,
such as what a DynamoDB-backed checkpointer has to get right.

**2. Why do Lyft's safety checks run in parallel and before any LLM call?**
Two separate wins. Running before means an unsafe request never reaches a model, so the invariant is
enforced by deterministic code rather than by a second stochastic component reviewing the first.
Running in parallel means they cost the max of their latencies, not the sum, which is what makes
"always run them" affordable — and a safety control that is skipped under load is not a control.

**3. Why would a stateful router be better than a one-shot classifier?**
Because support conversations change subject. A stateful router keeps the turn, gets control back from
the specialist, and can re-classify when a billing conversation turns into a safety report. It also
keeps the escalation path in one place. The cost is that router accuracy bounds system accuracy — a
misrouted request cannot be rescued by a perfect specialist — so it is the first thing to evaluate and
alert on.

**4. Why implement a custom checkpointer instead of using a stock backend?**
Because the state store should be something the org already runs. DynamoDB was already in the estate,
the access pattern is a perfect fit — everything is keyed by conversation, "latest checkpoint" is one
query on a time-ordered sort key — and it brings managed durability, TTL and streams with no new
operational surface. The interesting work is in the details: item-size limits against growing
histories, conditional writes for concurrency, and real deletion versus TTL.

**5. What would you want to know before making changes to that platform?**
Where the state actually lives and how big it gets; what the single-writer story is per conversation;
what is gated in CI versus reported; how a prompt change reaches production on the self-serve path and
how it is rolled back; and what the degraded path is when Bedrock is unavailable. Those five answers
determine what can be changed safely and what needs to be built first.

**6. What do you make of the 87% resolution-time reduction?**
It is a real and large result, and it is a latency metric on an average. The engineering questions it
raises are what happened to resolution quality, to repeat-contact rate, and to the distribution rather
than the mean — an average can improve enormously while a tail gets worse, and in a support context the
tail is where the harm lives. I would want resolution rate paired with false-resolution rate before
concluding.

**7. How would you add the eighth agent to this platform?**
Through the self-serve path if it fits, because the marginal cost of the next agent is the thing that
determines whether a platform scales. That means: a JSON configuration, prompts versioned in the
registry, a tool set scoped to least privilege, and an eval set stood up before launch rather than
after. Then a shadow run on real traffic, a ramp with guardrail metrics, and a rollback path. If it does
not fit the self-serve shape, the interesting question is which platform primitive is missing.

**8. What is the biggest risk you see in this architecture?**
The self-serve configuration path, if it lacks the gates the code path has. Configuration that changes
production behaviour without review, eval and staged rollout is a way to bypass every control placed on
code — and prompts are logic. Second would be checkpoint growth against DynamoDB's 400 KB item limit,
which is the kind of constraint that is invisible until a long conversation hits it in production.

**9. Why did you choose Lyft?** **[Reported at Lyft]**
Answer specifically or do not bother. The honest version here: a production multi-agent platform at real
scale, in a safety domain where being wrong actually matters, run by a team that publishes its own
failures — the simulator distribution-shift write-up is a team being intellectually honest in public.
Plus the problems are the ones I have spent 13 years on wearing new clothes: durable state, supervision,
routing, delivery guarantees.
