# Real-Time Chat with Delivery Guarantees — full worked design

> **Priority:** Required
> **Est. time:** 120 min
> **Track:** Both
> **HelloInterview:** System Design in a Hurry → Common Patterns → Real-time Updates; Key Technologies → Redis, Kafka, DynamoDB, Cassandra; Core Concepts → Networking Essentials

**This is the single highest-value design problem in this loop.** Reported at Lyft in four variants:
*"Design a scalable real-time chat system with delivery guarantees"*, *"Design 1:1 chat"*,
*"Design a WhatsApp-like service"*, and messaging follow-ups inside other designs. It is also an exact
match for the target org — Global Support & Partnerships runs rider/driver support messaging with human
agents and LLM agents on the same threads.

Study this file until you can produce §3–§8 and §13 from memory in under 25 minutes.

---

## 1 · Frame the problem in one sentence

> "A conversation service that accepts messages from riders, drivers, human agents, and automated
> agents; guarantees that once we acknowledge a message it is never lost; delivers it to every
> participant's devices in per-conversation order; and reconciles state after a client has been
> offline."

The phrase **"delivery guarantees"** in the prompt is the whole exam. Do not design a message bus and
bolt guarantees on at minute 50. Decide the guarantee in minute 5 and let it drive the write path.

---

## 2 · Requirements and scoping

### 2.1 Functional

| # | Requirement |
|---|-------------|
| F1 | Send a message to a conversation (1:1 and small group; support threads are 2–5 participants) |
| F2 | Deliver in near-real time to all online participants, all devices |
| F3 | Fetch history and resume after being offline |
| F4 | Delivery and read receipts |
| F5 | Presence and typing indicators |
| F6 | Push notification when the recipient is offline |
| F7 | Attachments by reference |

### 2.2 Non-functional (the ones that drive the design)

| # | Requirement | Consequence |
|---|-------------|-------------|
| N1 | **No message loss after server ack** | Durable write before ack; no fire-and-forget |
| N2 | **Per-conversation total order**, no global order | Sequencer per conversation, not per system |
| N3 | **No duplicates visible to the user** | Client-generated idempotency ID + dedupe on write |
| N4 | p99 in-session delivery < 500 ms | At most one storage hop on the send path |
| N5 | Client resumes correctly after hours offline | Cursor-based sync, not a replay of a live stream |
| N6 | Availability > strict freshness for presence | Presence may be stale; messages may not be lost |

### 2.3 Out of scope — say it and get agreement

End-to-end encryption (breaks server-side search, abuse detection, and agent handoff — a bad trade for
a *support* product, and worth saying why), voice/video, message editing history, compliance archival.

### 2.4 Scale assumptions

```
2M DAU · 200k support conversations/day · 20 messages each = 4M messages/day
40 writes/s average, ~120/s peak · ~1,200 reads/s peak
~50k concurrent WebSocket connections · 500 bytes/message
```

Derivations in [napkin-math.md §8](napkin-math.md). **State the conclusion immediately:** these numbers
are small. The engineering difficulty is entirely in ordering, delivery semantics, and reconnection —
not throughput. Saying this early prevents an hour of misplaced sharding talk and is itself a signal.

---

## 3 · API surface first

### 3.1 HTTP/gRPC (the durable path)

```
POST /v1/conversations/{cid}/messages
  Idempotency-Key: <uuid>                    # == client_msg_id, 24h dedupe window
  { "client_msg_id": "...", "body": "...", "attachment_ids": [] }
  -> 201 { "message_id": "...", "seq": 10432, "server_ts": "2026-08-22T10:00:00.123Z" }
  -> 200 (replay of an already-accepted client_msg_id, same body -> same response)
  -> 422 same key, different body

GET  /v1/conversations/{cid}/messages?after_seq=10400&limit=100
  -> { "messages": [...], "next_after_seq": 10500, "has_more": true }

POST /v1/conversations/{cid}/read     { "up_to_seq": 10432 }
GET  /v1/sync?since=<opaque cursor>   -> changed conversations + their latest seq
```

**Why `seq` and not timestamps in the cursor.** Timestamps are not unique, not monotonic across
machines, and clock skew means a "resume after `t`" query silently drops messages written by a node
whose clock was behind. A per-conversation integer sequence is unique, dense, and makes gap detection
trivial. Say this out loud; it is one of the highest-signal sentences in the whole design.

### 3.2 The WebSocket protocol (the delivery path)

The socket is a **delivery optimisation over a durable, pollable API** — not the source of truth.
Anything that arrives over the socket can also be obtained by calling `GET /messages`. This single
architectural decision makes reconnection, backpressure, and failover all tractable.

| Frame | Direction | Payload |
|-------|-----------|---------|
| `HELLO` | C→S | auth token, device id, `{conversation_id: last_seq}` resume map |
| `HELLO_ACK` | S→C | session id, server time, heartbeat interval |
| `SEND` | C→S | `client_msg_id`, conversation, body (optional fast path; POST is the fallback) |
| `SEND_ACK` | S→C | `client_msg_id` → `{message_id, seq}` — **only after the durable write** |
| `MESSAGE` | S→C | `{conversation_id, seq, message_id, sender, body, server_ts}` |
| `RECEIPT` | S↔C | `{conversation_id, user_id, delivered_up_to, read_up_to}` |
| `PRESENCE` | S→C | `{user_id, state, last_seen_bucket}` |
| `PING`/`PONG` | both | heartbeat, 30 s interval |
| `RESYNC` | S→C | "your stream is broken, refetch from `after_seq=N`" — the universal escape hatch |

### 3.3 Protobuf sketch

Lyft is protobuf-between-services. Sketching the schema costs 40 seconds and reads as schema-first
experience. See [gRPC & Protobuf Schema Design](grpc_protobuf_schema_design.md).

