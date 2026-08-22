# Metrics, Logs and Traces

> **Priority:** Required
> **Est. time:** 60 min
> **Track:** Server
> **HelloInterview:** none

The "three pillars" framing is over-used and slightly wrong — they are three *encodings* of the same
underlying events, chosen for different cost and query characteristics. What matters in an interview is
knowing which one answers which question, what each costs, and the specific failure mode that kills each
system at scale.

---

## 1 · The three signals and what each answers

| Signal | Shape | Answers | Cost driver | Retention typical |
|--------|-------|---------|-------------|-------------------|
| **Metrics** | Numeric time series, pre-aggregated at fixed intervals | *Is something wrong? How much? Since when? Is it getting worse?* | Number of active time series | 13–15 months at reduced resolution |
| **Logs** | Discrete timestamped records with arbitrary fields | *What exactly happened in this specific request?* | Bytes ingested and indexed | 7–30 days hot, longer cold |
| **Traces** | Causally linked spans across process boundaries | *Where did the time go? Which hop failed? What was the call structure?* | Spans ingested = traffic × spans per request | 3–14 days |

Two signals that belong in the list and usually get left out:

| Signal | Shape | Answers |
|--------|-------|---------|
| **Change events** | Deploys, config changes, feature-flag flips, infra changes | *What changed just before this started?* — statistically the highest-yield question in any incident |
| **Continuous profiles** | Sampled stacks with CPU/allocation attribution | *Which code is burning the CPU or allocating?* — the gap between "this service is slow" and a line number |

If a team has metrics, logs and traces but no deploy markers on their dashboards, fixing that is a
one-afternoon change with a larger MTTR impact than most instrumentation work.

### 1.1 The routing table

| Question | Right tool | Wrong tool and why |
|----------|-----------|-------------------|
| Is the service healthy right now? | Metrics | Logs — too slow, too expensive to aggregate |
| Did the p99 regress after the 14:05 deploy? | Metrics + change events | Traces — sampled, so not a reliable comparison of aggregates |
| Why is *this* customer's request failing? | Logs (or a trace, if sampled in) | Metrics — the customer ID must not be a metric label |
| Which of the 9 downstream calls made this slow? | Traces | Metrics — per-service latency does not tell you the critical path |
| How many times did this happen today? | Metrics | Traces — sampling makes counts wrong |
| What was the exact payload we rejected? | Logs | Metrics, traces — neither should carry payloads |
| Is this one bad host or the whole fleet? | Metrics, sliced by instance | Logs — you will grep for an hour |
| Did the retry logic amplify the load? | Traces | Metrics — you see the load, not the causal structure |

---

## 2 · Where each signal is the wrong tool

**Metrics are wrong for**: anything per-entity (per user, per request, per tenant when tenants are
numerous), rare events (a metric that is zero 99.99% of the time buys you nothing over a log), anything
where you need the exact value rather than the aggregate, and anything you might want to slice by a
dimension you have not thought of yet. Metrics require you to decide your questions in advance.

**Logs are wrong for**: alerting at scale (log-derived alerts are slow, expensive, and break when the log
format changes), computing percentiles (you are paying to store and scan every event to compute something
a histogram gives you for free), and long-term trend analysis (nobody keeps a year of raw logs). The
classic expensive mistake is a dashboard whose panels are all log queries: it works at 10 req/s and
costs five figures a month at 10,000 req/s.

**Traces are wrong for**: exact counts and anything billing-related (sampling), detecting rare failures
under head sampling (a 1-in-100,000 failure at 1% sampling is invisible), and single-process performance
work at instruction granularity (that is profiling).

The single most common architecture mistake is **using logs as a metrics system**. It is seductive because
logs are already there and the query language is expressive. It is fatal because cost scales linearly with
traffic and the query is a full scan. The correction is: for anything you would put on a dashboard or an
alert, emit a metric; keep the log for the drill-down.

---

## 3 · Cardinality: the thing that kills metrics systems

### 3.1 The arithmetic

Cardinality is the number of distinct time series, and it is the **product** of the distinct values of
every label:

```
http_requests_total{service, endpoint, method, status, region}

  1 service × 50 endpoints × 4 methods × 8 statuses × 3 regions  =  4,800 series
```

Fine. Now someone adds `customer_id`, because it seemed useful:

```
  4,800 × 100,000 customers  =  480,000,000 series
```

