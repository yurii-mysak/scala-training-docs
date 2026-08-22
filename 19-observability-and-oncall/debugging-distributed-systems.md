# Debugging Distributed Systems

> **Priority:** Recommended
> **Est. time:** 60 min
> **Track:** Server
> **HelloInterview:** none

This is a **method**, not a checklist of failure modes. Checklists fail on the failure you have not seen
before; a method narrows the search space regardless of what is broken. The failure modes at the end
(§6–§7) are heuristics that shortcut the method when they apply — not a substitute for it.

---

## 1 · The method

### Step 0 — Is it real, and is it ours?

Before anything else, look at the user-facing SLI. Two minutes here saves an hour of investigating a
monitoring artefact.

- Does the symptom appear in the SLI, or only in an internal metric?
- Is the metrics pipeline itself healthy? (A collector outage looks exactly like a total outage. So does a
  dashboard whose time range is wrong, or one silently pinned to a stale datasource.)
- Is a dependency's status page already reporting it?

### Step 1 — When did it start?

**The highest-value question in any investigation**, and the one most often skipped in the rush to
hypothesise. An exact start time converts an open-ended search into "what happened at 14:03?"

Zoom out to 7 days first, then 24 hours, then 1 hour. Zooming out first is what tells you whether this is
a step change, a gradual ramp, or a periodic pattern — three completely different classes of cause:

| Shape | Almost always |
|-------|--------------|
| **Step change at a specific minute** | A change: deploy, config, flag, DNS, certificate, dependency, traffic shift |
| **Gradual ramp over hours or days** | A leak, a growing dataset, a filling disk, a queue with arrival rate slightly above service rate, cache hit rate decaying |
| **Periodic** | Cron, batch job, GC, cache expiry, a scheduled partner call, traffic seasonality |
| **Correlated with traffic** | Capacity or contention |
| **Uncorrelated with traffic** | External dependency or infrastructure |

### Step 2 — What changed?

Statistically, **a change caused it.** Deploys, config changes, feature flags, infrastructure changes,
dependency deploys, data changes, traffic pattern changes, expiries (certs, tokens, credentials), and the
calendar (month end, DST transitions, a marketing campaign).

Make this cheap to answer rather than heroic:
- **Deploy markers on every dashboard.** A vertical line at each deploy. This is a one-afternoon change
  with a larger MTTR impact than most instrumentation work.
- **A change feed** — every deploy, flag flip and config change in one timestamped stream, queryable by
  time window and by service.
- **Feature-flag audit log** with who and when. Flags are the most common invisible change, because they
  do not look like deploys.
- Remember that **the change may not be yours**. A dependency deployed, a cloud provider migrated your
  instance, a partner changed a response format, a certificate rotated.

### Step 3 — Narrow by layer

Walk the request path and find the first layer where the symptom is visible. Binary search, not
exhaustive search — check the middle of the path first.

```
client → DNS → CDN/WAF → load balancer → API gateway → service mesh sidecar
       → application → connection pool → dependency → datastore → disk/network
```

At each layer ask the same question: *does the symptom exist here?* The boundary between "clean" and
"dirty" is where the problem lives. Concretely, comparing the edge's error rate with the application's own
error rate immediately separates "requests are failing inside the app" from "requests are not reaching
the app" — two completely different investigations that look identical from a user complaint.

### Step 4 — Narrow by dimension

Slice the symptom by every dimension you have. Each answer eliminates a large class of causes:

| Slice | If it is isolated to one value | If it is uniform across values |
|-------|-------------------------------|-------------------------------|
| **Instance / pod** | Bad host: disk, noisy neighbour, degraded NIC, a stuck thread, one bad restart | Not a host problem |
| **Availability zone** | Infrastructure or a cross-AZ network partition | Not infrastructure-local |
| **Region** | Regional dependency, regional config, regional deploy | Global |
| **Version** | The deploy. **Roll back now** and debug afterwards | Not the deploy |
| **Endpoint / route** | Code path specific to that route | Systemic: shared resource, pool, or infra |
| **Customer / tenant** | Data-specific: their payload, their volume, a hot shard | Not data-specific |
| **Shard / partition** | Hot key, skewed partition, one bad replica | Not partition skew |
| **Client version** | A mobile release, an SDK change, a retry-policy change on the client | Not client-driven |

