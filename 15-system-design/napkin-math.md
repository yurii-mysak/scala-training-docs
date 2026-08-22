# Napkin Math — latency, storage, QPS, cores, and memory, out loud

> **Priority:** Required
> **Est. time:** 60 min
> **Track:** Both
> **HelloInterview:** System Design in a Hurry → Core Concepts → Numbers to Know

**Live back-of-envelope math on memory and CPU is a named probe in the Lyft design round.** Not
storage only — expect "how much RAM does that cache need" and "how many cores does that service take".
The skill being tested is not arithmetic; it is whether you can bound a system in your head fast
enough that the estimate shapes the design rather than decorating it.

---

## 1 · The rules that stop you stalling

1. **One significant figure. Always.** 86,400 s/day is 10^5. 2,592,000 s/month is 2.6 × 10^6. Nobody
   wants three digits and every extra digit is a chance to lose the thread.
2. **Everything in powers of ten.** Convert to scientific notation before you multiply, and count
   exponents separately from mantissas. `4 × 10^6 / 10^5 = 40`. That is the whole technique.
3. **Say the assumption, then the arithmetic, then the answer, then the sanity check.** Four beats:
   "Call it 2 million DAU. 10% open a support chat, so 200k sessions. Twenty messages each is 4 million
   messages a day. Over 10^5 seconds that is 40 writes a second — which is nothing, so storage is not
   the interesting part of this design."
4. **Round in the direction that makes the conclusion safe.** If you are checking whether something
   fits, round up. If you are checking whether it is worth optimising, round down.
5. **Always land on a conclusion.** A number with no decision attached is wasted time. Every estimate
   ends with "so X is/is not the bottleneck" or "so this fits on N machines".
6. **Write it on the canvas.** Numbers in a text box are evidence. Numbers spoken and lost are not.
7. **If you are stuck on a factor, state a range and move on.** "Somewhere between 200 bytes and 2 KB
   per message; I will use 500 bytes and the conclusion does not change at either end."

---

## 2 · The numbers to know

### 2.1 Latency ladder (order of magnitude, one machine and one datacentre)

| Operation | Time | Mnemonic |
|-----------|------|----------|
| L1 cache reference | ~1 ns | |
| Branch mispredict | ~3 ns | |
| L2 cache reference | ~4 ns | |
| Mutex lock/unlock, uncontended | ~20 ns | |
| Main memory reference | ~100 ns | **100 ns is the memory unit** |
| Compress 1 KB (fast codec) | ~1–2 µs | |
| Send 1 KB over 10 Gbps LAN | ~1 µs | |
| SSD random read (NVMe) | ~50–150 µs | **100 µs is the SSD unit** |
| Read 1 MB sequentially from memory | ~50 µs | |
| Round trip within a datacentre | ~0.5 ms | **0.5 ms is the RPC unit** |
| Read 1 MB sequentially from SSD | ~200–500 µs | |
| Disk seek (spinning) | ~5–10 ms | |
| Read 1 MB from spinning disk | ~10–20 ms | |
| Same-continent network RTT | ~30–50 ms | |
| Cross-continent RTT (US↔EU) | ~80–100 ms | |
| Global RTT (US↔SG/AU) | ~150–250 ms | |
| TLS handshake (full, 2-RTT) | ~2 × RTT | Session resumption kills this |
| Envoy sidecar hop | ~0.5–1 ms added | Two hops per call (out and in) |

**Derived facts worth quoting:** memory is ~1000x faster than SSD, SSD is ~100x faster than spinning
disk. A cross-region round trip costs more than 100 local disk reads. Anything that turns one network
call into a serial chain of five costs you 2.5 ms of pure latency before any work happens.

### 2.2 Throughput and capacity, per modern commodity node

| Resource | Rough capacity |
|----------|----------------|
| One CPU core, simple request handling | 1k–10k simple ops/s (Python), 10k–100k (Go/JVM) |
| NVMe SSD | 100k–1M IOPS, 2–7 GB/s sequential |
| 10 Gbps NIC | 1.25 GB/s ≈ 10^9 bytes/s |
| Redis, single instance | 50k–150k ops/s at sub-ms p99 |
| Postgres, single primary | 5k–20k simple writes/s, more reads with replicas |
| Kafka, one broker | 100k+ msgs/s, disk-bandwidth bound |
| One WebSocket gateway node | 50k–200k idle connections (memory and fd bound) |
| Typical cloud VM | 8–64 vCPU, 32–256 GB RAM |

