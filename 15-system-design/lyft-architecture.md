# Lyft's Real Architecture — free Staff-instinct points

> **Priority:** Required
> **Est. time:** 45 min
> **Track:** Both
> **HelloInterview:** System Design in a Hurry → Key Technologies → Redis, DynamoDB, API Gateway; Advanced → Proximity Search

Every fact in this file is sourced from Lyft's public engineering output. Knowing them is cheap; the
value is not the trivia but the ability to invoke each one as an **informed opinion with a stated
cost**. "Lyft uses Envoy" is a fact. "I would put retries and circuit breaking in the sidecar rather
than in each service's client library, which is exactly why Lyft built Envoy — and the cost is an extra
hop and a control plane to operate" is a Staff answer.

---

## 1 · How to use this file

**Do not recite.** Nothing reads worse than a candidate listing a company's stack back at it. The
pattern that works:

> *Constraint appears in the design* → *name the technique* → *state what it buys* → *state what it
> costs* → *optionally note that this is the shape Lyft already runs.*

Roughly one such reference every fifteen minutes. Three is confident preparation; ten is a recital.

And be ready to be wrong in the room: their current architecture may have moved on. Frame with
"as I understand it" and treat any correction as free information about their real system.

---

## 2 · The stack at a glance

| Layer | Technology | Note |
|-------|-----------|------|
| Backend languages | **Python (primary) and Go** | A "Backend Language Tooling" team owns both. **No JVM in product engineering** |
| Data platform | Flink, Spark, Scala | The only place JVM languages live |
| HTTP framework | Flask | Python APIs |
| Service-to-service | **Protocol Buffers**, gRPC | Schema-first |
| Service mesh | **Envoy**, sidecar per app server | Lyft built it and donated it to the CNCF |
| Orchestration | Kubernetes, Docker | |
| Workflow | Flyte | Lyft-built, also donated |
| Cloud | AWS | |
| Hot geospatial state | **Redis Cluster, sorted sets keyed by timestamp, ~30 s expiry** | Active driver discovery |
| Geospatial indexing | **Google S2, level 5** | Chosen deliberately to avoid hot shards |
| Managed KV | **DynamoDB** | Serialised map data; agent conversation state |
| Rate limiting | Redis-backed config at **both edge and service-mesh** layers | |
| Matching | **~30-second batching window** before re-matching riders | |
| Support agents | **LangGraph + LangSmith** multi-agent platform, Claude via Amazon Bedrock | The target team |

---

## 3 · Envoy and the sidecar model

**What it is.** An L7 proxy deployed as a sidecar container next to every application process. All
inbound and outbound traffic passes through it. A control plane (xDS) pushes configuration
dynamically — no restarts to change a route, a timeout, or a retry policy.

**What it buys:**

| Benefit | Why it matters |
|---------|----------------|
| Uniform L7 behaviour across languages | Retries, timeouts, circuit breaking, outlier detection, and load balancing behave identically in Python and Go. **This is the reason it exists**: Lyft had two backend languages and did not want two divergent client libraries |
| Observability for free | Consistent per-dependency RED metrics, tracing headers, and access logs without touching application code |
| mTLS and identity at the edge of every process | Security policy without per-service crypto code |
| Traffic shifting | Canary, blue/green, and fault injection as configuration rather than deploys |
| Failure policy out of the app | Retry budgets, outlier ejection, and concurrency limits configured centrally — see [third-party-failure-modes.md](third-party-failure-modes.md) |

**What it costs — say these, they are what make it an opinion rather than a fact:**

| Cost | Detail |
|------|--------|
| Latency | ~0.5–1 ms per hop, and there are **two hops per call** (caller's sidecar out, callee's sidecar in) |
| Memory and CPU per pod | Tens to low hundreds of MB per sidecar; at thousands of pods this is real money |
| Operational complexity | The control plane becomes a critical dependency; a bad config push is a fleet-wide incident |
| Debugging | Two layers to inspect. "Is this the app or the sidecar?" is a daily question, and 503s can come from either |
| Lifecycle races | In Kubernetes, the app can start before the sidecar is ready or outlive it during shutdown, producing confusing connection failures |

**When not to reach for it:** a single-language shop where one good client library covers everything;
an extremely latency-sensitive path where 1 ms matters; a fleet small enough that the control plane
costs more than it saves. The 2024-onward alternative worth naming is **sidecar-less / ambient mesh**,
which moves L4 into a per-node proxy and makes L7 opt-in — lower overhead, less isolation.