Signature patterns worth memorising:

| Signature | Likely class |
|-----------|-------------|
| 100% of one endpoint, 0% of others | Code or a dependency on that path |
| ~3% of everything, evenly | One bad instance out of ~33, or one bad shard |
| One AZ only | Infrastructure or cross-AZ networking |
| Only requests with a large payload | Timeout, buffer, or serialisation limit |
| Only the newest deploy's pods | The deploy — roll back |
| Everything, at exactly the same second | Config, DNS, certificate, credential, or a shared dependency |
| Only at :00 of each hour | Cron / batch collision |
| Grows steadily and resets on restart | A leak — memory, file descriptors, connections, threads |

### Step 5 — Hypothesise predictively

State a hypothesis that **predicts a specific observation you have not yet made**, then check it. "I think
the connection pool is exhausted" is weak. "If the pool is exhausted, then pool-wait time should have
risen at 14:03, in-flight requests should be pinned at exactly the pool size, and downstream latency
should be flat" is strong — because it is falsifiable in thirty seconds and one of the three checks will
disconfirm it if it is wrong.

This discipline is what stops the classic incident failure mode of confirming a first guess for forty
minutes.

### Step 6 — Mitigate as soon as you can

The moment you have a plausible mitigation, take it — even without understanding. See
`incident-response.md` §4. Then keep debugging with the clock no longer running against you. Capture
evidence before you destroy it.

---

## 2 · Correlating deploys with regressions

The default hypothesis is "something changed", and it is right more often than any other single guess. Set
up so that testing it takes seconds:

- **Deploy markers** on the SLI dashboard, annotated with the SHA and the deployer.
- **Version as a metric label.** `http_requests_total{version="a91f3c2"}` lets you compare error rate and
  latency between the old and new version *during a rolling deploy*, which is the single most decisive
  piece of evidence available and it is free once the label exists. If the new version's pods have a 4%
  error rate and the old version's have 0%, the investigation is over.
- **`git log --since` and the change feed** for the 30 minutes before the start time.
- **Correlate, but do not assume causation blindly**: a deploy at 14:03 and a symptom at 14:05 is strong
  evidence; a deploy at 09:00 and a symptom at 14:05 usually is not — *unless* the mechanism is
  cumulative (a leak, a cache filling, a slow migration) or triggered (new code path only exercised by a
  daily batch job at 14:00). Ramps and step changes have different plausible lags.
- **Rolling deploys give you a natural A/B.** During the rollout the two populations coexist. Once the
  rollout completes, that evidence is gone — which is an argument for slower rollouts of risky changes,
  not just for canaries.

---

## 3 · Using traces to find the slow hop

### 3.1 Read the critical path, not the total

In a fan-out, only the slowest branch matters. Ten parallel calls where nine take 20 ms and one takes
900 ms is a 900 ms request, and optimising the nine is worth nothing. The trace waterfall shows this
instantly; per-service latency metrics never will.

### 3.2 What to look for, in order

| Observation | Meaning |
|-------------|---------|
| One child span dominates the parent's duration | The slow hop. Recurse into it |
| Children are sequential but independent | Parallelise — often the cheapest large latency win available |
| Large **self time**: a gap in the parent not covered by children | Uninstrumented work, lock contention, connection-pool wait, GC pause, or serialisation of a big payload |
| Many sibling spans with the same operation name | N+1 pattern, or retries. Count them |
| Span count varies wildly per request | Data-dependent fan-out — a pagination or batching bug |
| Child starts long after the parent starts | Queueing or pool wait before the call was made, not slowness in the callee |
| A downstream span is fast but the parent's view of it is slow | The time is in the network, the sidecar, serialisation, or the client library — not the server |

That last row is the one people miss and is worth calling out in an interview: **the server's own latency
metric and the client's measurement of that server disagree**, and the gap is where the interesting
problem lives. Compare client-observed and server-observed latency for the same hop; the difference is
network, proxy, queueing or connection acquisition.