```protobuf
message Message {
  string conversation_id = 1;
  uint64 seq             = 2;   // server-assigned, dense, per conversation
  string message_id      = 3;   // ULID, globally unique
  string client_msg_id   = 4;   // client-generated, the idempotency key
  string sender_id       = 5;
  int64  server_ts_ms    = 6;
  oneof content { string text = 7; Attachment attachment = 8; }
  reserved 9;                    // was: legacy_body, removed v3
}
```

---

## 4 · Transport: WebSocket vs SSE vs long-poll vs polling

| | Short polling | Long polling | SSE | WebSocket |
|---|---|---|---|---|
| Direction | C→S | C→S | S→C only | Bidirectional |
| Latency | Up to poll interval | ~RTT | ~RTT | ~RTT |
| Server cost | Wasted requests | One held request/client | One held connection/client | One connection/client |
| Per-message overhead | Full HTTP request | Full HTTP response | ~10 bytes framing | ~6 bytes framing |
| Proxy/LB friendliness | Perfect | Good | Good (it is HTTP) | Needs upgrade support and long idle timeouts |
| Reconnect semantics | Trivial | Trivial | Built in (`Last-Event-ID`, auto-retry) | You build it |
| Server statefulness | Stateless | Nearly stateless | Stateful-ish | **Stateful** — this is the real cost |
| HTTP/2 multiplexing | Yes | Yes | Yes | No (separate connection; HTTP/3 changes little here) |
| Browser connection limit | 6/host (HTTP/1.1) | 6/host | 6/host (a real SSE gotcha) | Not subject to it |
| Binary | No | No | **No — text only** | Yes |
| Mobile battery/radio | Bad (wakes radio) | Medium | Medium | Best with long heartbeats |

**Decision for this problem: WebSocket**, because the client both sends and receives, message volume
per connection is high enough that per-message HTTP overhead matters, and typing indicators and
receipts are chatty in both directions.

**But say what it costs and what would flip it:**

- WebSocket makes the gateway tier **stateful**, which forces a connection registry, sticky-ish
  routing, and a deploy strategy that does not disconnect everyone at once.
- Corporate proxies and some mobile networks break `Upgrade`. Ship a **fallback ladder**: WSS on 443 →
  SSE + POST → long-poll. All three are thin adapters over the same durable API, which is only cheap
  because of the §3.2 decision.
- If the product were read-mostly (a live order status feed), **SSE would be the better answer**: it is
  plain HTTP, reconnects itself, replays from `Last-Event-ID`, and needs no custom framing.

**Operational details that show you have run this:**

- Always **WSS on 443**. Plain `ws://` on an odd port is blocked everywhere.
- Idle timeouts kill sockets: LB/Envoy idle timeout must exceed the heartbeat interval. Heartbeat every
  ~30 s (NAT bindings commonly expire around 60 s), and treat two missed PONGs as dead.
- Envoy supports WebSocket upgrade explicitly (`upgrade_configs`); make sure per-route timeouts are not
  the default 15 s or every socket dies on schedule.
- Deploys: drain gracefully — stop accepting new sockets, send `GOAWAY`-style close with a **jittered**
  reconnect hint, and roll a small percentage of nodes at a time.

Repo background: [Networking — Routing & Reverse Proxy](../10-networking/Networking-Routing-Reverse-Proxy.md),
[HTTPS & TLS](../10-networking/Networking-HTTPS-TLS.md).

---

## 5 · Connection registry and fan-out

### 5.1 The shape

```
   clients ──WSS──> [ Gateway tier (stateful) ] ──gRPC──> [ Chat service (stateless) ]
                             │  ▲                                │
                registry     │  │  delivery                      │ durable write
                             ▼  │                                ▼
                      [ Redis: conn registry ]            [ Message store ]
                             ▲                                   │
                             └──────── [ Fan-out worker ] <──── outbox/stream
```

**Split gateway from business logic.** The gateway owns sockets, auth, framing, and heartbeats and
holds no domain state. The chat service owns sequencing and persistence and is stateless, so it scales
and deploys normally. This split is the single most useful structural decision in the design: it
confines statefulness to one tier.

### 5.2 The registry

```
Redis:  conn:{user_id}  ->  HASH { conn_id -> "gateway-7|device=ios|ts" }   TTL refreshed by heartbeat
        node:{gateway}  ->  SET of conn_ids                   (for fast eviction on node loss)
```

- Gateway registers on `HELLO`, refreshes TTL on every heartbeat, deletes on close.
- **TTL is the failure detector.** If a gateway dies, its entries expire in ~45 s with no cleanup job,
  no leader election, and no distributed coordination. This is the same "TTL as self-healing state"
  pattern Lyft uses for driver discovery (see [lyft-architecture.md](lyft-architecture.md) §5) and it
  is worth naming as a principle: *state that expires cannot leak.*
- The registry is a **cache of routing information, never a source of truth**. If Redis is empty, every
  user simply looks offline; messages still persist and are delivered on the client's next sync. Say
  this — a design where losing Redis loses messages is a bad design.

### 5.3 Directed routing vs broadcast

| | Directed (registry lookup → target gateway) | Broadcast (publish to all gateways) |
|---|---|---|
| Work per message | O(recipient devices) | O(gateway nodes) |
| Extra dependency | Registry on the delivery path | Pub/sub only |
| Behaviour at 5 gateways | More complex, no benefit | Simpler and fine |
| Behaviour at 500 gateways | Scales | 500× amplification; each node filters 99.8% away |
| Failure mode | Stale registry → missed push (recovered by sync) | Pub/sub fan-out saturates the bus |

**The honest answer at this scale: broadcast over Redis pub/sub is fine** for ~50k connections across a
handful of nodes, and it is much simpler. State the crossover: "I would switch to directed routing when
the gateway count times the message rate exceeds what a single pub/sub channel handles comfortably — a
few tens of nodes. I would design the delivery interface so that switch is one component change."

