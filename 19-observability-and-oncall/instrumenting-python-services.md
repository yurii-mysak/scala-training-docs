# Instrumenting Python Services

> **Priority:** Recommended
> **Est. time:** 60 min
> **Track:** Server
> **HelloInterview:** none

Practical instrumentation for a Python service, ending with the part that matters most for the target
team: what to measure in an LLM-agent pipeline. Doubles as Python practice — the SDK-shaped code here is
worth typing out rather than reading, since Python fluency is a separate gap.

> **Note on runnable code.** The OpenTelemetry SDK is a set of pip packages and cannot be installed in
> this repo's offline setup, so the OTel snippets below are **illustrative** — correct in shape, not
> executable here. The one block marked **runnable** (§9) is standard library only and works with
> `python3 file.py` on a bare interpreter.

---

## 1 · The mental model before the API

Three objects, and everything else is configuration:

| Concept | What it is | Lifetime |
|---------|-----------|----------|
| **Resource** | Immutable identity of *the thing producing telemetry*: `service.name`, `service.version`, `deployment.environment`, `cloud.region`, `k8s.pod.name` | Process |
| **Provider** | The factory (`TracerProvider`, `MeterProvider`) holding the resource, samplers, processors and exporters | Process, configured once at startup |
| **Span / instrument** | The individual measurement | Per operation |

Get the **Resource** right first. Every dashboard, alert and query filters on it, and a service that
reports `service.name: "unknown_service:python"` — the default when nobody set it — is invisible in a
shared backend. Set `service.name`, `service.version` (the deploy SHA), and `deployment.environment` at
minimum. Version is what lets you compare error rate and latency between old and new pods *during* a
rolling deploy, which is the single most decisive signal in a regression investigation.

---

## 2 · SDK setup

```python
# ILLUSTRATIVE — requires: opentelemetry-sdk, opentelemetry-exporter-otlp
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

resource = Resource.create({
    "service.name": "support-router",
    "service.version": os.environ["GIT_SHA"],
    "deployment.environment": os.environ["ENV"],
})

provider = TracerProvider(
    resource=resource,
    # ParentBased: honour the caller's decision; only apply the ratio at the root.
    # Without ParentBased you get broken traces — some services keep a span, others drop it.
    sampler=ParentBased(root=TraceIdRatioBased(0.05)),
)
provider.add_span_processor(
    BatchSpanProcessor(              # never SimpleSpanProcessor in production:
        OTLPSpanExporter(            # it exports synchronously on the request path
            endpoint=os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"],
        ),
        max_queue_size=2048,
        max_export_batch_size=512,
        schedule_delay_millis=5000,
    )
)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)
```

Three configuration points that are load-bearing:

- **`ParentBased`** — the sampling decision must be made once, at the root, and honoured by everyone
  downstream. A per-service independent ratio produces fragments: root spans with no children, children
  with no parents.
- **`BatchSpanProcessor`, never `SimpleSpanProcessor`** in production. The simple processor exports
  synchronously on the request path, so your p99 becomes the exporter's p99.
- **Export to a local Collector**, not directly to a vendor. See `metrics-logs-traces.md` §7.2 — the
  Collector absorbs backpressure, does tail sampling, and makes a vendor change a config change.

Most of this can also be set through environment variables (`OTEL_SERVICE_NAME`,
`OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_TRACES_SAMPLER`), which is preferable in Kubernetes because the
values differ per environment and should not be baked into the image.

---

## 3 · Auto-instrumentation first

```bash
# ILLUSTRATIVE
pip install opentelemetry-distro opentelemetry-instrumentation-flask \
            opentelemetry-instrumentation-requests opentelemetry-instrumentation-botocore
opentelemetry-bootstrap -a install          # detects installed libs, installs matching instrumentation
opentelemetry-instrument python app.py      # wraps the process, no code changes
```

Or explicitly, which is easier to reason about and to disable selectively:

```python
# ILLUSTRATIVE
FlaskInstrumentor().instrument_app(app)     # Lyft's Python APIs are Flask
RequestsInstrumentor().instrument()         # outbound HTTP, with context injected
BotocoreInstrumentor().instrument()         # AWS SDK: DynamoDB, Bedrock, SQS
Psycopg2Instrumentor().instrument()
RedisInstrumentor().instrument()
```

