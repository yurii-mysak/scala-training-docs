# Design Round Protocol — a repeatable 60-minute structure

> **Priority:** Required
> **Est. time:** 45 min
> **Track:** Both
> **HelloInterview:** System Design in a Hurry → Delivery Framework; Core Concepts → API Design

The senior/staff loop shape is **one coding round and two design rounds**. Design is therefore the
highest-weight surface in the loop, and it is the surface where downlevelling to Senior is decided.

---

## 1 · What this round actually is

Lyft's design round is **not an abstract FAANG design round**. Reported characteristics:

| Expected | Not expected |
|----------|--------------|
| Real coding inside the design round | Pure box-drawing for 60 minutes |
| Code review of a snippet you or they wrote | Memorised reference architectures |
| Library and technology choices, defended | Naming products without trade-offs |
| Testing strategy for the thing you designed | "We'd add tests" as a closing line |
| Concrete schemas, keys, and API signatures | Hand-waving at "a database" |
| Live back-of-envelope math on **memory and CPU** | Deferring numbers to "we'd measure it" |
| **NoSQL depth** — partition keys, hot partitions, access patterns | "Cassandra scales, so Cassandra" |

Two probes recur by name and you should assume both will appear:

1. **NoSQL depth.** Expect to be pushed past "we use DynamoDB" into partition key choice, sort key,
   item size, GSIs, hot partitions, and what breaks at 10x. Pre-load
   [DynamoDB Refresher](../06-databases-and-distributed-data/dynamodb_refresher.md) and
   [Cassandra Partition vs Clustering Keys](../06-databases-and-distributed-data/cassandra_partition_clustering.md).
2. **Live napkin math on memory and CPU.** Not storage-only. Expect "how much RAM does that cache
   need" and "how many cores does that service need". See [napkin-math.md](napkin-math.md).

**The bar, from an interviewer explaining a rejection:**

> *"Having a full working design is not the same as having a good design. Answering all questions the
> interviewer has does not mean that you gave satisfactory answers."*

Read that twice. Completeness is table stakes; it is not the signal. The signal is **judgement made
visible** — that you considered alternatives, priced them, and chose.

---

## 2 · The 60-minute clock

Announce the plan in the first minute. It costs 15 seconds and it buys you the right to control the
session. If the interviewer wants a different order, they will say so — that is also information.

| Minute | Phase | Output on the canvas |
|--------|-------|----------------------|
| 0–2 | Frame | One sentence: what we are building, for whom, at what scale |
| 2–8 | **Requirements & scoping** | Functional list (3–5), non-functional list (3–5), explicit out-of-scope |
| 8–10 | Scale assumptions | 4–6 numbers, stated as assumptions, written down |
| 10–18 | **API surface** | 4–8 endpoints/RPCs with request and response shapes |
| 18–28 | **Data model** | Entities, access-pattern table, store choice, keys |
| 28–33 | High-level diagram | 6–9 boxes, arrows labelled with protocol |
| 33–43 | **Scale** | Where it breaks first, sharding, caching, the math |
| 43–52 | **Failure modes** | Component-by-component table, degraded behaviour |
| 52–58 | **Trade-off summary** | Two designs, priced; what you chose and why; what you would do with more time |
| 58–60 | Questions for them | One real question about their systems |

Two rules for the clock:

- **Say the time out loud at transitions.** "That is about ten minutes on requirements and API — I want
  to move to the data model now unless you want more here." This reads as senior; silent drift reads
  as junior.
- **Never let a phase run over by more than 3 minutes.** A design that reaches the failure-mode section
  beats a beautiful data model with nothing after it.

---

## 3 · Phase 1 — requirements and scoping (minutes 2–8)

The purpose is not to gather requirements. It is to **demonstrate that you narrow before you build**,
and to buy yourself the right to declare things out of scope.

### 3.1 The scoping question bank

Ask 4–6 of these, not all of them. Pick the ones whose answer would change the design.

