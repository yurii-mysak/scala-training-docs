# Third-Party Dependency Failure Modes — full worked design

> **Priority:** Required
> **Est. time:** 60 min
> **Track:** Server
> **HelloInterview:** System Design in a Hurry → Common Patterns → Dealing with Contention; Managing Long Running Tasks; Core Concepts → API Design

This is a **verbatim reported Lyft design prompt**: *"a web application with a lot of third-party
dependencies that have a variety of failure modes."* It was reported from a T4 loop, but it is the
single most on-domain design question in the whole bank for this team — the Global Support platform is
explicitly described as building *"integration platforms that seamlessly link global customers to an
exceptional customer care experience."* Integration platform is another way of saying "a system whose
job is to survive other people's outages."

It is also the design question where a Staff answer separates itself most cleanly from a Senior one. A
Senior answer names retries, timeouts and a circuit breaker. A Staff answer starts from the observation
that **every dependency has a different failure signature and a different correct response**, builds a
taxonomy, and then designs one mechanism per class rather than one mechanism for everything.

---

## 1 · Framing the problem

Do not begin by listing resilience patterns. Begin by asking what the dependencies actually are, because
the answer determines the whole design. For a customer-support platform the realistic set is:

| Dependency | Shape | If it fails |
|---|---|---|
| Payments / refunds provider | Synchronous, **money-moving**, non-idempotent by default | Cannot fake success. Must not double-charge. |
| LLM provider (Bedrock/Anthropic) | Synchronous, slow (seconds), rate-limited, occasionally wrong | Degrade to human or scripted flow |
| Identity / SSO | Synchronous, on the critical path for every request | Hard outage; cached sessions buy time |
| Email / SMS / push vendor | Asynchronous, fire-and-forget-ish | Queue and retry; user rarely notices minutes |
| Maps / geocoding | Synchronous, cacheable, degradable | Serve stale or coarse results |
| CRM / ticketing (Jira, Salesforce) | Asynchronous, write-heavy, rate-limited | Buffer writes, reconcile later |
| Analytics / logging sink | Asynchronous, lossy-tolerable | Drop on the floor under pressure |

The first Staff move in this interview is to say out loud: *"these need different treatment, so let me
classify them before I design anything."* Then propose the two axes that matter.

**Axis 1 — is it on the critical path?** Can the user's request succeed if this call fails? If yes, the
dependency is *degradable* and the design question is "what do we serve instead?" If no, it is *critical*
and the design question is "how do we reduce the blast radius and recover?"

**Axis 2 — is the operation safe to repeat?** Reads are. Idempotent writes are, if the provider supports
an idempotency key. Non-idempotent writes are not, and they need the exactly-once machinery in
[idempotency-and-deduplication.md](idempotency-and-deduplication.md) rather than a retry policy.

That two-by-two gives four quadrants and four different designs. Everything below hangs off it.

---

## 2 · The failure taxonomy

"Down" is the easy case and the one candidates over-index on. Name the others, because interviewers probe
here and because the hard ones are the ones that take production down.

| Failure mode | What it looks like | Why it is dangerous |
|---|---|---|
| **Hard down** | Connection refused, DNS failure, 5xx immediately | Easiest. Fails fast, circuit opens, you degrade. |
| **Slow** | Responses in 30s instead of 200ms | **The dangerous one.** Threads/connections pile up, your own service dies from resource exhaustion, not from theirs. |
| **Partial** | 5% error rate, or one region failing | Circuit breakers tuned for binary state flap. Needs percentage thresholds. |
| **Rate limited** | 429s under load, often exactly when you need it most | Naive retry makes it strictly worse. Needs backoff plus client-side throttling. |
| **Wrong** | 200 OK with corrupt, stale or hallucinated data | No transport-level signal at all. Only caught by validation. |
| **Slow-then-succeed** | Eventually returns, after your client gave up | You have an orphaned side effect at the provider. This is where double-charges come from. |
| **Contract drift** | Field removed, enum value added, semantics changed | Silent until it isn't. Caught by contract tests, not by monitoring. |