That is not a bigger bill; that is a metrics backend that does not exist. And the label was added in a
one-line pull request with no obvious signal that anything was wrong until the ingester OOMed.

Rough memory model: an active series in a Prometheus-style head block costs on the order of a few
kilobytes once you count the label index and the in-memory chunk. So:

| Active series | Rough head memory | Verdict |
|---------------|-------------------|---------|
| 10,000 | tens of MB | Trivial |
| 1,000,000 | several GB | A real but manageable Prometheus |
| 10,000,000 | tens of GB | Needs sharding / a purpose-built backend |
| 480,000,000 | — | Not a thing on any single node |

The cost is **per active series, essentially independent of how often the series is written**. A series
scraped every 15 seconds and a series scraped every 60 seconds cost nearly the same in index; only the
sample volume differs. This is why cardinality, not request volume, is the metrics cost driver.

### 3.2 The label denylist

Never use as a metric label:

| Label | Why |
|-------|-----|
| `user_id`, `customer_id`, `account_id` | Unbounded, grows with your business |
| `request_id`, `trace_id`, `session_id` | Unique per event — one series per request |
| Raw URL path (`/rides/9f2a-...`) | Unbounded. Normalise to the route template `/rides/{id}` |
| Error message string | Unbounded, and it changes when someone edits a string literal |
| Timestamps, dates | Unbounded and already the x-axis |
| `pod_name`, `container_id`, `instance_id` in an autoscaled or frequently-deployed environment | **Churn** |
| Full SQL query text | Unbounded. Normalise to a statement digest |
| Email addresses, phone numbers, anything personal | Unbounded *and* a data-protection incident |

### 3.3 Churn is the hidden half

Churn is the rate at which series are created and destroyed. It is separate from, and often worse than,
raw cardinality, because dead series still occupy the index for the retention period and still cost memory
in the head block.

The canonical churn generator is a `pod` label in Kubernetes. If you have 200 pods and deploy 20 times a
day, you create 4,000 new series *per metric name per day* — and the pods that died this morning are still
in the index. Add a horizontal autoscaler and it gets worse.

Rule: **labels should identify things that are stable and things you would actually group by.**
`service`, `version`, `region`, `az`, `route`, `status_class` are stable. `pod` is not, and you almost
never want to group by it — you want to *find the outlier pod*, which you can do from a small number of
per-pod series that only exist for the metrics where per-pod granularity is genuinely needed
(saturation, restarts), not for every business counter.

### 3.4 Controlling it

- **Normalise before labelling.** Route templates, status *classes* (`2xx`/`4xx`/`5xx`) alongside — not
  instead of — the exact code where you need it, error *types* rather than error messages.
- **Allowlist label values.** If `error_type` can take any string a developer invents, map unknown values
  to `other`. This bounds the damage from a future pull request.
- **Use histograms rather than one gauge per entity.** Instead of `queue_age{queue_id=...}` for 50,000
  queues, emit a histogram of queue ages plus a top-N list computed elsewhere.
- **Push the high-cardinality dimension into traces or logs, and link.** This is what **exemplars** are
  for: a Prometheus histogram bucket sample can carry a trace ID, so a graph point at the top of the p99
  is clickable through to an actual slow trace. That is the correct division of labour — the metric is
  low-cardinality and cheap, the example is high-cardinality and sampled.
- **Monitor your own cardinality.** Alert on series count per metric name and on ingestion churn rate.
  Publish the top 20 metrics by series count monthly. Teams fix what they can see.
- **Enforce at ingest.** A relabelling rule or an ingest-time limit that drops or truncates offending
  labels is the only control that survives contact with a large organisation.

Note the contrast with **wide events** (§4.2) and columnar observability backends: those systems
deliberately accept high cardinality because they store raw events columnar rather than pre-aggregating
into series. If your backend is a time-series database, cardinality is your enemy; if it is a columnar
event store, it is the feature you are paying for. Know which one you have.

---

## 4 · Structured logging

### 4.1 Objects, not sentences

```
# Bad: unparseable, un-aggregatable, breaks when someone edits the string.
2026-08-22 14:05:03 ERROR Failed to charge user 8813 for ride 4471: card declined

# Good: every field is queryable, the message is a stable event name.
{"ts":"2026-08-22T14:05:03.221Z","level":"error","event":"payment.charge_failed",
 "service":"payments","version":"a91f3c2","env":"prod","region":"eu-central-1",
 "trace_id":"4bf92f3577b34da6a3ce929d0e0e4736","span_id":"00f067aa0ba902b7",
 "user_id":"8813","ride_id":"4471","reason":"card_declined","provider":"stripe",
 "attempt":2,"duration_ms":412}
```