### 3.3 Comparative tracing

The strongest technique: take a slow trace and a fast trace for the same operation and diff their span
trees. Different span count, an extra retry, a cache miss where the fast one had a hit, an extra hop
because a shard was rebalancing. The comparison finds things no single trace reveals, because it controls
for everything the two have in common.

---

## 4 · Tail latency and coordinated omission

### 4.1 Why the tail is the number that matters

If a user-facing request fans out to *n* backend calls and must wait for all of them, then the probability
that *none* of them lands in the slow tail is `(1 − p)ⁿ`:

```
Single call: p99 = 500 ms   (1% of calls exceed 500 ms)

n = 10  →  P(all under 500 ms) = 0.99¹⁰  = 0.904  →  ~10% of requests exceed 500 ms
n = 100 →  P(all under 500 ms) = 0.99¹⁰⁰ = 0.366  →  ~63% of requests exceed 500 ms
```

So at a fan-out of 100, **the single-call p99 becomes roughly the user-visible median.** This is the "tail
at scale" argument, and it has three consequences worth stating:

1. Improving the p99 of a backend improves the *median* of a fanned-out service. Tail work has leverage
   far beyond the 1% of requests it appears to touch.
2. Reducing fan-out is a latency optimisation in itself.
3. Hedged requests — issue to a second replica if the first has not answered by the p95, take the first
   response — cost a few percent extra load and cut the tail dramatically. Use with a budget so a
   degraded system does not double its own load.

### 4.2 Coordinated omission

A load generator that sends the next request only after receiving the previous response **stops sending
during a stall**. The requests that would have arrived during the stall are never issued, so they are
never measured, and the reported latency distribution omits exactly the worst period. Reported p99 can be
an order of magnitude better than reality.

```
Closed-loop (wrong):   send → wait → send → wait ...
                       system stalls for 5 s → generator sends nothing → 0 slow samples recorded

Open-loop (right):     requests scheduled at a fixed rate regardless of responses;
                       latency measured from the INTENDED send time, not the actual one
```

Fixes: use a constant-throughput / open-workload generator, measure from intended send time, and correct
for omission where the tool supports it. See `../12-testing/Testing-load_testing.md`.

The production equivalent is just as important: **client-side timeouts truncate the observed
distribution.** If the client times out at 2 s, the server never records anything above 2 s — the tail is
not fast, it is invisible. Always check the timeout value before believing a suspiciously clean tail, and
count timeouts as a separate first-class metric.

### 4.3 Percentiles do not average

You cannot average p99s — across shards, across instances, or across time buckets. `avg(p99)` is not a
percentile of anything. The correct approach is mergeable histograms: Prometheus histogram buckets,
HDRHistogram, or t-digest, aggregated as counts and then quantiled once at the end. This is also the
reason SLIs are defined as ratios over bucket counters rather than as percentile values — see
`slos-and-error-budgets.md` §2.1.

---

## 5 · Thundering herds, retry storms and metastable failures

### 5.1 Thundering herd

Many clients acting simultaneously because they were synchronised by a shared event.

| Trigger | Mechanism |
|---------|-----------|
| Cache stampede | A hot key expires; every request misses simultaneously and hits the origin |
| Reconnect storm | A service restarts; every client reconnects at once |
| Cron alignment | Everything scheduled at `0 * * * *` |
| Deploy | All pods restart their connections and warm their caches at once |
| Token expiry | Every client's credential expires at the same second |

Fixes: **jitter everything** (TTLs, retries, cron schedules, reconnect backoff — the single most effective
one-line fix in distributed systems); **single-flight / request coalescing** so that concurrent misses on
the same key produce one origin request; **probabilistic early expiration**, where each request has a
small chance of refreshing the value before it expires, spreading the refresh; and **staggered rollouts**.

### 5.2 Retry storms

Retries multiply load at exactly the moment the system is least able to serve it. The amplification is
multiplicative across layers:

