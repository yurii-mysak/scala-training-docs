# LangGraph Patterns

> **Priority:** Required
> **Est. time:** 75 min
> **Track:** Server
> **HelloInterview:** System Design in a Hurry → Common Patterns → Managing Long Running Tasks

LangGraph is the framework the target team builds on. Read it as **a durable state machine with a
message-passing runtime**, not as an "AI framework". Once you see it that way, almost every concept
maps onto something you have already shipped in Akka, and the interesting engineering questions are
the ones you already know how to ask: where is the state, who is the single writer, what happens on
partial failure, and what is the supervision strategy.

Running example throughout: the Lyft support platform — a **meta agent acting as a stateful router**
that classifies requests and dispatches to specialist subagents via `Command(goto=...)`, with
**separate rider and driver routers** and **safety checks fanned out in parallel before any LLM
reasoning**. Facts in [lyft-scc-case-study.md](lyft-scc-case-study.md).

> Code in this file is illustrative. Unlike the rest of the repo it is not standard-library-only:
> LangGraph is a third-party dependency. Snippets are for reading, not for running.

---

## 1 · The core model: graph as state machine

Three primitives, and that is genuinely all of it.

| Primitive | Definition |
|---|---|
| **State** | A typed dict describing everything the graph knows. Each key is a *channel*. |
| **Node** | `f(state) -> partial_state`. A plain function. May call a model, a tool, a database, nothing. |
| **Edge** | Where control goes next. Static (`A -> B`), conditional (`A -> f(state)`), or returned by the node itself. |

Execution proceeds in **supersteps** (the vocabulary and the model come from Pregel): the set of
nodes scheduled for this step all run, their returned partial states are merged into the global state
via per-channel **reducers**, and the next set of nodes is scheduled. A checkpoint is written per
superstep.

That last sentence is the whole design. It gives you: deterministic merge semantics, a natural
persistence boundary, free parallelism within a step, and a resume point after a crash.

```python
from typing import Annotated, TypedDict
from operator import add

class SupportState(TypedDict):
    messages:      Annotated[list, add]      # reducer: append, do not overwrite
    intent:        str | None                # reducer: last-write-wins (default)
    safety_flags:  Annotated[list, add]      # several parallel nodes write here
    user_kind:     str                       # "rider" | "driver"
    resolution:    str | None
```

**Reducers are the important detail.** The default is last-write-wins, which is fine for a scalar and
catastrophic for a list two parallel nodes both append to. Choosing a reducer is choosing a merge
function for concurrent writes — the same decision you make when you pick a CRDT or write a
`ddata` merge in Akka Distributed Data. If two nodes in the same superstep write the same
last-write-wins channel, the result is unspecified; that is a design bug, not a framework bug.

---

## 2 · Akka analogue map

This table is the fastest way to convert 13 years of actor-system experience into credibility on
this stack. Worth being able to reproduce it from memory.

| LangGraph | Akka analogue | The difference that matters |
|---|---|---|
| `StateGraph` | An Akka Typed FSM / `context.become` state machine | Transitions are *data* in a graph you can inspect, visualise and diff — not closures buried in behaviours. |
| Node | An actor's message handler, or an Akka Streams stage | A node is a pure-ish function of state, not a long-lived entity with private mutable state. |
| State channel + reducer | Event fold in Akka Persistence, or a `ddata` merge function | Reducer is per-key. Concurrent writes to one key need a commutative reducer, exactly like a CRDT. |
| Conditional edge | `context.become(next)` after inspecting the message | Routing logic is a named function you can unit test in isolation. |
| `Command(goto=..., update=...)` | `tell` the next actor *and* persist state in one step | Atomic: routing decision and state mutation land in the same checkpoint. No window where you have updated but not dispatched. |
| Supervisor node | Parent actor with a `Router` + supervision strategy | Routes on message *content*, not load. Same key property: the parent decides, the child never chooses its own fate. |
| Subgraph | Child actor hierarchy / cluster-sharded entity | Own state schema, own checkpoint namespace, composable as a single node in the parent. |
| Fan-out / fan-in superstep | `Broadcast` + `Zip` in the Streams graph DSL, or `ask` + `Future.sequence` | The join is implicit: the superstep ends when every scheduled node has returned. |
| Checkpointer | Akka Persistence journal + snapshot store | Snapshots of full state per superstep rather than an event log — closer to a snapshot store than a journal. See [agent-state-and-checkpointing.md](agent-state-and-checkpointing.md). |
| `thread_id` | `persistenceId` / sharded entity id | Same role: the unit of recovery and the unit of single-writer discipline. |
| `interrupt()` | `stash()` until an external message arrives | The process actually stops and the state is durable; resumption can be days later, in a different process. |
| Retry policy per node | `Restart` supervision with `BackoffSupervisor` | Per-node, declarative, and the checkpoint gives you the "restart from last good state" that `Restart` does not. |
| `recursion_limit` | `max-nr-of-retries` / mailbox bounds | Guards against runaway loops. Non-negotiable in production. |
| Streaming output | `Source` with demand-based backpressure | Weaker: token streams are push. You do not get `request(n)`; the only real backpressure is cancellation. |

