# Support Case Routing — full worked design

> **Priority:** Required
> **Est. time:** 90 min
> **Track:** Server
> **HelloInterview:** System Design in a Hurry → Common Patterns → Real-time Updates, Dealing with Contention, Multi-step Processes; Key Technologies → Redis, DynamoDB, Kafka

**This is not a verbatim reported prompt — say so if asked how you know it, and say it anyway, because
it is the single highest-probability design for this specific team.** Global Support & Partnerships /
Safety & Customer Care's actual production system, per its own published facts
([lyft-architecture.md §9](lyft-architecture.md), [lyft-scc-case-study.md](../20-llm-agent-systems/lyft-scc-case-study.md)),
*is* a routing problem: a meta agent that classifies an inbound request and dispatches it to a
specialist — human or AI — with safety checks run before any model reasoning. "Design the system that
decides who or what handles an inbound support contact" is the design question this team would actually
ask, because it is the design question they actually answered. Study this file until you can produce
§5–§11 from memory in under 30 minutes.

It sits next to two reported prompts and should be cross-studied with both: the delivery mechanics are
[Real-Time Chat with Delivery Guarantees](realtime-chat-delivery-guarantees.md), and the third-party
failure mode this design is built around — *"a web application with a lot of third-party dependencies
that have a variety of failure modes"* — is exactly what an LLM call is from a routing engine's point of
view.

---

## 1 · Frame the problem in one sentence

> "A service that takes an inbound contact from any channel, decides — fast, and correctly under
> failure — whether an AI agent or a human should handle it and which one, tracks that decision against
> an SLA, and re-routes cleanly when the first choice cannot finish the job."

The exam inside this prompt is **the routing decision must be fast, cheap, and safe even when the thing
it is often routing *to* — an LLM call — is slow, expensive, and occasionally wrong.** A design that
only works when the model answers in 400 ms is not a design, it is a demo.

---

## 2 · Requirements and scoping

### 2.1 Functional

| # | Requirement |
|---|-------------|
| F1 | Accept an inbound contact from chat, in-app messaging, or phone, and normalise it into one canonical shape |
| F2 | Classify intent, and detect a small set of safety-critical intents before anything else runs |
| F3 | Assign a priority/SLA tier and start its clock at intake, not at classification |
| F4 | Route to an AI specialist agent or a human with the matching skill set |
| F5 | Track the decision, the handler, and the SLA against a queryable case record |
| F6 | Escalate — automatically on signal, always on explicit request — from AI to human without the user repeating themselves |
| F7 | Keep routing decisions and cases flowing when the LLM provider is slow, rate-limited, or down |

### 2.2 Non-functional (the ones that drive the design)

| # | Requirement | Consequence |
|---|-------------|-------------|
| N1 | Routing must be **more available than the thing it routes to** | The router cannot be a synchronous wrapper around an LLM call; it must have a path that does not depend on the model answering |
| N2 | No case is silently dropped | At-least-once intake, durable case record before any routing decision is acted on |
| N3 | A safety-tier case is never queued behind a routing decision | Safety classification runs as a cheap, deterministic, parallel pre-check, not as a stage inside the LLM path |
| N4 | Routing latency budget: **p99 < 2 s** for chat/in-app, **immediate** accept for phone | A model call cannot sit synchronously in the accept path for every channel |
| N5 | Fair allocation across skill groups under load | A queue design with an explicit anti-starvation rule, not "first come first served" dressed up as fair |
| N6 | Every routing decision is auditable | A compliance and a debugging requirement for a Safety & Customer Care org — log the *why*, not just the *what* |

### 2.3 Out of scope — say it and get agreement

The reasoning *inside* one specialist agent (prompting, tool use, retrieval) — that is
[20-llm-agent-systems](../20-llm-agent-systems/README.md) and a different round. Billing/payment
resolution logic. Building the classifier model itself (treat classification as a call to a scoring
service with a documented contract, the same way §7 of [design-round-protocol.md](design-round-protocol.md)
tells you to box out anything that is "a model", not "a system").

### 2.4 Scale assumptions

Reuse the platform-wide numbers already derived in
[napkin-math.md §8](napkin-math.md) rather than re-deriving them:

```
2M DAU · 10% start a support conversation/day = 200k conversations/day
30% get a human agent directly, 70% are agent-assisted    (napkin-math.md §8)
+ phone and in-app contacts not captured by the chat count: assumption, stated: +25% -> ~250k contacts/day
3x peak factor
```