```
Client retries 3× → Gateway retries 3× → Service retries 3×
   1 user request  →  27 requests at the datastore
```

The system is already struggling at 1×. At 27× it has no chance of recovering, and the retries themselves
now sustain the failure.

| Control | What it does |
|---------|-------------|
| **Retry budget** | Cap retries as a percentage of live requests (e.g. 10%). Envoy retry budgets and gRPC retry throttling implement this. **The most important control** — it bounds amplification globally rather than per-call |
| **Exponential backoff with full jitter** | `sleep = random(0, min(cap, base × 2^attempt))`. Full jitter, not "backoff plus a bit of jitter" — synchronised retries are the problem |
| **Retry only at one layer** | Pick the layer with the best information — usually the one closest to the caller that knows the operation is idempotent. Retrying at every layer is how you get 27× |
| **Circuit breakers** | Stop calling a dependency that is failing; fail fast; probe periodically to reopen |
| **Deadline propagation** | Pass the remaining deadline down the call chain. Never retry a request whose deadline has already passed — that work is guaranteed waste, and it is load you are adding for nothing |
| **Idempotency** | Retry only idempotent operations, or use idempotency keys. See `../15-system-design/payments_interview_prep_expanded.md` |

### 5.3 Metastable failures

A **metastable failure** is one where the system remains in a failed state *after the triggering condition
has been removed*, because a feedback loop now sustains it.

```
Trigger (a traffic spike, a slow dependency, a cold cache)
   → latency rises
      → clients time out and retry
         → load increases
            → latency rises further        ← the loop is now self-sustaining
   Trigger removed → load returns to normal → THE SYSTEM DOES NOT RECOVER
```

**The diagnostic signature: the cause is gone and the system is still down.** Traffic is back to normal
levels, the slow dependency recovered, the deploy was rolled back — and error rates stay pinned. If you
find yourself saying "but we already fixed the thing that started it", you are looking at a metastable
failure and you should stop looking for a new cause.

Common sustaining loops: retry amplification; a cache that cannot re-warm because every request is timing
out before it can populate it; a queue backlog where consumers spend all their time on work whose
deadline has already passed; GC pressure from queued request objects causing pauses that cause more
queueing; connection-pool thrash where connections are torn down and re-established faster than they can
be used.

**Breaking the loop** requires deliberately reducing load below the level the system can serve, which
feels wrong during an outage but is the only exit:

- **Shed load aggressively** — reject a large fraction of requests fast so the remainder can succeed.
- **Drain the queue**, discarding work past its deadline rather than processing it.
- **Restart with a controlled ramp**, not all at once — a simultaneous restart of everything walks
  straight back into a thundering herd and re-enters the loop.
- **Disable retries entirely** at the edge, temporarily.
- **Re-warm caches deliberately** before restoring full traffic.

**Prevention** is architectural, and this is the Staff-level answer: admission control and load shedding
*before* saturation; **bounded queues** everywhere, because an unbounded queue converts a latency problem
into a total outage; **LIFO with deadline dropping** under overload rather than FIFO — counter-intuitive,
but under overload the oldest queued requests are the ones whose clients have already given up, so serving
them is pure waste; retry budgets; and circuit breakers.

### 5.4 Little's Law — the napkin maths

```
L = λ × W          concurrency = arrival rate × latency
```

Worked: a service at 1,000 req/s with 200 ms mean latency has `1000 × 0.2 = 200` requests in flight. If
the thread pool or connection pool holds 100, half the requests are queueing before they start — and the
observed latency will be *higher* than 200 ms, which increases *L*, which increases queueing. That is the
feedback loop of §5.3 in two lines of arithmetic.

Use it in reverse to size pools, and use it during an incident: if latency doubled and throughput is
flat, in-flight count doubled, and you should check whether you have just hit a pool limit. This is
exactly the kind of live napkin maths a Lyft design round probes for.

---

## 6 · The heuristics: it is always DNS, GC, or a queue

Not literally true; true often enough to check first, because all three are cheap to rule out.

### 6.1 DNS

