# Production LLMOps

> **Priority:** Recommended
> **Est. time:** 60 min
> **Track:** Both
> **HelloInterview:** System Design in a Hurry → Core Concepts → Caching

Running an agent platform is running a distributed system whose most important dependency is a
third-party service with variable latency, variable output, rate limits, and periodic silent behaviour
changes. Almost everything here is a familiar operational practice with one twist. The twist is worth
naming each time, because that is what turns "I have read about this" into "I have run this".

Lyft's stack, per public material: **Claude via Amazon Bedrock**, **LangGraph** for orchestration,
**LangSmith** for tracing and prompt management, DynamoDB for state.
See [lyft-scc-case-study.md](lyft-scc-case-study.md).

---

## 1 · Tracing: the non-optional part

You cannot debug an agent from logs. The unit of investigation is the **trajectory**, and a trajectory
is a tree, not a line. Tracing is not an observability nicety here; it is the primary debugging
interface and the raw material for every eval in
[evaluating-agents.md](evaluating-agents.md).

Span hierarchy that works:

```
run (thread_id, user_id_hash, entry_point)
├── superstep 1
│   ├── node: safety_pii            (deterministic, 12 ms)
│   ├── node: safety_abuse          (deterministic, 18 ms)
│   └── node: safety_incident       (deterministic, 9 ms)
├── superstep 2
│   └── node: meta_router
│       └── llm_call (model, version, prompt_version, in/out tokens, cost, ttft, cache hit)
├── superstep 3
│   └── node: billing_agent
│       ├── llm_call
│       ├── tool_call: get_ride_receipt   (latency, status, retries, bytes returned)
│       └── llm_call
└── outcome (resolved | escalated | abandoned | budget_exceeded)
```

Attributes worth carrying on every span, because you will want to slice on all of them:
`thread_id`, `checkpoint_id`, `prompt_version`, `model_version`, `agent_name`, `route`,
`user_kind` (rider/driver), `tokens_in`, `tokens_out`, `cost_cents`, `cache_hit`, `ttft_ms`,
`outcome`, `experiment_variant`, `eval_run_id`.

Details that matter in practice:

* **Correlate with the rest of the estate.** The trace id must join to the service-mesh request id, so
  an agent trace and the downstream service traces are one picture. At Lyft that means Envoy request
  ids. See [instrumenting Python services](../19-observability-and-oncall/instrumenting-python-services.md)
  and [metrics, logs and traces](../19-observability-and-oncall/metrics-logs-traces.md).
* **Sampling.** Head sampling loses the interesting runs. Sample all errors, all escalations, all
  budget-exceeded runs, all experiment traffic, and a percentage of the rest — tail-based where the
  infrastructure supports it.
* **Retention is a cost line.** Full trajectories with message bodies are large. Two tiers: short
  retention for full payloads, long retention for metadata and metrics.
* **The trace is a PII store.** It holds raw user messages. Same access controls, redaction and deletion
  path as the checkpoint store — §9.

---

## 2 · What to log, and what never to log

| Log | Do not log |
|---|---|
| Prompt *version identifier* | Full prompt text on every call (log the hash, store the version once) |
| Token counts and cost | Raw payloads in application logs (they belong in the trace store, with access control) |
| Tool name, latency, status | Tool arguments containing PII, unredacted |
| Model and provider version | Credentials, obviously — and note the model output can contain them if a tool returned them |
| Outcome and route | Anything you cannot delete on a user's request |

The uncomfortable one: **a model's output can leak whatever was in its context.** If a tool returned a
full customer record, that record can end up in the reply, the trace and the log. Redact at the tool
boundary, on the way in, not at the presentation layer on the way out.

---

## 3 · Prompt versioning and a prompt registry

Prompts are the highest-churn, highest-blast-radius artifacts in the system and they are frequently
edited by people who are not deploying code. Treat them as **releasable artifacts**.

Requirements:

| Requirement | Why |
|---|---|
| Immutable versions with content-addressed ids | So a trace can name exactly what ran |
| Environment pinning (dev / staging / prod point at explicit versions) | So editing a prompt does not change production |
| Promotion flow with an eval gate | A prompt change is a release; it goes through the offline suite |
| Instant rollback | The commonest incident is a prompt change; the commonest fix is reverting it |
| Diff and review | Prompts are logic. Two-person review for production prompts |
| Templated variables with validation | An unfilled placeholder should fail loudly, not ship `{user_name}` to a customer |

LangSmith's **Prompt Hub** is this registry, and Lyft's **JSON-configured self-serve agents pull their
prompts from it**. That is the important architectural consequence: it turns "add an agent" from a code
change into a configuration change, which is what makes 7 production agents — and the next 20 —
tractable for one platform team.

The trade-off has to be stated, because it is the Staff-level observation: **configuration is a
deployment channel with no code review by default.** If a prompt edit reaches production without an
eval gate, you have built a way to change production behaviour that bypasses every control you put on
code. The self-serve path needs the same gates as the code path — versioning, staged rollout,
automatic eval, rollback — or it is a liability rather than leverage.

---

## 4 · Cost and token budgeting

Cost is a resource dimension with the same operational shape as memory: it is finite, it is consumed by
retries, and unbounded consumption is an incident.