### 2.3 Time and size conversions

| Quantity | Value | Round to |
|----------|-------|----------|
| Seconds per day | 86,400 | **10^5** |
| Seconds per month (30 d) | 2,592,000 | **2.6 × 10^6** |
| Seconds per year | 31,536,000 | **3 × 10^7** |
| 1 QPS sustained for a day | 86,400 requests | 10^5/day |
| 1 QPS sustained for a year | 31.5 M requests | 3 × 10^7/year |
| 1 M/day | 11.6 QPS | **~12 QPS** |
| 1 M/month | 0.4 QPS | |
| 1 B/month | 385 QPS | ~400 QPS |
| 2^10 / 2^20 / 2^30 / 2^40 | KB / MB / GB / TB | 10^3 / 10^6 / 10^9 / 10^12 |
| Bytes in a UUID (text / binary) | 36 / 16 | |
| Bytes in a timestamp (ms epoch) | 8 | |
| Typical chat message row | 200–600 bytes | **500 bytes** |
| Typical HTML page | 50–150 KB | **100 KB** |
| Typical JPEG photo | 1–5 MB | |

### 2.4 Common multipliers people forget

| Multiplier | Typical value | Why it matters |
|------------|---------------|----------------|
| Replication factor | ×3 | Your 1 TB is 3 TB on disk |
| Index overhead | ×1.2–2 on the table | Secondary indexes are not free |
| Peak / average | ×2–3 (×10 for spiky events) | Capacity is sized on peak |
| Read : write | 10:1 to 1000:1 | Decides where the effort goes |
| Compression | ÷3 to ÷10 on text | Do not forget it for logs and HTML |
| Retention | ×N years | Storage grows even if traffic does not |
| Fan-out | ×recipients | Turns a small write rate into a large push rate |
| Retries | ×1.05–1.5 | Budget for it or it surprises you in an incident |

---

## 3 · Storage estimation

**Recipe:** `items/day × bytes/item × retention_days × replication × (1 + index_overhead) ÷ compression`

Worked, for a support-chat message table:

```
4 × 10^6 messages/day        (from §6.1)
× 500 bytes                  -> 2 × 10^9 B/day = 2 GB/day
× 365 days                   -> 730 GB/year
× 3 (replication)            -> ~2.2 TB/year
+ index overhead ~30%        -> ~2.9 TB/year
```

**Conclusion to say out loud:** "Under 3 TB a year, all in. That fits on one machine's disk, so storage
volume is not a design constraint here — the constraints are access pattern and retention policy, not
capacity. If we keep everything for seven years for compliance, it is ~20 TB, and *then* I want tiered
storage with cold data in S3."

That last sentence is the whole point: the estimate produced a design decision.

---

## 4 · QPS estimation

**Recipe:** `DAU × actions_per_user_per_day ÷ 10^5 × peak_factor`

| Step | Value |
|------|-------|
| DAU | 2 × 10^6 |
| Support sessions per DAU per day | 0.1 |
| Sessions/day | 2 × 10^5 |
| Messages per session | 20 |
| Messages/day | 4 × 10^6 |
| Average write QPS | 4 × 10^6 / 10^5 = **40/s** |
| Peak factor | ×3 |
| **Peak write QPS** | **~120/s** |
| Read:write for message history | 10:1 |
| **Peak read QPS** | **~1,200/s** |

Two refinements that show experience:

- **Traffic is not uniform.** A consumer product concentrates ~80% of its traffic in ~8 hours, which is
  already roughly a 3x peak factor. Do not multiply a diurnal peak by another peak factor and end up
  sizing for 10x you will never see.
- **Support traffic follows incidents.** The mean is boring; the interesting number is the surge when
  something breaks fleet-wide. Size the queue and the shedding policy for the surge, size the steady
  fleet for the mean plus headroom.

---

## 5 · QPS to cores — the CPU probe

This is the estimate most candidates cannot do live. Learn the two formulas.

### 5.1 The core-count formula

```
cores = QPS × CPU_seconds_per_request ÷ target_utilisation
```

`CPU_seconds_per_request` is **CPU time, not wall-clock latency**. A request that waits 200 ms on a
database and burns 5 ms of CPU costs you 5 ms of core, not 205 ms.