This gets you inbound HTTP spans, outbound HTTP with the `traceparent` header injected automatically,
database spans with statement digests, and AWS SDK spans — roughly 70% of the value for an afternoon of
work. **Do this before writing a single manual span.**

What auto-instrumentation cannot know is your *domain*. That is §4.

---

## 4 · Useful default spans

| Span | Source | Attributes worth having |
|------|--------|------------------------|
| Inbound request | Auto | route template (**not** the raw path — cardinality), method, status, user tier |
| Outbound HTTP / gRPC | Auto | target service, route, status, retry attempt number |
| Database query | Auto | statement digest, table, rows returned, whether it hit an index |
| Cache operation | Auto | hit/miss, key *prefix* (never the full key) |
| Queue publish / consume | Auto | topic, partition, lag at consume time |
| **Business operation** | **Manual** | The identifiers and outcomes that make the trace tell a story |

```python
# ILLUSTRATIVE
with tracer.start_as_current_span("ride.match") as span:
    span.set_attribute("ride.city_id", city_id)
    span.set_attribute("ride.candidate_drivers", len(candidates))
    try:
        result = matcher.match(request, candidates)
    except NoDriverAvailable as exc:
        span.set_status(Status(StatusCode.ERROR, "no driver available"))
        span.record_exception(exc)
        raise
    span.set_attribute("ride.matched", result.matched)
    span.set_attribute("ride.wait_estimate_s", result.eta_seconds)
    return result
```

**Attributes vs events vs metrics** — the distinction people get wrong:

| | Use for | Cardinality |
|---|---------|-------------|
| **Span attribute** | A property of this operation: IDs, sizes, outcomes, decisions | High cardinality is **fine and desirable** — that is the point of spans |
| **Span event** | A timestamped moment inside the span: "cache miss", "retry 2 started", "fell back to stale" | Fine |
| **Metric label** | A dimension you will group by on a dashboard | **Must be bounded.** See `metrics-logs-traces.md` §3 |

Budget roughly **10–50 spans per request**. Below that you cannot see the structure; above about 100 you
are paying for a waterfall nobody can read.

---

## 5 · Context propagation in Python

The mechanism is `contextvars`. Knowing where it breaks is the practical knowledge:

| Situation | Behaviour | Fix |
|-----------|-----------|-----|
| Normal function calls | Context flows | — |
| `asyncio.create_task()` | Context is **copied** at creation | Works |
| `await` | Context flows | Works |
| `ThreadPoolExecutor.submit()` | Context is **lost** | `ctx = contextvars.copy_context()` then `executor.submit(ctx.run, fn, *args)` |
| `threading.Thread` | Lost | Same pattern; capture the context in the parent, run inside it in the child |
| `multiprocessing` | Lost — different process | Serialise the `traceparent` and re-establish it in the child |
| Celery / SQS / Kafka | Lost — different process, later in time | Inject `traceparent` into message headers on publish; extract on consume, and use a **span link** rather than a parent-child relation when consumption is decoupled in time |
| A callback from a C extension | Usually lost | Capture the context before the call and restore it in the callback |

```python
# ILLUSTRATIVE — the ThreadPoolExecutor pattern, which is the common bug
import contextvars
from concurrent.futures import ThreadPoolExecutor

def run_checks_in_parallel(checks, payload):
    ctx = contextvars.copy_context()          # capture parent context, including the active span
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(ctx.run, check, payload) for check in checks]
        return [f.result() for f in futures]
```

Without `ctx.run`, each safety check produces an orphan root span and the trace shows a parent with no
children — which reads as "400 ms of unexplained self time" and sends you debugging the wrong thing.

---

## 6 · RED and USE dashboards

Two dashboards per service. Do not invent a third layout per team — a shared template is what makes an
unfamiliar service debuggable at 03:00.

### 6.1 RED — per service and per endpoint (user-facing, drives alerts)

| Panel | PromQL sketch |
|-------|--------------|
| **Rate** | `sum by (route) (rate(http_server_requests_total[5m]))` |
| **Errors** | `sum by (route) (rate(http_server_requests_total{status=~"5.."}[5m])) / sum by (route) (rate(http_server_requests_total[5m]))` |
| **Duration** | `histogram_quantile(0.99, sum by (le, route) (rate(http_server_duration_seconds_bucket[5m])))` |
| **SLI + budget** | The good/valid ratio and remaining error budget (`slos-and-error-budgets.md`) |
| **Deploy markers** | Annotation query against the change feed — non-optional |