| Category | Question | What the answer changes |
|----------|----------|-------------------------|
| Users | Who are the actors — riders, drivers, support agents, internal services? | API shape, auth model |
| Scale | DAU, peak-to-average ratio, read:write ratio? | Sharding, caching, cost |
| Consistency | Is a stale read acceptable? For how long? | Store choice, replication mode |
| Durability | What is the cost of losing one record? | Write path, ack semantics |
| Latency | What is the p99 budget end to end? | Sync vs async, hop count |
| Correctness | What must never happen — duplicate charge, lost message, wrong recipient? | Idempotency, transactions |
| Lifecycle | Retention, deletion, GDPR/right to erasure? | Partitioning, TTL, crypto-shredding |
| Multi-region | One region or several? Data residency constraints? | The hardest constraint; ask early |
| Clients | Mobile, web, service-to-service? | Transport, payload format, offline |
| Existing | Is there a system today, and what is wrong with it? | Migration is often the real question |

### 3.2 Write it down in this shape

```
FUNCTIONAL
  F1  Agent and rider exchange messages in a case thread
  F2  Messages survive client restart and are delivered when the client returns
  F3  Read receipts and typing indicators
NON-FUNCTIONAL
  N1  p99 in-session delivery < 500 ms
  N2  No message loss once the server has acked (durability > latency here)
  N3  Ordering per conversation, not global
OUT OF SCOPE (say it, get agreement)
  Voice/video, attachments beyond a link, E2E encryption, compliance archival
ASSUMPTIONS
  2M DAU, 200k support sessions/day, 20 msgs/session, 3x peak
```

### 3.3 The scoping moves that read as Staff

- **Name the hardest requirement and say why.** "Of these, N2 is the expensive one — it forces a
  durable write before ack, which puts a storage round trip on the hot path."
- **Cut scope explicitly, with the cost.** "I am dropping E2E encryption. It would prevent server-side
  search and abuse detection, which for a support product is a bad trade. If safety review needs it,
  the design changes here and here."
- **Refuse to design for a scale nobody asked for.** If the number is small, say so. Real example from
  Lyft's own published support platform: **~270k agent interactions per month** is about **0.1 requests
  per second on average**. A design that opens with Kafka and sharded Cassandra for that load is a
  *worse* design, not a better one, and saying so is a strong signal.

---

## 4 · Phase 2 — API surface first (minutes 10–18)

**Why API before data model.** The API is the contract; the data model is an implementation detail
that serves it. Designing the schema first makes you leak storage decisions into the interface, and it
is much harder to notice a missing requirement while staring at a table definition. Writing the API
first also forces you to answer "who calls this and what do they get back", which is where most
ambiguity actually lives.

### 4.1 What to write

For each operation: name, direction, request, response, error cases, idempotency, and pagination.

```
POST /v1/conversations/{cid}/messages
  Idempotency-Key: <client uuid>            # required, dedupe window 24h
  { "client_msg_id": "...", "body": "...", "attachments": [] }
  -> 201 { "message_id": "...", "seq": 10432, "server_ts": "..." }
  -> 409 duplicate client_msg_id -> returns the original message (not an error to the user)
  -> 422 same Idempotency-Key with a different body

GET  /v1/conversations/{cid}/messages?since_seq=10400&limit=100
  -> 200 { "messages": [...], "next_seq": 10500, "has_more": true }
```

### 4.2 The checklist to run over every API you draw

| Item | Question to answer out loud |
|------|-----------------------------|
| Idempotency | Which writes are retryable, and what makes the retry safe? |
| Pagination | Cursor or offset? Cursors, because offset breaks under concurrent inserts |
| Versioning | Path version, or additive-only fields? At Lyft: protobuf field numbers |
| Errors | Typed error codes, retryable flag, `Retry-After` |
| Auth | Who is the caller, and what scopes are checked where? |
| Bulk | Is there an N+1 pattern that needs a batch endpoint? |
| Streaming | Does any endpoint need server-push, and via what transport? |
| Deadlines | Does the caller pass a deadline you must propagate? |

### 4.3 Lyft-flavoured API notes