| Workload | CPU per request | 5,000 QPS needs (at 60% util) |
|----------|-----------------|-------------------------------|
| Proxy / routing, no parsing | 0.1 ms | 0.8 cores |
| JSON API, small payload, Go | 1 ms | 8 cores |
| JSON API, small payload, Python/Flask | 5–10 ms | 42–83 cores |
| Protobuf decode + business logic + 2 RPCs | 8 ms | **67 cores** |
| Template render or heavy serialisation | 30 ms | 250 cores |
| Image resize | 200 ms | 1,667 cores |

Worked: `5,000 × 0.008 / 0.6 = 66.7` → **~67 cores ≈ 9 boxes of 8 vCPU, so 12 for headroom and AZ
spread.** Say the box count, not just the core count — box count is what an on-call engineer thinks in.

### 5.2 Why utilisation must stay below ~70%

Queueing theory, one formula: for an M/M/1 queue the time in system is `S / (1 - ρ)` where `S` is
service time and `ρ` is utilisation.

| Utilisation ρ | Latency multiplier `1/(1-ρ)` |
|---------------|------------------------------|
| 50% | 2× |
| 70% | 3.3× |
| 80% | 5× |
| 90% | 10× |
| 95% | 20× |
| 99% | 100× |

**The quotable version:** "Above about 70% utilisation, latency stops being linear in load. I size for
60–70% steady-state so a 30% traffic spike costs latency instead of an outage." This one sentence is
worth more than any storage estimate you will do in the round.

### 5.3 Little's Law — concurrency from rate and latency

```
concurrency = arrival_rate × latency
```

At 2,000 rps with 150 ms latency you have **300 requests in flight** at any instant. Consequences you
can state immediately:

- You need ≥300 concurrent workers/threads/coroutines, plus headroom, or you queue.
- You need ≥300 connections available across your database pools, or you queue on connections instead.
- If latency doubles under stress to 300 ms, in-flight doubles to 600 — this is how a slow dependency
  exhausts a pool and takes down an unrelated endpoint. See
  [third-party-failure-modes.md](third-party-failure-modes.md).

### 5.4 Python-specific arithmetic (Lyft's primary backend language)

- One CPython process holds the **GIL**: one core of Python bytecode per process, regardless of threads.
  Threads still help for I/O-bound work because the GIL is released during I/O.
- Sizing rule of thumb for sync WSGI (gunicorn/Flask): `workers ≈ 2 × cores + 1`, each worker handling
  one request at a time. At 8 ms CPU + 100 ms I/O per request, one *sync* worker does ~9 rps, so
  5,000 rps needs ~550 worker processes — clearly wrong. That arithmetic is exactly why the answer is
  **async workers or Go for high-concurrency I/O-bound services**, and being able to derive it live is
  a much better answer than asserting it.
- With async (asyncio/gevent), concurrency per process is bounded by CPU: `rps_per_process ≈ 1 /
  cpu_seconds_per_request × 0.7`. At 8 ms CPU that is ~87 rps per process, so 5,000 rps ≈ 58 processes.
- Memory per Python process: 50–150 MB baseline plus your data. 58 processes at 100 MB is ~6 GB before
  any caching, which affects your instance-type choice.

---

## 6 · Memory sizing

### 6.1 Cache sizing

```
cache_bytes = entries × (key_bytes + value_bytes + per_entry_overhead)
```

| Structure | Per-entry overhead |
|-----------|--------------------|
| Redis string key | ~50–100 bytes (key object, expiry, dict entry) |
| Redis hash field (small hash, ziplist-encoded) | ~10–20 bytes |
| Redis sorted-set member | ~60–100 bytes (skiplist node + hash entry) |
| Python dict entry | ~100 bytes + the objects themselves |
| Go map entry | ~50 bytes + key/value |
| Java HashMap entry | ~48–64 bytes + boxing |

Worked: cache the last-50-messages page for the 5 M most active conversations, ~400 bytes each.

```
5 × 10^6 × (400 + 100) = 2.5 × 10^9 = 2.5 GB
```

**Conclusion:** fits in one Redis node with room; the design question is not capacity but **invalidation
and stampede**. If it had come out at 250 GB, the answer would flip to "cache only the hot tail — size
the working set from the hit-rate curve, not from the total key count."

