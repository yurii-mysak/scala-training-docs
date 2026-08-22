# LLM Agent Architectures

> **Priority:** Required
> **Est. time:** 60 min
> **Track:** Server
> **HelloInterview:** System Design in a Hurry → Common Patterns → Multi-step Processes

The whole section rests on one framing: **an agent is a distributed system with an unusually
unreliable component in the control path.** Everything you already know about supervision,
timeouts, idempotency, backpressure and partial failure applies. What is new is that one node
in the graph is non-deterministic, costs money per invocation, has a finite working memory,
and will confidently do the wrong thing rather than return an error.

---

## 1 · The decomposition: model, tools, memory, loop

Strip the marketing away and an agent is four parts.

| Part | What it is | Distributed-systems analogue |
|------|------------|------------------------------|
| **Model** | A stateless function `(prompt) -> tokens`. No memory between calls. | A pure, slow, expensive, flaky RPC to a third party. |
| **Tools** | Functions the model may request, described by a JSON schema. Executed by *your* code. | RPC stubs. The model emits a request; your runtime is the transport and the authoriser. |
| **Memory** | Everything re-sent on each call: message history, scratchpad, retrieved documents, summaries. | Session state. Because the model is stateless, memory is *your* durability problem. |
| **Loop** | The driver: call model → if it asked for a tool, run it, append result, call again → until it emits a final answer or a limit trips. | An event loop / actor receive loop with a termination condition. |

Two consequences fall straight out of this and are worth saying out loud in an interview:

* **The model never "remembers" anything.** Every turn re-sends the whole relevant history. Conversation
  state is a storage and serialisation problem, not a model problem. See
  [agent-state-and-checkpointing.md](agent-state-and-checkpointing.md).
* **The model never executes anything.** It emits a *request* to call a tool. Your runtime decides
  whether to honour it. Every authorisation, rate limit, and safety check lives in your code, never
  in the prompt. A prompt is not an access-control mechanism.

### 1.1 The loop, in pseudo-code

```python
def run(user_msg: str, state: State, tools: dict[str, Callable]) -> str:
    state.messages.append({"role": "user", "content": user_msg})
    for step in range(MAX_STEPS):                  # hard bound: no unbounded recursion
        reply = model.call(state.messages, tool_schemas(tools))
        state.messages.append(reply)
        if not reply.tool_calls:
            return reply.content                   # terminal
        for call in reply.tool_calls:              # may be several; can run in parallel
            result = dispatch(tools, call)         # your code: authz, timeout, retry, redact
            state.messages.append(tool_result(call.id, result))
    raise StepLimitExceeded                        # treat as a first-class outcome, not a bug
```

Everything else in this file is a variation on the shape of that loop and on who owns it.

---

## 2 · Tool calling and function schemas

The model is trained to emit structured calls against a JSON Schema you supply. The schema is
an API contract with an unusual consumer: it is read by a language model, so **the description
fields are load-bearing**, not documentation.

```json
{
  "name": "get_ride_receipt",
  "description": "Fetch the receipt for one completed ride. Use only when the rider asks about a charge on a specific ride. Does not work for scheduled or cancelled rides.",
  "input_schema": {
    "type": "object",
    "properties": {
      "ride_id": {"type": "string", "description": "Ride UUID, from list_recent_rides. Never guess."}
    },
    "required": ["ride_id"]
  }
}
```

Design rules that hold up in production:

| Rule | Why |
|------|-----|
| Few tools, sharply distinguished | Selection accuracy degrades as the tool set grows and as descriptions overlap. Ten well-separated tools beat forty near-duplicates. Above ~20, route to a subagent that owns a smaller set. |
| Say what the tool is *not* for | Most mis-selection is a boundary problem, not a comprehension problem. |
| Constrain the argument space | Enums over free strings; IDs over names. Fewer degrees of freedom, fewer hallucinated arguments. |
| Return errors as data, not exceptions | `{"error": "ride_not_found", "hint": "call list_recent_rides first"}` lets the model recover. A stack trace or a raised exception ends the turn. |
| Keep results small | Tool output goes into the context window and is re-sent on every subsequent call. A 200 KB JSON blob is a memory leak that you pay for on every turn. Summarise or paginate at the tool boundary. |
| Make tools idempotent where you can | The loop retries. The model also sometimes re-issues a call it has already made. Idempotency keys are the same mechanic you would use on a payments endpoint. |
| Separate read tools from write tools | Reads can be speculative and parallel. Writes need confirmation, authorisation, and often a human gate. Treat this as a hard architectural line, not a convention. |