### 6.2 USE — per resource (internal, drives diagnosis)

| Resource | Utilisation | Saturation | Errors |
|----------|-------------|-----------|--------|
| CPU | Busy fraction | Run-queue depth, CPU steal | Throttling events (cgroup) |
| Memory | Used / limit | Page faults, swap | OOM kills |
| Thread / worker pool | Busy workers / total | **Queue depth and wait time** | Rejections |
| Connection pool | In-use / size | **Checkout wait time** | Timeouts acquiring |
| Event loop (asyncio) | Loop utilisation | **Loop lag** — time between scheduled and actual callback | — |
| Disk | Used | I/O queue depth | I/O errors |

The bolded rows are the ones people forget and the ones that actually explain latency incidents.
**Connection-pool checkout wait** and **asyncio loop lag** are the two highest-value Python-specific
metrics in this table and neither comes for free — you have to emit them.

```python
# ILLUSTRATIVE — event loop lag, which no auto-instrumentation gives you
async def measure_loop_lag(meter, interval=1.0):
    hist = meter.create_histogram("asyncio.loop.lag", unit="s")
    while True:
        start = time.perf_counter()
        await asyncio.sleep(interval)
        hist.record((time.perf_counter() - start) - interval)
```

A rising loop lag means something synchronous is blocking the loop, and it explains
all-endpoints-slow-on-one-worker with no downstream cause — the Python analogue of a GC pause.

---

## 7 · Instrumenting an LLM-agent pipeline

This is the part that connects to the actual team: a LangGraph multi-agent support platform on Bedrock,
with a stateful meta-router dispatching to specialist subagents, parallel safety checks before any LLM
reasoning, and a DynamoDB checkpoint saver. See section 20 (LLM & agent systems) for the architecture.

### 7.1 Span structure

```
agent.turn                              (root — one per inbound user message)
├── safety.check   name=pii_scan        ┐
├── safety.check   name=abuse_filter    ├─ fanned out in PARALLEL, before any LLM call
├── safety.check   name=policy_gate     ┘
├── router.classify                     (the meta agent deciding where to send this)
│   └── llm.call   model=... purpose=classification
├── checkpoint.load                      (DynamoDB read)
├── agent.refunds                        (the dispatched specialist subagent)
│   ├── llm.call
│   ├── tool.lookup_ride
│   │   └── http.client  GET /v1/rides/...
│   ├── llm.call                          (second turn after tool result)
│   └── tool.issue_refund
└── checkpoint.save                       (DynamoDB write)
```

The structure itself is the deliverable: it makes "which agent, which tool, how many LLM round trips, and
where did the eight seconds go" answerable from one waterfall.

### 7.2 What to put on each span

**LLM calls.** OpenTelemetry has GenAI semantic conventions — use them where they fit, but note they are
still marked experimental and the names have moved, so pin a version and be prepared to remap.

| Attribute | Why it earns its place |
|-----------|----------------------|
| `gen_ai.system` (`aws.bedrock`), `gen_ai.request.model` | Compare models and providers; attribute cost |
| `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens` | **Cost and latency both scale with these.** The single most valuable pair |
| `gen_ai.response.finish_reasons` | `max_tokens` truncation is a silent quality failure that no error rate catches |
| Time to first token (streaming) | The number the user actually perceives; total duration is not it |
| `llm.retry_count`, `llm.throttled` | Bedrock throttling shows up as latency, not errors, if you retry silently |
| `llm.cache_hit` | Prompt caching changes both cost and latency by a large factor |
| `llm.prompt_version` / LangSmith prompt hub reference | Correlates a quality regression with a prompt change — the equivalent of a deploy marker |

Do **not** put prompts or completions in span attributes by default: they are large, they are personal
data, and they will end up in a vendor backend with a long retention. Capture them behind an explicit
flag, redacted, with a short retention, sampled — or store a reference to a record held in your own
system with your own retention policy.

**Router and orchestration.**

| Metric / attribute | What it detects |
|--------------------|-----------------|
| `agent.route.selected` | Routing distribution; a shift is a regression signal |
| `agent.route.confidence` | Low-confidence routes correlate with escalations |
| `agent.handoff.count` per conversation | Agents bouncing a user between each other |
| `agent.graph.depth`, turns per conversation | **Loop detection.** A cyclical graph that fails to terminate is the characteristic agent failure mode, and it is expensive — bound it and alert on the bound |
| `agent.node` on every span | Lets you compute per-node latency and error rate across all conversations |

