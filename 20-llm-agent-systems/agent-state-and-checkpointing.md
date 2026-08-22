# Agent State and Checkpointing

> **Priority:** Required
> **Est. time:** 60 min
> **Track:** Server
> **HelloInterview:** System Design in a Hurry → Key Technologies → DynamoDB; Common Patterns → Dealing with Contention

The model is stateless. Every turn re-sends whatever the model is supposed to know. That single fact
turns "conversation memory" from an AI problem into a **durability, concurrency and serialisation
problem** — which is home ground. Lyft implemented a custom **`DynamoDBSaver` against LangGraph's
`BaseCheckpointSaver` interface**, and reasoning through what that implementation has to get right is
one of the highest-value hours of preparation for this loop: it is simultaneously the target team's
real code, a NoSQL data-modelling exercise, and the "NoSQL depth" probe the design rounds are known
to run.

Prerequisites: [DynamoDB refresher](../06-databases-and-distributed-data/dynamodb_refresher.md),
[Event Sourcing Guide](../06-databases-and-distributed-data/Event-Sourcing-Guide.md).

---

## 1 · What actually has to persist

| Content | Grows with | Must survive a crash? | Notes |
|---|---|---|---|
| Message history (user, assistant, tool results) | Turns | Yes | The dominant size term. Tool results are usually larger than the human text. |
| Current node / next frontier | Fixed | Yes | Without it you cannot resume; you can only restart. |
| Routing decision (`intent`, chosen specialist) | Fixed | Yes | Persist the *decision*, not just its inputs — re-deriving from a stochastic classifier can land elsewhere. |
| Scratchpad / intermediate reasoning | Steps | Usually | Needed for resume mid-trajectory; often prunable at turn boundaries. |
| Pending writes from a partially-completed superstep | Fan-out width | Yes | Otherwise resume re-runs work that already had side effects. |
| Pending interrupt payload | Fixed | Yes | The thing the human is being asked to approve. |
| Idempotency keys for external side effects | Side effects | Yes | The difference between one refund and three. |
| Cost and token accounting | Steps | Preferably | Enforcing a per-conversation budget requires it to be durable, or a retry loop resets the counter. |
| Retrieved documents | Retrievals | No | Re-retrievable. Store the *query and doc ids*, not the text. Biggest single size win available. |

The last row is the general principle: **persist what you cannot recompute, reference what you can.**
Same call as choosing what goes in an event versus what a projection derives.

---

## 2 · The interface: `BaseCheckpointSaver`

LangGraph's checkpointer contract is small. Roughly four operations (plus async twins):

| Operation | Semantics |
|---|---|
| `put(config, checkpoint, metadata, new_versions)` | Persist one checkpoint for a thread. Returns an updated config carrying the new `checkpoint_id`. |
| `put_writes(config, writes, task_id)` | Persist the pending writes produced by an individual task within a superstep, before the superstep completes. |
| `get_tuple(config)` | Fetch a specific checkpoint by id, or the latest for the thread if none given, together with its pending writes and parent pointer. |
| `list(config, filter, before, limit)` | Enumerate checkpoints for a thread, newest first. Backs time travel, forking and debugging. |

Three identifiers appear in the config and all three matter:

* **`thread_id`** — the conversation. The unit of recovery and of single-writer discipline. Direct
  analogue of `persistenceId` in Akka Persistence, or a cluster-sharded entity id.
* **`checkpoint_ns`** — the namespace, non-empty inside subgraphs. A rider-router subgraph gets its own
  namespace so its checkpoints do not collide with the parent's.
* **`checkpoint_id`** — one point in the thread's history. Checkpoints form a linked list via a parent
  pointer, which is what makes time travel and forking possible.

`put_writes` is the operation people skip when they first read the interface, and it is the one that
makes crash recovery correct. Without it, a crash halfway through a fanned-out superstep loses the
results of the tasks that had finished, and resume re-runs them — at-least-once execution with side
effects. With it, completed task writes are durable and replay skips them.