| Symptom | Cause |
|---------|-------|
| Intermittent failures across unrelated services, at the same moment | Resolver saturation or a DNS server problem |
| Failures that resolve themselves in exactly TTL seconds | Negative caching of a transient failure |
| A failover that never takes effect | A client library that resolved once at startup and cached the address forever — very common in JVM and in connection pools |
| High latency on the first call to a new host | Resolution latency, plus TCP and TLS handshake |
| In Kubernetes: 5× more DNS queries than expected, intermittent timeouts | `ndots: 5` in the pod's `resolv.conf`. A name with fewer than 5 dots is tried against every search domain first, so `api.example.com` produces several failed lookups before the real one — doubled by parallel A and AAAA queries |

Checks: query the resolver directly from inside the pod, compare against an external resolver, look at
CoreDNS metrics and error rates, check conntrack table usage, and use a fully-qualified name with a
trailing dot to bypass the search list. Related: `../10-networking/Networking-DNS-DHCP.md`.

### 6.2 GC and runtime pauses

Signature: latency spikes that are **periodic**, affect **all endpoints on one instance simultaneously**,
show **no corresponding downstream latency**, and correlate with memory or allocation rate rather than
with request rate.

On the JVM this is stop-the-world collection, and the candidate's existing material covers the diagnosis
in depth: `../05-jvm-internals/JVM-Garbage_Collection.md`,
`../05-jvm-internals/JVM-GC_Profiling_and_Tuning.md`, `../05-jvm-internals/JVM-PerformanceTuning.md`. The
short version: enable GC logging, look at pause distribution rather than total GC time, and distinguish
allocation-rate problems from live-set problems, because the fixes are opposite.

**Python's equivalents are different and worth knowing given the target stack**:

| Mechanism | Symptom |
|-----------|---------|
| **The GIL** | CPU-bound work in one thread blocks all others in the process. Latency spikes correlated with CPU work, not with memory. The fix is processes or native/async offload, not more threads |
| **Generational GC over a large object graph** | Periodic pauses proportional to the number of *container* objects. A large in-memory cache of Python objects is the usual culprit; `gc.freeze()` after startup and moving bulk data out of Python objects both help |
| **Reference-cycle collection** | Cycles are only reclaimed by the cyclic collector, so memory looks like a slow leak with periodic drops |
| **Copy-on-write defeat after fork** | Refcount updates dirty shared pages, so pre-fork memory is not actually shared. Memory grows with worker count more than expected |
| **Blocking the event loop (asyncio)** | One synchronous call blocks *every* concurrent request in that process. The signature is all-endpoints latency spikes on one worker, exactly like a GC pause but correlated with a specific slow call |

That last row is the most common Python production surprise and worth stating explicitly in an interview:
a single synchronous DNS lookup or file read inside an async handler stalls every in-flight request in
that worker.

### 6.3 A queue

Any buffer between a producer and a consumer, whether or not it is called a queue:

- Kafka consumer lag (`../07-messaging-and-streaming/Messaging-kafka_fundamentals.md`)
- Thread-pool work queue
- Connection-pool wait queue — **the most common invisible bottleneck**
- Kernel accept backlog / listen queue
- Sidecar and proxy buffers
- Application-level batching buffers
- Disk I/O queue depth
- Stream backpressure boundaries (`../03-akka-ecosystem/akka_streaming_and_backpressure_detailed_guide.md`)

**Measure age, not just depth.** A queue with 10,000 items whose oldest item is 200 ms old is fine. A
queue with 50 items whose oldest is 90 seconds old is broken — a stuck consumer, a poison message, or a
partition whose consumer died. Depth alone is nearly useless as a signal; **age of the oldest item** is
the metric that tells you the truth, and most teams do not emit it.

And the structural rule: **an unbounded queue converts a latency problem into an outage.** It absorbs
overload silently until every item in it is past its deadline, at which point the system is doing 100%
wasted work. Bound every queue, and decide explicitly what happens when it is full — reject, shed, or
backpressure — rather than discovering the default.

### 6.4 The rest of the usual suspects