A third option worth mentioning: **shard the pub/sub channel by `hash(conversation_id) % N`** so each
gateway subscribes only to the shards it holds participants for. It gets most of the benefit of
directed routing with none of the registry-on-the-hot-path cost.

### 5.4 Reconnect storms

Losing one gateway with 100k sockets means 100k simultaneous reconnects, each doing a TLS handshake, an
auth check, and a sync query. Mitigations, all of which you should name:

- **Full-jitter backoff on the client** (`sleep = random(0, min(cap, base·2^n))`); never a fixed retry.
- **Cap connections per node** so the reconnect wave is survivable by the remaining nodes.
- **Admission control at the gateway**: accept the socket, then rate-limit the initial sync, so clients
  connect fast and backfill slowly.
- **Cheap resume**: `HELLO` carries `{conversation_id: last_seq}` so the server answers with deltas, not
  full history.

---

## 6 · Message ordering

### 6.1 The guarantee to promise

**Total order per conversation. No global order. No cross-conversation guarantee.** This is what users
perceive, and it is the only guarantee that is cheap. Promising global order would force a single
sequencer for the whole system.

### 6.2 How to produce it

A **dense, monotonic `seq` per conversation, assigned server-side at commit**:

| Mechanism | How | Notes |
|-----------|-----|-------|
| DB-native | `UPDATE conversations SET next_seq = next_seq + 1 RETURNING next_seq` in the same transaction as the insert | Simple, correct, serialises per conversation — which is exactly the scope you want |
| DynamoDB | `UpdateItem` with `ADD next_seq :1` and `ReturnValues: UPDATED_NEW`, then conditional `PutItem` on `(cid, seq)` | Two round trips; the conditional put makes the retry safe |
| Cassandra | Do **not** use a counter; use a per-conversation LWT or an external sequencer | Counters are not idempotent under retry |
| Partitioned log | One Kafka partition per conversation-hash; the offset *is* the order | Works, but couples read path to the log |

**Cost to state honestly:** the sequencer is a per-conversation serialisation point. That caps a single
conversation at maybe a few hundred writes/second. For 1:1 and support threads that is irrelevant. For
a 1 M-member broadcast channel it is fatal, and there the answer is a different design (no total order;
order per sender with a merge rule).

### 6.3 Why not client timestamps

- Clocks drift; phone clocks are user-settable. A message can be "sent" in 1970 or 2030.
- Two messages can share a millisecond.
- Ordering by client time lets a client with a fast clock permanently pin its messages to the top.

**Correct use of time:** display uses `server_ts`; ordering uses `seq`; the client's own optimistic
render uses local time only until `SEND_ACK` arrives, at which point it re-sorts by `seq`.

If you are pushed on distributed ordering theory: **Lamport clocks** give a consistent total order but
not causality; **vector clocks** capture causality at O(participants) size; **hybrid logical clocks**
give near-physical timestamps that are monotonic and comparable. Mention that you would only reach for
HLC in a multi-writer, multi-region design (§14) — for a single home region, a database sequence wins on
simplicity.

### 6.4 Gap detection and repair

Because `seq` is dense, the client can detect loss without the server tracking anything: if it holds 41
and receives 43, something is missing. Two responses:

- Buffer 43 briefly (a hundred milliseconds) in case 42 is merely out of order in transit.
- If the gap persists, `GET /messages?after_seq=41` — a cheap, targeted repair.

This is the coding sub-question in §15.1.

Related repo material: [Kafka Fundamentals](../07-messaging-and-streaming/Messaging-kafka_fundamentals.md)
(ordering is per-partition, never per-topic) and
[Linearizability vs Serializability](../06-databases-and-distributed-data/linearizability_vs_serializability.md).

---

## 7 · Delivery semantics: at-least-once, and why exactly-once is a fiction

### 7.1 The three semantics

| Semantics | How | When acceptable |
|-----------|-----|-----------------|
| At-most-once | Send, do not retry | Typing indicators, presence — losing one is free |
| **At-least-once** | Retry until acked, dedupe at the receiver | **Messages, receipts** |
| "Exactly-once" | Does not exist across a network boundary | — |

### 7.2 Why exactly-once cannot exist here

The sender cannot distinguish "the request was lost" from "the response was lost". Therefore it must
either retry (risking a duplicate) or not (risking a loss). This is the Two Generals problem, and no
protocol removes it. What you *can* build is **at-least-once transport plus an idempotent receiver**,
which yields **effectively-once** — the user sees each message once.

Kafka's "exactly-once semantics" is a real feature but a bounded one: it is exactly-once *within
Kafka's own read-process-write boundary*, via idempotent producers and transactional offsets. The
moment an effect leaves that boundary — an HTTP call, a push notification, a payment — you are back to
at-least-once plus idempotency. Say this precisely; it is a strong NoSQL/streaming-depth signal.
Details in [idempotency-and-deduplication.md](idempotency-and-deduplication.md) and
[Delivery Guarantees (QoS), DLQs & HA](../07-messaging-and-streaming/Messaging-delivery_qos_dlq_ha.md).

### 7.3 The end-to-end argument

Dedup must happen where the effect is observed: at the **receiving client** (and at the storage write).
Middle layers can dedupe as an optimisation, but they cannot be the guarantee, because a middle layer
cannot know whether the effect actually landed downstream.

### 7.4 The ack chain

```
client A ──SEND(client_msg_id)──▶ gateway ─▶ chat svc ─▶ [durable write + seq]
                                                              │
    A ◀────────── SEND_ACK{message_id, seq} ◀──────────────────┘     (1) "stored"
                                                              │
                                              fan-out ────────▶ B's devices
    A ◀─ RECEIPT{delivered_up_to} ◀── B's client acks receipt        (2) "delivered"
    A ◀─ RECEIPT{read_up_to}      ◀── B opens the thread             (3) "read"
```