Lyft is **protobuf + gRPC between services**, Flask for HTTP APIs, Envoy in front of everything.
Sketch the proto, not just the REST path — it takes the same time and it signals you have worked in a
schema-first shop:

```protobuf
service Conversations {
  rpc SendMessage(SendMessageRequest) returns (SendMessageResponse);
  rpc StreamEvents(StreamEventsRequest) returns (stream ConversationEvent);
}
message SendMessageRequest {
  string conversation_id = 1;
  string client_msg_id   = 2;  // idempotency key, client-generated
  string body            = 3;
  reserved 4;                  // was: plaintext_attachment_url, removed in v3
}
```

Details: [gRPC & Protobuf Schema Design](grpc_protobuf_schema_design.md),
[lyft-architecture.md](lyft-architecture.md).

---

## 5 · Phase 3 — data model second (minutes 18–28)

This is where the **NoSQL depth probe** lands. The sequence that survives the probe:

1. **List entities and relationships** — 4–7 boxes, no more.
2. **Write the access-pattern table before naming any database.** This is the single highest-value
   artefact in the round.
3. **Then** choose the store, per access pattern, and justify it.
4. **Then** write the keys explicitly.

### 5.1 The access-pattern table

| # | Access pattern | Frequency | Latency budget | Consistency |
|---|----------------|-----------|----------------|-------------|
| A1 | Fetch last 50 messages in a conversation | 5k/s | 50 ms | Read-your-writes |
| A2 | Append a message | 150/s | 100 ms | Durable before ack |
| A3 | List a user's conversations by recency | 500/s | 100 ms | Eventual OK |
| A4 | Full-text search across a user's cases | 20/s | 500 ms | Eventual OK |
| A5 | Rebuild an agent's queue after failover | rare | 10 s | Strong |

Now the store choice writes itself: A1/A2 want a partitioned log-shaped store keyed by conversation;
A3 wants a secondary index or a separate inbox table; A4 wants Elasticsearch fed by CDC; A5 wants the
source of truth, not the cache.

### 5.2 Say the key out loud, always

Never say "we store it in DynamoDB". Say:

> `PK = conversation_id`, `SK = seq` (monotonic per conversation), item ~400 bytes, hot conversations
> bounded by time-bucketing the PK to `conversation_id#yyyymm` so no item collection approaches the
> 10 GB limit, and so a single very long thread cannot pin one partition.

Then immediately price it: "That gives me A1 as a single query with a range on the sort key. It costs
me A3 — listing a user's conversations is now a GSI on `user_id` with `last_message_at` as the sort
key, which is eventually consistent and has its own throttling behaviour."

### 5.3 The follow-ups you must have answers for

| Probe | Have ready |
|-------|-----------|
| "What if one partition gets 100x the traffic?" | Key salting/sharding suffix, time bucketing, write-through cache, and the read-path change each forces |
| "What is your item size, and what happens at the limit?" | 400 KB DynamoDB item limit; offload blobs to S3, store the pointer |
| "How do you query by something that is not the key?" | GSI (and its cost, eventual consistency, and independent throttling) or a search index fed by streams/CDC |
| "Why not Postgres?" | Have the honest answer: for many of these, Postgres *is* right up to a large scale. Say the crossover point |
| "How do you delete a user's data?" | Partitioning by user, TTL, or crypto-shredding with a per-user key |
| "How do you evolve the schema?" | Additive fields, dual-write/dual-read migration, backfill job, version tag on the item |

Background already in the repo:
[RDBMS vs NoSQL](../06-databases-and-distributed-data/RDBMS_vs_NoSQL.md) ·
[Partition Strategies](../06-databases-and-distributed-data/partition_strategies.md) ·
[Partitioning & Rebalancing](../06-databases-and-distributed-data/Partitioning_Rebalancing.md) ·
[Wide-Column vs Document](../06-databases-and-distributed-data/WideColumn_vs_Document.md) ·
[Indexing & Query Optimisation](../06-databases-and-distributed-data/Indexing_Optim.md).

---

## 6 · Phase 4 — scale (minutes 33–43)

Do not "scale everything". Answer three questions in order:

1. **What breaks first?** Name one component and the number at which it breaks. This is a math
   question, so do the math — see [napkin-math.md](napkin-math.md).
2. **What is the cheapest fix?** Usually: cache, then read replica, then shard. Reach for sharding
   last, and say that you are reaching for it last.
3. **What does the fix cost?** Cache adds staleness and an invalidation problem. Replicas add
   replication lag and read-your-writes bugs. Sharding adds cross-shard queries and rebalancing.

Template sentence:

> "At 150 writes/s the storage is fine — that is nothing for a single Postgres. The first thing to
> break is the fan-out: at 3x peak and an average of 40 recipients that is 18k pushes/s through one
> gateway tier, and a single node holding 60k WebSockets at ~50 KB each is already 3 GB of connection
> state. So I shard gateways by connection and put the routing table in Redis rather than growing the
> node."

---

## 7 · Phase 5 — failure modes (minutes 43–52)

Most candidates run out of time here. Budget for it, because it is where "working design" becomes
"good design". Run the table, one row per component, out loud:

| Component | Failure | Detection | Mitigation | User-visible behaviour |
|-----------|---------|-----------|------------|------------------------|
| Gateway node | Crash | Heartbeat TTL expiry | Client reconnects with jittered backoff, resyncs from `since_seq` | Brief gap, no loss |
| Primary DB | Failover | Health check, write errors | Retry with idempotency key; reads to replica | Elevated latency, some 503s |
| Cache | Cold / evicted | Hit-rate alarm | Request coalescing, warm from source | Latency spike, correct answers |
| Queue consumer | Lag | Consumer lag metric | Scale out; DLQ for poison messages | Delayed side effects |
| Third-party API | Slow, not down | Latency SLO, breaker state | Timeout + breaker + fallback | Degraded feature, not an outage |

Four questions to force yourself through every design:

- **What if this call is retried?** (Idempotency — see [idempotency-and-deduplication.md](idempotency-and-deduplication.md))
- **What if this component is slow rather than dead?** (The harder case — see [third-party-failure-modes.md](third-party-failure-modes.md))
- **What if it comes back after being down for hours?** (Backlog, thundering herd, catch-up budget)
- **What is the blast radius?** (Bulkheads, per-tenant isolation, shed order)

---

## 8 · Phase 6 — surfacing trade-offs explicitly (minutes 52–58)

A reported interviewer wanted **"the pro and con of your design, more than one design consideration"**.
This is the most actionable feedback in the whole corpus: the failure was not a wrong design, it was
presenting **one** answer as if it were the only one.

### 8.1 The alternatives ledger

Keep a running list in the corner of the canvas from minute 10. Every time you make a choice, add a
row. At minute 52 you read it back. It takes five seconds per row to record and it is the entire
difference between "answered the questions" and "gave satisfactory answers".

| Decision | Chose | Alternative | Why chosen | What it costs | When I would flip |
|----------|-------|-------------|------------|---------------|-------------------|
| Transport | WebSocket | SSE + POST | Bidirectional, low per-message overhead | Stateful gateways, LB and proxy config | Read-mostly feed, or corporate proxies break WS |
| Ordering | Server-assigned per-conversation seq | Client timestamps | No clock-skew bugs, gap detection is free | Sequencer is a per-conversation serialisation point | Ordering not required |
| Store | DynamoDB `PK=conv#bucket, SK=seq` | Cassandra | Managed, TTL, conditional writes | Access patterns fixed early, GSI cost | Self-hosted, need multi-DC writes |
| Receipts | `last_read_seq` per participant | Per-message receipt rows | O(1) writes instead of O(messages) | Cannot show per-message read state | Small groups where per-message UX matters |

### 8.2 Sentence stems that make trade-offs audible

- "There are two reasonable designs here. A is ..., B is .... I am picking A because ..., and the price
  I pay is ...."
- "This is the wrong choice if <condition>. The signal that would make me switch is <metric>."
- "The simple version is <X>. I would ship that first, and only add <Y> when <specific number> is hit."
- "I want to flag that this is the riskiest part of the design, and here is how I would de-risk it."
- "That is a real cost and I do not have a great answer for it. The mitigation I would try first is ...."