Mandatory fields on every line, injected by the logging setup rather than by hand:
`ts`, `level`, `service`, `version`, `env`, `region`, `trace_id`, `span_id`.
The `trace_id` is what makes logs and traces a single system rather than two silos — it turns
"find the logs for this slow trace" from a timestamp-and-grep exercise into a filter.

Use a stable `event` name (a short dotted identifier) as the primary grouping key, and put the variable
parts in fields. Then "how often does `payment.charge_failed` happen, broken down by `reason`" is a query
rather than a regular expression that breaks next sprint.

### 4.2 The canonical log line (wide events)

Instead of scattering fifteen `logger.debug` calls through a request path, accumulate a single structured
event per unit of work and emit it once at the end:

```
{"event":"http.request","route":"/v1/rides","method":"POST","status":200,
 "duration_ms":184,"db_queries":3,"db_ms":22,"cache_hits":2,"cache_misses":1,
 "downstream_calls":4,"downstream_ms":97,"retries":1,"user_tier":"plus",
 "experiment_bucket":"B","trace_id":"...","version":"a91f3c2"}
```

Why this is better:

- **One record per request** instead of fifteen — an order of magnitude cheaper to ingest and store.
- **Joinable in one query.** "Show me requests slower than 1 s where `retries > 0` and
  `experiment_bucket = B`" is a single filter, not a correlation across fifteen line types.
- **High cardinality is fine here.** Fields on a log event cost bytes, not series. `user_id` is welcome
  in a log and forbidden in a metric label. That asymmetry is the core insight.
- It is the natural bridge to columnar observability tooling, where wide events are the primary data model.

Keep a small number of narrow logs for genuinely exceptional detail (stack traces, rejected payloads,
state machine transitions), but make the wide event the default.

### 4.3 Levels, discipline, and hygiene

| Level | Meaning | Test |
|-------|---------|------|
| ERROR | Something failed that a human should eventually look at | If nobody would ever act on it, it is not an ERROR |
| WARN | Handled, but anomalous — a retry succeeded, a fallback fired, a deprecated path was used | If it happens 10,000 times an hour it is a metric, not a WARN |
| INFO | Business-meaningful events; the default production level | The canonical log line lives here |
| DEBUG | Developer detail | Off in production, switchable per-logger at runtime without a deploy |

Two operational requirements:

- **Runtime log-level control per logger**, changeable without a redeploy. During an incident you want
  DEBUG for one module on three hosts for ten minutes, not a rollout.
- **Redaction in the logging library, not in the reviewer's head.** A field allowlist or a redacting
  formatter that masks tokens, card numbers, auth headers, and configured PII fields. For a team operating
  in the EU, this is a GDPR control, not a nicety: log retention is data retention, and "we accidentally
  logged the full request body" is a reportable incident. Related: `../11-security/Security-threats.md`.

---

## 5 · Sampling

### 5.1 Where the decision is made

| Strategy | Decision point | Pros | Cons |
|----------|---------------|------|------|
| **Head sampling** | At the root span, before the work happens; the decision propagates | Trivially cheap; every service agrees; no buffering | You cannot sample on the outcome — errors and slow requests are dropped at the same rate as everything else |
| **Tail sampling** | After the trace completes, in a collector that buffered all its spans | Keep 100% of errors and slow traces, 1% of the boring ones | The collector must buffer spans until the trace is complete; needs all spans of a trace routed to the same collector instance; memory-hungry |
| **Adaptive / per-route** | Per route or per operation, rates adjusted to a target volume | Rare routes stay visible; hot routes stop dominating | More moving parts; rates must be recorded to correct counts |

The usual production answer is a hybrid: head-sample at a low base rate to control volume, force-keep
anything already known to be interesting at the root (error responses, requests from an internal debug
header, a specific tenant under investigation), and add tail sampling in the collector for
outcome-based policies.

### 5.2 Consistency is non-negotiable

If each service samples independently, you get *fragments* — a root span with no children, orphan spans
whose parents were dropped. Useless.