Say explicitly: **the slow failure is worse than the down failure**, because a dependency that is down
sheds your load and a dependency that is slow consumes it. That single sentence signals production
experience more than any pattern name.

---

## 3 · The mechanism per failure mode

### Timeouts — the foundation, and the one most often wrong

Every outbound call gets a timeout. Two of them: a **connect timeout** (short, hundreds of ms — either
the socket opens or the provider is unreachable) and a **read timeout** (derived from the provider's own
latency distribution, not guessed).

Set the read timeout from the p99, not the mean. If p99 is 800ms, a 1s timeout cuts off the legitimate
tail; a 30s timeout means a slow provider holds your worker for 30 seconds. A useful rule: timeout at
roughly p99.9, and treat anything slower as failed rather than waiting.

The critical constraint is that **your timeout budget must be nested**. If your own SLA is 2s and you
call three dependencies serially, they cannot each have a 2s timeout. Propagate a deadline down the call
chain — each hop subtracts its elapsed time and passes the remainder. gRPC does this natively; over HTTP
you carry it in a header. Without deadline propagation, a request that is already doomed keeps consuming
capacity at every downstream layer.

### Bulkheads — the mechanism people forget

Give each dependency its own connection pool and its own concurrency limit. If the LLM provider is slow
and you have a shared 200-connection pool, the LLM saturates all 200 and payments starts failing too.
Separate pools mean the LLM can only ever consume its own allocation.

This is the specific answer to "how do you stop one slow dependency taking down the whole app," and it is
the pattern most candidates miss. It is also the direct analogue of the actor-supervision boundary from
[Akka](../03-akka-ecosystem/AkkaAdvanced.md) — worth naming if the interviewer asks about your background.

### Circuit breakers — with the honest caveats

Closed → open on a failure threshold → half-open after a cooldown → closed on success.

The details interviewers push on:

- Trip on **error rate over a window with a minimum request count**, not on consecutive failures. Three
  consecutive failures out of five requests is noise; 30% errors over 200 requests is a signal.
- Half-open must admit **a limited number of probes**, not full traffic, or you re-kill a recovering
  provider.
- Breakers are **per-dependency and ideally per-endpoint**. A provider whose search is broken but whose
  reads are fine should not be fully cut off.
- State is per-instance unless you share it. Distributed breaker state is usually not worth the
  complexity; local state on enough instances converges to the right answer.

### Retries — the pattern most likely to cause the outage

Retries are the main way a small incident becomes a large one. Constrain them:

- **Exponential backoff with full jitter**, always. Synchronised retries from a thousand clients are a
  self-inflicted DDoS.
- **Only retry idempotent operations**, or operations carrying an idempotency key the provider honours.
- **Cap total attempts and total elapsed time**, not just attempt count.
- **Never retry at multiple layers.** Retry once, at one layer. Three layers each retrying three times is
  27 requests to a struggling provider.
- **Do not retry a 4xx** other than 429 and 408. A 400 will be 400 again.
- **Budget retries** — cap retries at a small percentage of total traffic (say 10%). When the budget is
  exhausted, fail fast. This is what stops retry storms and metastable failure.

Cross-reference: [debugging-distributed-systems.md](../19-observability-and-oncall/debugging-distributed-systems.md)
covers metastable failure, where a system stays down after the trigger is removed because retries keep it
saturated.

### Fallbacks and graceful degradation

For each degradable dependency, decide in advance what "degraded" means and make it a product decision,
not an engineering accident:

| Dependency | Degraded behaviour |
|---|---|
| Maps/geocoding | Serve cached or coarser location; hide the map, keep the flow |
| LLM agent | Fall back to a scripted decision tree, then to a human queue |
| Recommendations | Serve a static popular list |
| CRM write | Buffer to a durable queue, reconcile asynchronously |
| Identity | Honour existing sessions; block only new logins |
| Payments | **No fallback.** Fail explicitly and tell the user. |