---

## 3 · Designing the DynamoDB table

The exercise: implement that interface on DynamoDB, for a support platform where a conversation is
long-lived, resumable, occasionally interrupted for a human, and subject to retention rules.

### 3.1 Keys

```
PK  =  "THREAD#<thread_id>#NS#<checkpoint_ns>"
SK  =  "CKPT#<checkpoint_id>"                       -- checkpoint items
SK  =  "WRITE#<checkpoint_id>#<task_id>#<idx>"      -- pending-write items
```

Reasoning, which is the part interviewers actually grade:

* **Partition key is the thread.** Every access pattern — get latest, get by id, list history, fetch
  pending writes, delete the conversation — is scoped to one conversation. One partition, one query,
  no scatter. The same instinct as keeping an aggregate's events under one `persistenceId`.
* **Namespace in the PK, not the SK.** A subgraph's checkpoints are a logically separate stream with its
  own lifecycle; keeping them in a separate partition means a subgraph's history cannot be dragged into
  a parent query, and it distributes rather than concentrates load.
* **Sort key must sort chronologically.** LangGraph checkpoint ids are UUIDv6-style, which are
  lexicographically ordered by time. Preserve that and "get the latest checkpoint" is
  `Query(PK, ScanIndexForward=False, Limit=1, ConsistentRead=True)` — one read, no GSI, no scan.
  If you ever generate ids yourself, use ULID or a zero-padded monotonic counter. A random UUIDv4 here
  would be a design error: you would have to maintain a separate "latest" pointer item and keep it
  consistent, which is a whole class of bugs bought for nothing.
* **Pending writes share the partition and sort adjacent to their checkpoint.** `get_tuple` needs the
  checkpoint *and* its writes; a single `Query` with a `begins_with` on the prefix returns both.
  Putting writes in a separate table would make the commonest read a cross-table fan-out.
* **Prefixed sort keys** are the standard single-table technique — see
  [DynamoDB refresher](../06-databases-and-distributed-data/dynamodb_refresher.md) and
  [partition strategies](../06-databases-and-distributed-data/partition_strategies.md).

### 3.2 Access patterns, and how each is served

| Pattern | Operation |
|---|---|
| Resume a conversation | `Query(PK=thread, SK begins_with "CKPT#", ScanIndexForward=False, Limit=1, ConsistentRead=True)` |
| Get a specific checkpoint plus its writes | `Query(PK=thread, SK between "CKPT#id" and "WRITE#id~")` — one round trip |
| Write a checkpoint | `PutItem` with `ConditionExpression="attribute_not_exists(SK)"` |
| Record a task's pending writes | `PutItem` per task, same condition |
| List history / time travel | `Query(PK=thread, SK begins_with "CKPT#", ScanIndexForward=False, Limit=n)` |
| Delete a conversation (right to erasure) | `Query` keys, then `BatchWriteItem` deletes. Not TTL — see §7. |
| "All threads for user X" | Needs a **GSI** on `user_id` with the thread as sort key. Note the checkpoint items themselves should not be the GSI target; project a single thread-metadata item instead, or the index duplicates the whole history. |

That last row is the trap. A naive GSI on `user_id` over a table whose items are full conversation
snapshots replicates every snapshot into the index: storage and write cost multiply, for a query you
could serve from a one-item-per-thread metadata record. **Sparse index**: only the metadata item
carries the `user_id` attribute, so only it lands in the GSI.

### 3.3 Item size: the constraint that shapes everything

DynamoDB's hard limit is **400 KB per item**. A checkpoint is a snapshot of full graph state, and
message history grows monotonically. This is not a theoretical concern — a support conversation with
a dozen tool results carrying ride histories and receipts reaches hundreds of kilobytes without
anybody doing anything unusual.

Options, roughly in order of how much I would reach for them:

| Strategy | Mechanism | Cost |
|---|---|---|
| **Do not store what you can recompute** | Persist retrieval *queries and doc ids*, rehydrate on resume | Slower resume; usually the best first move |
| **Compress the serialised blob** | msgpack + a compressor before writing | CPU; opaque items you cannot query into |
| **Externalise to S3 above a threshold** | Store a pointer; keep small checkpoints inline | Second round trip, second failure mode, lifecycle to manage. Classic large-blob pattern |
| **Summarise history** | Replace the first N turns with a model-generated summary at a size threshold | Lossy — and the loss is invisible until a specific question needs the dropped turn |
| **Chunk across items** | `SK = "CKPT#<id>#PART#0007"`, reassemble on read | Multi-item writes are not atomic without `TransactWriteItems`, which caps at 100 items and 4 MB |
| **Store deltas, snapshot periodically** | Journal + snapshot, exactly Akka Persistence | Replay cost on read; a real redesign, not a tweak |

The last row is worth arguing explicitly in an interview because it is the honest architectural
observation: **LangGraph's checkpointer is a snapshot store, not a journal.** Akka Persistence writes
events and snapshots occasionally; LangGraph writes a full snapshot every superstep. That trades write
volume for read simplicity — recovery is one read, not a fold over a stream. For conversations of a few
dozen turns, the snapshot model is the right call. For unbounded histories, it is the wrong one, and
the fix is to make the state bounded (summarise, externalise) rather than to invent a journal on top.

---

## 4 · Concurrency: the read-modify-write hazards

Anywhere a checkpoint is read, mutated and written back, two writers can interleave. The realistic
sources of a second writer, in a support platform, are all mundane:

1. **The user double-sends.** Two taps, or a client retry after a timeout the server actually served.
2. **The client retries a request the server is still processing.** Now two graph invocations are live
   on one `thread_id`.
3. **A human support agent takes over** while the bot is mid-turn. Two writers by design.
4. **A resume races the original invocation** — the original was slow, not dead.
5. **An async callback lands** (a payment webhook, a background job finishing) and writes to the thread.

Mitigations, strongest first:

| Mitigation | How | Trade-off |
|---|---|---|
| **Single writer per thread** | Route all invocations for a `thread_id` to one owner: consistent hashing at the ingress, or an actual lock | Strongest, and the direct analogue of Akka cluster sharding guaranteeing one entity instance per id. Needs a routing tier and a story for owner failure |
| **Conditional writes** | `PutItem` with `attribute_not_exists(SK)`; a checkpoint id is written once or the write fails | Free, and gives idempotent replay. Does not by itself stop two *divergent* branches |
| **Optimistic concurrency on a thread-metadata item** | Version attribute, `ConditionExpression="version = :expected"`, retry on failure | Serialises the two writers; cost is a second item and a retry loop |
| **Distributed lease** | Lock item with owner and expiry, conditional acquire | Standard, and standard problems: expiry tuning, fencing tokens, the lease that outlives its holder |
| **Idempotency key on the request** | Client-supplied key stored with the checkpoint; duplicate keys return the stored result | Solves cause 1 and 2 outright — the same idempotency-key design as a payments endpoint |

The right answer for a support agent is usually **the first plus the last**: a routing tier that pins
a conversation to one worker, and idempotency keys so the client's retries are free. Then conditional
writes as the belt-and-braces that make a checkpoint write itself idempotent.

Note what the checkpoint's parent pointer gives you for free: two concurrent writers do not corrupt
state, they **fork** it — two checkpoints with the same parent. That is a branch, not a lost update,
which is strictly better than clobbering. But you still have to decide which branch is canonical, and
"whichever `Limit=1` happened to return" is not a decision. Detect the fork (two children of one
parent) and resolve it explicitly. Compare with
[linearizability vs serializability](../06-databases-and-distributed-data/linearizability_vs_serializability.md);
this is the same conversation as sibling versions in a Dynamo-style store, and the same conclusion —
the store can preserve concurrency for you, but it cannot decide semantics.