The fix is **consistent sampling**: the decision is a deterministic function of the trace ID
(e.g. keep if the trace ID's low bits fall below the rate threshold), taken once and propagated in the
`traceparent` sampled flag. Every service in the path independently computes or receives the same answer.
The same trick applied to logs — sample log lines by the same hash of the trace ID — means a sampled
request has *both* its trace and its logs, which is exactly what you want at 3 a.m.

### 5.3 Correcting counts from sampled data

If you count anything from sampled data, you must scale by the inverse of the rate — and you can only do
that if the rate is recorded on the event:

```
{"event":"http.request", "sample_rate": 100, ...}   # this event represents 100 requests
```

Estimated total = Σ (1 / rate) over retained events, or equivalently Σ sample_rate. Without the field you
have no way to correct after the fact, especially once rates vary per route. **Always record the rate.**

And the standing warning: **never compute an SLI from sampled data.** SLIs come from metrics, which are
not sampled. Traces and logs are for explanation, not for measurement.

---

## 6 · Distributed tracing

### 6.1 The data model

- **Span** — a named, timed operation: name, start/end timestamps, `trace_id`, `span_id`, `parent_span_id`,
  a status (ok / error), key-value **attributes**, timestamped **events** inside it, and optional **links**
  to causally-related spans in other traces.
- **Trace** — the set of spans sharing a `trace_id`, forming a DAG (usually a tree) rooted at the entry
  point.
- **Link** — used when the relationship is not parent-child in the same logical request: a Kafka consumer
  processing a message published an hour ago should *link* to the producer span, not claim it as a parent.
  Batch consumers link to many producer spans from one consume span.

### 6.2 Context propagation

The W3C Trace Context standard defines two headers:

```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
             │  │                                │                │
             │  │                                │                └─ flags (01 = sampled)
             │  │                                └─ parent span id (16 hex)
             │  └─ trace id (32 hex)
             └─ version

tracestate:  vendor1=value,vendor2=value          (vendor-specific, ordered, size-limited)
```

Plus **baggage** (`baggage: key=value,...`) for propagating application-defined values across the whole
call graph — tenant ID, experiment bucket, a "this is a test request" flag. Baggage is powerful and
dangerous: it travels on *every* hop, so it costs bytes on every request, and anything you put in it may
be forwarded to third parties. Keep it to a few small, non-sensitive keys.

Propagation carriers by transport:

| Transport | Carrier | Gotcha |
|-----------|---------|--------|
| HTTP | Request headers | A proxy or gateway that strips unknown headers silently breaks tracing |
| gRPC | Metadata | Straightforward; use the standard interceptors |
| Kafka / SQS | Message headers/attributes | Use span *links*, not parent-child, when consumption is decoupled in time |
| Async in-process | Language context (Python `contextvars`, JVM thread locals / scoped values) | Thread pools lose context unless you explicitly copy it |
| Scheduled jobs | No inbound context | Start a new root trace; add an attribute identifying the schedule |

**Service mesh note.** Envoy — which Lyft built — generates spans at the sidecar for both inbound and
outbound traffic without any application change. But the sidecar cannot connect an inbound request to the
outbound calls it caused: only the application knows that. So the application **must forward the tracing
headers** (`traceparent`, and Envoy's `x-request-id` family) from the inbound request onto its outbound
calls. If it does not, you get a pile of one-span traces that look like tracing but explain nothing. This
is a good, specific thing to know for a Lyft design round.

### 6.3 What traces show that metrics cannot

1. **Which hop consumed the latency.** Metrics tell you service A is slow and service D is slow; only a
   trace tells you that A is slow *because* it waits on D, and that B and C are irrelevant.
2. **Fan-out amplification.** One inbound request producing 340 downstream calls is invisible in
   per-service request-rate metrics (which just look busy) and glaring in a trace. N+1 query patterns are
   the classic case.
3. **Serial vs parallel structure.** Six calls at 100 ms each is 600 ms if sequential and 100 ms if
   concurrent. The metrics are identical. The trace waterfall shows it instantly, and "make these
   concurrent" is often the cheapest latency win available.
4. **Retry amplification.** Retries appear in a trace as sibling spans with the same operation name.
   Seeing three layers each retrying three times — 27 leaf calls from one user request — is a trace
   observation. See `debugging-distributed-systems.md`.
5. **The critical path.** In a fan-out, only the slowest branch matters. Optimising a branch that is not on
   the critical path is wasted work, and the trace is what tells you which one it is.
6. **Causal ordering across processes.** Which write happened before which read, across four services and
   two queues.

### 6.4 Limits and lies

- **Sampling** means the trace you want may not exist. Mitigate with tail sampling on errors/latency and a
  debug header that forces sampling for a specific request.
- **Gaps** mean missing instrumentation, not idle time. A 400 ms hole between a parent span's start and
  its first child is an uninstrumented call, a lock wait, or a GC pause — the trace shows you *that* time
  was lost, not *where*.
- **Clock skew.** Spans are timestamped by the host that produced them. With hosts a few milliseconds out
  of sync, a child span can appear to start before its parent or end after it. Never draw conclusions from
  sub-10-ms cross-host orderings; do check that NTP is healthy.
- **Span count inflation.** Auto-instrumenting every function produces thousands of spans per request,
  which costs money and makes the waterfall unreadable. Target roughly 10–50 spans per request.

---

## 7 · OpenTelemetry

### 7.1 What it actually is

OpenTelemetry (OTel) is the CNCF project that merged OpenTracing and OpenCensus. It is four things, and
conflating them causes confusion:

| Component | What it is | Why you care |
|-----------|-----------|--------------|
| **API** | Vendor-neutral interfaces you call from application code | Libraries can instrument themselves without picking a vendor |
| **SDK** | The implementation: samplers, processors, exporters, resource detection | This is what you configure |
| **OTLP** | The wire protocol (gRPC or HTTP/protobuf) for traces, metrics and logs | One protocol for all three signals |
| **Collector** | A standalone process: receivers → processors → exporters | The most valuable and most under-used piece |
| **Semantic conventions** | Standard attribute names (`http.request.method`, `db.system`, `server.address`, `error.type`) | Dashboards and alerts become portable across services and vendors |

Signal maturity differs: tracing and metrics are stable across the major SDKs; the logs signal arrived
later and is most often used via a bridge from an existing logging library rather than as a
first-class API.

### 7.2 The Collector is the point

```
  app + OTel SDK ──OTLP──┐
  app + OTel SDK ──OTLP──┤
  Envoy sidecar ─────────┼──▶ Collector (agent, per node)
  infra exporters ───────┘         │
                                   ▼
                        Collector (gateway, pool)
                          receivers → processors → exporters
                          • batching                  ├──▶ tracing backend
                          • tail sampling             ├──▶ metrics backend (Prometheus remote write)
                          • attribute redaction/PII   └──▶ log/archive backend
                          • resource attributes
                          • rate limiting
```

What this buys you, and why it is a Staff-level architectural argument rather than a tooling preference:

- **Vendor changes stop being application changes.** Switching or dual-writing to a second backend is a
  Collector config change, not a redeploy of 400 services.
- **Tail sampling has somewhere to live.** It requires buffering whole traces, which an application
  process cannot sensibly do.
- **Redaction is centralised.** One processor strips authorisation headers and PII attributes for
  everything, instead of trusting 400 services.
- **Resource attributes are injected once** — cluster, region, environment, cloud account — rather than
  configured (and mis-configured) per service.
- **It absorbs backpressure.** Exporting directly from application processes to a backend means the
  backend's slowness becomes your application's slowness.

### 7.3 Auto-instrumentation vs manual

Auto-instrumentation gives you framework spans free: inbound HTTP, outbound HTTP, database drivers, cache
clients, queue clients. That is roughly 70% of the value for near-zero effort and it should be the default.

Manual instrumentation is for the part auto-instrumentation cannot know: your *domain* operations.
"Match rider to driver", "run safety checks", "evaluate pricing" are the spans that make a trace tell a
story rather than list HTTP calls. The rule of thumb: **auto-instrument the transport, hand-instrument the
business logic.**

### 7.4 Semantic conventions matter more than they look

If every service names the same concept the same way, then one dashboard template, one alert template and
one set of SLO recording rules work for every service. If each team invents `http_status`, `status_code`,
`response_code` and `code`, nothing is reusable and every team pays the dashboard cost again. Adopting the
OTel semantic conventions is the cheapest standardisation decision available.

---

## 8 · Cost model

| | Metrics | Logs | Traces |
|---|--------|------|--------|
| **Unit of cost** | Active time series (+ samples) | Bytes ingested, indexed, retained | Spans ingested |
| **Scales with traffic?** | **No** — mostly independent | **Yes** — linearly | Yes, but sampling decouples it |
| **Scales with cardinality?** | **Yes — multiplicatively** | Only as bytes | Only as bytes |
| **Main lever** | Label discipline, series limits | Sampling, level, field pruning, tiering | Sampling rate, spans per request |
| **Failure mode when it blows up** | Ingester OOM, queries time out, whole system down for everyone | Bill shock; ingestion lag; index pressure | Collector OOM, dropped spans |
| **Blast radius** | Shared — one team's bad label breaks everyone's monitoring | Usually per-index/per-team | Usually contained |

The blast-radius row is why cardinality control needs to be a platform-enforced limit and not a guideline.

### 8.1 Napkin maths (this is a named interview probe)

A service at **1,000 req/s**, 40 instances:

**Metrics**
```
~500 series per instance × 40 instances     = 20,000 series
20,000 series × ~3 KB/series (head)          ≈ 60 MB memory
samples: 20,000 × (1/15s) × 86,400           ≈ 115 M samples/day
         at ~1.5–2 bytes/sample compressed   ≈ 200 MB/day on disk
```
Verdict: negligible. Metrics are essentially free *until* someone adds a bad label.

**Logs**
```
1,000 req/s × 1 KB/request                   = 1 MB/s
1 MB/s × 86,400                              ≈ 86 GB/day  ≈ 2.6 TB/month
```
Verdict: this is the line item on the bill. Halving the average event size or sampling successful requests
at 10% (keeping all errors) takes it to single-digit GB/day.

**Traces**
```
1,000 req/s × 20 spans/request               = 20,000 spans/s
20,000 spans/s × ~500 B/span                 = 10 MB/s  ≈ 844 GB/day unsampled
at 1% head sampling + keep-all-errors        ≈ 9–12 GB/day
```
Verdict: unsampled tracing costs ten times what logging costs; sampled tracing costs a tenth of it. The
sampling rate *is* the tracing budget.

The shape to remember: **metrics are cheap and fixed, logs are expensive and linear, traces are the most
expensive per unit and the most compressible by sampling.**

### 8.2 Retention tiering

| Tier | Age | Content | Use |
|------|-----|---------|-----|
| Hot | 0–7 days | Everything, full resolution, indexed | Incident response |
| Warm | 7–30 days | Logs sampled or partially indexed; metrics full | Postmortems, weekly analysis |
| Cold / archive | 30 days–1 year | Compressed object storage, queryable slowly | Compliance, rare forensics |
| Downsampled metrics | 1–15 months | 5-minute resolution, key series only | Capacity planning, SLO trends |

Trace retention is short by nature: a trace older than a couple of weeks is rarely useful because the code
has changed. Metric retention is long because trend and seasonality analysis needs a year.

---

## 9 · Putting it together: the drill-down path

The signals earn their cost only if they are *linked*. The path a good setup supports:

```
Burn-rate alert fires (metric)
   → SLO dashboard: which route, which region, since when (metrics)
   → deploy marker at 14:05 on the same panel (change events)
   → exemplar on the p99 histogram bucket → an actual slow trace (metric → trace)
   → trace waterfall: 80% of the time in one downstream call (trace)
   → filter logs by that trace_id → the exception and the parameters (trace → logs)
   → profile of that service over the window → the hot path (profile)
```

Each arrow is a specific integration you have to build or configure: exemplars, `trace_id` in log fields,
deploy markers on dashboards, runbook links in alert annotations. Teams that have all three signals but
none of the arrows have three silos and a long MTTR. **The arrows are the deliverable.**

Cross-links: `alert-design.md` (what to alert on), `instrumenting-python-services.md` (doing this in
Python), `debugging-distributed-systems.md` (using it under pressure),
`../14-cloud-and-infrastructure/kubernetes-debugging-playbook.md`.

---

## Interview questions

**1. When would you use a log instead of a metric, and vice versa?**
Metrics for anything aggregate — health, rates, latency distributions, anything on a dashboard or an
alert — because their cost is per time series and independent of traffic. Logs for per-event detail you
need to inspect individually, especially anything high-cardinality like a user or request ID. The failure
mode I look for is teams deriving dashboards and alerts from log queries: it works at low traffic and
becomes both slow and enormously expensive as traffic grows.

**2. What is cardinality and why does it kill metrics systems?**
Cardinality is the number of distinct time series, which is the product of the distinct values of every
label. Cost is per active series and roughly independent of scrape frequency, so adding one unbounded
label — a user ID, a raw URL with an ID in it, an error message — multiplies your series count by that
label's cardinality and can take a metrics backend from a few hundred thousand series to hundreds of
millions. The damage is shared: one team's bad label can take down monitoring for everyone, which is why
it needs an enforced ingest-time limit rather than a style guide.

**3. You need to break down errors by customer. How do you do it without exploding cardinality?**
Not with a metric label. Either put the customer ID on log events and traces and query there, or, if it
must be a metric, bound it — top-N customers by an allowlist with everything else mapped to `other`, or
bucket customers into tiers. The proper pattern is exemplars: keep the metric low-cardinality, attach a
trace ID to the histogram sample, and click through from the graph to a real request with the full
high-cardinality context on it.

**4. What does distributed tracing show you that metrics cannot?**
The causal structure of a single request: which downstream hop consumed the latency, whether calls were
serial or parallel, how much fan-out one request produced, and whether retries multiplied. Per-service
metrics can tell me that two services are slow but not that one is slow *because* it is blocked on the
other, and they cannot show that a single inbound request produced 300 downstream calls. Traces also give
me the critical path, which is what tells me that optimising a particular branch is pointless.

**5. Explain head sampling versus tail sampling.**
Head sampling decides at the root span before the work happens and propagates the decision, so it is cheap
and consistent, but it cannot sample on outcome — errors get dropped at the same rate as successes. Tail
sampling decides after the trace is complete, in a collector that buffers all the spans, so you can keep
100% of errors and slow traces and 1% of the rest — at the cost of memory and needing all spans of a trace
to reach the same collector instance. Most production setups do both: a low head rate with a force-keep
for known-interesting requests, plus tail policies in the collector.

**6. What is OpenTelemetry and what does the Collector give you?**
OTel is the vendor-neutral standard for instrumentation: an API, SDKs, the OTLP wire protocol, semantic
conventions, and the Collector. The Collector is the piece I would insist on architecturally — it is a
receiver/processor/exporter pipeline that sits between applications and backends, so changing or
dual-writing to a vendor is a config change instead of redeploying every service, tail sampling has
somewhere to live, PII redaction and resource attributes are applied centrally, and backend slowness
becomes the Collector's backpressure problem rather than the application's.

**7. Your logging bill has tripled after a traffic increase. What do you do?**
Measure first: bytes by service, by event name, and by level, because a small number of sources is usually
most of the volume. Then in order — delete debug-level logging left on in production, collapse chatty
per-step logs into one canonical wide event per request, drop or truncate large fields like payloads and
stack traces on non-errors, sample successful requests consistently by trace ID while keeping 100% of
errors and slow requests, and move anything currently being counted from logs into a metric. Finally,
tier retention rather than keeping everything hot for 30 days.

**8. How would you connect a spike on a dashboard to a specific failing request?**
Through exemplars and trace IDs. The histogram metric carries exemplars, so a point at the top of the p99
bucket links directly to a sampled trace. From the trace, the trace ID filters the logs to exactly that
request across every service it touched. That requires three integrations that are easy to skip: exemplar
support in the metrics pipeline, `trace_id` and `span_id` as fields on every log line, and deploy markers
on the dashboard so I can see what changed at that moment.

**9. Traces show a 400 ms gap in a span with no child spans. What is happening?**
Not idle time — uninstrumented time. Typical causes are a call through a library nobody instrumented, time
spent waiting on a lock or a connection-pool checkout, a garbage-collection pause, or serialisation of a
large payload. The trace has narrowed it to one process and one window, so the next step is a continuous
profile or a thread dump over that window, plus checking GC and pool-saturation metrics for that instance.
Note also that cross-host span timestamps can be a few milliseconds off from clock skew, so never read
fine-grained ordering across processes as truth.

**10. How do you decide the tracing sample rate?**
Backwards from a budget. Spans per day equals traffic times spans per request, so at 1,000 req/s and 20
spans that is roughly 844 GB/day unsampled; the sample rate is whatever divides that into the budget. But
uniform rates are the wrong shape: force-keep 100% of errors and slow traces via tail sampling, use higher
rates on low-traffic routes so they remain visible at all, and record the effective sample rate on the
event so any count derived from traces can be corrected. And never compute an SLI from sampled data — SLIs
come from metrics.