The last row matters most. Say it out loud: **you cannot degrade money.** Knowing where fallback is
forbidden is a stronger signal than knowing where it is possible.

### Asynchrony — the structural fix

The strongest answer to "third-party dependencies fail" is often "then do not call them synchronously."
Accept the user's request, persist intent durably, return, and let a worker drive the third-party call to
completion with retries and reconciliation. The user sees success; the integration completes eventually.

This converts a availability problem into a latency problem, which is almost always the better trade. It
is exactly the shape of the outbox pattern in
[event_sourcing_cqrs_sagas_guide.md](event_sourcing_cqrs_sagas_guide.md) — write the state change and the
outbound intent in the same local transaction, then publish from the outbox.

For multi-step flows across several providers, this becomes a **saga** with explicit compensating actions,
since you cannot hold a distributed transaction across vendors.

### Caching as an availability tool

Cache third-party responses not only for latency but for survival. Two TTLs: a soft TTL after which you
refresh in the background, and a hard TTL after which the data is unusable. When the provider is down,
serve past the soft TTL and label the response stale. **Stale-while-revalidate and stale-if-error turn a
cache into an availability buffer.**

---

## 4 · Putting it together — the reference architecture

```
        ┌─────────────────────────────────────────────┐
client →│  API layer (deadline set here)              │
        └──────────────┬──────────────────────────────┘
                       │ deadline propagated
        ┌──────────────▼──────────────────────────────┐
        │  Integration layer — one adapter per vendor │
        │  ┌────────────────────────────────────────┐ │
        │  │ per-adapter: bulkhead (own pool),      │ │
        │  │ timeout, breaker, retry budget,        │ │
        │  │ response validation, metrics           │ │
        │  └────────────────────────────────────────┘ │
        └───┬────────────┬────────────┬───────────────┘
            │            │            │
        ┌───▼───┐   ┌────▼────┐  ┌────▼──────┐
        │payment│   │  LLM    │  │  CRM      │
        │(sync, │   │(sync,   │  │(async via │
        │ idem  │   │ degrad- │  │ outbox +  │
        │ key)  │   │ able)   │  │ worker)   │
        └───────┘   └─────────┘  └───────────┘
```

The single most important structural decision: **one adapter per vendor, and the resilience policy lives
in the adapter, not scattered through business logic.** Business code calls `refunds.issue(...)` and does
not know about breakers. This is what makes the policy auditable and tunable per vendor, and it is what
lets you answer "how would you add a seventh provider?" with "write one adapter."

At Lyft specifically, some of this lives in the **Envoy** sidecar rather than in application code — outlier
detection, retries, timeouts and circuit breaking are mesh-level concerns there. Naming that is a strong
move: see [lyft-architecture.md](lyft-architecture.md). But be precise that the mesh handles transport-level
policy, while idempotency keys, fallbacks and semantic validation stay in the application.

---

## 5 · Observability for integrations

Per dependency, not aggregated: request rate, error rate broken down by class (timeout, 5xx, 429, validation
failure), latency percentiles, breaker state transitions, retry count and retry-budget consumption, and
fallback invocation rate.

The one people forget: **alert on fallback rate.** A system serving fallbacks is technically "up" and will
look green on availability dashboards while quietly serving degraded results to every user. Fallback rate
is the SLI that catches it.

Also track **vendor SLA compliance** as a business artifact. If a provider promises 99.9% and delivers
99.5%, you want the numbers when the contract is renegotiated. That is a Staff-scope behaviour: the
engineering system feeding the commercial relationship.

---

## 6 · Testing

- **Contract tests** against a recorded or vendor-provided spec, run in CI, so drift breaks a build rather
  than production.
- **Fault injection** — force timeouts, 500s, 429s and malformed bodies in a staging environment. If you
  have never seen your fallback path execute, you do not have a fallback path.
- **Sandbox environments** where the vendor provides one; a stub that only returns success is worse than
  no test because it builds false confidence.