**How to invoke it in a round:** when you reach retries, timeouts, or circuit breaking, say *"I would
put this in the mesh rather than in each service, so the policy is uniform and configurable without a
deploy — that is the Envoy model. The costs are an extra hop and a control plane that is now on the
critical path."*

---

## 4 · Protocol Buffers and gRPC

**What it buys:** the schema is the contract, code generation keeps Python and Go in sync, the wire
format is compact and fast to parse, gRPC gives streaming and first-class **deadlines** (which
propagate — see [third-party-failure-modes.md](third-party-failure-modes.md)), and field-number-based
evolution makes backward-compatible change the default path.

**What it costs:**

- Binary payloads are not human-readable; you need tooling to debug what `curl` would have shown you.
- Breaking changes are easy to make by accident (renumbering, changing a field's type, reusing a
  removed number). Discipline required: **never reuse a field number, always `reserved`**.
- Browsers need grpc-web or a JSON transcoding gateway.
- Build tooling and a schema registry become infrastructure you must own.
- Optionality is subtle: proto3 scalar defaults are indistinguishable from unset unless you use
  `optional` or wrappers, which is a real source of bugs when "0" and "not provided" differ.

**Evolution rules to state:** additive only; new fields optional with sane defaults; `reserved` for
removed numbers and names; never change a field's meaning; version the *service* when the semantics
change, not the message.

Repo: [gRPC & Protobuf Schema Design](grpc_protobuf_schema_design.md).

---

## 5 · Redis Cluster: sorted sets keyed by timestamp with ~30 s expiry

The mechanism Lyft uses for **active driver discovery**.

```
key    = <geo cell id>
member = driver_id
score  = last_update_unix_ts

ZADD  cell:1234  1755859200  driver:42          # location ping
ZRANGEBYSCORE cell:1234  (now-30)  +inf         # who is here AND fresh
ZREMRANGEBYSCORE cell:1234  -inf  (now-30)      # sweep the stale
```

**What this buys — and it is more elegant than it looks:**

| Property | Why |
|----------|-----|
| Membership and freshness in one structure | The score *is* the timestamp, so "who is in this cell" and "who is still alive" are the same query |
| **State that expires cannot leak** | A driver who goes offline, crashes, or loses signal disappears in ~30 s with no delete path, no tombstones, and no cleanup job |
| Self-healing after data loss | The store is a *derived* cache of a location stream. Lose the whole Redis cluster and it rebuilds itself within one expiry window as pings arrive |
| Cheap | `ZADD` and `ZRANGEBYSCORE` are O(log N) and O(log N + M); a single node does 50k–150k ops/s |

**What it costs:**

- Redis is not durable enough to be a source of truth; this only works because it is derived state.
- Memory per member is ~60–100 bytes (skiplist node plus hash entry); size it —
  see [napkin-math.md §6.1](napkin-math.md).
- **Cluster mode constrains multi-key operations**: keys must share a hash slot (via hash tags like
  `{cell1234}`) for a multi-key command to work. Cross-cell queries become client-side scatter-gather.
- A hot cell is a hot key on one node. The mitigation is cell granularity (§6) and, if needed, splitting
  a key into `cell:1234:{0..n}` sub-keys.
- The sweep must actually run, or the sorted set grows even though queries filter correctly.

**The generalisable principle worth stating out loud:** *TTL as a failure detector.* The same pattern
carries the connection registry and presence in
[realtime-chat-delivery-guarantees.md](realtime-chat-delivery-guarantees.md) §5.2 and §11, and agent
availability in [support-case-routing.md](support-case-routing.md). Naming it as a pattern rather than
a trick is what makes it a Staff answer.

Repo: [Key-Value Stores](../06-databases-and-distributed-data/KeyValue_Stores.md).

---

## 6 · Google S2 at level 5

**What S2 is.** A hierarchical decomposition of the sphere: the Earth is projected onto the six faces
of a cube, each face is subdivided recursively into four, and cells are numbered along a **Hilbert
curve** so that nearby cell IDs are usually nearby on the ground. Levels run 0–30, and **each level
quarters the area of the previous one**. A cell ID is a 64-bit integer, which makes it a perfect index
key and a perfect Redis key.

**Lyft uses level 5, chosen deliberately to avoid hot shards** (~kilometre-scale cells, per the source).