**Tools.** Tool calls are ordinary RPCs and deserve ordinary RED metrics per tool: rate, error rate,
duration. A tool that fails 8% of the time is a much more common cause of bad conversations than the model
is, and it is invisible if you only measure "did the conversation succeed".

**Checkpointing (the custom `DynamoDBSaver`).**

| Measure | Why |
|---------|-----|
| Checkpoint write latency and error rate | It is on the critical path of every turn |
| **Serialised state size** | DynamoDB's 400 KB item limit is a hard cliff. State that grows with conversation length will hit it, and the failure appears only in long conversations — the ones with the most invested users |
| DynamoDB throttling / consumed capacity | Throttles present as latency then as failure |
| Checkpoint read-after-write consistency errors | A stateful router reading a stale checkpoint produces incoherent behaviour that looks like a model problem |

See `../06-databases-and-distributed-data/dynamodb_refresher.md`.

### 7.3 The metric set

| Metric | Type | Labels (bounded) |
|--------|------|-----------------|
| `agent.turns` | Counter | `agent`, `outcome` |
| `agent.turn.duration` | Histogram | `agent` |
| `agent.time_to_first_token` | Histogram | `agent` |
| `agent.escalations` | Counter | `agent`, `reason` |
| `llm.tokens` | Counter | `model`, `direction` (in/out) |
| `llm.call.duration` | Histogram | `model`, `purpose` |
| `llm.errors` | Counter | `model`, `error_type` (bounded set!) |
| `tool.calls` | Counter | `tool`, `outcome` |
| `tool.duration` | Histogram | `tool` |
| `safety.check.duration` | Histogram | `check` |
| `safety.check.blocked` | Counter | `check` |
| `checkpoint.size_bytes` | Histogram | `agent` |
| `conversation.cost_usd` | Histogram | `agent` |

Note `conversation.cost_usd` as a **histogram, not a counter**. The total spend is a finance number; the
*distribution* is an engineering number, because the p99 conversation costing 40× the median is a runaway
loop, and a counter hides that entirely inside a healthy-looking average.

**Per-agent success rate needs an outcome definition**, agreed and written down before you build the
dashboard. A workable taxonomy: `resolved` / `escalated_to_human` / `abandoned_by_user` /
`error` / `blocked_by_safety`. Then per-agent success rate is `resolved / total`, and each other outcome
is separately trackable — because "escalated" and "errored" mean completely different things and averaging
them into one number destroys the signal.

### 7.4 Detecting distribution shift

Lyft has published an honest and specific failure: their offline agent simulator showed **90% pass rates
while production revealed a distribution shift** — off-the-shelf LLM user simulators behave like nice,
helpful assistants, while real users send brief, impatient messages. They fixed it by fine-tuning the
simulators on real customer verbatims.

The observability lesson generalises, and it is a strong thing to raise unprompted: **if your offline eval
and your production outcomes disagree, the gap is in the input distribution, so instrument the inputs.**

| Input feature | Emit as | Detects |
|---------------|---------|---------|
| Message length (chars/tokens) | Histogram | The simulator/reality gap directly |
| Turns per conversation | Histogram | Users giving up, or agents looping |
| Time between user messages | Histogram | Impatience; abandonment |
| Language / locale | Counter, bounded | Coverage gaps |
| Retry/rephrase rate (user repeats themselves) | Counter | The agent is not understanding |
| Share of conversations opening with a complaint or escalation demand | Counter | Sentiment mix shift |

Then compare the **production distribution against the evaluation-set distribution** on the same metrics.
That comparison is the alert: not "quality dropped" — which you learn late, from outcomes — but "the
inputs no longer look like what we tested on", which you learn early, from the first hour of traffic after
a change in the world.

### 7.5 What to alert on

Per `alert-design.md`: symptoms, on SLO burn, not on resource utilisation.