The one thing with no clean Akka analogue is **`interrupt` + durable resume across process
boundaries**. Akka Persistence gets you recovery after a crash; LangGraph interrupts are designed for
a human taking hours to respond. That is closer to a saga with a durable timer than to actor recovery.
See [Event Sourcing, CQRS, Sagas](../15-system-design/event_sourcing_cqrs_sagas_guide.md).

---

## 3 · Nodes and edges in practice

```python
from langgraph.graph import StateGraph, START, END

g = StateGraph(SupportState)

g.add_node("safety_pii",     check_pii)          # deterministic
g.add_node("safety_abuse",   check_abuse)        # deterministic
g.add_node("safety_incident", check_incident)    # deterministic
g.add_node("meta_router",    classify_and_dispatch)
g.add_node("rider_router",   rider_subgraph)
g.add_node("driver_router",  driver_subgraph)
g.add_node("escalate",       escalate_to_human)

# fan-out: all three safety nodes run in the same superstep
g.add_edge(START, "safety_pii")
g.add_edge(START, "safety_abuse")
g.add_edge(START, "safety_incident")

# implicit join: meta_router is scheduled once all three have returned
g.add_edge("safety_pii",      "meta_router")
g.add_edge("safety_abuse",    "meta_router")
g.add_edge("safety_incident", "meta_router")

g.add_edge("escalate", END)
app = g.compile(checkpointer=DynamoDBSaver(table="agent_checkpoints"))
```

**Conditional edges** put the routing function outside the node:

```python
def route_by_user_kind(state: SupportState) -> str:
    if state["safety_flags"]:
        return "escalate"
    return "rider_router" if state["user_kind"] == "rider" else "driver_router"

g.add_conditional_edges("meta_router", route_by_user_kind,
                        {"escalate": "escalate",
                         "rider_router": "rider_router",
                         "driver_router": "driver_router"})
```