**Read consistency**: always `ConsistentRead=True` when fetching the checkpoint you are about to
resume from. An eventually-consistent read that misses the last checkpoint replays a superstep, which
means re-running tool calls. And never resume off a GSI: global secondary indexes are eventually
consistent, full stop.

---

## 5 · Checkpoint granularity and write amplification

| Granularity | Recovery | Write volume |
|---|---|---|
| Per superstep (default) | Resume mid-trajectory, lose at most one step | Highest |
| Per turn | Resume at the last user message; a whole trajectory re-runs | ~1/N |
| At exit only | No mid-conversation recovery at all | Lowest |
| Per token | Not a thing anyone should do | Absurd |

**Napkin math, using the published 270k interactions/month.**

* Average rate: 270,000 / (30 x 86,400) ≈ **0.1 conversations/s**. At 20x peak, ~2/s.
* Say 10 supersteps per conversation and a checkpoint averaging 50 KB. WCUs are billed per 1 KB, so
  each write is ~50 WCU: **500 WCU-seconds per conversation**.
* Sustained: 0.1 x 500 = **~50 WCU average**, ~1,000 WCU at 20x peak. Trivial for DynamoDB.
* Reads are smaller still: one consistent read of ~50 KB is ~13 RCU (4 KB per strongly-consistent RCU).

**The conclusion is the interesting part**: aggregate throughput is a non-issue at this scale. The
binding constraints are (a) the 400 KB item limit as histories grow, and (b) per-partition throughput,
because one conversation is one partition key and a DynamoDB partition tops out around 1,000 WCU and
3,000 RCU. Fifty-KB checkpoints mean roughly 20 checkpoint writes per second for a *single*
conversation before that one thread throttles — plenty for a human conversation, and not plenty for a
fan-out of 50 parallel tool calls each writing pending writes into the same partition. Saying that out
loud, unprompted, is what a "NoSQL depth" probe is looking for.

Cost is the other axis. Halving checkpoint size halves the write bill and the restore latency; that is
usually a bigger lever than tuning capacity mode.

---

## 6 · Resumption, replay and time travel

* **Resume after crash**: read the latest checkpoint plus its pending writes, re-enter the graph at the
  recorded frontier, skip tasks whose writes are already durable.
* **Replay for debugging**: fetch checkpoint *k* and run forward. Because the model is non-deterministic,
  this reproduces the *state*, not the trajectory. Do not promise a bug reproduction; promise a state
  reproduction. This surprises people who expect event-sourcing-style determinism.
* **Fork**: resume from an old checkpoint with modified state to try an alternative — "what if the
  router had classified this as billing?" This is the single most useful debugging affordance the
  design buys you, and it is worth being able to name.
* **Time travel** in general is the same capability event sourcing gives you (see
  [Event Sourcing Guide](../06-databases-and-distributed-data/Event-Sourcing-Guide.md)), with the
  caveat that you are travelling over snapshots rather than over decisions, so you can see *what the
  state was* but not *why the model chose it*. That "why" lives in traces, which is why tracing is not
  optional — [production-llmops.md](production-llmops.md).

---

## 7 · TTL, retention and deletion

* **TTL is a cost and hygiene mechanism, not a compliance mechanism.** DynamoDB deletes expired items
  on a best-effort basis, typically within 48 hours. A "delete my data" request needs an explicit
  delete path: query the thread's keys, `BatchWriteItem` the deletes, and prove it.
* **Set the TTL attribute on every item at write time.** Retrofitting it means a full-table backfill.
* **TTL deletes appear in DynamoDB Streams**, so downstream projections and analytics stores can be
  kept in step — [reactive read-side](../03-akka-ecosystem/reactive_readside.md) is the same pattern.
* **Different classes of data want different retention.** A conversation for an open incident, a
  conversation used as an eval fixture, and a routine resolved chat are three different lifecycles.
  Encode the class in the item, drive TTL from it.