| Alert | Severity | Rationale |
|-------|----------|-----------|
| Burn rate on the platform SLO (turn succeeded within latency bound) | Page | The reliability symptom |
| Burn rate on time-to-first-token | Page | The perceived-latency symptom |
| Escalation rate above its baseline band for 30 min | Ticket | Quality regression; rarely warrants a 3 a.m. page |
| Tool error rate per tool above baseline | Ticket | Usually a downstream service problem |
| Turns-per-conversation p99 above the loop bound | Page | Runaway loops burn money fast |
| `conversation.cost_usd` p99 above threshold | Page | Same failure, measured in currency |
| Checkpoint size p99 approaching 400 KB | Ticket | A cliff you want warning of |
| Safety-check failure or timeout rate | **Page** | Safety checks fan out before LLM reasoning; if they fail open, that is a safety incident, not a latency one |
| Input-distribution drift vs the eval set | Ticket | The §7.4 early-warning signal |

The safety row deserves emphasis in an interview: it is worth asking explicitly whether a failing safety
check **fails open or fails closed**, and instrumenting that decision, because "the safety check timed out
so we proceeded" is the kind of thing that is invisible in every aggregate metric until it is a headline.

---

## 8 · Anti-patterns

| Anti-pattern | Consequence |
|--------------|-------------|
| `SimpleSpanProcessor` in production | Exporter latency becomes request latency |
| Per-service sampling ratios without `ParentBased` | Fragmented, useless traces |
| Raw URL path as a metric label or span name | Cardinality explosion; unusable aggregates |
| Prompts and completions as default span attributes | Cost, and personal data in a vendor's store |
| `user_id` as a metric label | See `metrics-logs-traces.md` §3 |
| Instrumenting every function | 800-span waterfalls nobody reads |
| Measuring total LLM latency but not time-to-first-token | Optimising a number the user does not experience |
| Success rate with no written outcome taxonomy | "Success" silently means something different per agent |
| Exporting straight to a vendor from the app | No tail sampling, no redaction, no backpressure absorption |
| Forgetting `contextvars` in a thread pool | Orphan spans that read as unexplained self time |

---

## 9 · Runnable: trace context and structured logging, standard library only

Works on a bare `python3` with no packages. It is a teaching shim, not a replacement for the SDK — but it
contains the three mechanics that actually matter (a contextvar holding the active context, W3C
`traceparent` parse/format, and log records that automatically carry the trace IDs), and typing it out is
worth more than reading about the SDK.

```python
"""Minimal trace-context + structured-logging shim. Standard library only.
Run:  python3 otel_shim.py
"""
from __future__ import annotations

import contextvars
import json
import logging
import secrets
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator


@dataclass(frozen=True)
class SpanContext:
    trace_id: str          # 32 hex chars
    span_id: str           # 16 hex chars
    sampled: bool = True

    def traceparent(self) -> str:
        """Serialise to the W3C Trace Context header value."""
        return f"00-{self.trace_id}-{self.span_id}-{'01' if self.sampled else '00'}"

    @staticmethod
    def parse(header: str) -> "SpanContext | None":
        """Parse an inbound `traceparent`. Returns None if malformed."""
        parts = header.strip().split("-")
        if len(parts) != 4:
            return None
        version, trace_id, span_id, flags = parts
        if version != "00" or len(trace_id) != 32 or len(span_id) != 16:
            return None
        if trace_id == "0" * 32 or span_id == "0" * 16:
            return None
        try:
            sampled = bool(int(flags, 16) & 0x01)
        except ValueError:
            return None
        return SpanContext(trace_id, span_id, sampled)


_current: contextvars.ContextVar[SpanContext | None] = contextvars.ContextVar(
    "span_context", default=None
)


def current_context() -> SpanContext | None:
    return _current.get()


@contextmanager
def span(name: str, **attributes: Any) -> Iterator[SpanContext]:
    """Start a span: inherit the parent's trace id, mint a new span id."""
    parent = _current.get()
    ctx = SpanContext(
        trace_id=parent.trace_id if parent else secrets.token_hex(16),
        span_id=secrets.token_hex(8),
        sampled=parent.sampled if parent else True,
    )
    token = _current.set(ctx)
    started = time.perf_counter()
    status = "ok"
    try:
        yield ctx
    except Exception as exc:
        status = "error"
        logging.getLogger(__name__).error(
            "span.error",
            extra={"fields": {"span_name": name, "error_type": type(exc).__name__}},
        )
        raise
    finally:
        duration_ms = round((time.perf_counter() - started) * 1000, 3)
        logging.getLogger(__name__).info(
            "span.end",
            extra={"fields": {"span_name": name, "duration_ms": duration_ms,
                              "status": status, **attributes}},
        )
        _current.reset(token)


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per record, with trace context injected."""

    def __init__(self, service: str, version: str) -> None:
        super().__init__()
        self.service = service
        self.version = version

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)) + "Z",
            "level": record.levelname.lower(),
            "event": record.getMessage(),
            "service": self.service,
            "version": self.version,
            "logger": record.name,
        }
        ctx = current_context()
        if ctx is not None:
            payload["trace_id"] = ctx.trace_id
            payload["span_id"] = ctx.span_id
        payload.update(getattr(record, "fields", {}))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"))


def configure(service: str, version: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(service, version))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


def outbound_headers() -> dict[str, str]:
    """Headers to attach to an outbound call so the trace continues."""
    ctx = current_context()
    return {"traceparent": ctx.traceparent()} if ctx else {}


if __name__ == "__main__":
    configure(service="support-router", version="a91f3c2")
    log = logging.getLogger("demo")

    inbound = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    token = _current.set(SpanContext.parse(inbound))

    with span("agent.turn", conversation_id="c-8813", channel="chat"):
        log.info("router.classify", extra={"fields": {"intent": "refund_request"}})
        with span("safety.check", check="pii_scan"):
            time.sleep(0.01)
        with span("llm.call", model="claude-sonnet", input_tokens=812, output_tokens=140):
            time.sleep(0.02)
            log.info("llm.headers_for_next_hop",
                     extra={"fields": {"headers": outbound_headers()}})

    _current.reset(token)
```