**Where the tokens go.** Per-conversation token use grows roughly **quadratically** with turn count,
because turn *k* re-sends turns 1..*k-1*. Long conversations, and verbose tool results, dominate the
bill. Napkin math and the 270k/month arithmetic are in
[agent-architectures.md](agent-architectures.md#7--napkin-math-to-have-ready).

**Controls, in the order I would apply them:**

| Control | Typical effect |
|---|---|
| Trim or summarise history beyond N turns | Attacks the quadratic directly; the largest single lever |
| Keep tool results small (paginate, project, summarise at the tool boundary) | Tool output is usually bigger than human text and is re-sent forever |
| Prompt/prefix caching for the stable system prompt and tool schemas | Large saving on the fixed prefix, which is most of a short turn |
| Smaller model for the router and for extraction | The router runs on every request; it does not need the frontier model |
| Store retrieval ids, not retrieved text, in state | Also fixes the checkpoint size problem |
| Hard caps: max steps, max tokens, max cost per conversation | The backstop. Exceeding is a designed outcome (escalate), not an exception |

**Budget enforcement must be durable.** If the counter lives in memory, a retry resets it and the cap
does nothing. It belongs in checkpointed state —
[agent-state-and-checkpointing.md](agent-state-and-checkpointing.md).

**Make cost an SLO.** "Cost per resolved conversation, p95" on a dashboard, alerted, with a named owner.
Cost regressions otherwise surface as a finance question a month later.

---

## 5 · Latency budgets and streaming UX

Where the time goes in a typical support turn:

| Stage | Order of magnitude |
|---|---|
| Deterministic safety checks (parallel) | 10-50 ms |
| Router model call | 300 ms - 1 s (small model, short prompt) |
| Specialist model call | 1-3 s |
| Tool calls | 50 ms - 2 s each, parallelisable |
| Final composition call | 1-3 s |

A four-call trajectory is comfortably 5-8 seconds. Three ways to make that acceptable:

1. **Optimise time-to-first-token, not total.** Stream. Perceived latency is dominated by TTFT. Budget
   and alert on TTFT separately from end-to-end.
2. **Parallelise everything independent.** Safety checks in one superstep, independent tool calls in one
   step. Cost becomes `max` rather than `sum` — this is why Lyft's parallel safety fan-out is a latency
   decision as much as a safety one.
3. **Emit progress, not a spinner.** Node-level events ("checking your recent rides") are free and
   change the perceived experience more than shaving a second.

Also: **speculative work.** While the router classifies, start the retrieval or the profile fetch that
most routes will need. Wasted work is cheap relative to a second of user-visible latency — the same
trade you make with prefetching.

---

## 6 · Caching

| Cache | Key | Risk |
|---|---|---|
| **Prompt / prefix cache** | The provider's cache of a stable prompt prefix | Low. Requires stable ordering: system prompt and tool schemas first, volatile content last. A single reordered token invalidates the prefix |
| **Exact-match response cache** | Hash of the full request | Low, but the hit rate on conversational traffic is near zero |
| **Semantic cache** | Embedding similarity to a previous query | **High.** "Refund my ride from Tuesday" and "Refund my ride from Thursday" are semantically close and factually different. Only safe for content with no user-specific or time-specific answer, and even then with a conservative threshold |
| **Embedding cache** | Document hash | Low. Pure saving |
| **Tool-result cache** | Tool + arguments, short TTL | Correctness risk if state changed. Never cache across users; scope the key to the identity |
| **Idempotency cache** | Client idempotency key | Not a cache so much as a duplicate-suppression store, but it lives in the same layer |

**Prefix caching is the one to actually build for.** It changes the arithmetic of long system prompts:
a 4k-token tool schema block that is cached costs a fraction of an uncached one, so the design question
"can we afford this many tool definitions" gets a different answer. It requires discipline about
prompt ordering, which is a good reason to construct prompts programmatically rather than by
concatenating strings in each agent.

Semantic caching is where teams hurt themselves. In a support context, where answers depend on *this*
user's *specific* ride, the safe scope is narrow: policy questions, how-to answers, general FAQ. Never
transactional answers.

---

## 7 · Rate limits, retries, provider failover

This is the "web application with a lot of third-party dependencies that have a variety of failure
modes" question, which is a reported Lyft design prompt, applied to model providers.

| Failure | Handling |
|---|---|
| **429 / throttling** | Exponential backoff with jitter; respect `retry-after`. Client-side token-bucket so you shape load rather than discovering the limit |
| **Provider 5xx** | Retry with backoff, bounded. Circuit breaker so a sick provider does not consume your whole thread pool |
| **Timeout** | Per-call deadline derived from the remaining request budget, not a fixed constant. A call that cannot finish inside the remaining budget should not be started |
| **Sustained outage** | Failover: alternate region for the same model, then a fallback model, then a degraded non-agent path (FAQ + escalate to human). Decide the ladder in advance |
| **Quota exhaustion** | Per-tenant and per-agent quotas so one runaway agent cannot starve the rest. Bulkheads |
| **Long-tail latency** | Hedged requests for short idempotent calls (router, classification). Not for generation — you would pay twice for the expensive call |
| **Silent model update** | Pin model versions. Treat provider version changes as dependency upgrades with an eval gate |

**The degraded path is the design.** An agent platform without a defined non-agent fallback has made
the model provider a hard dependency of customer support. The fallback for a support agent is
concrete and cheap: serve the FAQ, collect the request, queue it for a human, tell the user honestly.
Test it — a fallback path that has never run in anger does not work.

**Load shedding.** Under overload, shed the least valuable work first: retries before first attempts,
low-priority agents before safety-critical ones, speculative work before required work. Queue with a
deadline and drop requests whose deadline has passed rather than doing work nobody is waiting for.

---

## 8 · Guardrails and safety

Layered, and the ordering is the point:

1. **Input guardrails, deterministic, before the model.** PII detection, abuse detection, incident
   keywords, allow-list of supported topics. Fan out in parallel. This is the Lyft pattern.
2. **Tool authorisation, in code.** The model requests; your runtime authorises against the actual user's
   actual entitlements. A prompt saying "only refund rides belonging to this user" is not an
   authorisation mechanism.
3. **Structural limits.** Read tools freely; write tools gated, rate-limited, amount-capped, and for
   irreversible actions, interrupted for human approval.
4. **Output guardrails.** Policy classifier, PII scan on the way out, required-disclaimer checks.
   Necessary, but weaker than input guardrails, because by this point you have paid for generation and
   are relying on a second stochastic component.
5. **Prompt injection.** Any text reaching the context is untrusted: user messages, ticket bodies,
   retrieved documents, tool results. There is no escaping primitive equivalent to a prepared
   statement, so the mitigation is structural — least privilege on tools, deterministic authorisation,
   human gates on irreversible actions, and never letting retrieved content decide what tool to call.
   See [security threats](../11-security/Security-threats.md).

**The rule from [agent-architectures.md](agent-architectures.md): models choose among legal options,
code decides which options are legal.**

---

## 9 · PII in a support context

Support conversations are dense with personal data — names, addresses, pickup and dropoff locations,
payment details, and whatever the user volunteers.

* **Redact on the way in.** Detect and tokenise before the message reaches the model where you can
  (`<CARD_1>`, `<ADDRESS_2>`), rehydrate on the way out if a tool needs the real value. Reduces exposure
  to the provider and shrinks the blast radius of a trace leak.
* **PII lands in four places**: the checkpoint store, the trace store, application logs, and the eval
  corpus. A deletion path that covers only the first is not a deletion path.
* **De-identify eval fixtures at capture time**, not later. Then an erasure request does not invalidate
  your eval set — the honest resolution of a genuinely awkward conflict.
* **Data residency and vendor terms.** Which region does the model call go to, and what may the provider
  do with the payload? Using a model through a cloud provider's own service (Bedrock) rather than
  directly is frequently a data-governance decision as much as a procurement one.
* **Access control on traces.** A trace viewer showing raw customer conversations is a customer-data
  system. Authenticate, authorise, audit access, and set retention.
* **Encryption**: at rest with a customer-managed key where policy requires it, in transit everywhere.
  See [security cryptography](../11-security/Security-cryptography.md).

---

## 10 · Deploy, rollback, on-call

**Things that can change behaviour in production**, each needing its own release discipline:

| Change | Gate |
|---|---|
| Code (graph topology, tools) | Normal CI/CD, plus offline eval |
| Prompt version | Eval gate, staged rollout, one-click rollback |
| Model version | Full offline eval, shadow, then A/B. Never an in-place swap |
| Tool schema / description | Eval gate — a description edit changes selection behaviour as much as a code change |
| Config for a self-serve agent | Same gates as prompts, enforced by the platform |
| Provider-side model update | Not yours to control: pin versions so it cannot happen implicitly |

**SLOs for an agent platform:** availability, p95 end-to-end latency, p95 TTFT, harmful-action rate,
cost per resolved conversation, false-resolution rate.

**Alerts that are actually actionable:** escalation-rate spike (something broke upstream of the human
handoff), budget-exceeded rate, tool error rate by tool, router-distribution shift (traffic suddenly
routing differently means either the world changed or a prompt did), TTFT regression, cache-hit-rate
collapse.

**Runbook entries worth having before you need them:** how to roll back a prompt; how to disable one
agent and route its traffic to escalation; how to switch region or model; how to drain and expire
interrupted threads; how to find every conversation affected by a bad prompt version (this is why
`prompt_version` is on the span).

---

## 11 · Cross-references

* [Instrumenting Python services](../19-observability-and-oncall/instrumenting-python-services.md) and
  [metrics, logs and traces](../19-observability-and-oncall/metrics-logs-traces.md) — the general
  tracing and metrics practice this specialises.
* [SLOs and error budgets](../19-observability-and-oncall/slos-and-error-budgets.md),
  [alert design](../19-observability-and-oncall/alert-design.md) — §10 applies both to agent platforms.
* [evaluating-agents.md](evaluating-agents.md) — traces feed the eval corpus.
* [agent-state-and-checkpointing.md](agent-state-and-checkpointing.md) — the other PII store.
* [Security: threats](../11-security/Security-threats.md),
  [cryptography](../11-security/Security-cryptography.md).
* [Delivery QoS, DLQ, HA](../07-messaging-and-streaming/Messaging-delivery_qos_dlq_ha.md) — retries,
  idempotency, dead-lettering.

---

## Interview questions

**1. A web application depends on several third-party services with different failure modes. How do you keep it reliable?** **[Reported at Lyft]**
Isolate each dependency: its own timeout derived from the remaining request budget, its own circuit
breaker, its own connection pool so one sick dependency cannot starve the others. Retry with jittered
backoff and a bound, respecting `retry-after`. Define the degraded path per dependency in advance and
exercise it — for a model provider that ladder is alternate region, fallback model, then a non-agent
path that serves the FAQ and queues a human. Shed load by priority under overload, dropping work whose
deadline has already passed.

**2. How do you debug an agent that gave a wrong answer three days ago?**
From the trace, not the logs. Pull the trajectory by `thread_id`: routing decision, each model call with
its prompt version and model version, each tool call with arguments and results. That usually localises
it to one of three things — wrong route, bad tool result, or a prompt change. Because `prompt_version`
is on every span you can also find every other conversation that ran the same version, which turns one
report into a blast-radius estimate.

**3. What do you monitor on an agent platform?**
Availability and p95 latency, with time-to-first-token tracked separately because it drives perceived
quality. Harmful-action rate, alerted rather than averaged. Cost per resolved conversation as a real
SLO. Escalation rate, false-resolution rate, tool error rate by tool, and the distribution of routing
decisions — a sudden shift in routing means either the world changed or a prompt did, and both are
worth waking up for.

**4. How do you control cost?**
Attack the quadratic first: per-conversation tokens grow with the square of turn count because each
turn re-sends the history, so trimming and summarising old turns is the biggest single lever. Then keep
tool results small, since they are usually bigger than the human text and are re-sent forever. Prefix
caching on the stable system prompt and tool schemas. A smaller model for the router, which runs on
every request. Hard per-conversation caps as the backstop — and the counter must live in checkpointed
state or a retry resets it.

**5. How would you manage prompts across seven agents and a self-serve platform?**
A registry with immutable content-addressed versions, environments pinned to explicit versions, and a
promotion flow gated by the offline eval suite, with instant rollback. Every trace records the prompt
version. The important consequence of a self-serve JSON-configured path is that configuration becomes a
deployment channel — so it needs the same gates as code, or you have built a way to change production
behaviour that bypasses review.

**6. Where would you put guardrails?**
Deterministic input checks first, in parallel, before any model call — an unsafe request should never
reach a model, and parallel fan-out makes that cost `max` not `sum`. Tool authorisation in code against
the real user's entitlements, never in the prompt. Write tools gated and capped, with human approval on
irreversible actions. Output classifiers as defence in depth, understanding they are weaker because by
then you have already generated and are relying on a second stochastic component.

**7. How do you handle prompt injection?**
Structurally, because there is no escaping primitive — no equivalent of a prepared statement. Treat all
text reaching the context as untrusted, including retrieved documents and tool results, not just user
messages. Then constrain what a compromised turn can do: least-privilege tool sets per agent,
authorisation enforced in code, no write tool reachable without verification, human approval on
irreversible actions, and never letting retrieved content decide which tool gets called.

**8. Is semantic caching a good idea for a support agent?**
Mostly not. "Refund my Tuesday ride" and "Refund my Thursday ride" are semantically close and factually
different, so a semantic cache in a transactional context returns confidently wrong answers. It is safe
only for content with no user-specific or time-specific answer — policy and how-to questions — with a
conservative threshold. Prefix caching of the stable system prompt is the version of caching that
actually pays, and it just needs disciplined prompt ordering.

**9. How do you roll out a new model version?**
Never as an in-place swap. Pin the current version so a provider-side update cannot change behaviour
implicitly. Run the full offline suite on the candidate, then shadow it on real traffic to get realistic
input distribution with zero user risk, then A/B with guardrail metrics and automatic rollback. Ramp
with observation windows sized to the slowest metric that matters. The failure this prevents is the one
where behaviour changed and nobody deployed anything.

**10. Where does PII live in this system, and how do you delete it?**
Four places: the checkpoint store, the trace store, application logs, and the eval corpus. Redact and
tokenise on the way in so the provider sees less and a trace leak is smaller. The deletion path has to
cover all four, and TTL does not count as deletion because it is best-effort. The eval corpus is the
awkward one, which is why fixtures get de-identified at capture time — then an erasure request does not
invalidate the eval set.