**The critical rule: `SEND_ACK` is emitted only after the durable write commits.** Acking on receipt at
the gateway is the classic bug — it converts a gateway crash into silent message loss, which violates
N1. If you take one sentence from this file into the interview, take that one.

---

## 8 · Idempotent message IDs

| Property | Choice | Why |
|----------|--------|-----|
| Who generates | **The client** | The server cannot tell a retry from a new message; only the client knows its intent |
| Format | UUIDv4 or ULID | ULID sorts by time, which helps client-side ordering before ack |
| Dedupe key | `(conversation_id, client_msg_id)` | Scoped, so a malicious client cannot collide with another conversation |
| Enforcement | Unique constraint / conditional write, **not** read-then-write | Read-check-write is a race under concurrent retries |
| Window | 24 h (must exceed the client's maximum retry horizon) | See [idempotency-and-deduplication.md §6](idempotency-and-deduplication.md) |
| On duplicate | Return the **original** `{message_id, seq}` with 200 | A retry must be indistinguishable from success, not an error |

```sql
-- Postgres: the guarantee is the index, not the application code
CREATE UNIQUE INDEX ON messages (conversation_id, client_msg_id);
INSERT INTO messages (...) VALUES (...)
ON CONFLICT (conversation_id, client_msg_id) DO NOTHING
RETURNING message_id, seq;      -- empty result => it was a duplicate; SELECT the original
```

```
# DynamoDB: same guarantee, different mechanism
PutItem  Item={pk: "CONV#c1#DEDUP", sk: "CMID#<client_msg_id>", seq: N}
         ConditionExpression="attribute_not_exists(sk)"
         # ConditionalCheckFailedException => duplicate, read the stored seq
```

**The subtle case worth raising unprompted:** the same `client_msg_id` arriving with a *different body*
means a buggy or malicious client, not a retry. Return 422 rather than silently accepting either
version. Interviewers rarely ask this and always notice it.

---

## 9 · Acks and read receipts

### 9.1 The per-message state machine

```
                  ┌─ (client optimistic) ─┐
   composing ──▶ pending ──▶ stored ──▶ delivered(per recipient) ──▶ read(per recipient)
                     │                       ▲
                     └── failed ─────────────┘  (retry with same client_msg_id)
```

### 9.2 The write-amplification trap, and the design that avoids it

Naive: one receipt row per `(message, recipient, state)`. For a 5-participant thread and 20 messages
that is 200 receipt writes for 20 message writes — **a 10x write amplification on the cheapest data in
the system**. In a large group it is catastrophic.

**Better: store a watermark per participant per conversation.**

```
participant_state:  (conversation_id, user_id) -> { delivered_up_to_seq, read_up_to_seq, last_seen_ms }
```

- A single small row per participant, updated in place. O(1) writes regardless of message volume.
- "Is message 10432 read by Bob?" becomes `bob.read_up_to_seq >= 10432` — an O(1) comparison.
- Unread count is `conversation.max_seq - read_up_to_seq`, free.

**What it costs:** you cannot represent "read message 5 but not message 4", and you cannot show
per-message read state for out-of-order reading. For 1:1 and support threads that is a non-issue, and
it is exactly the kind of priced trade-off §8 of the [protocol](design-round-protocol.md#8--phase-6--surfacing-trade-offs-explicitly-minutes-5258) asks for.

**Batching:** receipts are the highest-volume, lowest-value traffic in a chat system. Coalesce
client-side on a ~1 s timer and send only the maximum watermark. Never send one receipt per message.

**Typing indicators:** at-most-once, never persisted, TTL of ~5 s, throttled to at most one event every
2–3 seconds per user. They are pure ephemeral state — say that you would run them over the socket and
never through the durable path.

---

## 10 · Offline delivery, sync, and push

### 10.1 The sync protocol

Reconnecting clients do **not** replay a live stream — they **pull deltas**:

```
HELLO { resume: { "conv-1": 10432, "conv-2": 771 }, sync_cursor: "..." }
  ->  for each conversation: messages after the given seq, capped at N per conversation
  ->  conversations not in the resume map: fetched lazily on open
  ->  if the client is too far behind (> N messages or > T days): RESET
      { "truncated": true, "start_seq": ... } and the client refetches page by page
```

A cold or very stale client must not be able to force an unbounded query. Cap the resume response, tell
the client it was truncated, and let it page. This bound is what stops a mass-reconnect event from
becoming a database outage.

### 10.2 The inbox question — fan-out on write vs on read

| | Fan-out on read (shared conversation log) | Fan-out on write (per-user inbox copy) |
|---|---|---|
| Write cost | 1 write | N writes (N = participants) |
| Read "my conversations" | Join/GSI on participants | Single partition scan |
| Storage | 1 copy | N copies |
| Fits | 1:1 and small groups — **this problem** | Huge fan-out feeds |

For 2–5 participants, **fan-out on read** with a small per-user conversation index is correct. Say the
crossover: "fan-out on write starts paying at hundreds of recipients, and the hybrid — fan-out on write
for normal users, fan-out on read for high-fan-out ones — is what large systems actually ship."

### 10.3 Push notifications

```
message stored ─▶ outbox/stream ─▶ delivery worker
                                     ├─ registry lookup: any live socket for user B?
                                     ├─ yes -> push over socket, start a delivery timer
                                     └─ no (or timer expires) -> APNs / FCM
```

- **Decide on the socket, not on the client.** "Offline" means "no live connection in the registry",
  and the registry can be stale, so the two paths must be safe to *both* fire.
- **Dedupe on the device.** The push payload carries `message_id`; if the client already has it from the
  socket, it suppresses the alert. This is the end-to-end argument again.
- **Prefer a silent/data push that triggers a sync** over putting the message body in the payload:
  smaller payloads, no stale content in the notification tray, and no plaintext leaving your control.
  The trade-off is an extra round trip before the user sees content, and unreliable delivery of silent
  pushes on iOS — so in practice: body in the alert for latency, `message_id` for dedupe, and a sync on
  open.
- **Token lifecycle:** tokens expire and get reassigned. Handle the provider's "unregistered" response
  by deleting the token, or you will push a stranger's messages to a recycled device.
- **Badge counts** come from the watermark (`max_seq - read_up_to_seq`), computed at push time — never
  incremented client-side, which drifts.

---

## 11 · Presence

Presence is the feature that looks cheap and is not. **Its cost is fan-out, not storage.**

```
Redis:  presence:{user_id} -> "online"   EX 45     # refreshed by the socket heartbeat
```

- **Derive presence from the connection, not from a separate protocol.** A live socket with fresh
  heartbeats *is* the online signal. TTL expiry handles crashes for free — same self-healing pattern as
  the registry.
- **The fan-out problem:** naively, one user going offline notifies everyone who can see them. With 50k
  concurrent users and 100 contacts each, a 1% churn per second is 50k notifications/second — an order
  of magnitude more traffic than the actual messages.
- **Mitigations, in the order you should offer them:**
  1. **Subscribe on view.** Only push presence for conversations currently open on screen. This alone
     removes ~99% of the cost and is what real clients do.
  2. **Coalesce and delay.** Batch presence changes into ~5 s windows; nobody needs sub-second presence.
  3. **Degrade precision.** "Active now / active recently / active today" instead of exact timestamps.
     Cheaper *and* better for privacy.
  4. **Pull on open** rather than push, for large contact lists.
- **In a support product, the presence that matters is agent presence** — a small, high-value set
  (thousands, not millions) that also feeds routing (see
  [support-case-routing.md](support-case-routing.md)). Splitting "agent presence" (accurate, pushed,
  used for routing) from "user presence" (approximate, pulled, cosmetic) is a good scoping move.

---

## 12 · Storage model — the partition key is the design

This section is where the **NoSQL depth probe** lands. Do not name a database before you have written
the key.

### 12.1 Access patterns first

| # | Pattern | Rate | Shape |
|---|---------|------|-------|
| A1 | Append a message to a conversation | 120/s peak | Single-item write, needs uniqueness on `client_msg_id` |
| A2 | Read the last 50 messages of a conversation | 1,000/s | Range scan, descending, bounded |
| A3 | Read messages after `seq` (resume) | 200/s | Range scan, ascending, bounded |
| A4 | List a user's conversations by recency | 200/s | Secondary access path |
| A5 | Update a participant watermark | 500/s | Small in-place update |
| A6 | Search a user's message history | 20/s | Not a KV pattern — needs a search index |

### 12.2 Candidate partition keys, and what each breaks

| PK / SK | A1, A2, A3 | A4 | Breaks when |
|---------|-----------|-----|-------------|
| `PK=conversation_id`, `SK=seq` | Ideal: append is a put, history is one range query | Needs a GSI | A single conversation grows without bound: DynamoDB caps an item collection with LSIs at 10 GB, and any one partition has a throughput ceiling. A 3-year support thread or a hot broadcast conversation hits it |
| **`PK=conversation_id#yyyymm`, `SK=seq`** | Same, plus a bounded partition | Needs a GSI | Reads spanning a month boundary touch two partitions — cheap and predictable. **This is the answer** |
| `PK=user_id`, `SK=ts` (inbox) | Write amplification ×participants | Free | Fan-out cost; and a message now exists in N places, so edits/deletes are N writes |
| `PK=message_id` | Point reads only | No | Kills A2 and A3 entirely — history becomes a scan. A common wrong answer |
| `PK=hash(conversation_id) % N` | Spreads load | Needs a GSI | Loses locality: history requires a scatter-gather. Only right if a single conversation is genuinely too hot |

**Say the whole reasoning chain, not the conclusion:**

> "`conversation_id` as the partition key, `seq` as the sort key, because A1 is then a single put and
> A2/A3 are one bounded range query — which is 90% of my traffic. The risk is an unbounded item
> collection, so I bucket the key by month: `conv#2026-08`. That costs me a two-partition read across
> month boundaries and a little client-side logic to walk buckets backwards, and it buys a hard bound
> on partition size and a natural tiering boundary for archiving. A4 is not this table's job — it is a
> GSI on `user_id` sorted by `last_message_at`, or a separate small conversation-index table, which I
> prefer because I can update it once per conversation instead of once per message."

### 12.3 Store choice

| Store | Verdict at this scale |
|-------|----------------------|
| **Postgres** | **Genuinely sufficient.** 120 writes/s is nothing. `messages(conversation_id, seq)` primary key, partitioned by month. Gives transactions, unique constraints, and joins for free. The honest first answer |
| **DynamoDB** | Right if you want managed scale, per-item TTL, conditional writes for idempotency, and Streams for CDC. Lyft already runs DynamoDB. Costs: access patterns fixed early, 400 KB item limit, GSI throttling can back-pressure the base table |
| **Cassandra** | Right at much larger scale or multi-DC writes. Partition `conversation_id`, clustering `seq DESC`. Watch tombstones on deletes and repair cost |
| **Kafka as the store** | It is a log, not a database. Excellent as the ordering and fan-out spine, wrong as the query surface |
| **Redis** | Hot last-N-messages cache and registry only. Not durable enough for N1 |

Repo: [DynamoDB Refresher](../06-databases-and-distributed-data/dynamodb_refresher.md) ·
[Cassandra Partition vs Clustering Keys](../06-databases-and-distributed-data/cassandra_partition_clustering.md) ·
[Cassandra LSM](../06-databases-and-distributed-data/Cassandra_LSM.md) ·
[Partition Strategies](../06-databases-and-distributed-data/partition_strategies.md) ·
[Wide-Column vs Document](../06-databases-and-distributed-data/WideColumn_vs_Document.md).

### 12.4 Attachments and search

- **Attachments never go through the chat service.** Client requests a pre-signed S3 URL, uploads
  directly, then sends a message referencing `attachment_id`. This keeps blobs off the message path and
  out of the item-size limit. Scan asynchronously for malware before making it downloadable.
- **Search** is a separate system fed by CDC (DynamoDB Streams / Postgres logical decoding) into
  Elasticsearch. Eventually consistent, and say so. See
  [Elasticsearch Basics](../06-databases-and-distributed-data/Elasticsearch_Basics.md).

---

## 13 · Backpressure

The insight that makes chat backpressure tractable: **the socket is disposable.** Because every message
is durably stored and reachable via `GET /messages?after_seq=`, the gateway is allowed to give up on a
slow client at any time without losing data.

| Pressure point | Symptom | Response |
|----------------|---------|----------|
| Slow client (bad network, background tab) | Per-connection send queue grows | Bound the queue (e.g. 100 messages / 1 MB). On overflow: **drop the socket with `RESYNC`**, do not buffer unboundedly and do not drop individual messages |
| Chatty client (spam, buggy retry loop) | Inbound rate spikes | Per-connection and per-user token bucket; reject with a typed error and `Retry-After`; disconnect on repeat |
| Fan-out worker behind | Delivery lag grows | Consumer lag metric; scale out workers; the durable log absorbs the burst |
| Storage write saturation | Write latency climbs | Shed *low-value* traffic first: typing indicators, then presence, then receipts. **Never shed messages** — that violates N1 |
| Mass reconnect | Sync queries stampede | Admission control on sync; cap resume size; jittered client backoff |

**The rule to state:** *drop the connection, never the acknowledged message.* Dropping a socket costs a
reconnect and a delta fetch. Dropping an acked message costs correctness. Ranking what you shed — and
saying that ordering out loud — is a Staff-level answer to a question most candidates answer with "we
add a queue".

Repo: [Akka Streams & Backpressure](../03-akka-ecosystem/akka_streaming_and_backpressure_detailed_guide.md)
(mechanics) · [High-Throughput, Low-Latency Systems](../07-messaging-and-streaming/Messaging-high_throughput_low_latency_systems_expanded.md).

---

## 14 · Multi-region

Only design this if asked — but have the answer, because "how does this work in two regions" is a
standard escalation.

| Model | How | Verdict |
|-------|-----|---------|
| **Home region per conversation** | Each conversation has an owning region; writes route there; other regions read a replica | **The right default.** Preserves the single sequencer, so ordering stays trivially correct. Costs cross-region write latency for participants far from home |
| Active-active with global tables | Both regions accept writes; replication resolves conflicts by last-writer-wins | LWW on messages means **silent message loss** when two writes collide on the same key. Only safe if keys are globally unique per message (they are: `message_id`), and `seq` assignment is still region-owned |
| Regional sequencers with HLC | Each region assigns its own sequence; merge on read using a hybrid logical clock | Correct, complex, and hard to explain in a receipt UI. Reach for it only if per-region write locality is a hard requirement |

Additional points that show operational awareness:

- **Route by conversation, not by user.** A rider in the EU talking to an agent in the US has one
  conversation; it needs one home.
- **Data residency** may force the home region rather than latency. For a support product handling PII,
  that is often the deciding constraint — mention it before someone else does.
- **Failover:** promoting a replica means a new sequencer. Guard against split-brain by fencing —
  monotonically increasing epoch in the conversation record, and reject writes carrying an older epoch.
- **Push and presence stay regional**; only the durable log replicates.

Repo: [CAP & Consistency](../06-databases-and-distributed-data/CAP_Consistency.md) ·
[Distributed Transactions](../06-databases-and-distributed-data/Distributed_Transactions.md).

---

## 15 · The coding sub-question the round may pivot to

Lyft's design round includes **real coding**. For a chat design, these three are the most likely pivots.
All are stdlib-only Python 3.10-compatible and readable-first — readability is explicitly graded.

### 15.1 Ordered delivery with gap detection (most likely)

*"The client receives messages out of order and sometimes duplicated. Write the buffer that emits them
in order."*

```python
class OrderedDelivery:
    """Releases per-conversation messages in gap-free sequence order.

    The server stamps every message in a conversation with a contiguous
    sequence number. A client may receive them out of order, duplicated, or
    with holes. This buffers what is ahead of the watermark and releases as
    soon as the hole is filled.
    """

    def __init__(self, next_seq: int = 1, max_buffer: int = 256) -> None:
        self.next_seq = next_seq
        self.max_buffer = max_buffer
        self._pending: dict[int, object] = {}

    def offer(self, seq: int, payload: object) -> list[tuple[int, object]]:
        """Accept one message; return the messages now deliverable, in order."""
        if seq < self.next_seq or seq in self._pending:
            return []                      # duplicate or already delivered
        self._pending[seq] = payload
        released: list[tuple[int, object]] = []
        while self.next_seq in self._pending:
            released.append((self.next_seq, self._pending.pop(self.next_seq)))
            self.next_seq += 1
        return released

    def needs_resync(self) -> bool:
        """True when the hole is too old to wait for; refetch from storage."""
        return len(self._pending) > self.max_buffer

    def missing(self) -> list[int]:
        """Sequence numbers we are waiting on, for a targeted backfill."""
        if not self._pending:
            return []
        return [s for s in range(self.next_seq, max(self._pending))
                if s not in self._pending]
```

```python
import unittest

class TestOrderedDelivery(unittest.TestCase):
    def test_out_of_order_and_gap_fill(self):
        d = OrderedDelivery()
        self.assertEqual(d.offer(3, "c"), [])
        self.assertEqual(d.offer(2, "b"), [])
        self.assertEqual(d.missing(), [1])
        self.assertEqual(d.offer(1, "a"), [(1, "a"), (2, "b"), (3, "c")])

    def test_duplicates_dropped(self):
        d = OrderedDelivery()
        d.offer(1, "a")
        self.assertEqual(d.offer(1, "a-again"), [])

    def test_resync_when_buffer_overflows(self):
        d = OrderedDelivery(max_buffer=2)
        for s in (5, 6, 7):
            d.offer(s, s)
        self.assertTrue(d.needs_resync())
```

**What to say while writing it:** amortised O(1) per message; the buffer is bounded because an
unfillable gap must not consume memory forever; overflow escalates to a `RESYNC` against durable
storage, which is safe precisely because the socket is not the source of truth.

### 15.2 Connection registry with TTL heartbeats

*"Where do you keep which server holds which user's connection, and what happens when a server dies?"*

```python
import heapq
from dataclasses import dataclass


@dataclass
class _Conn:
    conn_id: str
    node: str
    expires_at: float


class ConnectionRegistry:
    """Which gateway node holds which user's live sockets.

    Models the Redis layout: a per-user set of connections, each refreshed by
    heartbeat and reaped on TTL expiry, so a crashed gateway self-cleans.
    """

    def __init__(self, ttl: float = 30.0) -> None:
        self.ttl = ttl
        self._by_user: dict[str, dict[str, _Conn]] = {}
        self._expiry: list[tuple[float, str, str]] = []   # heap of (exp, user, conn)

    def register(self, user_id: str, conn_id: str, node: str, now: float) -> None:
        conn = _Conn(conn_id, node, now + self.ttl)
        self._by_user.setdefault(user_id, {})[conn_id] = conn
        heapq.heappush(self._expiry, (conn.expires_at, user_id, conn_id))

    def heartbeat(self, user_id: str, conn_id: str, now: float) -> bool:
        conn = self._by_user.get(user_id, {}).get(conn_id)
        if conn is None:
            return False                    # client must re-register
        conn.expires_at = now + self.ttl
        heapq.heappush(self._expiry, (conn.expires_at, user_id, conn_id))
        return True

    def unregister(self, user_id: str, conn_id: str) -> None:
        conns = self._by_user.get(user_id)
        if conns:
            conns.pop(conn_id, None)
            if not conns:
                del self._by_user[user_id]

    def reap(self, now: float) -> int:
        """Drop expired entries. Stale heap entries are skipped lazily."""
        dropped = 0
        while self._expiry and self._expiry[0][0] <= now:
            _, user_id, conn_id = heapq.heappop(self._expiry)
            conn = self._by_user.get(user_id, {}).get(conn_id)
            if conn is not None and conn.expires_at <= now:
                self.unregister(user_id, conn_id)
                dropped += 1
        return dropped

    def routes(self, user_id: str) -> list[str]:
        """Gateway nodes to deliver to; empty means the user is offline."""
        return sorted({c.node for c in self._by_user.get(user_id, {}).values()})
```

**The two details that earn the point:** heartbeats push a *new* heap entry rather than mutating the old
one (a heap cannot reorder in place), so `reap` must re-check `expires_at` and skip stale entries; and
`routes()` returning empty is a *hint*, not a fact, so the delivery path must be safe when the registry
is wrong in either direction.

### 15.3 Other plausible pivots

- **A sliding-window rate limiter** for message sends (per-user token bucket in Redis, with the
  `INCR`/`EXPIRE` race and the fix via Lua or `SET NX`).
- **Unread count** across conversations from watermarks — a one-liner if you chose the watermark model
  in §9, and an O(messages) mess if you did not. That is the payoff of the earlier decision.
- **Merge K sorted message streams** (per-conversation logs into one timeline) — a heap problem; see
  [Binary Heap](../08-algorithms-and-data-structures/binary_heap_summary.md).

---

## 16 · Failure modes

| Component | Failure | Detection | Mitigation | User sees |
|-----------|---------|-----------|------------|-----------|
| Gateway node | Crash | Registry TTL expiry; health check | Client reconnects with jitter, resumes from `last_seq` | 1–5 s gap, no loss |
| Gateway | Slow client | Send-queue high-water mark | Close socket with `RESYNC` | Brief reconnect |
| Chat service | Down | 5xx rate, health check | Client retries `POST` with the same `client_msg_id`; no duplicate | Spinner, then success |
| Sequencer | Contention on one hot conversation | Write latency on that partition | Conversation-level rate limit; consider per-sender ordering for broadcast threads | Slower sends in that thread |
| Message store | Failover | Write errors | Retry with idempotency key; **do not ack** until committed | Message shows "sending" |
| Redis registry | Total loss | Connection errors | Everyone looks offline; delivery falls back to push + sync | Presence wrong, messages fine |
| Pub/sub | Partition/overload | Publish errors, lag | Fall back to polling sync; messages already durable | Higher latency |
| Push provider (APNs/FCM) | Down or throttling | Error rate, breaker | Queue and retry with backoff; socket delivery unaffected | Late notification |
| CDC → search | Lag | Lag metric | Search results stale; messaging unaffected | Stale search only |
| Whole region | Outage | Health checks | Failover to replica with a fenced epoch bump | Reconnect, possible brief read-only |

Two failure narratives worth rehearsing in one sentence each:

- **Ack-before-durable:** "If we acked at the gateway and the gateway crashed before the write
  committed, the sender would show a delivered checkmark for a message nobody will ever receive. That
  is why `SEND_ACK` follows the commit."
- **Duplicate under retry:** "If the response is lost, the client retries with the same
  `client_msg_id`; the conditional write fails; we return the original `seq`. The client cannot tell
  the difference, and neither can the recipient."

---

## 17 · Working design vs good design, for this problem

| Working | Good |
|---------|------|
| "Clients connect over WebSocket" | WebSocket **with a fallback ladder**, and the socket is an optimisation over a durable pollable API |
| "Messages go to a database" | `PK=conversation_id#yyyymm`, `SK=seq`, ~500 B items, bounded partitions, uniqueness on `client_msg_id` |
| "We use at-least-once" | At-least-once **plus** an idempotent receiver, dedupe key named, window sized, and "exactly-once is a fiction" said explicitly |
| "Messages are ordered" | Per-conversation dense `seq` assigned at commit, why not timestamps, and how the client detects and repairs a gap |
| "We show read receipts" | Watermarks per participant, because per-message receipts are a 10x write amplification |
| "Presence via heartbeat" | Presence derived from the socket, TTL as failure detector, subscribe-on-view because fan-out is the real cost |
| "Add a queue for backpressure" | Bounded per-connection queues, an explicit shed order, and *drop the socket, never the acked message* |
| "It scales" | 120 writes/s is small; the design effort goes to reconnect storms and correctness, not throughput |

---

## Interview questions

**1. Design a scalable real-time chat system with delivery guarantees.** **[Reported at Lyft]**
Clients hold a WebSocket to a stateful gateway tier that owns only sockets; a stateless chat service
assigns a dense per-conversation sequence number and writes durably before any acknowledgement; fan-out
happens from the durable write, not from the inbound request. Guarantee is at-least-once transport plus
an idempotent receiver keyed on a client-generated message ID, which gives effectively-once. Offline
clients resume by pulling deltas after their last sequence number, so the socket is only an
optimisation over a durable, pollable API.

**2. Why not exactly-once delivery?** **[Reported at Lyft]**
Because the sender cannot distinguish a lost request from a lost response, so it must either retry and
risk a duplicate or not retry and risk a loss. The achievable design is at-least-once plus dedupe at
the point where the effect is observed. Kafka's exactly-once is real but bounded to its own
read-process-write cycle; the moment an effect leaves that boundary you are back to at-least-once.

**3. WebSocket, SSE, or long polling — how do you choose?** **[Reported at Lyft]**
WebSocket when the client both sends and receives frequently, which chat does; SSE when the flow is
server-to-client only, because it is plain HTTP, reconnects itself, and replays from `Last-Event-ID`;
long polling as a fallback where proxies break upgrades. The real cost of WebSocket is that it makes
the gateway tier stateful, which forces a connection registry and a careful deploy strategy.

**4. How do you guarantee message ordering?**
Per conversation, not globally, using a dense integer sequence assigned server-side at commit. Client
timestamps are unusable because clocks drift and are user-settable, and they cannot detect gaps. Dense
sequences make gap detection free: if the client holds 41 and receives 43 it knows to buffer briefly
and then refetch. The cost is that the sequencer serialises writes within one conversation, which is
fine at a few hundred writes per second per thread.

**5. What partition key would you use for the messages table, and what breaks?** **[Reported at Lyft]**
`conversation_id` as the partition key with `seq` as the sort key, because appends become a single put
and history becomes one bounded range query. The failure mode is an unbounded partition for a long-lived
thread — DynamoDB caps an item collection with an LSI at 10 GB and any single partition has a throughput
ceiling — so I bucket the key by month. That costs a two-partition read at month boundaries and buys a
hard size bound plus a natural archive boundary.

**6. How do read receipts work at scale?**
As a watermark per participant per conversation — `delivered_up_to_seq` and `read_up_to_seq` — rather
than a row per message per recipient. Per-message receipts are a write amplification of roughly the
participant count on the cheapest data in the system. The watermark makes unread counts a subtraction
and "has Bob read this" a comparison; the cost is that you cannot represent out-of-order reads.

**7. A client has been offline for two days. What happens when it reconnects?**
It sends its last known sequence number per conversation in the handshake and receives capped deltas,
not a replay of a live stream. If it is too far behind, the server returns a truncation marker and the
client pages through history. The cap is essential: without it, a mass reconnect after an incident
turns into an unbounded query storm against the store.

**8. How do you handle a slow consumer?**
Bound the per-connection send queue and, on overflow, close the socket with a resync instruction rather
than buffering or dropping individual messages. That is safe only because every message is durably
stored and reachable by sequence number. The shed order under load is typing indicators, then presence,
then receipts, and never messages.

**9. How much does presence cost, and how would you reduce it?**
More than the messages, because the cost is fan-out: every state change notifies everyone who can see
that user. I derive presence from the socket heartbeat with a TTL so crashes clean themselves up, then
cut the fan-out by only subscribing to presence for conversations currently on screen, batching changes
into multi-second windows, and degrading precision to "active recently".

**10. How would you extend this to two regions?**
Home region per conversation: writes route to the owning region, so the single sequencer and the
ordering guarantee survive unchanged, and other regions serve replicated reads. Active-active with
last-writer-wins replication is the trap, because a conflict on a message key is silent data loss. On
failover I would fence with a monotonically increasing epoch so a recovered old primary cannot resume
writing.

**11. Where does the LLM agent fit in this design?**
As just another participant on the conversation, writing through the same API with its own idempotency
keys, so ordering, receipts, and history need no special cases. What differs is that it is a slow
third-party call on a human-visible path, so it needs a per-call deadline, a visible "agent is typing"
state, and a fallback to human routing when it times out — see
[support-case-routing.md](support-case-routing.md) and
[third-party-failure-modes.md](third-party-failure-modes.md).

**12. What is the single most common mistake in this design?**
Acknowledging the send at the gateway instead of after the durable commit. It looks harmless and it
converts every gateway crash into silent message loss, which is exactly the guarantee the question asks
you to provide.