**Verify the level-to-area mapping before you quote a specific area in an interview.** Because each
level quarters the area, level numbers and areas are extremely easy to misquote by orders of magnitude.
The safe form is: *"a coarse level — around 5 — because cell granularity is the hot-shard knob."*
Arguing the curve is what earns the point; the exact number is not what is being tested.

**The trade-off curve — this is the part to actually explain:**

| Cell level | Effect |
|-----------|--------|
| Too fine | Enormous key cardinality; a radius query must union many cells (fan-out and latency); per-cell metadata and index overhead dominate; a dense block still concentrates on one key anyway |
| Too coarse | A whole dense district collapses into a single key on a single node — a guaranteed hot key, and every query over-fetches drivers far outside the radius |
| Right | Enough cells that load spreads across shards, few enough that a radius query touches a handful of them |

Two further points that make the hot-shard reasoning concrete:

- **Hash the cell ID into the shard space; do not range-shard on it.** S2 IDs are Hilbert-ordered, so
  spatially adjacent cells have adjacent IDs. Range-sharding therefore places an entire dense city on
  one shard, which is precisely the hot shard you were trying to avoid. Hashing breaks that locality
  deliberately.
- **With a bounded number of coarse cells, hot keys are individually mitigable** — you can split a known
  hot cell into `n` sub-keys and fan out reads, which is impractical if you have billions of tiny cells.

**Alternatives to name:**

| Scheme | Property |
|--------|----------|
| **Geohash** (base-32 string) | Prefix = containment, so prefix queries are natural in any string-keyed store. Cells are lat/lon rectangles that distort badly toward the poles, and neighbours can differ in their first character |
| **S2** | Equal-area-ish cells, integer IDs, Hilbert locality, cheap containment and neighbour operations |
| **H3** (Uber) | Hexagons: every neighbour is equidistant, which is nicer for diffusion, flow, and heatmap smoothing. Hexagons do not tile hierarchically perfectly, so parent/child containment is approximate |
| **PostGIS / R-tree** | True geometry and arbitrary polygon queries; a database round trip rather than an in-memory key lookup |
| **Redis GEO** | `GEOADD`/`GEOSEARCH` are geohash-backed sorted sets. Convenient, but the score is the geohash, so you cannot also use the score for freshness — which is exactly why the timestamp-scored design in §5 exists |

That last row is the sharpest observation available here: Lyft's sorted-set-by-timestamp design is a
*deliberate rejection* of Redis GEO, because freshness matters more than built-in radius search when
your cell already bounds the geography.

Details and worked design in [driver-location-matching.md](driver-location-matching.md).

---

## 7 · DynamoDB

Used for **serialised map data** and for **agent conversation state**.

**What it buys:** single-digit-millisecond point reads and writes at any scale, fully managed with no
operational burden, **per-item TTL** (deletion as a data property, not a cron job), **conditional
writes** (`attribute_not_exists`) which are the primitive behind idempotency and optimistic
concurrency, and **Streams** for change data capture into search indexes or analytics.

**What it costs:**