| Suspect | Signature |
|---------|-----------|
| **Connection pools** | Latency rises with no downstream latency change; in-flight count pinned at exactly the pool size |
| **Clock skew** | Token or certificate validation failing on some hosts; traces with children starting before parents; TTL logic misbehaving |
| **Timeout misconfiguration** | The caller's timeout is shorter than the callee's, so the callee keeps working on requests nobody is waiting for — wasted capacity that grows under load. Timeouts must *decrease* down the call chain |
| **Load balancer health-check trap** | Least-connections routing sends *more* traffic to a broken instance because it fails fast and therefore has fewest connections. A "black hole" that attracts traffic |
| **TLS / certificate expiry** | Everything breaks at once, at a round timestamp, with no deploy |
| **Disk full** | Bizarre, unrelated symptoms — logging fails, temp files fail, the database refuses writes |
| **File descriptor exhaustion** | Accept failures, connection errors, gradual onset, resets on restart |
| **Noisy neighbour / degraded hardware** | One instance slow across all endpoints, CPU steal time elevated |
| **Data-dependent** | A single tenant's payload or volume; often a new large customer |

---

## 7 · A worked walkthrough

> *"p99 latency on ride creation doubled at 14:05. No error-rate change."*

1. **Confirm in the SLI.** Latency SLI dropped from 99.94% to 99.1% at 14:05. Real. Errors flat — so this
   is slowness, not failure, which rules out a large class of causes immediately.
2. **Zoom out to 7 days.** No prior occurrence, no weekly pattern. **Step change**, not a ramp → look for
   a change (§1 Step 1).
3. **Change feed for 13:45–14:10.** Two candidates: a `pricing-service` deploy at 14:03, and a feature
   flag flipped at 13:58.
4. **Slice by version.** During the rolling deploy, the new `pricing-service` pods show p99 of 900 ms; the
   old pods show 210 ms. **Decisive.**
5. **Mitigate.** Roll back. Do not wait to understand. User impact ends at 14:19.
6. **Now debug with the clock stopped.** Pull a slow trace from the window and a fast trace from before.
7. **Diff them.** The slow trace has 43 spans named `db.query`; the fast trace has 4. Classic N+1.
8. **Confirm predictively.** If it is an N+1, then database QPS should have risen ~10× at 14:05 while
   per-query latency stayed flat. Check: QPS 11×, per-query p99 unchanged. Hypothesis confirmed.
9. **Find the change.** A refactor replaced a batched fetch with a per-item lookup inside a loop.
10. **Contributing factors, by defence layer** (`incident-response.md` §6.4):
    - *Prevent* — no test asserting query count for that endpoint.
    - *Detect* — the canary stage ran for 3 minutes at 1% traffic, below the level where the p99 shift was
      visible.
    - *Mitigate* — rollback took 14 minutes because of a manual approval step; target is under 5.
    - *Reduce impact* — no per-endpoint query-count metric would have caught it in staging either.

Note what did the work: the start time, the change feed, the version slice, and the trace diff. No deep
knowledge of the pricing service was required. **That is the point of having a method.**

---

## 8 · Cross-references

| Topic | Where |
|-------|-------|
| Kubernetes-specific debugging | `../14-cloud-and-infrastructure/kubernetes-debugging-playbook.md` |
| JVM GC diagnosis | `../05-jvm-internals/JVM-Garbage_Collection.md`, `../05-jvm-internals/JVM-GC_Profiling_and_Tuning.md` |
| JVM performance tuning | `../05-jvm-internals/JVM-PerformanceTuning.md` |
| Kafka lag and consumer groups | `../07-messaging-and-streaming/Messaging-kafka_fundamentals.md` |
| Delivery guarantees, DLQs, poison messages | `../07-messaging-and-streaming/Messaging-delivery_qos_dlq_ha.md` |
| Backpressure | `../03-akka-ecosystem/akka_streaming_and_backpressure_detailed_guide.md` |
| High-throughput / low-latency design | `../07-messaging-and-streaming/Messaging-high_throughput_low_latency_systems_expanded.md` |
| DNS behaviour | `../10-networking/Networking-DNS-DHCP.md` |
| Load generation and coordinated omission | `../12-testing/Testing-load_testing.md` |
| Idempotency and retries | `../15-system-design/payments_interview_prep_expanded.md` |
| Consistency trade-offs under partition | `../06-databases-and-distributed-data/CAP_Consistency.md` |