- **Game days** — deliberately break a dependency in a controlled window and confirm the runbook works.

---

## 7 · What a Staff answer sounds like

Say these things explicitly; they are what distinguishes the level:

1. "Let me classify the dependencies first — critical vs degradable, idempotent vs not — because they
   need different mechanisms."
2. "The slow failure is more dangerous than the hard failure, so bulkheads matter more than breakers."
3. "Timeouts have to be a propagated deadline, not an independent per-call number."
4. "Retries need a budget, not just a count, or we cause the second outage ourselves."
5. "For payments there is no fallback — we fail loudly. Not everything degrades."
6. "The policy lives in an adapter per vendor so it is auditable and tunable, and so adding a vendor is one
   file."
7. "I would alert on fallback rate, because a fully-degraded system looks healthy on an availability
   dashboard."

---

## Interview questions

**1. A third-party API starts responding in 30 seconds instead of 200ms. Walk me through what happens to
your service. [Reported at Lyft]**
Without protection: request threads block, the connection pool for that vendor drains, and because the pool
is shared, unrelated endpoints start failing. Load balancer health checks time out, instances are pulled,
remaining instances take more load, and the whole service collapses from someone else's latency. With
bulkheads the damage is contained to that vendor's allocation; with a deadline the request is abandoned at
the SLA boundary; with a breaker the calls stop entirely after the error rate crosses threshold and the
fallback path takes over.

**2. When would you not retry a failed call?**
Non-idempotent writes without an idempotency key — a payment retry risks a double charge. Any 4xx other
than 429 and 408, because the request is malformed and will fail identically. When the retry budget is
exhausted, because at that point retries are amplifying an incident. And when the deadline has already
passed, since a successful response would be discarded anyway.

**3. How do you set a timeout value?**
From the dependency's observed latency distribution, at roughly p99.9, not from a guess. Then check it
against your own SLA: the sum of serial call timeouts must fit inside your latency budget, which usually
means propagating a deadline rather than setting independent per-call values. Re-derive it periodically —
a timeout set against last year's p99 is wrong now.

**4. Your circuit breaker keeps flapping between open and closed. What is wrong?**
Almost always a threshold tuned on consecutive failures rather than error rate over a window with a minimum
request count, so low traffic trips it on noise. The other common cause is half-open admitting full traffic,
which re-kills a provider that was just starting to recover — half-open should admit a small number of
probes. Longer windows and a slow-start ramp on recovery fix both.

**5. How do you handle a provider that returns 200 with wrong data?**
Transport-level resilience cannot see this, so it needs semantic validation in the adapter: schema checks,
range and sanity checks, and cross-checks against known invariants. Treat a validation failure as a failure
for breaker and metric purposes. For LLM providers specifically this is the normal case rather than an
exception, which is why the eval and guardrail machinery in
[../20-llm-agent-systems/evaluating-agents.md](../20-llm-agent-systems/evaluating-agents.md) exists.

**6. Twenty different third-party integrations. How do you keep this maintainable?**
One adapter per vendor with a shared resilience library, so policy is declarative per vendor and consistent
in mechanism. A registry of dependencies with their classification, SLA, owner and degraded behaviour
documented. Uniform metric names so one dashboard template works for all twenty. And contract tests in CI
so vendor drift is a build failure rather than an incident.

**7. Where does asynchrony fit?**
Anywhere the user does not need the third-party result to complete their action. Persist the intent
durably in the same transaction as the state change via an outbox, return success, and let a worker drive
the call with retries and reconciliation. It converts an availability dependency into a latency one, which
is nearly always the better trade. The cost is that you now owe the user a way to see eventual failure.

**8. How would you know your fallback paths actually work?**
Fault injection in staging plus periodic game days in production, because untested fallback code is
aspirational. Alert on fallback rate so you know when they are being used for real. And track the last time
each fallback path executed — one that has never run in production is a hypothesis, not a feature.