| Quantity | Derivation | Answer |
|----------|------------|--------|
| Routing decisions/day | 250k contacts (each needs at least one) | 250k |
| Avg routing QPS | 250k / 86,400 | ~3/s |
| Peak routing QPS | ×3 | ~9/s |
| AI-first attempts/day | 70% of 250k | 175k |
| Assumption: mid-conversation escalation rate | stated, not sourced: 25% of AI-first conversations escalate | ~44k/day escalate |
| Human-touched, total | 30% direct + 25%×70% escalated | **~47.5%** of contacts, roughly half |
| Concurrent LLM calls in flight | 0.1 rps average platform load × 3 s/call (napkin-math.md §8, Little's Law) | ~1.5 avg, size for a multiple of peak |

**State the conclusion immediately, same as every other file in this section:** these numbers are small.
Nine routing decisions a second is not a scaling problem. The entire design difficulty is in
**decision quality under a slow, unreliable dependency, and fairness under bursty load** — an incident
that makes ten thousand riders open support at once does not care that steady state was nine per second.

---

## 3 · API surface first

```
POST /v1/contacts
  { "channel": "chat" | "in_app" | "phone",
    "user_type": "rider" | "driver",
    "user_id": "...",
    "context_ref": { "trip_id": "...", "channel_session_id": "..." } }
  -> 202 { "case_id": "...", "sla_tier": "P2", "state": "CLASSIFYING" }

GET  /v1/cases/{case_id}
  -> { "case_id", "state", "sla_tier", "handler": {"type": "ai"|"human", "id": "..."},
       "opened_at", "sla_due_at", "routing_history": [...] }

POST /v1/cases/{case_id}/escalate
  { "reason": "user_requested" | "low_confidence" | "sentiment" | "timeout" | "max_turns" }
  -> 200 { "case_id", "state": "QUEUED_FOR_HUMAN", "queue_position_hint": 4 }

POST /v1/cases/{case_id}/resolve   { "outcome": "resolved" | "abandoned", "csat": 4 }

GET  /v1/queues/{skill_group}      -> depth, oldest_wait_s, agents_online   (ops surface)
```

**Why intake returns `202` and a case in state `CLASSIFYING`, not a synchronous routing result.**
Classification may call an LLM. N4's latency budget is on *routing*, not on the model call finishing —
the client gets a case handle immediately and either opens a WebSocket/SSE stream on `case_id` for state
transitions (reusing the transport decision already made in
[realtime-chat-delivery-guarantees.md §4](realtime-chat-delivery-guarantees.md)) or polls `GET
/v1/cases/{id}`. This is the same "durable API, socket is an optimisation" shape as the chat design, for
the same reason: it makes the slow path safe to be slow.

**Phone is not a special case at this layer.** A telephony/IVR webhook creates a contact the instant the
call connects (`context_ref` empty), then `PATCH`-style transcript deltas stream into the same case as
they arrive from speech-to-text. Routing runs on whatever transcript exists so far — see §4.3 — rather
than waiting for the call to end.

```protobuf
message RoutingDecision {
  string case_id       = 1;
  string intent        = 2;          // taxonomy id, e.g. "safety.accident", "billing.refund"
  float  confidence     = 3;
  string sla_tier       = 4;         // P0..P3
  string handler_type   = 5;         // "ai" | "human"
  string handler_id     = 6;         // agent name or human queue id
  string decided_by     = 7;         // "rules" | "classifier" | "meta_agent" | "fallback"
  int64  decided_at_ms  = 8;
  reserved 9;                        // was: legacy_priority_int, replaced by sla_tier string
}
```

---

## 4 · Intake and normalisation across channels

### 4.1 Why normalise before anything else touches the contact

Classification, priority scoring, and routing must not know which channel a contact arrived on, or every
one of those components grows a channel switch statement and drifts out of sync. Everything downstream
of intake operates on one **Case** shape; the channel only determines how a Case gets created and how a
decision gets delivered back.

### 4.2 Channel adapters

| Channel | What creates the case | Latency shape | Special handling |
|---------|------------------------|----------------|-------------------|
| Chat widget / in-app messaging | First message, synchronously | Sub-second | Full text available immediately |
| In-app (non-chat) support flow | A structured form or a tap-to-report | Sub-second | Often already has `intent` as a strong prior — a "report an accident" button is worth more than any classifier |
| Phone / IVR | Call-connect webhook, before a word is transcribed | Streams in over the call duration | Route on partial signal, revise as more transcript arrives (§4.3) |

### 4.3 The phone problem: routing before you have the full input

A chat message is routed on a complete string. A phone call is not complete until the caller hangs up,
and you cannot hold routing for that. The answer is the same principle as
[Real-Time Chat §6.4](realtime-chat-delivery-guarantees.md) applied to a different stream: **treat the
transcript as an append-only, partially-ordered feed and act on a prefix, correcting later.**

- Route on the **IVR menu selection plus the first ~10 seconds of transcript**, not the whole call.
- Emit a `case.reclassified` event if the running transcript changes the intent materially (a caller who
  selected "billing" but says "I was in an accident" thirty seconds in) — this is a **re-routing** event,
  not a correction to history, and it must be able to jump a P2 case to P0 mid-call.
- Never block call answering on transcription. **Connect the human/AI fast; refine routing underneath
  the live interaction.** A caller who says "I need help" and hears silence for three seconds while a
  classifier thinks is a worse outcome than an imperfect first routing guess that self-corrects.

### 4.4 Context enrichment — fan out, do not chain

Before classification, the router pulls context that changes the decision: recent trip state, account
flags, prior case history, safety-hold status. Fetch all of it **in parallel**, not as a serial chain of
calls, and cap the wait — a slow enrichment call must degrade the *quality* of routing, never its
*latency*. This is the same shape as the "safety checks fanned out in parallel before any LLM reasoning"
principle from the target team's real platform (§5.1) — enrichment and safety checks are two instances of
the same scatter-gather-with-a-deadline pattern.

---

## 5 · Classification: rules, the safety fast path, and the LLM

### 5.1 Two stages, in a fixed order, and the order is the design

```
contact ──▶ [ deterministic pre-checks, run in PARALLEL, no LLM ] ──▶ safety hit? ──▶ P0, human, done
                                                                           │ no
                                                                           ▼
                                                        [ LLM / classifier: intent + confidence ]
```

**Deterministic checks come first and never touch the model.** Keyword and structured-signal matches —
an in-app "report a safety issue" button, an account already flagged, a transcript containing a small,
reviewed list of high-risk terms — run as cheap parallel lookups with a latency budget in the tens of
milliseconds. This is not a simplification of the real design; it is a direct restatement of the
published architecture: *safety checks are fanned out in parallel, before any LLM reasoning*
([lyft-architecture.md §9](lyft-architecture.md), detailed in
[lyft-scc-case-study.md §3.2](../20-llm-agent-systems/lyft-scc-case-study.md)). The reason to say this
unprompted: an LLM is a probabilistic function with latency and cost; a safety gate must be neither, and
putting it first means a scoring model or provider outage **cannot suppress a safety escalation** — it
can only fail to enrich one that is already guaranteed to go to a human.

**Everything that does not trip a deterministic rule goes to intent classification** — a call to a
scoring service (embedding similarity against a labelled intent taxonomy, or a small classifier prompt)
that returns `(intent, confidence)`. Whether that scoring step is itself "the LLM" or a cheaper model in
front of it is an implementation detail worth naming as a lever: a fast, cheap classifier for the common
case, with the expensive model reserved for cases the cheap one is unsure about — the same
cheap-filter-in-front-of-an-expensive-check shape as the crawler's bloom filter in front of an exact
store ([distributed-web-crawler.md §6.2](distributed-web-crawler.md)).

### 5.2 Confidence, and what "below threshold" means

| Confidence | Action |
|------------|--------|
| High (example: ≥ 0.85) | Route to the matching specialist AI agent |
| Medium | Route to a **generalist** AI agent with a broader tool surface, not a narrow specialist — a wrong narrow specialist is worse than a competent generalist |
| Low | Route directly to a human skill queue; do not let the AI attempt it "and see" |

**The thresholds above are illustrative, not a claimed Lyft number** — the point to make out loud is the
*shape*: confidence is a three-way gate (specialist / generalist / human), not a single pass/fail line,
because a narrow specialist agent given the wrong intent produces confidently wrong answers, which is a
worse failure than routing broad.

---

## 6 · Priority and SLA tiers

| Tier | Examples | First-response target | Who may handle it | Queue behaviour |
|------|----------|------------------------|--------------------|-----------------|
| **P0 — Safety** | accident, threat, medical emergency mentioned, active fraud | Immediate; page on-call human capacity if none free | Human only; an AI agent may assist a human but never resolves alone | Bypasses every queue; pre-empts |
| **P1 — Urgent** | active trip issue, driver stranded, payment dispute in progress, account locked | Seconds | AI attempt allowed, tight confidence bar, fast auto-escalation on any doubt | High-priority lane, small bounded wait |
| **P2 — Standard** | most billing questions, lost item, general account issue | Near-instant AI first response; human SLA in minutes if escalated | AI-first | Normal skill-group queue |
| **P3 — Low urgency / self-serve** | FAQ, receipt requests, generic how-to | Best effort; AI/self-serve first, human only on explicit request | AI/self-serve first | Lowest priority; **first to shed under load** (§9.3) |

**Start the SLA clock at intake, not at classification.** If the clock starts once the system knows what
it is dealing with, classification latency becomes invisible in your own metrics — you would be hiding
your slowest, most failure-prone component from your own SLA. Starting the clock at `POST /contacts`
means a slow classifier shows up immediately as an SLA risk, which is the honest measurement and the one
that survives a "how did you measure?" follow-up.

---

## 7 · Skill-based routing

### 7.1 Skill dimensions

| Dimension | Example values | Why it exists |
|-----------|-----------------|----------------|
| Product line | rider, driver, partner/fleet | Different policies, different tools, different risk profile — mirrors the platform's actual separate rider/driver routers ([lyft-architecture.md §9](lyft-architecture.md)) |
| Language/locale | en, uk, es, ... | Legal and quality requirement, not a nice-to-have |
| Certification | safety-trained, payments-trained, general | P0 cases require a specific certification, not just "an available human" |
| Handler capability | ai:billing-agent, ai:generalist, human:tier1, human:tier2-safety | Lets the same queueing machinery hold both AI and human handlers as interchangeable "workers with declared skills" |

### 7.2 Representing a skill set cheaply

Represent required and held skills as bitmasks (a skill taxonomy of a few dozen tags fits comfortably in
a 64-bit integer) so matching a case to a queue is a single AND, not a query:

```
case.required_skills = LANG_EN | PRODUCT_DRIVER | CERT_SAFETY
handler.skills        = LANG_EN | LANG_UK | PRODUCT_DRIVER | PRODUCT_RIDER | CERT_SAFETY
match  =  (case.required_skills & handler.skills) == case.required_skills   # O(1)
```

This is the same "cheap structural check in front of anything expensive" instinct as §5.1 — the match
test should never be the bottleneck; the wait for a matching worker to be free is where the real cost
lives.

### 7.3 Best-fit vs first-fit, and why first-fit usually wins here

Best-fit (route to the single most-qualified free handler) concentrates load on your most skilled agents
and starves everyone else's skill development. **First-fit within a skill group — any handler whose
skills satisfy the requirement, chosen by longest-idle or by the fairness rule in §8 — is the right
default**, with best-fit reserved deliberately for P0, where "most qualified" is worth the concentration
risk.

---

## 8 · Queueing and fairness

### 8.1 One queue per skill group, priority tiers within it

Exactly the structural move the crawler's frontier makes for politeness
([distributed-web-crawler.md §4.2](distributed-web-crawler.md)): a single global queue cannot express two
constraints at once (here: *skill match* and *priority*), so split by skill group first, then order each
skill group's queue by tier.

### 8.2 The anti-starvation problem

Strict priority order inside a skill group means a sustained stream of P1 arrivals can leave a P3 case
waiting forever — the same starvation failure a naive OS scheduler has, and the same fix applies: **age
priority with wait time.** The scheduler in §12.1 implements this with a detail worth previewing here:
because every case ages at the same rate, the *relative* order between two cases already in the queue
never changes over time — what changes the order is a **new** higher-tier case arriving with no head
start on aging. That means the whole mechanism reduces to a single number computed once, at enqueue time.

### 8.3 Should routing batch, the way matching does?

[lyft-architecture.md §8.3](lyft-architecture.md) states the transferable principle directly: *a batching
window converts a stream of greedy online decisions into a sequence of small offline optimisations,
trading latency for quality* — and names support-case assignment as a place it applies. **Price it
before adopting it:**

- For **P0/P1**, no: the whole point of those tiers is that the assignment latency itself is the cost
  being minimised, so batching would violate the requirement it is meant to serve.
- For **P2/P3**, plausibly yes, in a narrow form: if ten P3 cases and six generalist agents become
  available within the same second, a batch assignment (minimising total wait, respecting skills) beats
  ten independent greedy assignments that might hand a Ukrainian-speaking case to an English-only agent
  because it happened to ask first. Given the scale in §2.4 (single digits of decisions per second), a
  batching window of even one second is unlikely to accumulate enough volume to matter — **name the
  option, then say why the numbers do not justify building it here.** That is the more Staff-shaped
  answer than building it because the principle transfers.

---

## 9 · The AI-agent-first path

### 9.1 Shape

For everything that clears the safety gate and is not low-confidence, the default is an attempt by an AI
specialist agent, using the target team's actual pattern rather than inventing a new one: a **meta agent
acting as a stateful router**, dispatching via `Command(goto=...)` to a specialist subagent, with
conversation state checkpointed so a crash mid-conversation resumes instead of restarting. The mechanics
of the graph, the checkpointer, and the state machine are not re-derived here — see
[langgraph-patterns.md](../20-llm-agent-systems/langgraph-patterns.md) and
[agent-state-and-checkpointing.md](../20-llm-agent-systems/agent-state-and-checkpointing.md). This file's
job is the boundary around that subsystem: how a case enters it, and the rules for when it must leave.

**Two authoring tiers hold the same interface.** The platform mixes hand-built specialist agents with
JSON-configured "self-serve" agents pulling prompts from a prompt registry
([lyft-architecture.md §9](lyft-architecture.md)). The router does not need to know which kind it is
dispatching to — both declare a skill set and a confidence contract, and both are held in the same
handler registry as the human queues from §7.

### 9.2 Confidence thresholds and the triggers that override them

A conversation escalates from AI to human on **whichever comes first**:

| Trigger | Type | Notes |
|---------|------|-------|
| User explicitly asks for a human | Hard rule, always honoured | Never resisted, never re-attempted by the AI first — see §10.1 |
| Per-turn resolution confidence below a floor | Soft, model-reported | The agent's own uncertainty signal, not just the initial classifier's |
| N consecutive failed clarification turns (example: 2) | Structural | The agent is looping, not converging |
| Negative sentiment / frustration signal | Soft, scored | Cheap sentiment scoring, not an LLM call, sits in the loop for latency reasons |
| Max turns or max wall-clock time without resolution | Structural, hard cap | Bounds worst-case AI dwell time regardless of confidence |
| Safety keyword surfaces mid-conversation | Hard rule | Same deterministic gate as §5.1, re-run continuously, not just at intake |

### 9.3 The handoff packet

What must survive the AI-to-human transition is exactly the "what has to persist" question from
[agent-state-and-checkpointing.md §1](../20-llm-agent-systems/agent-state-and-checkpointing.md), scoped to
what a human needs: full transcript, extracted structured fields (trip id, amounts, dates already
parsed out), the escalation reason and confidence score, and a suggested next action. **The user must
never be asked to re-explain.** That is the same end-to-end argument as message deduplication in
[realtime-chat-delivery-guarantees.md §7.3](realtime-chat-delivery-guarantees.md): the effect (context
transfer) has to be guaranteed at the point it is observed (the human agent's screen), not assumed to
have happened because a handoff event was published.

---

## 10 · Escalation to a human

### 10.1 The one rule that is never soft

If a user asks for a human, they get queued for a human — immediately, with no additional AI turn spent
trying to talk them out of it. This is worth stating as an explicit design rule, not an emergent
behaviour: it is a hard `if`, checked before the meta-agent gets another turn, and it is the single
detail most likely to separate "worked in the demo" from "would survive a support-quality review."

### 10.2 Escalation must not reset the user's position

A case that escalates from AI to human keeps its **original `opened_at`** for SLA purposes, and its
queue insertion uses that original time for aging (§8.2), not the escalation time. Otherwise a user who
waited three minutes in an unsuccessful AI conversation is penalised twice: once for the AI's failure,
once by going to the back of the human line.

### 10.3 Warm handoff, not cold transfer

The handoff packet from §9.3 is attached to the case *before* it reaches a human queue, so an agent
picking it up sees the summary immediately rather than fetching it as a second step. Making the summary
part of the queue entry itself, not a follow-up lookup, is what keeps a busy agent from opening a case
cold under load — the same "don't make the recipient chase context" instinct as attaching the enrichment
result (§4.4) to the case record rather than requiring a second round trip.

---

## 11 · When the LLM is slow or down

This is the section a good interviewer pivots to, because it is where N1 either holds or breaks.

### 11.1 Per-call deadline

Reuse the number already derived for this exact workload: **napkin-math.md §8** sizes the target team's
agent calls at ~3 seconds average with Little's Law giving ~1.5 concurrent calls at steady state — so a
**hard per-call deadline, on the order of a few seconds**, is not arbitrary, it is sized from the
platform's own observed shape. A call that exceeds its deadline is treated as a failure, not retried
inline on the user's clock — see §11.2.

### 11.2 Circuit breaker, not a retry loop

A timed-out or erroring call increments a failure counter; past a threshold, the breaker opens and **the
router stops trying the AI path entirely for a cooldown window**, sending every case that would have gone
to that agent straight to §5.2's "low confidence" human path instead. This is the identical mechanism to
the crawler's per-host park/probe breaker
([distributed-web-crawler.md §10.2](distributed-web-crawler.md)) applied to a model provider instead of a
web host: park, do not hammer; probe on a half-open state; close on sustained success. Implemented in
§12.2.

**Never let a user's wait time depend on the LLM retrying.** One retry with jitter at the call layer is
defensible; a user-visible spinner tied to an unbounded retry loop is the retry-storm failure mode this
whole program flags repeatedly (rate limiting, §11.3 below, and
[rate-limiter.md](rate-limiter.md)) — and it is worse here, because the "client" retrying is your own
routing service under its own SLA.

### 11.3 The load-shedding consequence, and the shed order

If the AI path is unavailable, **every** case that would have gone to it now needs a human — for the
scale in §2.4 that is a 70% surge in human-bound volume, arriving with no warning. The router cannot
treat this as "route them all and let the queue absorb it"; it must shed, in this order, cheapest and
lowest-value first:

1. **P3 self-serve traffic degrades to static help-centre content** — no case opened at all, not queued
   with everyone else.
2. **P2 traffic queues normally but with a relaxed SLA**, communicated to the user, not silently missed.
3. **P1 and P0 are never shed** — they are the reason the human queues exist at all; if capacity is
   truly insufficient at that tier, the answer is paging more human capacity, not dropping cases.

This is the same shedding discipline as
[realtime-chat-delivery-guarantees.md §13](realtime-chat-delivery-guarantees.md) — *rank what you shed,
and never shed the thing the design exists to protect* — applied to human queue capacity instead of a
message send queue.

### 11.4 Degraded classification, not just degraded resolution

A provider outage can take down the intent classifier too, not only the resolution agent. The fallback
is the deterministic layer from §5.1, widened: a small, versioned keyword/regex ruleset that assigns a
coarse intent and a **conservative (never lower than warranted) tier** — coarse routing beats no routing,
and erring toward a higher tier under uncertainty is the safe direction to be wrong in.

---

## 12 · Storage model

### 12.1 Access patterns

| # | Pattern | Rate | Shape |
|---|---------|------|-------|
| A1 | Create a case | ~9/s peak | Single-item write |
| A2 | Read/update one case by id | High | Point read/write |
| A3 | "What is due soonest in skill group X" | Per dequeue, continuous | Range scan by due time within a partition |
| A4 | "Cases nearing SLA breach, across all groups" | Ops/alerting, periodic | Cross-partition — a GSI or a separate index, not the base table |
| A5 | Routing decision log for one case (audit) | Low, read on demand | Range scan on case id |

### 12.2 The queue is the crawler's frontier again

The routing queue is, structurally, the exact same problem as the crawler's frontier
([distributed-web-crawler.md §4.4](distributed-web-crawler.md)): a durable, lease-based table beats an
in-memory-only queue for the same reason — a crashed router node must not lose or double-assign a case.

```
queue_entries
  PK = skill_group                       # e.g. "human#driver#en#cert_safety"
  SK = agent_key#case_id                 # agent_key = tier + AGING_PER_SECOND*opened_at, see §12.3 code
  state = ENUM(WAITING, LEASED, DONE)
  owner, lease_until                     # a crashed dispatcher's lease simply expires — same pattern as §10.4 of the crawler file
```

`skill_group` as the partition key keeps each queue's range scan cheap and bounded; a case with multiple
acceptable skill groups (rare, but real for generalist handling) is written once per eligible group and
the losing copies are marked `DONE` on assignment — cheap, because queue entries are tiny and short-lived,
unlike the message-store bound that drove the month-bucketing decision in the chat design.

### 12.3 The case record itself

```
cases (PK = case_id)
  channel, user_type, user_id
  intent, confidence, sla_tier
  handler_type, handler_id
  state: ENUM(CLASSIFYING, ROUTED_AI, ROUTED_HUMAN, ESCALATED, RESOLVED, ABANDONED)
  opened_at, sla_due_at, resolved_at
  routing_history: [ {decided_by, intent, confidence, tier, at_ms} ]   # append-only, small, kept inline
```

DynamoDB fits this well for the reasons already established in
[lyft-architecture.md §7](lyft-architecture.md): known access patterns, small items, conditional writes
for exactly the idempotent-intake guarantee N2 needs (`PutItem` with
`ConditionExpression="attribute_not_exists(case_id)"` on a client-generated id makes a retried `POST
/contacts` safe), and per-item TTL for eventual case-record expiry once resolved cases age out of hot
storage.

---

## 13 · Code the round may ask for

### 13.1 Fair skill queue with anti-starvation

*"Cases pile up faster than agents free up during an incident. How do you make sure low-priority cases
are not starved forever?"*

```python
import heapq
import itertools
from dataclasses import dataclass, field


@dataclass(order=True)
class _Entry:
    key: float
    seq: int
    case_id: str = field(compare=False)
    tier: int = field(compare=False)


class SkillQueue:
    """Priority queue for one skill group, ageing low-tier cases so a
    steady stream of *new* high-tier arrivals cannot starve them forever.

    Tier 0 is most urgent. Strict priority pops every tier-0 case before
    touching a single tier-3 one, so a sustained P1 surge can leave a P3
    case waiting indefinitely. The fix is to age priority linearly with
    wait time -- but recomputing every entry's score on every pop is
    O(n log n) and pointless. Because every entry ages at the *same* rate,
    the relative order between two entries already in the queue never
    changes as time passes: what changes the order is a new entry arriving
    with no head start. That makes the score a pure function of
    (tier, arrival_time), computable once at enqueue time -- the heap
    never needs rescoring.
    """

    AGING_PER_SECOND = 0.02   # priority points recovered per second waited

    def __init__(self) -> None:
        self._heap: list[_Entry] = []
        self._counter = itertools.count()

    def enqueue(self, case_id: str, tier: int, now: float) -> None:
        """`now` is a monotonic clock reading in seconds (e.g. time.monotonic()),
        used as the arrival timestamp -- not wall-clock epoch time, to keep
        the key small."""
        key = tier + self.AGING_PER_SECOND * now
        heapq.heappush(self._heap, _Entry(key, next(self._counter), case_id, tier))

    def dequeue(self) -> str | None:
        if not self._heap:
            return None
        return heapq.heappop(self._heap).case_id

    def __len__(self) -> int:
        return len(self._heap)
```

```python
import unittest


class TestSkillQueue(unittest.TestCase):
    def test_strict_priority_among_simultaneous_arrivals(self):
        q = SkillQueue()
        q.enqueue("p3-case", tier=3, now=0.0)
        q.enqueue("p1-case", tier=1, now=0.0)
        q.enqueue("p0-case", tier=0, now=0.0)
        self.assertEqual(q.dequeue(), "p0-case")
        self.assertEqual(q.dequeue(), "p1-case")
        self.assertEqual(q.dequeue(), "p3-case")

    def test_aging_lets_an_old_low_tier_case_overtake_a_fresh_high_tier_one(self):
        q = SkillQueue()
        q.enqueue("old-p3", tier=3, now=0.0)
        # 200s later a fresh P1 arrives; at 0.02/s the P3 case has aged 4.0 points
        q.enqueue("new-p1", tier=1, now=200.0)
        self.assertEqual(q.dequeue(), "old-p3")
        self.assertEqual(q.dequeue(), "new-p1")

    def test_fifo_within_the_same_tier(self):
        q = SkillQueue()
        q.enqueue("first", tier=2, now=10.0)
        q.enqueue("second", tier=2, now=11.0)
        self.assertEqual(q.dequeue(), "first")

    def test_empty_queue_returns_none(self):
        self.assertIsNone(SkillQueue().dequeue())


if __name__ == "__main__":
    unittest.main()
```

**What to say while writing it:** the insight is not "add aging" — every candidate says that — it is
*why* aging collapses to a static key here (uniform rate, so the comparison's time-dependent term
cancels), which turns an O(n log n)-per-pop mechanism into a plain heap with no rescoring at all. That is
the kind of simplification the "readable over clever" grading rewards: fewer moving parts, not more.

### 13.2 Circuit breaker around the AI path

*"What happens to routing when the LLM provider is slow?"*

```python
from dataclasses import dataclass
from enum import Enum, auto


class _State(Enum):
    CLOSED = auto()      # calling the agent normally
    OPEN = auto()         # short-circuiting straight to a human, no call attempted
    HALF_OPEN = auto()    # letting exactly one probe call through


@dataclass
class BreakerConfig:
    failure_threshold: int = 5    # consecutive failures/timeouts before opening
    cooldown_s: float = 30.0      # time spent OPEN before a probe is allowed
    call_deadline_s: float = 3.0  # napkin-math.md's per-call budget for this workload


class AgentCallBreaker:
    """Guards the call into the AI routing path so a slow or dead LLM
    provider degrades to human routing instead of hanging every case
    behind it -- N1's requirement made concrete.

    The deadline itself is enforced by the caller (e.g.
    `ThreadPoolExecutor(...).submit(call_agent, case).result(timeout=...)`
    or an asyncio `wait_for`); this class only tracks whether that deadline
    was met and decides whether the *next* case should even try.

    Simplified for a single router instance: a concurrent deployment needs
    a compare-and-swap (or one designated prober) around the OPEN-to-
    HALF_OPEN transition, or several nodes can all launch a probe at once
    the instant cooldown elapses -- a small thundering herd against a
    provider that is only just recovering.
    """

    def __init__(self, config: BreakerConfig | None = None) -> None:
        self.config = config or BreakerConfig()
        self._state = _State.CLOSED
        self._consecutive_failures = 0
        self._opened_at = 0.0

    def allow_call(self, now: float) -> bool:
        """True if the AI path should be tried at all right now."""
        if self._state == _State.OPEN:
            if now - self._opened_at >= self.config.cooldown_s:
                self._state = _State.HALF_OPEN
                return True                       # the single probe call
            return False
        return True                                # CLOSED or HALF_OPEN

    def record_success(self) -> None:
        self._state = _State.CLOSED
        self._consecutive_failures = 0

    def record_failure(self, now: float) -> None:
        self._consecutive_failures += 1
        if self._state == _State.HALF_OPEN or \
                self._consecutive_failures >= self.config.failure_threshold:
            self._state = _State.OPEN
            self._opened_at = now

    @property
    def state(self) -> str:
        return self._state.name
```

```python
import unittest


class TestAgentCallBreaker(unittest.TestCase):
    def test_opens_after_threshold_consecutive_failures(self):
        b = AgentCallBreaker(BreakerConfig(failure_threshold=3, cooldown_s=30))
        for t in (0, 1, 2):
            self.assertTrue(b.allow_call(now=t))
            b.record_failure(now=t)
        self.assertEqual(b.state, "OPEN")
        self.assertFalse(b.allow_call(now=5))       # still inside the cooldown

    def test_half_open_probe_after_cooldown_then_closes_on_success(self):
        b = AgentCallBreaker(BreakerConfig(failure_threshold=1, cooldown_s=10))
        b.record_failure(now=0)
        self.assertEqual(b.state, "OPEN")
        self.assertFalse(b.allow_call(now=5))
        self.assertTrue(b.allow_call(now=11))       # cooldown elapsed: one probe allowed
        self.assertEqual(b.state, "HALF_OPEN")
        b.record_success()
        self.assertEqual(b.state, "CLOSED")

    def test_failed_probe_reopens_immediately(self):
        b = AgentCallBreaker(BreakerConfig(failure_threshold=1, cooldown_s=10))
        b.record_failure(now=0)
        b.allow_call(now=11)                        # -> HALF_OPEN
        b.record_failure(now=11)
        self.assertEqual(b.state, "OPEN")

    def test_success_resets_the_failure_count(self):
        b = AgentCallBreaker(BreakerConfig(failure_threshold=3))
        b.record_failure(now=0)
        b.record_failure(now=1)
        b.record_success()
        b.record_failure(now=2)
        self.assertEqual(b.state, "CLOSED")         # count was reset; only one failure since


if __name__ == "__main__":
    unittest.main()
```

---

## 14 · Failure modes

| Component | Failure | Detection | Mitigation | User sees |
|-----------|---------|-----------|------------|-----------|
| Intent classifier / LLM | Slow or down | Deadline breach rate, breaker state | Breaker opens; route via §11.4's deterministic fallback | Slightly generic first response, no delay |
| Specialist AI agent | Wrong/looping | Max-turns cap, confidence floor | Auto-escalate to human with full handoff packet | A human joins, already briefed |
| Safety pre-check service | Down | Health check | **Fail closed**: treat as a potential safety case, route to human — never fail open on this one check | Possibly over-escalated, never under-escalated |
| Queue table (DynamoDB) | Partition throttled | Write latency/error rate | Backoff and retry with the idempotent case id; queue entries are small and cheap to retry | Slight delay in appearing in a queue |
| Router node | Crash mid-lease | Lease TTL expiry | Another node picks up the leased-but-unfinished assignment | Brief reassignment delay, no lost case |
| Skill-group starvation | Real agent shortage in one language/product | Queue-depth and oldest-wait alerting per skill group | Page for cross-trained coverage; widen the skill match temporarily as a documented degrade, not silently | Longer wait, ideally communicated |
| Phone transcription | Lag or failure | Transcript staleness metric | Route on IVR menu selection alone; flag case for human transcript review | Call still connects promptly |

---

## 15 · Working design vs good design, for this problem

| Working | Good |
|---------|------|
| "Classify with an LLM, then route" | Deterministic safety checks run first, in parallel, and never depend on the model being up |
| "AI handles it or a human does" | A three-way confidence gate — specialist / generalist / human — because a wrong specialist is worse than a competent generalist |
| "Priority queue by tier" | Tier plus wait-time ageing, collapsed into a single static sort key so the heap never needs rescoring |
| "If the LLM is down, retry" | A circuit breaker with a bounded deadline, cooldown, and half-open probe; the shed order for the resulting human-queue surge is stated explicitly |
| "Escalate to a human" | The handoff packet carries full context so the user never repeats themselves, and the case keeps its original SLA clock |
| "It's a queue and a classifier" | Structurally the crawler's leased frontier applied to skill groups instead of hosts — the same durability pattern, reused rather than reinvented |

---

## Interview questions

**1. How would you design routing for inbound support contacts across chat, in-app, and phone?**
Normalise every channel into one canonical case shape at intake, run deterministic safety checks in
parallel before any model call, then classify intent and confidence to decide between a specialist AI
agent, a generalist AI agent, or a human skill queue. The design has to assume the LLM step is slow or
absent: routing itself must stay available and fast even when the thing it is often routing to is not.

**2. Why run safety checks before the LLM instead of as part of the agent's reasoning?**
Because an LLM call is a probabilistic function with latency and cost, and a safety gate must be neither
— it needs to be a fixed, fast, deterministic check that a model outage cannot suppress. Running it in
parallel, ahead of any reasoning step, means the worst a broken classifier can do is fail to *enrich* a
safety escalation, never fail to *trigger* one. This mirrors the target team's actual published design.

**3. What happens to routing when the LLM provider is slow or down?**
A per-call deadline sized from the platform's own observed latency, a circuit breaker that stops trying
the AI path after repeated failures rather than retrying on the user's clock, and an explicit shed order
for the resulting surge in human-bound volume: self-serve traffic degrades to static content first,
standard traffic queues with a relaxed SLA, and urgent/safety traffic is never shed.

**4. How do you keep a low-priority case from waiting forever during a high-priority surge?**
Age its effective priority with wait time. The efficient version of that idea is a single static sort key
computed at enqueue time — tier plus a small constant times arrival time — because every entry ages at
the same rate, so the order between two already-queued entries never changes; only a fresh, unaged
arrival can outrank an old one. That avoids ever rescoring the whole queue.

**5. When does an AI-handled conversation escalate to a human?**
Whichever comes first: an explicit user request, honoured immediately with no further AI turn; the
agent's own per-turn confidence dropping below a floor; a small fixed number of failed clarification
turns; a negative-sentiment signal; a hard cap on turns or wall-clock time; or a safety keyword surfacing
mid-conversation, using the same deterministic gate as intake.

**6. What state has to transfer when a case moves from AI to human?**
Everything a human needs to avoid making the user repeat themselves: the full transcript, any structured
fields already extracted, the escalation reason and confidence, and a suggested next action — attached to
the case before it reaches the human queue, not fetched as a second step. The case also keeps its
original open time for SLA and queue-fairness purposes, so escalating does not penalise the user twice.

**7. What partition key would you use for the routing queue?**
Skill group as the partition key, an aging-based composite score plus case id as the sort key — the same
lease-based, durable-queue shape as the web crawler's frontier, applied to skill groups instead of hosts.
A crashed dispatcher's lease simply expires and another node picks the case back up.

**8. How is this different from a generic priority queue?**
Two constraints have to be satisfied at once — skill match and priority — and a single global queue can
express only one of them well. Splitting by skill group first and ordering by an ageing-aware priority
inside each group is structurally identical to the reason a web crawler cannot use one global URL queue:
politeness and priority are different axes, and conflating them either starves fairness or breaks the
constraint.

**9. Would you batch routing decisions the way ride matching batches riders and drivers?**
The principle transfers — a batching window turns greedy online assignment into a small offline
optimisation — but pricing it kills it for the top two tiers, where minimising assignment latency *is*
the requirement, and the volumes in the lower tiers are too small at this scale for a batch to
meaningfully improve on greedy first-fit. Naming the option and then declining it with a stated reason is
the stronger answer than building it because the principle applies.

**10. What is the single most important design decision in this file?**
That the router has to be more available than the model it routes to. Every other decision — the
deterministic safety gate running first, the circuit breaker around the AI path, the explicit shed order,
the fallback classifier — is a consequence of treating the LLM as a third-party dependency with its own
failure modes, not as a reliable subroutine the design can assume will answer.