---

## Interview questions

**1. Latency is up and you have no idea why. Walk me through your approach.**
First confirm it is real in the user-facing SLI rather than an internal metric or a broken dashboard. Then
the highest-value question: exactly when did it start — I zoom out to seven days first, because a step
change, a gradual ramp and a periodic pattern have completely different causes. A step change sends me to
the change feed for that window: deploys, flags, config, certificates, dependencies. Then I narrow by
layer, comparing edge metrics against application metrics to separate "failing inside" from "not
arriving", and by dimension — version, region, AZ, endpoint, instance, tenant — because each slice
eliminates a whole class of causes. Finally I form a hypothesis that predicts an observation I have not
made yet and check it, rather than confirming my first guess for forty minutes. And I mitigate the moment
I have a plausible mitigation, understanding afterwards.

**2. Why is "when did it start" the most valuable question?**
Because it converts an unbounded search into "what happened at 14:03", and because the *shape* of the
onset classifies the cause before you know anything else. A step change at a specific minute is almost
always a change — deploy, config, flag, certificate, dependency. A gradual ramp is a leak, a growing
dataset, or a queue whose arrival rate slightly exceeds its service rate. A periodic pattern is a cron
job, GC, or a cache expiry. Correlation with traffic points to capacity or contention; no correlation
points to an external dependency. Zooming out before zooming in is what makes that distinction visible.

**3. How do you use traces to find where latency went?**
Read the critical path rather than the total: in a fan-out only the slowest branch matters, so optimising
the fast siblings is worthless. I look for a child span dominating its parent, sequential calls that could
be parallel, and large self-time — a gap in the parent not covered by any child, which means
uninstrumented work, lock contention, connection-pool wait, or a GC pause. Then the strongest technique is
comparative: diff a slow trace against a fast one for the same operation, which surfaces the extra retry,
the cache miss, or the N+1 that no single trace reveals. I also compare client-observed against
server-observed latency for the same hop — when they disagree, the time is in the network, the proxy, or
connection acquisition, not in the callee.

**4. What is a metastable failure and how do you get out of one?**
A failure that sustains itself after the trigger is gone, because a feedback loop now keeps it going — a
spike causes latency, latency causes timeouts and retries, retries cause more load. The diagnostic
signature is that you have already removed the cause and the system is still down. Getting out requires
deliberately reducing load below what the system can serve, which feels wrong during an outage: shed load
aggressively, drain queues by discarding work whose deadline has passed, disable retries at the edge, and
restart with a controlled ramp rather than all at once so you do not walk into a thundering herd.
Prevention is architectural — admission control before saturation, bounded queues everywhere, retry
budgets, circuit breakers, and LIFO with deadline dropping under overload.

**5. How do retry storms happen and how do you prevent them?**
Retries multiply load exactly when the system is weakest, and the amplification is multiplicative across
layers — three attempts at each of three layers turns one user request into twenty-seven at the datastore.
The most important control is a retry budget that caps retries as a percentage of live requests globally,
which is what Envoy retry budgets and gRPC retry throttling do; that bounds the amplification regardless
of how many places retry. Beyond that: exponential backoff with *full* jitter, because synchronised
retries are the actual problem; retrying at only one layer, chosen for having the best information about
idempotency; deadline propagation so nobody retries a request whose deadline already expired; and circuit
breakers to stop calling a dependency that is failing.

**6. Explain coordinated omission.**
A closed-loop load generator sends the next request only after the previous response arrives, so when the
system stalls the generator stops sending — and the requests that would have arrived during the stall are
never issued and never measured. The reported distribution omits precisely the worst period, and the p99
can be an order of magnitude better than reality. The fix is an open-workload generator that schedules
requests at a fixed rate regardless of responses, with latency measured from the *intended* send time. The
production equivalent matters just as much: a client timeout truncates the observed distribution, so a
suspiciously clean tail usually means the tail is invisible rather than fast — check the timeout and count
timeouts as a separate metric.