| Cost | Detail |
|------|--------|
| Access patterns must be known up front | The key schema *is* the query plan. Adding a new query later means a new GSI or a migration |
| 400 KB item limit | Large blobs go to S3 with a pointer in the item — which is exactly the shape "serialised map data" implies |
| 10 GB item-collection limit **when an LSI exists** | An unbounded partition eventually fails writes. Bucket the partition key (see the chat design's `conv#yyyymm`) |
| Hot partitions | A single partition key has a throughput ceiling; adaptive capacity helps but does not remove it |
| GSIs are not free | Eventually consistent, cost extra writes, and **a throttled GSI can back-pressure writes to the base table** — a favourite depth question |
| Cost model shapes design | Cheap for small keyed items, punishing for scans and large items. Query patterns are a cost decision, not just a latency one |
| No joins, no ad-hoc queries | Analytics goes elsewhere, via Streams |

**The conversation-state shape** (the target team's `DynamoDBSaver`, §9):

```
PK = "THREAD#<conversation_id>"
SK = "CKPT#<checkpoint_id>"          # sortable, so "latest" is one query, DESC, limit 1
attrs: serialized_state (blob or S3 pointer), parent_checkpoint_id, ts, ttl
```

This gets you: resume a conversation in one query, full history by range scan, automatic expiry via
TTL, and idempotent checkpoint writes via a conditional put on the checkpoint ID.

Repo: [DynamoDB Refresher](../06-databases-and-distributed-data/dynamodb_refresher.md) ·
[Wide-Column vs Document](../06-databases-and-distributed-data/WideColumn_vs_Document.md).

---

## 8 · Rate limiting at edge and mesh; the 30-second batching window

### 8.1 Two layers, two jobs

Lyft rate-limits with Redis-backed configuration at **both** the edge and the service-mesh layers.

| Layer | Protects against | Keyed by |
|-------|------------------|----------|
| **Edge** | The internet: scrapers, credential stuffing, abusive clients, accidental client retry storms | IP, API key, user, endpoint |
| **Mesh (service-to-service)** | Your own fleet: a misbehaving internal caller, a retry amplification cascade, one tenant starving another | Calling service, route, tenant |

The mesh layer is the one people forget, and it is the more interesting one: **most production overload
is self-inflicted**. A retry loop three services deep multiplies 3 × 3 × 3 into 27x the intended load,
and only a limiter inside the fleet can stop it.

### 8.2 Local vs global limiting

| | Local (per proxy instance) | Global (shared counter in Redis) |
|---|---|---|
| Accuracy | Approximate: the real limit is `n_instances × per-instance limit` | Accurate fleet-wide |
| Latency | Zero extra hops | One Redis round trip per decision |
| Failure mode | Degrades gracefully | The limiter itself becomes a dependency |
| Use for | Coarse protection, high-volume paths | Precise quotas, billing tiers |

Envoy supports both (a local rate-limit filter and a global rate-limit service). **The decision to state
explicitly: what happens when the limiter is unavailable — fail open or fail closed?** For abuse
protection, fail open (availability beats precision). For quota enforcement that costs money, fail
closed. Naming that choice is the point.

Algorithms worth a sentence: **token bucket** (allows bursts up to bucket size — usually what you
want), **fixed window** (simple, but a 2x burst at the window boundary), **sliding window log**
(accurate, memory-hungry), **GCRA / sliding window counter** (accurate and cheap — the usual production
choice).

### 8.3 The ~30-second batching window

Lyft waits roughly 30 seconds, batching riders before re-matching them to drivers.

**What it buys.** Greedy first-come matching assigns each rider to the best driver *available at that
instant*, which is locally optimal and globally poor: a driver two minutes away gets committed to
rider A, and rider B — who was around the corner from that driver — is then assigned someone far away.
Batching converts a stream of greedy online decisions into a sequence of small **offline optimisation**
problems: with 30 seconds of accumulated riders and drivers, you can solve an assignment problem
(Hungarian algorithm, or a good greedy on a bipartite graph scored by ETA) and minimise total pickup
time across the batch. It also lets supply that becomes available *during* the window participate.

**What it costs.** Up to 30 seconds of added latency before a rider sees a driver, which is a direct
UX cost mitigated by showing progress rather than a blank screen. It also adds a stateful scheduler and
a fairness question: a rider who waited through one window must not lose to a newcomer in the next, so
the objective needs a waiting-time term.

**The generalisable principle:** *a batching window converts an online greedy problem into a sequence
of small offline optimisations, trading latency for solution quality.* That sentence transfers directly
to support-case assignment ([support-case-routing.md](support-case-routing.md)), ad auctions, and
delivery-route planning — and being able to transfer it is what distinguishes a principle from a fact.

---

## 9 · The target team's agent platform

Global Support & Partnerships runs a **LangGraph + LangSmith multi-agent customer-support platform in
Python**. The published design:

| Component | What it is | What it buys | What it costs |
|-----------|-----------|--------------|---------------|
| **Meta agent as a stateful router** | Classifies the request and dispatches to a specialist subagent via `Command(goto=...)` | A state machine with explicit transitions instead of one mega-prompt: debuggable, testable, and each specialist has a small prompt and small tool surface | Routing errors are now a distinct failure class; classification must be measured on its own |
| **Separate rider and driver routers** | Two entry points | The domains have different policies, tools, and risk profiles; separation keeps each prompt small | Duplication of shared logic; drift between the two |
| **Custom `DynamoDBSaver`** implementing LangGraph's `BaseCheckpointSaver` | Conversation state persisted per thread | Durability and resumability: a crash mid-conversation resumes rather than restarting; TTL expires old state automatically | Every step now writes state; serialisation format becomes a compatibility surface |
| **Safety checks fanned out in parallel before any LLM reasoning** | Deterministic pre-checks run concurrently, ahead of the model | Latency (parallel, not serial) *and* a **fail-closed** boundary: unsafe content never reaches the reasoning step. For a Safety & Customer Care org this ordering is the design | Adds a fixed latency floor; a false positive blocks a legitimate user |
| **Hand-built plus JSON-configured "self-serve" agents**, prompts from LangSmith Prompt Hub | Two tiers of agent authoring | Non-engineers ship an agent without a code deploy; prompts version independently | Config sprawl and inconsistent quality; needs review and evaluation gates |

**Scale and outcome:** 7 production agents, **~270k interactions/month**, **87% reduction in average
resolution time**, Claude via **Amazon Bedrock**, under a named Anthropic partnership that includes
Anthropic training Lyft engineers on AI-assisted development.

**Read the scale number correctly:** 270k/month is about **0.1 requests per second**. Throughput is a
non-issue. The engineering is in latency per interaction, correctness, safety, and graceful failure —
which is exactly what to emphasise if you design anything adjacent to this in the round. See
[napkin-math.md §8](napkin-math.md).

---

## 10 · The published failure — the single best thing to bring up

Lyft published an honest post-mortem of their agent evaluation: **their offline agent simulator showed
90% pass rates, but production revealed a distribution shift.** Off-the-shelf LLM user simulators
behave like "nice, helpful assistants" — polite, verbose, cooperative — while real customers send
brief, impatient, ambiguous messages. They fixed it by **fine-tuning the simulators on real customer
verbatims**.

Why this is worth memorising:

- It is a **measurement** story, and "how did you measure?" appears verbatim in the behavioural round.
- It generalises far beyond LLMs: *your test distribution is a modelling assumption, and an untested
  one*. The same failure is a load test with uniform keys hiding a hot partition, or a staging
  environment with clean data hiding a parsing bug.
- It gives you an evaluation-design answer for any AI question: golden sets from production traffic,
  simulators calibrated against real distributions, online metrics (containment, escalation, reopen
  rate, resolution time) as the real scoreboard, and offline scores treated as a leading indicator
  rather than a verdict.
- Bringing it up shows you read their engineering writing, which is a cheap and unmistakable signal of
  genuine interest.

**How to deploy it:** *"The thing I found most interesting in your engineering writing was the
simulator distribution-shift result — 90% offline versus what production actually looked like. It
matches something I have hit myself: the test distribution is the assumption nobody validates."* Then
tell your own version of that story.

---

## 11 · Language and platform reality check

- **Python and Go are the backend languages.** There is no JVM in product engineering. **Do not propose
  Akka, Scala, or a JVM stack** in a design round — it signals you are designing for your background
  rather than their context. Flink and Spark exist on the data platform only.
- **Design in Python by default**, standard library first, and know the GIL consequences: one CPython
  process executes one thread of bytecode, so high-concurrency I/O means async or more processes, and
  CPU-bound work means multiprocessing or Go. The arithmetic is in [napkin-math.md §5.4](napkin-math.md).
- **Go for high-concurrency services** (a WebSocket gateway is a textbook case). Saying "I would write
  the gateway in Go and the business services in Python" is a well-calibrated answer in this shop.
- **Flask, not Django.** Small services, gRPC between them.
- **Kubernetes and Docker** for packaging; **Flyte** for orchestrated workflows and ML pipelines;
  **AWS** underneath. Repo: [Terraform / AWS Overview](../14-cloud-and-infrastructure/terraform_aws_overview.md).

---

## 12 · Deployment table — when they say X, you say Y

| Interviewer raises | Invoke | One-line form |
|--------------------|--------|---------------|
| Retries, timeouts, circuit breakers | Envoy sidecar | "Policy in the mesh, uniform across Python and Go; costs a hop and a control plane" |
| Cross-service contracts, versioning | Protobuf | "Schema is the contract; never reuse a field number; costs debuggability" |
| "Who is nearby / what is hot right now" | Redis sorted set scored by timestamp | "Membership and freshness in one structure; state that expires cannot leak" |
| Geospatial sharding | S2 cell granularity | "Cell level is the hot-shard knob; hash the cell ID into shards, do not range-shard the Hilbert order" |
| Conversation or session state | DynamoDB, `PK=thread`, `SK=checkpoint`, TTL | "Resume in one query; watch the 400 KB item limit and GSI back-pressure" |
| Overload, abusive callers | Rate limiting at edge *and* mesh | "Most overload is self-inflicted; decide fail-open vs fail-closed explicitly" |
| Matching, assignment, dispatch | 30-second batching window | "Converts online greedy into small offline optimisations; trades latency for quality" |
| Agent or LLM on a user path | Parallel safety pre-checks, checkpointed state | "Fail closed before reasoning; checkpoint so a crash resumes" |
| Evaluation, "how do you know it works" | The simulator distribution-shift result | "Offline 90% did not survive production; the test distribution is an untested assumption" |
| Long-running workflows | Flyte | "Orchestrate as a DAG with durable task state rather than chaining services" |

---

## Interview questions

**1. What do you know about how Lyft builds services?**
Python and Go behind an Envoy sidecar mesh, protobuf and gRPC between services, on AWS and Kubernetes,
with DynamoDB and Redis for the hot paths. What I find most interesting is that Envoy exists because
they had two backend languages and did not want two divergent sets of retry and circuit-breaking
semantics — pushing failure policy into the mesh is a language-independence decision as much as a
reliability one.

**2. Why would you run a service mesh, and what does it cost?**
It buys uniform L7 behaviour — retries, timeouts, outlier detection, mTLS, and consistent telemetry —
without per-language client libraries, and it makes those policies configuration rather than deploys.
It costs about a millisecond per hop with two hops per call, memory per pod, a control plane that is now
a critical dependency, and a permanent "is it the app or the sidecar" question during debugging.

**3. Why store active drivers in a Redis sorted set scored by timestamp rather than using Redis GEO?**
Because the score can only be one thing, and freshness is more valuable than built-in radius search once
the cell key already bounds the geography. Scoring by timestamp makes "who is in this cell and still
alive" a single range query, and it means a driver who disappears expires on their own within the
window — no delete path, no tombstones, and the whole structure rebuilds itself from the location
stream if Redis is lost.

**4. Lyft uses S2 cells at a coarse level to avoid hot shards. Explain the trade-off.**
Cell granularity is the knob. Too fine and a radius query has to union a huge number of cells while
per-cell overhead dominates; too coarse and an entire dense district becomes one key on one node. The
second half of the answer is the sharding function: S2 IDs follow a Hilbert curve, so range-sharding on
the ID puts a whole city on one shard — you hash the cell ID into the shard space precisely to break
that spatial locality.

**5. What would you use DynamoDB for, and when would you not?**
For keyed, high-volume access patterns known in advance — session and conversation state, idempotency
records, per-item TTL, conditional writes — and for change data capture through Streams. Not for ad-hoc
queries, analytics, or anything where the access patterns will keep changing, because the key schema is
the query plan. The depth detail I would raise is that a throttled GSI can back-pressure writes to the
base table.

**6. Why rate-limit inside the fleet as well as at the edge?**
Because most overload is self-inflicted. The edge stops abusive external traffic, but a retry loop three
services deep multiplies threefold at each layer into roughly 27 times the intended load, and only a
limiter between internal callers can stop that. The design decision to state explicitly is what the
limiter does when it is itself unavailable — fail open for abuse protection, fail closed for paid quota.

**7. Why would a dispatch system wait 30 seconds before matching?**
Because greedy instantaneous matching is locally optimal and globally poor: committing a driver to the
first rider can leave a closer rider with a distant driver. A batching window turns a stream of greedy
online decisions into a sequence of small offline assignment problems that minimise total pickup time,
and lets supply arriving during the window participate. The cost is up to thirty seconds of latency and
a fairness term so riders who already waited are not overtaken.

**8. Tell me something you found interesting in our engineering writing.**
The agent-simulator result: 90% pass rates offline, and production behaved differently because
off-the-shelf LLM user simulators act like polite, verbose assistants while real customers are brief and
impatient. Fine-tuning the simulators on real customer verbatims fixed it. It generalises well beyond
LLMs — a uniform-key load test hiding a hot partition is the same bug, which is that the test
distribution is an assumption nobody validated.

**9. How would you design conversation state for a multi-agent support system?**
A checkpoint per step keyed by thread — partition key on the conversation, sort key on a sortable
checkpoint ID — so resuming is one descending query with a limit of one, full history is a range scan,
and expiry is a TTL attribute rather than a cleanup job. That is the shape of a LangGraph
`BaseCheckpointSaver` backed by DynamoDB, and the trade-off is that every step becomes a write and the
serialisation format becomes a compatibility surface.

**10. Would you propose Akka or Scala for this?**
No. Lyft's product backend is Python and Go, with JVM languages confined to the data platform, so
proposing an Akka-based design would mean designing for my background rather than their context. I would
write business services in Python and reach for Go where connection concurrency dominates, such as a
WebSocket gateway.