**Working-set logic.** You almost never cache everything. Estimate: what fraction of keys serve what
fraction of reads? A typical 80/20 gives you 80% hit rate for 20% of the data. Say the hit rate you are
assuming and what it buys: at 1,200 read QPS and an 80% hit rate the database sees 240 QPS instead of
1,200 — a 5x reduction, which is the actual justification for the cache.

### 6.2 Connection memory (the WebSocket probe)

| Per-connection cost | Typical |
|---------------------|---------|
| Kernel socket buffers (send + recv, tunable) | 8–64 KB |
| TLS session state | ~10–20 KB |
| Application per-connection object + send queue | 5–50 KB |
| **Practical total** | **~50 KB** |

| Connections per node | Memory |
|---------------------|--------|
| 100k @ 10 KB (tuned buffers, no TLS termination here) | 1 GB |
| 100k @ 50 KB | 5 GB |
| 200k @ 50 KB | 10 GB |

Also bound by file descriptors (`ulimit -n`, `fs.file-max`), ephemeral ports on the *outbound* side,
and the accept/epoll loop's ability to wake. **Say the binding constraint**: "at 50 KB each, a 64 GB
node is memory-bound around 1 M connections in theory, but I would cap at 100–200k per node so that
losing one node reconnects a survivable number of clients at once."

### 6.3 Index sizing

```
index_bytes ≈ rows × (key_bytes + pointer_bytes ≈ 8–16) × ~1.4 (B-tree fill factor + internal nodes)
```

100 M rows with a 16-byte key: `100e6 × 32 × 1.4 ≈ 4.5 GB`. Compare that with RAM: if the index fits in
memory, lookups are ~100 µs; if it does not, each lookup adds an SSD read at ~100 µs per level and the
p99 falls off a cliff. **"Does the index fit in RAM" is one of the highest-leverage questions you can
ask about a database in a design round.**

### 6.4 Bloom filter sizing

```
bits = -n × ln(p) / (ln 2)^2          hashes k = (bits/n) × ln 2
```

| False-positive rate | Bits per element | 1 B elements | 10 B elements |
|---------------------|------------------|--------------|---------------|
| 10% | 4.8 | 0.6 GB | 6 GB |
| 1% | 9.6 (**~10, remember this**) | 1.2 GB | 12 GB |
| 0.1% | 14.4 | 1.8 GB | 18 GB |

**Remember one number: 1% false positives costs about 10 bits per element.** Everything else scales
from it. Used in [distributed-web-crawler.md](distributed-web-crawler.md) for the URL-seen set.

---

## 7 · Network and bandwidth

```
bytes/s = QPS × payload_bytes        Gbps = bytes/s × 8 / 10^9
```

| Scenario | Math | Result |
|----------|------|--------|
| 1,200 read QPS × 20 KB page | 24 MB/s | 0.2 Gbps — trivial |
| Crawler at 1,000 pages/s × 100 KB | 100 MB/s | 0.8 Gbps — one NIC, but check egress cost |
| 100k WebSockets, 1 msg/min, 200 B | 333 B/s aggregate | negligible payload; the cost is connections, not bytes |
| Video call, 100k users @ 1.5 Mbps | 150 Gbps | Do not build this yourself |

Two things people forget: **cross-AZ and cross-region traffic is billed**, and **fan-out multiplies
egress**. A 200-byte message to a 500-member group is 100 KB of egress per send.

---

## 8 · Worked example — sizing the support-chat platform end to end

Assumptions stated up front (and written on the canvas):

```
2M DAU · 10% start a support conversation/day · 20 messages/conversation
30% of conversations have a human agent, 70% are agent-assisted
3x peak factor · 500 bytes/message · 90-day hot retention, 7-year cold
```