### 8.3 Anti-patterns

| Anti-pattern | Why it reads as Senior, not Staff |
|--------------|-----------------------------------|
| Presenting one design as inevitable | No judgement is visible; you may have memorised it |
| Listing trade-offs without choosing | Judgement is choosing, not enumerating |
| "It depends" with no decision rule | State the rule: "under 10k QPS, Postgres; above, shard" |
| Only upside for your choice | Every choice has a cost. Naming yours is the credibility move |
| Defending under pushback | Update or hold, but say which and why. "Good point, that changes X" is strong |
| Adding components to look thorough | Kafka on a 0.1 QPS system is a negative signal |

---

## 9 · When the interviewer drills into implementation detail

This will happen — it is the defining feature of this round. Treat it as an invitation, not an
interruption. The failure mode is losing the thread of the design while you code.

**The protocol:**

1. **Acknowledge the level change.** "Let me drop into code for that — I will come back to the fan-out
   after."
2. **State the signature and the invariant first.** "`offer(seq, payload) -> list of deliverable
   messages`. Invariant: never emit a gap, never emit a duplicate."
3. **Write the smallest correct thing.** Readable beats clever; readability is 35% of the laptop
   round's grade and the same taste is being judged here.
4. **Say the complexity and the failure case.** "O(1) amortised per message; the unbounded case is a
   permanent gap, so the buffer is capped and overflow triggers a resync from storage."
5. **Say how you would test it.** Two or three named cases: happy path, duplicate, gap that never fills.
6. **Return to the diagram explicitly.** "Back up a level — that component sits here."

**Micro-implementations worth having in your pocket** (each is 15–25 lines and each appears in this
section's files):

| Snippet | File |
|---------|------|
| Ordered delivery buffer with gap detection | [realtime-chat-delivery-guarantees.md](realtime-chat-delivery-guarantees.md) |
| Connection registry with TTL heartbeats | [realtime-chat-delivery-guarantees.md](realtime-chat-delivery-guarantees.md) |
| Idempotency-key store with request fingerprint | [idempotency-and-deduplication.md](idempotency-and-deduplication.md) |
| Per-host politeness scheduler on a heap | [distributed-web-crawler.md](distributed-web-crawler.md) |
| URL canonicalisation | [distributed-web-crawler.md](distributed-web-crawler.md) |
| Base62 + Snowflake ID generation | [url-shortener.md](url-shortener.md) |
| Minimum-workers interval partitioning | [support-case-routing.md](support-case-routing.md) |
| Token-bucket / retry budget | [third-party-failure-modes.md](third-party-failure-modes.md) |

**Language note.** Lyft's backend is Python and Go. Write Python by default in this round, standard
library only, and keep it 3.10-compatible. Do not propose Akka or a JVM stack — there is no JVM in
Lyft product engineering.

---

## 10 · The other two sub-rounds: code review and testing strategy

### 10.1 If handed code to review

Review in this order, and say the order:

1. **Correctness** — race conditions, error paths not handled, off-by-one, unbounded growth.
2. **Failure behaviour** — what happens on retry, on partial failure, on a slow dependency.
3. **Contracts** — is the function's invariant stated and upheld? Are errors typed?
4. **Readability** — naming, function length, hidden control flow.
5. **Tests** — what is untested, and what test would have caught this bug.

Lead with the highest-severity issue, be specific about the failing input, and separate "must fix" from
"I would prefer". That separation is itself a Staff signal.

### 10.2 If asked for a testing strategy

Do not list test types. Map tests to the risks you already named in the failure-mode table:

| Risk you named | Test that covers it |
|----------------|---------------------|
| Duplicate delivery on retry | Property test: apply the same request twice, assert identical state |
| Out-of-order messages | Deterministic simulation with shuffled seq numbers |
| Slow third party | Fault injection at the mesh (delay/abort percentage), not a mock |
| Hot partition | Load test with a skewed key distribution, not uniform |
| Failover correctness | Kill the primary during a load test; assert zero acked-then-lost writes |

Repo material: [Property-Based Testing](../12-testing/Testing-property_based.md) ·
[Load Testing](../12-testing/Testing-load_testing.md) ·
[Test Types & Levels](../12-testing/Testing-types_levels.md).

---

## 11 · The Google Draw constraint

Lyft design rounds are drawn in a shared Google Drawing. It is slow, it has no snapping worth using,
and fighting it wastes minutes you cannot afford.

**Prepare, do not improvise.**

- **Build a stencil file before the loop.** One Google Drawing containing: 12 pre-made labelled
  rectangles, 4 cylinders (datastore), 3 queue shapes, a cloud, a stack of 3 boxes (service replicas),
  20 arrows, and 6 text boxes. In the round, copy-paste from a second tab. This is legitimate
  preparation and it saves 5–8 minutes.
- **Rehearse three canonical diagrams cold** until each takes under 3 minutes: client → gateway →
  service → store → queue → worker; a sharded store with a router; a stream pipeline with a read model.
- **Layout convention:** clients on the left, edge/gateway next, services in the middle, storage on the
  right, async/queues along the bottom. Keep it consistent so you can point instead of explain.
- **Label every arrow** with protocol and direction (`WSS`, `gRPC`, `Kafka: msg.created`). Unlabelled
  arrows invite exactly the questions you do not want.
- **Do not beautify.** No colours, no alignment passes, no shadows. Nobody scores the drawing.
- **Write the numbers on the canvas.** Assumptions, QPS, and the alternatives ledger live in a text box
  on the right. They are your notes and the interviewer's evidence that you did the math.
- **Zoom out before you talk.** Interviewers frequently see a corner of your canvas. Say "I am zooming
  out so you can see the whole thing."
- **Have a fallback.** If Drawing is broken, say "I will describe it and type the boxes as an indented
  list" and keep moving. Losing 4 minutes to a tool is worse than an ugly diagram.

---

## 12 · "Full working design" vs "good design"

| Working design | Good design |
|----------------|-------------|
| Every box is drawn | Every box has a reason, and one box was deliberately *not* drawn |
| Answers each question asked | Anticipates the next question and pre-empts it |
| Scales in principle | Names the number at which it breaks, and the next thing to break |
| Uses a database | Names the key, the item size, and the hot-partition mitigation |
| "We'd add caching" | "70% hit rate on a 5M-entry cache is 2.5 GB; here is the invalidation path" |
| Handles the happy path | Has a degraded mode, and says what the user sees in it |
| One architecture | Two, priced, with a decision rule between them |
| Complete | Simple where it can be, complex only where the requirement forces it |
| Silent about risk | "The riskiest part is X, here is how I would de-risk it in week one" |
| Ends at the diagram | Ends with rollout, migration, and how you would measure success |

Two closing moves that cost 60 seconds and land hard:

- **Rollout/migration.** "If this replaces an existing system: dual-write, shadow-read with diffing,
  then cut over per-tenant behind a flag, with a documented rollback."
- **Measurement.** "Success is p99 delivery under 500 ms and zero acked-then-lost messages; I would
  instrument the ack path end to end and alarm on the gap between messages accepted and messages
  persisted." The behavioural round asks **"how did you measure?"** verbatim — the same instinct is
  being scored here.

---

## 13 · Staff vs Senior signals

Downlevelling to Senior is the primary risk in this loop. The difference is rarely technical depth;
it is scope, priced judgement, and organisational awareness.

| Signal | Senior version | Staff version |
|--------|----------------|---------------|
| Scope | Designs the service asked for | Asks what else consumes this, and designs the contract for them |
| Trade-offs | Mentions them | Prices them and decides, with a stated decision rule |
| Simplicity | Builds the complete system | Ships the smallest thing that meets N1–N3, with a named upgrade trigger |
| Risk | Handles failures | Ranks failures by blast radius and picks where to spend |
| Cost | Ignores it | "That GSI doubles write cost; here is the cheaper access pattern" |
| Operations | Mentions monitoring | Names the SLI, the alarm threshold, and the runbook action |
| People | Answers alone | "I would write this as an ADR and get the storage team to review the key choice" |
| Disagreement | Defends | Updates on evidence, or holds and says exactly what would change their mind |

---

## 14 · Pre-round checklist

- [ ] Stencil Google Drawing open in a second tab.
- [ ] [napkin-math.md](napkin-math.md) numbers table memorised, not open — you will be watched.
- [ ] One sentence ready on: partition key choice, hot partitions, idempotency, backpressure.
- [ ] Two Lyft-specific opinions ready from [lyft-architecture.md](lyft-architecture.md)
      (Envoy sidecar, S2 cell granularity, Redis sorted sets with TTL, the 30s batching window).
- [ ] The alternatives-ledger table drawn empty in the corner of the canvas.
- [ ] A question for them: "How do you handle X in the support platform today?"

---

## Interview questions

**1. Walk me through how you approach a system design problem.**
Requirements and explicit out-of-scope first, then the API contract, then the data model driven by an
access-pattern table, then scale, then failure modes, then a trade-off summary. I keep a running list
of alternatives I rejected and read it back at the end, because the decision record is the part that
actually shows judgement.

**2. You have 60 minutes and the problem is big. What do you cut?**
I cut breadth, never depth. I pick the two or three components where the interesting decisions live —
usually the write path, the partition key, and the failure behaviour — and I say explicitly which
parts I am treating as solved. A design that goes deep on three things beats one that touches twelve.

**3. Your interviewer says "having a full working design is not the same as having a good design."
What do you think they mean?** **[Reported at Lyft]**
That completeness is table stakes. A good design shows the alternatives that were considered and
priced, names the constraint that drove each decision, is deliberately simpler than it could be, and
states where it breaks. If I can only describe one architecture and only its upside, I have not
demonstrated judgement — I have demonstrated recall.

**4. How do you present trade-offs without sounding indecisive?** **[Reported at Lyft]**
I always name at least two options, state the cost of the one I pick, and give a concrete decision
rule for flipping: "Postgres until 10k writes/s or 2 TB, then shard by tenant." Naming the switching
condition is what turns "it depends" into a decision.

**5. The interviewer stops the design and asks you to implement one piece. How do you handle it?**
I state the signature and the invariant, write the smallest readable correct version, then give the
complexity, the failure case, and two or three test cases. Then I explicitly zoom back out and point
at where that component sits in the diagram, so we do not lose the thread.

**6. How do you decide between SQL and NoSQL in a design round?**
From the access-pattern table, not from scale folklore. If the queries are known, keyed, and
high-volume, a partitioned KV wins and I state the partition key and the hot-partition mitigation. If
queries are ad hoc, relational or transactional across entities, Postgres wins and I state the point at
which it stops working. The wrong answer is picking NoSQL to sound scalable.

**7. How do you size a cache in the middle of a design discussion?**
Working set times entry size plus per-entry overhead, then check it against a machine. Five million
entries at 400 bytes of payload and 100 bytes of overhead is 2.5 GB, which fits on one node with
headroom, so the interesting question is not capacity but invalidation and stampede protection.

**8. What do you do when you disagree with the interviewer's suggestion?**
Restate their point so they know I heard it, then say what it costs and what evidence would change my
mind. If they are right, I say so and update the design on the canvas. If it is a genuine trade-off, I
add it to the alternatives ledger as a row rather than arguing it to a conclusion.

**9. How would you test the system you just designed?**
I map tests to the risks I named: property tests for idempotency, deterministic simulation for
ordering, fault injection at the service mesh for slow dependencies, skewed-key load tests for hot
partitions, and a kill-the-primary test that asserts no acked write was lost. Test types listed
without a risk attached are not a strategy.

**10. What questions do you ask the interviewer at the end?**
Something specific about their system that only they can answer: how conversation state is checkpointed
today, how they bound the blast radius of a slow third-party dependency, or what the hardest ordering
problem in their messaging path has been. It shows I was designing for their context, not from a
template.