* **Interrupted threads need a sweeper.** A thread waiting on a human who never answered will sit there
  until TTL. That is a leaked workflow, not just leaked storage: the user is waiting too. Sweep,
  escalate, and alert on the age distribution of pending interrupts.
* **PII**: a checkpoint contains raw user messages. Redaction, encryption with a customer-managed key,
  and access control belong here, not only at the model boundary —
  [production-llmops.md](production-llmops.md#9--pii-in-a-support-context) and
  [Security threats](../11-security/Security-threats.md).

---

## 8 · The Akka Persistence parallel

| Akka Persistence | LangGraph checkpointing | Comment |
|---|---|---|
| `persistenceId` | `thread_id` | Unit of recovery and single-writer scope. |
| Journal (append-only events) | — | No direct equivalent. Snapshots only. |
| Snapshot store | Checkpointer | LangGraph snapshots *every* superstep, not periodically. |
| `eventHandler` / `evolve` | Channel reducers | Fold new information into state deterministically. |
| Recovery = replay events, then snapshot | Recovery = read latest snapshot | One read instead of a fold. Simpler, but bounded by item size. |
| Cluster sharding = one entity instance per id | Your routing tier | LangGraph does not provide this. If you need single-writer, you build it. |
| `at-least-once` delivery, `deliver`/`confirmDelivery` | Pending writes + idempotency keys | Same problem, same solution shape. |
| Event adapters for schema evolution | Serialiser versioning on the checkpoint blob | Same trap: old checkpoints must stay readable after a state-schema change. |

That last row deserves a paragraph of its own, because it is the operational issue nobody anticipates.
State schema changes ship with every other feature — a new channel, a renamed field, a changed message
format. Live conversations hold checkpoints written by the *previous* version of the code. So either
the deserialiser tolerates unknown and missing fields (additive-only changes, defaults for everything
new), or you drain and expire in-flight threads before deploying a breaking change. Additive-only with
a version tag on the item is the sane default, and it is the same discipline as
[Protobuf schema evolution](../15-system-design/grpc_protobuf_schema_design.md) — never reuse a field,
never change a meaning, always default the new thing.

---

## 9 · Failure-mode checklist

Run through this against any agent-state design:

- [ ] Two concurrent invocations on one `thread_id` — what happens?
- [ ] Client retry after a server-side timeout — is the side effect duplicated?
- [ ] Crash mid-superstep with three parallel tool calls, one of which issued a refund.
- [ ] Checkpoint exceeds 400 KB on turn 40 of a long conversation.
- [ ] Deploy changes the state schema while conversations are in flight.
- [ ] Interrupted thread whose human never responds.
- [ ] A single conversation gets hot enough to throttle its partition.
- [ ] Right-to-erasure request against a thread that also seeds an eval set.
- [ ] Eventually-consistent read on resume, causing a superstep to re-run.
- [ ] Restore from PITR — do you get a coherent set of threads, or torn conversations?

---

## Interview questions

**1. Design the DynamoDB table behind an agent checkpointer.** **[Reported at Lyft]** *(NoSQL depth is a named probe in the design rounds)*
Partition key `THREAD#<thread_id>#NS#<checkpoint_ns>`, sort key `CKPT#<checkpoint_id>` for checkpoints
and `WRITE#<checkpoint_id>#<task_id>#<idx>` for pending writes, so one query returns a checkpoint and
its writes. Checkpoint ids are time-ordered UUIDv6/ULID, so "latest" is a query with
`ScanIndexForward=False, Limit=1, ConsistentRead=True` — no GSI and no maintained pointer item.
Conditional `attribute_not_exists(SK)` on write makes checkpoint writes idempotent. TTL attribute on
every item at write time.

**2. What is the hardest constraint in that design?**
The 400 KB item limit, because a checkpoint is a full snapshot and message history grows monotonically.
First move is to stop persisting recomputable things — store retrieval queries and document ids, not
the retrieved text. Then compression, then externalising the blob to S3 above a threshold with a
pointer in the item, then summarising old turns. Chunking across items is last, because multi-item
writes are not atomic without `TransactWriteItems`.

**3. Two writers on the same conversation. What breaks and how do you fix it?**
A read-modify-write race — a double-tap, a client retry, or a human agent taking over mid-turn.
Because checkpoints carry a parent pointer, concurrent writes fork rather than clobber, which is
better than a lost update but still needs a decision about which branch is canonical. The fix I would
ship is a routing tier pinning a `thread_id` to one worker — the same guarantee Akka cluster sharding
gives an entity — plus client idempotency keys so retries are free, with conditional writes underneath.

**4. Why not just use eventual consistency on reads?**
Because an eventually-consistent read on resume can miss the last checkpoint, which means re-running a
superstep, which means re-issuing tool calls that may have already had side effects. Strongly
consistent reads cost twice the RCU on a read path that is tiny compared with the writes. And a GSI is
eventually consistent by construction, so you never resume off an index.

**5. How does this compare to Akka Persistence?**
`thread_id` is `persistenceId`; reducers are the event handler; the checkpointer is a snapshot store.
The gap is that there is no journal — LangGraph snapshots full state every superstep instead of
appending events and snapshotting occasionally. That makes recovery a single read rather than a fold,
which is simpler, but it puts the whole burden on item size and gives you replay of state without
replay of decisions. And cluster sharding's single-writer guarantee is not provided; you build it.

**6. Estimate the DynamoDB capacity for 270k conversations a month.**
About 0.1 conversations/s average, 2/s at 20x peak. Ten supersteps at ~50 KB is ~500 WCU-seconds per
conversation, so ~50 WCU sustained and ~1,000 WCU at peak — nothing. The real limits are per-partition:
one conversation is one partition key, and a partition caps near 1,000 WCU, so a single thread throttles
at roughly 20 fifty-KB writes per second. That is fine for a human conversation and not fine for a wide
parallel fan-out writing pending writes into the same partition.

**7. You deploy a change to the state schema. What happens to in-flight conversations?**
They hold checkpoints serialised by the old code. Either the deserialiser tolerates missing and unknown
fields — additive-only changes with defaults, and a version tag on the item — or you drain and expire
in-flight threads before deploying. Same discipline as Protobuf evolution: never reuse a field number,
never change a field's meaning, always default the new thing. This is the operational issue teams hit
in month three and it is worth designing for on day one.

**8. How do you handle a "delete my data" request?**
Not with TTL. TTL is best-effort and can take up to 48 hours, so it is a cost and hygiene mechanism.
Erasure needs an explicit path: query the thread's key range, `BatchWriteItem` the deletes, propagate to
anything downstream that consumed the DynamoDB stream — traces, analytics, eval fixtures. The awkward
case is a conversation that seeded an eval set; the honest answer is that eval fixtures must be
de-identified at capture time so they are not personal data by the time you depend on them.

**9. What is `put_writes` for, and what goes wrong without it?**
It persists the writes produced by individual tasks inside a superstep before the superstep as a whole
completes. Without it, a crash mid-superstep loses the results of the tasks that had already finished,
so resume re-runs them — at-least-once execution, and if one of them issued a refund you have issued it
twice. With it, completed task writes are durable and replay skips them. It is the checkpointer's
equivalent of confirming delivery in an at-least-once protocol.

**10. Can you replay a conversation to reproduce a bug?**
You can reproduce the *state*, not the trajectory. Resuming from checkpoint k restores exactly what the
graph knew, but the model call from that state is non-deterministic, so the path forward may differ.
Temperature 0 narrows it and does not close it, and a provider-side model update changes it again. So
state replay is for forking and experimenting — "what if the router had said billing" — while the
question of why the model chose something is answered from traces, not from checkpoints.
