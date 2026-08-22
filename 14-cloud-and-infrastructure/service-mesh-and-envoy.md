# Service Mesh & Envoy

> **Priority:** Recommended
> **Est. time:** 30 min
> **Track:** Both
> **HelloInterview:** none

Envoy was built at Lyft. That makes this file more than general background — expect an interviewer
to probe whether you understand *why* a ride-sharing company ended up building and open-sourcing its
own networking layer, not just what a sidecar proxy does in the abstract.

---

## 1 · The Problem It Solves

As a system decomposes into many services — and, at a company running multiple backend languages,
many *languages* — cross-cutting network concerns (retries, timeouts, mTLS, load balancing,
observability) either get reimplemented per-service-per-language, inconsistently and expensively, or
get pushed into shared infrastructure that every service gets for free regardless of what it's
written in. A service mesh is that infrastructure.

---

## 2 · The Sidecar Model

- One proxy container runs alongside each application instance; all inbound and outbound traffic is
  transparently redirected through it — an `iptables` rule injected at Pod startup (or, increasingly,
  eBPF to skip that redirect hop entirely). The application talks to `localhost` and has no idea a
  mesh exists.
- **Data plane** (the proxies actually moving bytes) is architecturally separate from **control
  plane** (the system pushing configuration and policy to every proxy). Envoy is a data-plane proxy;
  Istio — or a much simpler static-config setup — is a control plane that configures it.
- The cost of this model is real: an extra hop and an extra process per instance (latency and memory
  overhead) in exchange for the same retry/timeout/mTLS/observability behavior everywhere, regardless
  of which language or framework wrote the application.

---

## 3 · Envoy, and Why This Is Lyft-Specific Context

Envoy was built at Lyft and open-sourced in 2016 to solve Lyft's own pain migrating from a monolith
to a polyglot microservices architecture, then donated to the CNCF in 2017, where it graduated
alongside Kubernetes and Prometheus. It's now the de facto data-plane proxy embedded inside Istio,
AWS App Mesh, and Gloo — and inside Lyft's own infrastructure, one Envoy sidecar per app server. See
[Lyft Architecture](../15-system-design/lyft-architecture.md) for the fuller company-specific picture
this plugs into.

Unlike a traditional L4 reverse proxy, Envoy is **L7-native from the ground up**: first-class
HTTP/1.1, HTTP/2, and gRPC support (including gRPC-Web), with configuration organized as dynamic
**xDS** resources pushed from a control plane rather than a static config file:

| xDS API | Configures |
|---|---|
| LDS (Listener Discovery) | What ports/protocols Envoy listens on |
| RDS (Route Discovery) | Which upstream cluster a request routes to |
| CDS (Cluster Discovery) | Upstream service groups and their policy (retries, circuit breaking) |
| EDS (Endpoint Discovery) | The actual healthy instance IPs within a cluster |