The explicit mapping dict is worth using even though it is optional: it makes the set of legal
destinations a declared, reviewable thing. An edge that does not exist cannot be taken — the
structural-safety argument from
[agent-architectures.md](agent-architectures.md#6--when-an-agent-is-the-wrong-answer).

---

## 4 · `Command(goto=...)`: dispatch and update as one step

A node can return a `Command` instead of a plain dict, combining "here is my state update" with
"here is where control goes next".

```python
from langgraph.types import Command
from typing import Literal

SPECIALISTS = ("billing", "safety_report", "lost_item", "account", "ride_issue")

def classify_and_dispatch(state: SupportState) -> Command[Literal[SPECIALISTS + ("escalate",)]]:
    if state["safety_flags"]:                      # deterministic short-circuit, no model call
        return Command(goto="escalate",
                       update={"resolution": "escalated_safety"})

    intent = intent_model.classify(state["messages"])   # constrained: returns one enum value
    if intent.confidence < THRESHOLD:
        return Command(goto="escalate", update={"intent": intent.label})

    return Command(goto=intent.label, update={"intent": intent.label})
```

Why this matters rather than being sugar:

* **Atomicity.** The state update and the routing decision are persisted in the same checkpoint.
  With a separate `add_conditional_edges`, the routing function re-derives the destination from state
  on resume; with `Command`, the decision *is* state. If the classifier is non-deterministic, re-deriving
  after a crash can send you somewhere different from where you were going. This is precisely the
  reason event-sourced systems persist the decision, not just the inputs — see
  [Event Sourcing Guide](../06-databases-and-distributed-data/Event-Sourcing-Guide.md).
* **The Akka analogue** is doing `persist(event) { e => state = apply(e); next ! Work(e) }` inside one
  `persist` callback rather than persisting and then separately deciding whom to tell.
* **`Command(goto=..., graph=Command.PARENT)`** hands control back up from a subgraph — the equivalent
  of a child actor replying to its parent's `ask` rather than continuing on its own.

**Type the return.** `Command[Literal[...]]` is how the compiled graph knows which edges exist. Without
it you lose the drawn graph and the static check that a destination is reachable — the thing you were
buying by using a graph framework at all.

---

## 5 · The supervisor / meta-agent pattern

The Lyft platform's central design. Worth being able to draw on a whiteboard.

```
                    ┌──────────── parallel safety supersteps ────────────┐
   request ──▶ START ├─▶ pii_scan ──┐                                    │
                     ├─▶ abuse_scan ─┼──▶ (implicit join) ──▶ meta_router │
                     └─▶ incident ───┘                            │      │
                                                                  ▼      │
                                      ┌───────────────────────────────┐  │
                                      │  Command(goto=<specialist>)   │  │
                                      └───────┬───────────────┬───────┘  │
                                              ▼               ▼          │
                                       rider_router     driver_router    │
                                       (subgraph)       (subgraph)       │
                                          │  │              │  │         │
                                    billing  lost_item  payouts  ride_issue
                                          └──┴────► Command(goto=PARENT) ─┘
                                                          │
                                                     meta_router (stateful: keeps the turn)
                                                          │
                                                        END / interrupt
```

Design properties worth articulating:

1. **Stateful router, not fire-and-forget.** The meta agent stays in the loop. A specialist returns
   control, and the router can re-classify — a user who opened with a billing question and then
   mentions a safety incident gets re-routed mid-conversation. A one-shot classifier cannot do this.
   Akka analogue: a parent that keeps the conversation's `ActorRef` and forwards, rather than handing
   the client a direct reference to the child.

2. **Safety before reasoning, in parallel.** Three deterministic checks in one superstep cost
   `max(latency)` not `sum(latency)`, and they run *before* any tokens are generated. An unsafe
   request never reaches a model. Compare with the weaker "generate then moderate", which pays for
   generation and relies on a second stochastic component. This is a genuinely good design decision
   and worth complimenting in the interview.

3. **Separate rider and driver routers.** Different tool sets, different policies, different
   authorisation scope, different eval sets, and plausibly different teams. It is bounded contexts
   applied to prompts. It also means one team's prompt change cannot regress the other side.

4. **Specialists are subgraphs, not prompts.** A subgraph has its own state schema and its own
   checkpoint namespace, so it can have its own loop, its own retries and its own interrupts.

5. **Two flavours of specialist.** Hand-built agents where the logic is intricate, and
   JSON-configured self-serve agents pulling prompts from LangSmith Prompt Hub for the long tail.
   That is a platform decision, not an agent decision: the marginal cost of the 20th agent has to
   approach zero or the platform does not scale. See
   [production-llmops.md](production-llmops.md#3--prompt-versioning-and-a-prompt-registry).

---

## 6 · Parallel fan-out and joins

Fan-out is expressed by giving one node several outgoing edges; the join is implicit at the next
superstep boundary.

```python
g.add_edge("meta_router", "fetch_ride_history")
g.add_edge("meta_router", "fetch_payment_status")
g.add_edge("meta_router", "fetch_open_tickets")
for n in ("fetch_ride_history", "fetch_payment_status", "fetch_open_tickets"):
    g.add_edge(n, "compose_answer")
```

Things to get right, all of which have direct precedents in stream processing:

| Concern | Handling |
|---|---|
| **Merge conflicts** | Any channel written by more than one parallel node needs a commutative, associative reducer. `Annotated[list, add]` for accumulation; a custom reducer for anything else. |
| **Slowest leg sets step latency** | Per-node timeouts and a fallback partial value. The join waits for all scheduled nodes. |
| **One leg fails** | Decide per node: retry policy, or return a sentinel the downstream node can reason about. A raised exception fails the superstep. |
| **Dynamic fan-out** | `Send(node, payload)` for a variable number of branches — the map half of map-reduce, one checkpointed task per element. |
| **Backpressure** | There is none from the graph. Concurrency limits belong in your tool clients and connection pools. Contrast with [Akka Streams backpressure](../03-akka-ecosystem/akka_streaming_and_backpressure_detailed_guide.md), where demand is signalled end to end. |

---

## 7 · Human-in-the-loop interrupts

```python
from langgraph.types import interrupt, Command

def confirm_refund(state: SupportState) -> dict:
    decision = interrupt({                       # execution stops; state is durable
        "kind": "approve_refund",
        "ride_id": state["ride_id"],
        "amount_cents": state["refund_cents"],
    })
    if decision["approved"]:
        return {"resolution": issue_refund(state["ride_id"], state["refund_cents"])}
    return {"resolution": "refund_declined_by_agent"}

# later, possibly in another process, hours later:
app.invoke(Command(resume={"approved": True}), config={"configurable": {"thread_id": tid}})
```

What is actually happening: `interrupt` raises a control-flow exception, the checkpointer persists the
state as of that superstep, and the invocation returns to the caller with the interrupt payload.
Resuming re-enters the graph at the interrupted node with the supplied value.

Consequences you should raise unprompted, because they are where the bugs live:

* **The node re-runs from its start on resume.** Anything before the `interrupt()` call executes twice.
  Put side effects *after* the interrupt, or make them idempotent. This is at-least-once execution
  with all the usual implications — see
  [Delivery QoS and DLQ](../07-messaging-and-streaming/Messaging-delivery_qos_dlq_ha.md).
* **Multiple interrupts in one superstep** resume in a defined order tied to task ids. Do not rely on
  incidental ordering.
* **There is no timer.** A thread interrupted forever is a leak: state sitting in DynamoDB with a
  human who never replied. You need an external sweeper and a TTL policy. This is the saga-timeout
  problem, not a framework feature.
* **Authorisation on resume** is yours. The resume payload is untrusted input arriving from a
  different request; validate that this human may approve this refund.

Use interrupts for: irreversible actions (refunds, account changes), low-confidence routing,
compliance-mandated review, and safety escalation. That last one is the natural landing point for
the parallel safety checks in §5.

---

## 8 · Streaming

Three distinct things are called "streaming" and conflating them causes real confusion:

| Mode | Emits | Use for |
|---|---|---|
| `stream_mode="values"` | Full state after each superstep | Server-side progress, checkpointing hooks, debugging |
| `stream_mode="updates"` | Only the diff each node returned | Efficient progress events over a socket |
| `stream_mode="messages"` | Individual LLM tokens as generated | User-facing typing effect |

Practical points:

* **TTFT dominates perceived latency.** A 6-second trajectory that starts emitting at 800 ms feels
  faster than a 3-second one that emits nothing until it is done. Budget and monitor time-to-first-token
  separately from total latency.
* **Emit node-level progress, not just tokens.** "Checking your ride history" during a tool call is
  worth more than a spinner and costs nothing.
* **No demand-based backpressure.** Unlike a `Source`, a token stream is push-only. If the client is
  slow, you buffer or you cancel. Bound the buffer and cancel on disconnect, or a closed browser tab
  keeps burning tokens.
* **Cancellation must propagate.** Client disconnect should abort in-flight model calls. Otherwise your
  cost per abandoned conversation is the same as a completed one.
* **Streaming and checkpointing interact.** Tokens are emitted before the superstep's checkpoint is
  durable. On a crash mid-stream the user has seen text that the resumed graph will not have recorded.
  Decide deliberately: either replay from the last checkpoint and accept a visible repeat, or
  checkpoint at a finer granularity for the final response node.

---

## 9 · Durability, retries and error handling

* **Per-node retry policy** (`RetryPolicy(max_attempts=..., retry_on=...)`) is declarative and applies
  to the node function. Equivalent to `BackoffSupervisor` around a child, with the advantage that the
  checkpoint defines the state to restart *from*.
* **Failure semantics**: an uncaught exception fails the superstep. State as of the *previous*
  superstep is durable, so resuming re-runs the whole failed superstep — including the nodes in it
  that had succeeded. That is at-least-once node execution. Non-idempotent side effects in a fanned-out
  superstep are a bug waiting for a bad day.
* **`recursion_limit`** bounds total supersteps per invocation. Set it deliberately; the default
  exists to stop runaway loops, and hitting it should be an alert, not a surprise.
* **Durability modes** trade write volume against recovery granularity: checkpoint every superstep, or
  only at exit. Cheaper writes, coarser resume. The write-amplification arithmetic is in
  [agent-state-and-checkpointing.md](agent-state-and-checkpointing.md#5--checkpoint-granularity-and-write-amplification).

---

## 10 · How the runtime actually works, in 40 lines

Demystifying the framework is worth the ten minutes; it also makes you much harder to bluff in an
interview. This is standard-library Python and captures the real semantics: supersteps, reducers,
implicit joins, checkpoint per step.

```python
from typing import Any, Callable

def run_graph(nodes: dict[str, Callable[[dict], dict]],
              edges: dict[str, list[str]],
              reducers: dict[str, Callable[[Any, Any], Any]],
              state: dict,
              save: Callable[[dict], None],
              start: list[str],
              limit: int = 25) -> dict:
    """Pregel-style execution: run a frontier of nodes, merge, checkpoint, advance."""
    frontier = list(start)
    for _ in range(limit):
        if not frontier:
            return state
        writes: list[tuple[str, Any]] = []
        nxt: list[str] = []
        for name in frontier:                       # in reality: run concurrently
            partial = nodes[name](state)
            writes.extend(partial.items())
            nxt.extend(edges.get(name, []))
        for key, value in writes:                   # merge via per-channel reducer
            reduce = reducers.get(key, lambda _old, new: new)   # default: last-write-wins
            state[key] = reduce(state.get(key), value)
        save(state)                                 # checkpoint the superstep
        frontier = list(dict.fromkeys(nxt))         # dedupe: the implicit join
    raise RecursionError("superstep limit exceeded")
```

Read that and the framework stops being magic: it is a scheduler, a merge function, and a durable
write per step. Everything else — `Command`, subgraphs, interrupts — is a variation on what a node is
allowed to return.

---

## 11 · Cross-references

* [agent-architectures.md](agent-architectures.md) — the topologies these graphs express.
* [agent-state-and-checkpointing.md](agent-state-and-checkpointing.md) — the checkpointer.
* [lyft-scc-case-study.md](lyft-scc-case-study.md) — the platform this file models.
* [Akka Cluster](../03-akka-ecosystem/Akka_Cluster.md) — sharding, single-writer, singleton.
* [Akka Streams: async boundaries and reactive streams](../07-messaging-and-streaming/Messaging-AsyncBoundariesReactiveStreams.md)
  — the fan-out/fan-in and backpressure comparison.

---

## Interview questions

**1. Explain LangGraph to someone who has never used it, in distributed-systems terms.**
It is a durable state machine with a Pregel-style runtime. You declare a typed state, functions that
return partial updates to it, and edges. Execution runs in supersteps: every node scheduled for this
step runs, the partial updates are merged per channel by a reducer, a checkpoint is written, and the
next frontier is scheduled. The value is that control flow is declared data you can inspect and
resume, not closures — and the persistence boundary is defined for you.

**2. What is a reducer and when does the default hurt you?**
A reducer is the merge function for one state channel. The default is last-write-wins, which is
correct for a scalar written by one node and wrong the moment two parallel nodes in the same superstep
write the same key — the outcome is unspecified. Anything accumulated across a fan-out needs a
commutative, associative reducer, which is exactly the CRDT merge-function decision from Akka
Distributed Data.

**3. Why `Command(goto=...)` rather than a conditional edge?**
`Command` persists the routing decision and the state update in the same checkpoint. A conditional
edge re-derives the destination from state at resume time, and if the deciding function is a model
call, re-derivation after a crash can pick a different branch. Persisting the decision rather than
just its inputs is the same discipline as event sourcing. It also expresses the actual intent, which
is "I am done and control goes here", in one place.

**4. Walk me through the Lyft support platform's graph shape.**
Deterministic safety checks fan out in parallel from START, all joining before anything else runs, so
an unsafe request never reaches a model and the checks cost max rather than sum of their latencies.
The meta agent is a stateful router: it classifies and dispatches to a specialist subagent via
`Command(goto=...)`, keeps the turn, and can re-route mid-conversation. Rider and driver traffic go to
separate routers with separate tool sets and policies. Specialists are subgraphs, some hand-built,
some JSON-configured pulling prompts from a registry.

**5. What is the Akka equivalent of a checkpointer, and where does the analogy break?**
Akka Persistence — journal plus snapshot store, with `thread_id` playing the role of `persistenceId`.
It breaks in two places. LangGraph snapshots full state per superstep rather than appending events,
so you get replay of state, not of decisions, and item size becomes a hard constraint. And LangGraph
interrupts are designed for a human replying hours later in a different process, which is closer to a
saga with a durable timer than to actor recovery.

**6. A node in a parallel superstep fails. What happens, and what does that force you to do?**
The superstep fails; state as of the previous superstep is what is durable. Resuming re-runs the whole
superstep, including the sibling nodes that had already succeeded. So node execution is at-least-once,
and any node with a side effect in a fanned-out step must be idempotent or must carry an idempotency
key. Same reasoning as an at-least-once consumer group re-processing a batch after a rebalance.

**7. How do human-in-the-loop interrupts work and what breaks?**
`interrupt()` persists state and returns control to the caller with a payload; resuming re-enters the
node with a supplied value. The trap is that the node re-runs from its beginning, so everything before
the interrupt call executes twice — side effects belong after the interrupt or must be idempotent.
There is also no built-in timer, so an interrupted thread nobody answers is a durable leak that needs
an external sweeper and a TTL policy, and the resume payload is untrusted input that needs its own
authorisation check.

**8. How would you keep an agent responsive when a trajectory takes six seconds?** **[Reported at Lyft]** *(the real-time chat design question rewards this framing)*
Optimise time-to-first-token rather than total latency, and stream. Emit node-level progress events as
well as tokens so the user sees "checking your ride history" instead of a spinner. Run independent
tool calls in the same superstep so they cost max not sum. Note that a token stream is push-only —
there is no demand signalling like a reactive `Source` — so bound the buffer and propagate client
disconnect as a cancellation, otherwise an abandoned tab keeps generating billable tokens.

**9. How do you test a graph?**
Three layers. Unit-test node functions as pure functions of state with the model mocked — that covers
most of the code. Test topology with a recorded/stubbed model: assert that a given classifier output
reaches the intended specialist, that safety flags short-circuit to escalation, and that the recursion
limit trips. Then test the model-in-the-loop behaviour statistically against a frozen eval set, which
is [evaluating-agents.md](evaluating-agents.md). Keep the first two deterministic and in CI on every
commit; the third runs on a schedule and on prompt changes.

**10. When would you not use a graph framework at all?**
When the flow is a fixed sequence with no branching on intermediate results — then it is a function,
and a framework adds a checkpointing bill and a dependency for nothing. The graph earns its cost when
you need durable resume across process boundaries, human-in-the-loop pauses, parallel supersteps with
defined merge semantics, or a control flow you want to inspect and evaluate as an artifact. Wanting a
diagram is not a reason; needing durability and legal-transition enforcement is.