**7. Why does a fan-out make tail latency the number that matters?**
Because if a request waits on n independent calls, the chance that none of them lands in the tail is
(1−p)ⁿ. At a fan-out of ten, roughly 10% of requests exceed the single-call p99; at a hundred, about 63%
do — so the backend's p99 becomes the user's median. Three consequences follow: tail work has leverage
far beyond the 1% of calls it appears to touch, reducing fan-out is itself a latency optimisation, and
hedged requests — issue to a second replica if the first has not answered by the p95 — buy a large tail
improvement for a few percent of extra load, provided you budget them so a degraded system does not
double its own traffic.

**8. Someone shows you a dashboard averaging p99 across ten instances. What do you say?**
That the number is meaningless — percentiles do not average. The average of ten p99s is not a percentile
of anything, and it will systematically understate the real tail. The correct approach is mergeable
histograms: sum the bucket counters across instances and compute the quantile once at the end, which is
what Prometheus histograms, HDRHistogram and t-digest exist for. This is the same reason SLIs are defined
as a ratio of requests under a threshold rather than as a percentile value — ratios compose across shards
and across time windows, and percentiles do not.

**9. "It's always DNS." What do you actually check?**
Whether failures are intermittent across unrelated services at the same moment, which points at resolver
saturation rather than any one service; whether failures resolve in exactly TTL seconds, which points at
negative caching; and whether a failover never took effect, which usually means a client library resolved
once at startup and cached the address forever. In Kubernetes specifically I check `ndots: 5` — a name
with fewer than five dots is tried against every search domain first, so one external lookup becomes
several failed queries, doubled by parallel A and AAAA lookups, which both inflates latency and can
saturate CoreDNS. Practically: query the resolver from inside the pod, compare with an external resolver,
check CoreDNS error rates and conntrack usage, and test with a fully-qualified trailing-dot name.

**10. How would you approach a web application with many third-party dependencies that fail in various ways? [Reported at Lyft]**
I would start by classifying each dependency on two axes: is it on the critical path, and what does
failure look like — hard error, slow, wrong data, or partial. That classification determines the defence.
Everything gets a timeout shorter than my caller's timeout, a circuit breaker, and a bounded concurrency
allocation so one slow dependency cannot consume the whole thread or connection pool — bulkheading is what
stops one bad partner taking down the page. Non-critical dependencies get a fallback: cached, stale, or
degraded-but-present, so their failure changes the page rather than breaking it. Retries only where the
operation is idempotent, with full jitter and a retry budget. And I would measure each dependency
separately with its own SLI, because the composition arithmetic tells me my achievable availability
ceiling and therefore which dependency is actually worth engineering around.

**11. A queue has 50,000 messages. Is that a problem?**
By itself, no — depth alone is nearly useless. The metric that matters is the age of the oldest unprocessed
item: 50,000 items with the oldest at 200 milliseconds is a healthy high-throughput queue, while 50 items
with the oldest at 90 seconds means a stuck consumer, a poison message, or a partition whose consumer
died. I would also check whether depth is stable, growing or shrinking, because a stable large depth is a
capacity decision while a growing one is arrival rate exceeding service rate and has a predictable time to
disaster. The structural point is that an unbounded queue converts a latency problem into an outage: it
absorbs overload silently until everything in it is past its deadline and the system is doing entirely
wasted work.

**12. How would you use Little's Law during an incident?**
Concurrency equals arrival rate times latency, so at 1,000 requests per second with 200 ms latency there
are 200 requests in flight. If the thread or connection pool is 100, half of them are queueing before they
even start — and the queueing raises observed latency, which raises in-flight count, which is the feedback
loop behind metastable failure written as arithmetic. During an incident I use it as a consistency check:
if latency doubled while throughput stayed flat, in-flight count doubled, so I go look at whether we just
hit a pool ceiling. I use it in reverse for sizing — pick the target latency and throughput, and that
gives the minimum pool size with headroom.