**Parallel tool calls.** Modern models emit several tool calls in one reply. Running them
concurrently is the single cheapest latency win available. It is scatter-gather: fan out, join,
append all results, resume. The same reasoning as `Future.sequence` over a set of `ask`s —
and the same hazard, that one slow leg sets the latency of the whole step, so each leg needs
its own timeout and a degraded-result path.

---

## 3 · Topologies

### 3.1 Single agent

One loop, one prompt, one tool set.

* Cheapest, lowest latency, easiest to evaluate: one trajectory, one prompt to version.
* Degrades when the prompt starts accumulating conditional instructions ("if the user is a driver,
  then ...; unless the ride was more than 30 days ago, then ..."). That is the signal to split.

### 3.2 Router / supervisor

A classifier — LLM or not — picks one specialist and hands the request over. The supervisor may be
one-shot (classify, dispatch, done) or **stateful**, staying in the loop and receiving control back.

This is the shape Lyft's platform uses: a **meta agent acting as a stateful router**, classifying
incoming requests and dispatching to specialist subagents via `Command(goto=...)`, with **separate
rider and driver routers**. See [langgraph-patterns.md](langgraph-patterns.md) and
[lyft-scc-case-study.md](lyft-scc-case-study.md).

* Each specialist gets a small tool set and a short prompt — both accuracy wins.
* The router is a single point of failure and the highest-leverage thing to evaluate. Router accuracy
  bounds system accuracy: a request routed to the wrong specialist cannot be recovered by a perfect
  specialist.
* **Akka analogue:** a parent actor with a `Router`, except selection is by message *content* rather
  than by load. The supervision relationship is the same: the parent decides what happens when a
  child fails, and the child never decides its own fate.

### 3.3 Multi-agent handoff (peer to peer)

Agents transfer control to each other directly; whoever holds the turn talks to the user.

* Good for genuinely sequential specialisations (triage → diagnosis → resolution).
* Bad property: control flow becomes a graph you did not draw. Two agents can hand off to each other
  forever. You need a hop budget and a loop detector — the same reason IP has a TTL field.

### 3.4 Hierarchical

Supervisors of supervisors; leaves are workers. Rider-router and driver-router under a top-level
classifier is a two-level version.

* Scales the *organisational* problem: separate teams own separate subtrees, each with its own prompts,
  tools and eval sets.
* Costs latency: every level adds at least one model call, and levels compose multiplicatively on
  accuracy. Three routing layers at 95% each is 86% end-to-end before any work is done.
* **Akka analogue:** the actor hierarchy, with the same trade-off — supervision boundaries buy
  isolation and cost message hops.

### 3.5 Comparison

| Topology | Model calls / request | Accuracy risk | Ops story | Use when |
|----------|----------------------|---------------|-----------|----------|
| Single | 1 + tool rounds | Prompt bloat | Trivial | One domain, <10 tools |
| Router | 1 + specialist | Router misclassification dominates | Good: per-specialist metrics | Several disjoint domains |
| Handoff | Unbounded without a budget | Cycles, context loss across handoffs | Hard: trajectory spans agents | Genuinely sequential stages |
| Hierarchical | Depth + work | Multiplicative routing error | Good if you own the tree | Many teams, many domains |

---

## 4 · Reasoning patterns inside a single agent

### 4.1 ReAct (reason, act, observe)

Interleave a short reasoning step with a tool call, repeat. This is what the loop in §1.1 already is.

* Strength: the model can react to what it actually observes, so it recovers from surprises.
* Weakness: no global plan, so it can wander. It is also the pattern most sensitive to a bad tool
  result — one misleading observation early poisons the rest of the trajectory. This is
  **error propagation in a pipeline with no checkpoint**; the fix is the same, checkpoint and allow
  a restart from a known state.

### 4.2 Plan-and-execute

One call produces a plan; subsequent (often cheaper, smaller-model) calls execute steps.

* Cheaper: the expensive model runs once. Faster: steps that do not depend on each other run in parallel.
* More legible: the plan is an artifact you can log, diff, evaluate and show a human for approval.
* Weakness: plans made before observing reality are wrong more often than they look. Always allow re-planning,
  and bound the number of re-plans.

### 4.3 Reflection / critic

A second call grades or repairs the first. Useful; also the pattern most often cargo-culted.

* Real gain when the critic has information the generator did not — a schema to validate against,
  test output, a retrieval result, a policy document.
* Little gain when the critic is the same model with the same context, which is why "just ask it to
  check its work" often produces a confident restatement. Related failure mode:
  [llm-as-judge.md](llm-as-judge.md).

### 4.4 Structured output as an alternative to reasoning

If the task is extraction or classification, do not run a loop at all. One call, constrained to a
schema, no tools. Cheaper, faster, far easier to evaluate, and deterministic enough to unit test.
Reach for this before reaching for an agent.

---

## 5 · Agents as distributed systems: the failure modes that are actually new

Most of an agent's failure modes are ones you have seen. A few are genuinely different, and being
crisp about which is which is the fastest way to sound like someone who has run one in production.

| Failure mode | Familiar? | Notes |
|---|---|---|
| Tool timeout, retry storm, cascading failure | Familiar | Standard circuit breakers, budgets, bulkheads. |
| Partial failure: tool executed but the result never reached the model | Familiar | Exactly the at-least-once problem. Idempotency keys; checkpoint *after* the write, replay is then safe. |
| Runaway loop | Familiar-ish | Bound steps, tokens, wall-clock and cost. Three of the four are new dimensions of the same old guard. |
| **Non-determinism in the control path** | **New** | The same input can take a different path tomorrow. You cannot assert on exact outputs; you assert on invariants and distributions. This is why [evaluating-agents.md](evaluating-agents.md) exists. |
| **Context-window exhaustion** | **New** | A finite working set that grows with conversation length. It behaves like memory pressure: performance degrades gradually, then the request fails. Needs an eviction policy (summarise, truncate, offload to retrieval). |
| **Cost as a first-class resource** | **New** | Every retry has a price. A retry storm is now a budget incident as well as a latency incident. Cost belongs in the SLO. |
| **Prompt injection** | **New** | Any text that reaches the context — a support ticket, a web page, a tool result — is untrusted input to the control plane. There is no escaping mechanism equivalent to a prepared statement. Mitigate structurally: least-privilege tools, deterministic authorisation, human gates on irreversible actions. |
| **Silent capability drift** | **New** | A provider-side model update changes behaviour without a deploy on your side. Pin versions; treat a model upgrade as a release with an eval gate. |
| **Correlated failure between agent and evaluator** | **New** | If your simulator, your judge and your agent are the same model family, their blind spots correlate. Covered in [evaluating-agents.md](evaluating-agents.md) — this is the single most interesting idea in this section. |

---

## 6 · When an agent is the wrong answer

Have an opinion here. Staff candidates are expected to push back on the premise, and "we should
not build an agent for this" is a strong signal when it is argued rather than asserted.

**The test I would state in an interview:** an agent earns its cost when the space of valid plans is
too large to enumerate at design time *and* the right next step depends on what earlier steps returned.
If you can enumerate the paths, encode them. If the steps are fixed, write the pipeline.

### 6.1 Three things that are usually mislabelled as agents

| Symptom | What it actually is | Build this instead |
|---|---|---|
| "The agent decides which of four flows to run" | A classifier | One constrained model call returning an enum, then a normal `if`. Testable, ~1 call, deterministic dispatch. |
| "The agent calls these five services in order and formats a summary" | A pipeline | A function. Use the model only for the final natural-language rendering. |
| "The agent walks the user through a refund" | A workflow with legal and financial invariants | An explicit state machine you own, where the model fills slots and phrases replies but never chooses transitions that have money attached. |

### 6.2 The costs you are accepting when you choose an agent

* **Latency**: an agent turn is N sequential model calls. Each is hundreds of milliseconds to seconds.
  A four-step trajectory is comfortably an order of magnitude slower than the pipeline it replaced.
* **Cost**: N calls, each re-sending a growing context. Token spend per conversation grows roughly
  quadratically with the number of steps, because step *k* re-sends everything from steps 1..k-1.
  That quadratic is the single most under-appreciated number in agent design.
* **Testability**: you have traded assertions for statistics. You no longer have a test that fails
  deterministically; you have a pass rate with a confidence interval.
* **Debuggability**: "why did it do that" is answered by reading a trajectory, not a stack trace.
* **Blast radius**: a bug is now a behaviour, and it can be caused by someone editing a prompt.

### 6.3 The middle ground, and why it is usually right

The strongest production shape is not "agent" or "pipeline" — it is **a deterministic graph you own,
with model calls at specific nodes**. The graph enforces legality; the model supplies judgement inside
a node. Illegal transitions are unrepresentable because the edge does not exist.

That is exactly what LangGraph is for, and exactly the shape of the Lyft platform: a state machine
whose routing node happens to be an LLM, with **safety checks fanned out in parallel before any LLM
reasoning runs at all**. The safety invariant is enforced by deterministic code positioned *upstream*
of the non-deterministic component. Note the direction — the guard does not review the model's output,
it gates the model's turn.

**The rule I would defend:** never let the model be the thing that enforces an invariant. Models are
for choosing among legal options; code is for deciding which options are legal.

---

## 7 · Napkin math to have ready

Lyft's design rounds explicitly probe live estimation, so practise these out loud.

Assume ~270k interactions/month (a published Lyft figure — see
[lyft-scc-case-study.md](lyft-scc-case-study.md)):

* **Rate**: 270,000 / (30 x 86,400) ≈ **0.1 requests/s** average. Even at 20x peak that is ~2 rps.
  The interesting constraints are *not* throughput.
* **Per-conversation tokens**: 6 turns, ~1.5k tokens of context growing to ~6k, plus tool results.
  Order 25k input + 3k output tokens per conversation.
* **Monthly tokens**: 270k x 28k ≈ **7.5 x 10^9 tokens/month**. This is the number that decides
  whether prompt caching and a smaller router model are optimisations or requirements.
* **Latency**: 4 sequential model calls at ~1.5 s each is 6 s before any tool latency. This is why
  time-to-first-token and streaming matter more than total latency for perceived quality, and why
  parallel safety checks are worth the engineering.

State the assumption, do the arithmetic out loud, then say which number the design is actually
sensitive to. That last step is what separates a Staff answer from a Senior one.

---

## 8 · Cross-references

* [langgraph-patterns.md](langgraph-patterns.md) — how these topologies are expressed as a graph.
* [agent-state-and-checkpointing.md](agent-state-and-checkpointing.md) — the memory half of the decomposition.
* [rag-and-retrieval.md](rag-and-retrieval.md) — how documents get into the context window.
* [Akka Actors Core](../03-akka-ecosystem/AkkaActorsCore.md) and
  [Akka Advanced](../03-akka-ecosystem/AkkaAdvanced.md) — supervision, mailboxes, stash.
* [Delivery QoS, DLQ, HA](../07-messaging-and-streaming/Messaging-delivery_qos_dlq_ha.md) — at-least-once
  and idempotency, which apply unchanged to tool calls.

---

## Interview questions

**1. What is an LLM agent, in one paragraph, to someone who builds distributed systems?**
A loop around a stateless, non-deterministic RPC. The model returns either a final answer or a request
to call a tool; your runtime executes tools, appends results, and calls again until a terminal answer
or a budget trips. Memory is entirely yours — the model re-reads the whole relevant history on every
call. Tools are RPC stubs the model asks you to invoke; it never executes anything itself.

**2. How do you stop an agent from looping forever?** **[Reported at Lyft]** *(the "third-party dependencies with a variety of failure modes" design question lands here)*
Four independent budgets: max steps, max tokens, max wall-clock, max cost — whichever trips first ends
the turn. Plus a repeat detector on (tool, arguments) pairs, since the commonest loop is re-issuing an
identical failing call. Exceeding a budget is a designed outcome with a defined user-facing behaviour
(escalate to a human), not an exception that leaks.

**3. When would you argue against building an agent?**
When the plan space is enumerable. If there are four flows, use one constrained call to classify and a
normal branch — you get determinism, unit tests, one model call instead of six, and a tenth of the
latency. Agents earn their cost when the next step genuinely depends on what previous steps returned
and the branching is combinatorial. I would also refuse to let a model choose transitions that move
money or close accounts; the model fills slots, the state machine owns the transitions.

**4. How do you design a tool schema so a model uses it correctly?**
Treat descriptions as load-bearing: say what the tool is for *and* what it is not for, because most
mis-selection is a boundary problem. Constrain arguments to enums and IDs rather than free text.
Return errors as structured data with a hint so the model can recover. Keep results small — everything
returned is re-sent on every subsequent call. Keep read and write tools architecturally separate.

**5. What is different about the failure modes of an agent versus a normal service?**
Most are the same: timeouts, retries, partial failure, cascading load. Four are genuinely new.
Non-determinism in the control path, so you assert on invariants and distributions rather than outputs.
Context-window exhaustion, which behaves like memory pressure and needs an eviction policy. Cost as a
resource dimension, so a retry storm is a budget incident. And prompt injection, where any text
reaching the context is untrusted input to the control plane with no escaping primitive available.

**6. Router versus multi-agent handoff — how do you choose?**
A router when the domains are disjoint and one specialist can finish the job; the supervisor keeps
control and the trajectory stays legible. Handoff when the work is genuinely sequential and the next
stage needs the previous stage's context. Handoff costs you a control-flow graph nobody drew, so it
needs a hop budget and a cycle detector — the same reason IP packets carry a TTL. Router accuracy
bounds system accuracy, so it is the first thing I would evaluate.

**7. Where would you put a safety check in an agent's flow, and why?**
Upstream of the model, in deterministic code, run in parallel so it costs latency only once. If the
check gates the model's turn rather than reviewing its output, an unsafe action is unreachable rather
than merely unlikely. Reviewing output after the fact means the model has already decided, and you are
relying on a second non-deterministic component to catch the first. That is the pattern Lyft uses:
safety checks fanned out in parallel before any LLM reasoning.

**8. Estimate the token cost of a support agent handling 270k conversations a month.**
Six turns, context growing from ~1.5k to ~6k tokens because every turn re-sends the history, plus tool
results: order 25k input and 3k output tokens per conversation, so roughly 7.5 billion tokens a month.
The important structural point is that per-conversation token use grows quadratically with turn count,
since step k re-sends steps 1..k-1. That is what makes prompt caching, history summarisation and a
small cheap router model load-bearing rather than optional.

**9. Your agent calls five downstream services with different failure characteristics. How do you keep it responsive?** **[Reported at Lyft]**
Per-tool timeouts and circuit breakers, and a degraded result the model can reason about rather than an
exception that ends the turn — `{"error": "billing_unavailable", "hint": "answer from ride history"}`.
Fan out independent calls in parallel and join with a deadline; the slow leg must not set the whole
step's latency. Bulkhead the connection pools so one sick dependency cannot starve the others, and make
the degraded path an explicitly evaluated scenario, not an untested branch.

**10. How do you unit test something non-deterministic?**
Test the deterministic parts deterministically: tool implementations, schema validation, routing on a
frozen classifier output, state reducers, budget enforcement. Then test the model-in-the-loop parts
statistically, with a frozen eval set, fixed seeds and temperature 0, asserting on a pass rate with a
noise floor you have measured rather than on an exact string. Mock the model with recorded responses
for graph-topology tests so CI does not depend on a provider.