This dynamic push model is what lets a mesh reconfigure routing, retries, or circuit-breaking policy
cluster-wide without restarting a single proxy — the same desired-state-over-imperative-command
philosophy as Kubernetes itself, applied one layer up the stack; see
[Kubernetes Core §1](kubernetes-core.md#1--the-desired-state-model-read-this-first).

---

## 4 · L7 Proxying and Traffic Shifting

- L7 awareness means routing can key off the actual request — path, header, method — not just
  IP:port, and means only genuinely idempotent methods get automatically retried.
- **Weighted clusters** split a route's traffic by percentage across two upstream versions — the
  actual mechanism behind canary releases and blue-green cutover, which
  [Kubernetes has no native primitive for](kubernetes-operations.md#1--rollouts--rollback) on its own.
- **Header/cookie-based routing** sends internal or opt-in traffic to a new version without touching
  the percentage split everyone else sees.
- **Traffic mirroring** ("dark traffic") sends a copy of live production requests to a new version
  without its response ever affecting the real caller — validating a change against real traffic
  shape with zero user-facing risk.

---

## 5 · Resilience Patterns at the Mesh Layer

- **Timeouts**: enforced per-route by the proxy regardless of whether the application itself
  remembered to set one — catches "the client forgot a timeout" before it becomes a stuck-thread
  pile-up.
- **Retries**: capped by a retry budget, scoped to specific retriable status codes, and applied only
  where safe. Naive blanket retries are exactly what turns one slow dependency into a self-inflicted
  traffic multiplication (a retry storm) on top of an already-struggling service.
- **Circuit breaking**: caps on pending requests/connections per upstream, so one overloaded
  dependency can't exhaust the *caller's* own resources waiting on it.
- **Outlier detection**: passive health checking — the proxy watches real response success/latency
  per upstream host and temporarily ejects a misbehaving one from the load-balancing pool, with no
  explicit health-check endpoint involved at all.

Together, these are the concrete answer to protecting a service that depends on several third-party
dependencies with a variety of failure modes: timeouts bound the wait, circuit breaking bounds the
concurrency spent waiting, budgeted retries absorb transient blips without amplifying a real outage,
and outlier detection routes around a host that's degrading before it ever fails a health check.

---

## 6 · Observability, For (Almost) Free

- Because every request already flows through the proxy, a mesh gets you request-rate/error-rate/
  duration — the "golden signals" — **per hop**, for every service, with zero application code
  changes, including for legacy or third-party services you couldn't instrument directly.
- Distributed tracing is the one piece that's *not* free: the proxy alone can't invent request
  causality across a network hop, so the application still has to propagate trace headers across each
  RPC boundary. What the proxy adds, once headers are propagated, is generating and reporting the
  per-hop span automatically. "The mesh gives you tracing for free" is a common but imprecise claim —
  worth being exact about this split if asked.

---

## 7 · mTLS

Sidecar-to-sidecar mutual TLS: each proxy holds a workload identity certificate (the SPIFFE model is
the common underlying standard), issued and rotated automatically by the control plane. The
application never touches key material or TLS configuration — connections between meshed sidecars are
mutually authenticated and encrypted by default. This buys two separately valuable things: encryption
in transit for every east-west hop, and a per-workload authenticated identity that authorization
policy can key off ("service A may call service B") — a zero-trust network posture without every team
hand-rolling client certs. See [HTTPS & TLS](../10-networking/Networking-HTTPS-TLS.md) for the
handshake mechanics mTLS builds on.

---

## Interview questions

1. **Why would a company build its own proxy instead of adopting nginx or HAProxy?**
   Neither was L7/gRPC-native with a dynamic config-push model out of the box — at the scale and
   polyglot-service shape a company like Lyft was solving for, hot-reloading routing/retry/
   circuit-breaking policy cluster-wide without proxy restarts was the actual requirement, which is
   exactly what Envoy's xDS model was designed around.

2. **[Reported at Lyft]** **How would you protect a service that depends on several third-party
   dependencies with a variety of failure modes?**
   No single mechanism covers every failure shape: per-route timeouts bound how long you'll wait,
   circuit breaking bounds concurrency spent waiting on a struggling dependency, retries with a budget
   absorb transient blips without amplifying a real outage into a storm, and outlier detection routes
   around a host that's degrading before it ever fails an explicit health check. At the mesh layer,
   all four apply uniformly across every service without per-language reimplementation.

3. **What's the actual mechanism by which traffic gets into the sidecar without the application
   knowing?**
   An `iptables` rule (or an eBPF program) injected at Pod startup transparently redirects the Pod's
   inbound and outbound traffic through the sidecar's ports — the application still just binds and
   connects to what looks like normal local addresses.

4. **Does a service mesh give you distributed tracing for free?**
   Only partially — the proxy can generate and report per-hop spans, but it can't invent causality
   across a network boundary on its own; the application still has to propagate trace headers on every
   outbound call for the spans to chain into one trace.

5. **How would you canary a new version to 5% of traffic without doubling your replica count?**
   Weighted-cluster traffic splitting at the mesh layer — an exact percentage split independent of
   replica counts — rather than the crude approximation of running one canary Pod out of twenty and
   hoping the load balancer distributes evenly.

6. **Why cap retries with a budget instead of just retrying every failed request a few times?**
   Blanket retries on an already-degraded dependency multiply the load hitting it — a retry storm that
   turns a slowdown into an outage. A budget caps total retry volume regardless of how many individual
   callers are each independently deciding to retry.

7. **What does mTLS in a mesh actually buy you beyond "traffic is encrypted"?**
   A per-workload authenticated identity that authorization policy can key off — not just confidential
   transport, but a basis for "service A is allowed to call service B" enforced at the network layer,
   without any application-level auth code.