| Quantity | Derivation | Answer | Design consequence |
|----------|------------|--------|--------------------|
| Conversations/day | 2e6 × 0.1 | 200k | |
| Messages/day | 200k × 20 | 4 M | |
| Avg write QPS | 4e6 / 1e5 | 40/s | Single Postgres would do; do not shard |
| Peak write QPS | ×3 | 120/s | |
| Peak read QPS | ×10 read:write | 1,200/s | Cache the last page; 80% hit rate → 240/s to the store |
| Hot storage | 4e6 × 500 B × 90 d × 3 | 540 GB | One node; no tiering needed for hot |
| 1-year storage | 4e6 × 500 B × 365 × 3 | 2.2 TB | Cold tier to S3 after 90 days |
| Concurrent sockets, active chats | 200k × 900 s / 1e5 = 2.1k avg, ×3 peak | ~6k | Tiny |
| Concurrent sockets, idle app sessions | 2.5% of 2 M DAU online at once | ~50k | **One gateway node could hold this** — so 3 nodes for AZ spread and failure headroom, not for capacity |
| Gateway memory | 50k × 50 KB | 2.5 GB | Trivial; the constraint is reconnect storms, not RAM |
| App cores | 1,200 QPS × 8 ms CPU / 0.6 | 16 cores | 3 boxes of 8 vCPU |
| Fan-out rate | 120 writes/s × ~3 recipients (rider, agent, supervisor view) | 360 pushes/s | No fan-out service needed |

**The conclusion that scores points:** every number here is small. The honest design is a Postgres or
DynamoDB table, a small stateless API tier, a modest gateway tier, and Redis for the connection
registry and hot pages. Reaching for Kafka, sharded Cassandra, or a multi-region active-active topology
at 120 writes/s is over-engineering, and saying so is a stronger signal than being able to draw it.

**Where the numbers do get big**, and therefore where the design effort belongs:

- **Concurrent connections during an incident.** A fleet-wide outage means everyone opens support at
  once. 10x on session starts is a reconnect and admission-control problem, not a storage problem.
- **LLM agent latency and cost.** Lyft runs **7 production agents at ~270k interactions/month** — which
  is **0.1 requests/second on average**, or under 0.5/s concentrated in business hours. The load is
  nothing; the budget is **latency and token cost per interaction**, plus the fact that a model call is
  a slow third-party dependency on the critical path. Size *that*: at 3 s per model call and 0.5 rps,
  Little's Law gives 1.5 concurrent calls — so the design question is per-call timeout, retry policy,
  and fallback to a human, not throughput.
- **Search over history.** Full-text across 7 years of messages is where index size and cost live.

---

## 9 · Sanity checks and common mistakes

| Mistake | Guard |
|---------|-------|
| Off by 10^3 | Re-derive with exponents only: `4e6 / 1e5 = 4e1` |
| Bits vs bytes | Network is bits, storage is bytes. `× 8` between them |
| Confusing CPU time with latency | Cores come from CPU time; concurrency comes from latency |
| Forgetting replication ×3 | Storage answers should almost always be multiplied |
| Forgetting peak | Capacity is sized on peak, cost is estimated on average |
| Sizing on total keys rather than working set | Caches hold the hot tail |
| Quoting a p99 you never derived | Say "I would target" rather than inventing a measurement |
| Multiplying two peak factors | Diurnal peak already is your 3x |
| Ignoring that a number is *small* | The most valuable estimate is often "this is trivially small" |

**The final sanity check, always:** "Does this fit on one machine?" If yes, say so and simplify the
design. A surprising number of interview systems fit on one machine plus a replica, and noticing that
is a senior-plus instinct.

---

## 10 · Drill set

Do these against a stopwatch; target 60 seconds each, spoken aloud.

| # | Question | Answer |
|---|----------|--------|
| 1 | 1 M requests/day in QPS | ~12 QPS |
| 2 | 10k QPS × 2 KB response, in Gbps | 20 MB/s = 0.16 Gbps |
| 3 | Cores for 20k QPS at 3 ms CPU, 70% util | 20,000 × 0.003 / 0.7 ≈ 86 cores ≈ 11 × 8-vCPU boxes |
| 4 | Memory for 50 M cache entries, 200 B values | 50e6 × 300 ≈ 15 GB |
| 5 | Storage for 500 M photos at 2 MB, RF 3 | 500e6 × 2e6 × 3 = 3 PB |
| 6 | Bloom filter for 1 B URLs at 1% | ~10 bits each ≈ 1.2 GB |
| 7 | In-flight requests at 5k rps, 80 ms | 400 |
| 8 | Latency multiplier at 90% utilisation | 10× |
| 9 | 3 sequential RPCs in one datacentre, minimum latency | ~1.5 ms plus work |
| 10 | 20 dependencies at 99.9% each, serial | 0.999^20 ≈ 98% — two orders worse than each part |
| 11 | 270k interactions/month in QPS | ~0.1/s |
| 12 | 100k WebSockets at 50 KB | 5 GB |

---

## 11 · Cross-references