Output (one JSON object per line — note that every record carries the **inbound** trace id, so all of it
joins to the caller's trace):

```
{"ts":"...","level":"info","event":"router.classify","service":"support-router",
 "version":"a91f3c2","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736","span_id":"53ae0d…","intent":"refund_request"}
{"ts":"...","event":"span.end","span_name":"safety.check","duration_ms":10.109,"status":"ok","check":"pii_scan", …}
{"ts":"...","event":"span.end","span_name":"llm.call","duration_ms":20.247,"model":"claude-sonnet","input_tokens":812, …}
{"ts":"...","event":"span.end","span_name":"agent.turn","duration_ms":30.685,"conversation_id":"c-8813", …}
```

Exercises worth doing, in ascending difficulty: add a `SpanProcessor` interface so spans go somewhere
other than the log; add a `TraceIdRatioBased` sampler that respects the inbound sampled flag; make it
work correctly across a `ThreadPoolExecutor` using `contextvars.copy_context()`; add a histogram
instrument with bucket boundaries and a `/metrics` text-format endpoint.

---

## Interview questions

**1. How would you instrument a Python service from scratch?**
Resource first — `service.name`, `service.version` set to the deploy SHA, and `deployment.environment` —
because everything filters on those and a service reporting the default `unknown_service:python` is
invisible in a shared backend. Then auto-instrumentation for the frameworks: Flask, requests, the AWS SDK,
the database driver, which gets inbound and outbound spans with context propagation for roughly an
afternoon of work. Then manual spans only for domain operations, because auto-instrumentation cannot know
what "match a rider" means. Configure a `ParentBased` sampler and a `BatchSpanProcessor`, export to a
local Collector rather than straight to a vendor, and make sure logs carry `trace_id` so the three signals
join up.

**2. What is the difference between a span attribute and a metric label?**
Cardinality tolerance, and it is the most consequential distinction in instrumentation. A span attribute
costs bytes on one event, so high-cardinality values — user ID, conversation ID, ride ID — are exactly
what belongs there. A metric label multiplies the number of active time series, so an unbounded label can
take a metrics backend from hundreds of thousands of series to hundreds of millions, and the blast radius
is shared with every other team. So: bounded dimensions you will group by go on metrics; identifiers go
on spans and logs, and exemplars link the two.

**3. Why do you need `ParentBased` sampling?**
Because the sampling decision has to be made once at the root and honoured by every service downstream. If
each service independently applies a 5% ratio, then a trace crossing five services is kept end-to-end
about one time in three million, and what you actually collect is fragments — root spans with no children
and children with no parents. `ParentBased` says: if there is an inbound decision, respect it; only apply
the ratio when I am the root. The same idea is why sampling must be deterministic in the trace ID rather
than random per span.

**4. Where does trace context get lost in Python?**
`contextvars` is the mechanism, and it flows correctly through normal calls, through `await`, and into
`asyncio.create_task` because the context is copied at task creation. It is lost across
`ThreadPoolExecutor` and raw threads — the fix is `contextvars.copy_context()` in the parent and
`executor.submit(ctx.run, fn, ...)` — and across process and message boundaries like Celery, SQS or Kafka,
where you inject `traceparent` into the message headers and extract on the other side. For a queue
consumed much later, use a span *link* rather than parent-child, because the consume is not causally
inside the publish. The symptom of getting this wrong is orphan spans that read as unexplained self time,
so you debug the wrong thing.

**5. What are RED and USE, and which drives alerts?**
RED is Rate, Errors and Duration per service or endpoint — user-facing, and where alerts come from. USE is
Utilisation, Saturation and Errors per resource — internal, and where explanations come from. Alerting on
USE metrics is the classic mistake: CPU at 90% with healthy latency is fine, and CPU at 35% with a
saturated connection pool is an outage. For Python specifically, the two USE metrics that actually explain
latency incidents are connection-pool checkout wait time and asyncio event-loop lag, and neither comes for
free from auto-instrumentation.

**6. Tell me some experience related to ML or Gen AI. [Reported at Lyft]**
The angle I would take is operational rather than modelling, because that is where my experience is
strongest and it is what an agent platform actually needs. Concretely: what an LLM pipeline needs
instrumented that an ordinary service does not — input and output token counts, because both cost and
latency scale with them; time to first token rather than total duration, because that is what the user
perceives; finish reason, because `max_tokens` truncation is a silent quality failure no error rate
catches; per-tool RED metrics, because tools fail far more often than models do; turns per conversation
with an alert on the bound, because a runaway loop is the characteristic agent failure and it burns money
quickly; and cost per conversation as a histogram rather than a counter, since the total hides the p99
runaway inside a healthy-looking average.

**7. How would you detect that an agent's quality has regressed?**
Two layers, because outcome metrics tell you late. The outcome layer is a written taxonomy — resolved,
escalated to a human, abandoned, error, blocked by safety — tracked per agent and per prompt version, so
"escalation rate rose after prompt v14" is one query; treating prompt versions like deploy markers is what
makes that possible. The earlier layer is input-distribution monitoring: message length, turns per
conversation, time between messages, rephrase rate, compared against the distribution of the offline
evaluation set. Lyft published exactly this failure — their simulator showed 90% pass rates while real
users sent brief, impatient messages that the simulator never produced. Instrumenting the input
distribution is what turns that from a postmortem into an alert.

**8. Should you log the prompt and the model's response?**
Not by default. They are large, so they dominate your logging bill; they are personal data, so they carry
retention and deletion obligations; and putting them in span attributes ships them to a vendor backend
with whatever retention that vendor has. What I would do is capture them behind an explicit sampling
policy — a small percentage plus 100% of escalated or failed conversations, redacted at the logging
library rather than by convention, stored in a system I control with a defined retention, and referenced
from the span by ID. That keeps the debugging capability, which is genuinely necessary, without making
every conversation a compliance liability.

**9. A LangGraph agent is looping and burning tokens. How would you have caught it?**
Three instruments, none of which is the error rate, because a loop is not an error. First, a bounded graph
depth or turn count per conversation with a hard limit, so the loop terminates — the instrumentation
question follows the safety question. Second, turns per conversation as a histogram with a page on the
p99 crossing the bound, since a loop shows up as a distribution change long before anything fails. Third,
cost per conversation as a histogram, because a runaway loop is most visible in currency and a p99 at 40×
the median is unmistakable while the total spend still looks normal. In the trace it is obvious — the same
`agent.node` span repeating — which is why putting the node name on every span pays for itself.

**10. What would you check about how safety checks are instrumented?**
Whether a failing or timing-out safety check fails open or fails closed, and whether that decision is
recorded on the span. Lyft's design fans safety checks out in parallel before any LLM reasoning, which is
the right shape — but the interesting operational question is what happens when one of them times out
under load. If it fails open silently, every aggregate metric stays green while unchecked content flows
through, and you find out from a headline rather than a dashboard. So: per-check latency and failure-rate
metrics, an explicit `safety.failed_open` counter that pages rather than tickets, and the check's outcome
as a span attribute so any individual conversation can be audited afterwards.