- [design-round-protocol.md](design-round-protocol.md) — where in the 60 minutes this happens.
- [Algorithmic Complexity](../08-algorithms-and-data-structures/Algorithmic_Complexity.md) — the
  asymptotic side of the same instinct.
- [High-Throughput, Low-Latency Systems](../07-messaging-and-streaming/Messaging-high_throughput_low_latency_systems_expanded.md)
  — batching, locality, and where throughput actually goes.
- [Key-Value Stores](../06-databases-and-distributed-data/KeyValue_Stores.md) — Redis internals behind
  the per-entry overhead numbers.
- [Indexing & Query Optimisation](../06-databases-and-distributed-data/Indexing_Optim.md) — index size
  and the fit-in-RAM question.
- [Load Testing](../12-testing/Testing-load_testing.md) — how you would replace the estimate with a
  measurement.

---

## Interview questions

**1. How much memory does a cache holding 5 million 400-byte entries need?** **[Reported at Lyft]**
Payload plus overhead: about 500 bytes each including the key object and expiry metadata, so 2.5 GB.
That fits on a single node, so capacity is not the issue — invalidation and stampede protection are.
If the working set were 100x that, I would cache only the hot tail and size from the hit-rate curve.

**2. How many cores does a service handling 5,000 QPS need?** **[Reported at Lyft]**
Cores equal QPS times CPU seconds per request divided by target utilisation. At 8 ms of CPU and 60%
utilisation that is 5,000 × 0.008 / 0.6 ≈ 67 cores, roughly nine 8-vCPU boxes, so I would run twelve
for AZ spread and headroom. The key subtlety is that CPU time is not latency — waiting on a database
costs no core.

**3. Why 60–70% target utilisation rather than 90%?**
Because queueing latency scales as 1/(1-ρ). At 70% utilisation the latency multiplier is about 3.3x
service time; at 90% it is 10x and at 95% it is 20x. Running hot means a modest traffic spike converts
directly into an SLO breach, so the headroom is buying tail latency, not idle machines.

**4. Estimate storage for a chat system with 4 million messages a day.**
About 500 bytes a message is 2 GB a day raw, 730 GB a year, roughly 2.2 TB with replication factor 3
and closer to 3 TB with index overhead. That fits on one machine, so the design question is retention
policy and cold tiering, not capacity.

**5. How many WebSocket connections fit on one node?**
Around 50 KB per connection once you count socket buffers, TLS state, and the application object, so
100k connections is about 5 GB and a 64 GB box is not memory-bound. In practice I cap well below the
theoretical limit — 100–200k — because the real constraint is how many clients reconnect simultaneously
when that node dies.

**6. Your product does 270,000 interactions a month. What does that tell you?**
That it is about 0.1 requests per second, well under one per second even concentrated into business
hours. Throughput is irrelevant at that scale, so the engineering should go into latency per
interaction, correctness, and failure handling. Proposing Kafka and sharded storage for that load would
make the design worse.

**7. How do you size a bloom filter?**
Ten bits per element for a 1% false-positive rate, with about seven hash functions; that is the anchor
I remember. A billion URLs is therefore roughly 1.2 GB. Tripling the bits gets you to 0.1%. I also
check the direction of the error: for a crawler's seen-set a false positive means skipping a page,
which is acceptable, while a false negative is impossible — that asymmetry is what makes it safe.

**8. A service takes 150 ms per request at 2,000 rps. How many concurrent requests are in flight?**
Little's Law: 2,000 × 0.15 = 300. So I need at least 300 concurrent execution slots and 300 available
connections across the pools. If a dependency slows and latency doubles, in-flight doubles too — which
is exactly how one slow dependency exhausts a shared pool and takes out unrelated endpoints.

**9. How do you do this math out loud without stalling?**
Assumption, arithmetic, answer, conclusion. One significant figure, everything in powers of ten,
86,400 rounded to 10^5. Then I always finish with the design consequence — "so storage is not the
bottleneck, the fan-out is" — because a number with no decision attached has not earned its time.

**10. When is the right answer "this is too small to matter"?**
Very often, and saying it is a positive signal. If the peak is 120 writes a second, one Postgres
primary handles it with two orders of magnitude of headroom, and adding a streaming platform buys
complexity and operational cost for no benefit. I would say that explicitly and spend the remaining
time on correctness and failure behaviour instead.
