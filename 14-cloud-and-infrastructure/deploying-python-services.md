# Deploying Python Services

> **Priority:** Recommended
> **Est. time:** 35 min
> **Track:** Server
> **HelloInterview:** none

Where [Kubernetes Core](kubernetes-core.md), [Kubernetes Operations](kubernetes-operations.md), and
[Docker & Containers](docker-and-containers.md) meet an actual service: containerizing a Flask/gRPC
Python app and running it well on Kubernetes. Written assuming Python fluency needs a refresh, not
assuming it — every mechanism is spelled out, not just named.

---

## 1 · Containerizing a Flask/gRPC Service

The [multi-stage pattern](docker-and-containers.md#3--multi-stage-builds) applied to a real service:

```dockerfile
FROM python:3.11-slim AS build
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
RUN useradd --uid 1000 --create-home appuser
COPY --from=build /root/.local /home/appuser/.local
COPY . /app
WORKDIR /app
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1
USER appuser
EXPOSE 8080
ENTRYPOINT ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
```

`PYTHONUNBUFFERED=1` matters specifically in a container: Python buffers `stdout` when it isn't
attached to a TTY, which it never is here — without this, log lines can sit in a buffer instead of
reaching `kubectl logs` promptly, which is confusing during exactly the incident where you need them
fastest.

---

## 2 · Worker Models: gunicorn, uvicorn, and gRPC's Own Server

- **WSGI (Flask, sync)**: gunicorn's `sync` worker handles one request per worker *process* at a
  time — fine for CPU-bound or fast handlers, bad for anything that blocks on I/O, since a slow
  downstream call ties up an entire worker process while it waits. `gthread` (a thread pool per
  worker) or `gevent` (cooperative greenlets) trade that for concurrency per process, at the cost of
  needing genuinely thread-safe or greenlet-safe application code.
- **ASGI (async frameworks)**: `uvicorn`, typically run as `gunicorn.workers.UvicornWorker` processes
  under gunicorn — gunicorn handles process management and restarts, uvicorn runs the actual async
  event loop. One worker can hold many concurrent I/O-bound requests via `async`/`await`, instead of
  one thread or greenlet per request.
- The `2 × cores + 1` worker-count heuristic assumes **CPU-bound** work. It's the wrong formula for an
  I/O-bound service, where the real limiting factor is downstream connection concurrency, not local
  CPU — size workers/threads around realistic concurrent in-flight requests and downstream
  connection-pool limits, not a formula that assumes CPU is the bottleneck.
- **gRPC services don't run under gunicorn or WSGI/ASGI at all.**
  `grpc.server(futures.ThreadPoolExecutor(max_workers=N))` is its own, separate concurrency model — a
  fixed thread pool serving RPCs directly. Worth being precise about this given how much gRPC is used
  in practice at a Python/Go shop: a Flask health-check endpoint and the actual gRPC service running
  in the same Pod are two independent servers with two independent concurrency models, not one config
  shared between them.

---

## 3 · Graceful Shutdown

The signal chain from [Docker & Containers §6](docker-and-containers.md#6--signal-handling--pid-1),
applied: kubelet marks the Pod Terminating, removes it from Service Endpoints, sends SIGTERM
(optionally after a `preStop` hook runs first), waits up to `terminationGracePeriodSeconds` (default
30s), then SIGKILLs.

**The race that actually bites production services**: removing the Pod from Endpoints and delivering
SIGTERM are *not* synchronized with "every in-flight connection has finished." A caller that already
has a connection open, or that resolved the old Endpoints list a moment before the update propagated,
can keep sending requests for a brief window *after* the app has started shutting down.

Standard fix, in order:

1. A short `preStop` sleep (a few seconds, tuned to your Endpoints/mesh propagation latency) that does
   nothing but delay SIGTERM delivery — giving kube-proxy (or the mesh sidecar, see
   [Service Mesh & Envoy](service-mesh-and-envoy.md#2--the-sidecar-model)) time to actually stop
   routing new traffic before the app starts refusing it.
2. gunicorn's own `graceful_timeout` — how long it waits for in-flight requests to finish after
   receiving SIGTERM before it SIGKILLs its own workers — set comfortably under
   `terminationGracePeriodSeconds`. A gRPC server calls `server.stop(grace_period_seconds)` for the
   same purpose on its side.
3. Process exit — all of this has to fit inside the Pod's total `terminationGracePeriodSeconds`
   budget, or the SIGKILL cuts the drain off mid-flight regardless of how well the application itself
   behaves.

---

## 4 · Health Endpoints

- **Liveness**: cheap, local, no dependency checks — "is the process itself alive and not deadlocked."
  Checking a downstream DB in a liveness probe is the exact mistake covered in
  [Kubernetes Operations §2](kubernetes-operations.md#2--probes-readiness-vs-liveness-vs-startup): a
  slow DB then kills otherwise-healthy Pods and adds restart load onto an already-struggling
  dependency.
- **Readiness**: allowed, and expected, to check real dependencies — DB connection pool up, required
  caches warmed, a downstream auth service reachable — because failing readiness only pulls the Pod
  from traffic, it doesn't restart anything.
- A plain `/healthz` HTTP endpoint works fine for the Flask side. For a **pure gRPC port**, an HTTP
  probe can't speak the protocol at all — use the standard gRPC health-checking protocol (a
  `Health`/`Watch` service every language's gRPC library implements) with `grpc_health_probe` as an
  `exec` probe command, or a native `grpc` probe type
  (`spec.containers[].readinessProbe.grpc.port`) on recent Kubernetes versions.

---

## 5 · Twelve-Factor Config

- Config (DB URLs, feature flags, downstream endpoints) comes from the environment, never baked into
  the image — the same image should be deployable unchanged to every environment. Maps directly onto
  ConfigMaps (non-secret) and Secrets (credentials) from
  [Kubernetes Core §9](kubernetes-core.md#9--configmaps--secrets), injected as env vars or mounted
  files.
- **Fail fast**: validate required config at process startup, before the readiness probe can possibly
  pass — a missing env var should surface as a `CrashLoopBackOff` diagnosable in seconds from
  `kubectl logs`, not as an intermittent 500 three hours into production traffic once that code path
  finally runs.
- Prefer mounted-file config over env vars for anything that needs to change without a restart — env
  vars are a one-time snapshot at container start, while a mounted ConfigMap file is kept in sync by
  the kubelet and an app can watch it for changes; readiness/liveness stay green throughout.

---

## 6 · Monorepo Image Builds

A large backend commonly lives in one monorepo. The naive `docker build .` at the repo root sends the
**entire repo** as build context to the daemon (slow) and makes every individual service's image
cache-invalidate on unrelated changes anywhere else in the repo.

Practical fixes:

- A per-service `.dockerignore` (or a build tool that constructs a minimal context) excluding
  everything except that service's own path plus the specific shared-library paths it actually
  imports.
- Pin shared internal packages by version/hash, so a shared-lib bump is a deliberate, visible
  dependency change rather than an invisible cache-buster hitting every service at once.
- For very large dependency graphs, a build system with real dependency-graph awareness (Bazel is the
  standard name here) so only services whose actual dependency closure changed get rebuilt at all.
- The Dockerfile itself commonly needs `COPY` paths scoped to `services/<name>/` plus
  `libs/<shared>/` rather than a single flat `COPY . .` — precisely so
  [layer caching](docker-and-containers.md#2--image-layers--caching) stays meaningful in a monorepo
  instead of invalidating on every commit to any service, anywhere in the tree.

---

## Interview questions

1. **A Flask app is under real production load — sync, gthread, or gevent gunicorn workers, and
   why?**
   Depends on whether handlers are CPU-bound or I/O-bound: sync ties up a whole worker process per
   blocking call, so an I/O-heavy service (calling other services, hitting a DB) needs gthread or
   gevent for real concurrency per process; a genuinely CPU-bound service gets little benefit from
   either and should just size sync workers to available cores.

2. **Why is `2 × cores + 1` the wrong worker-count formula for an I/O-heavy service?**
   It assumes CPU is the bottleneck. For I/O-bound work the real constraint is concurrent in-flight
   requests and downstream connection-pool limits — a service can profitably run far more concurrency
   than that formula suggests if most of the time is spent waiting on the network, not the CPU.

3. **A rolling deploy causes a burst of connection-reset errors even though the app shuts down
   cleanly on SIGTERM. Why?**
   The race between "Pod removed from Service Endpoints" and "in-flight traffic has actually stopped
   arriving" — some callers still send requests for a brief window after shutdown begins. Fixed with a
   short `preStop` sleep before SIGTERM is even delivered.

4. **Should a liveness probe check the database? Why or why not?**
   No — liveness failing triggers a restart, not a traffic pull. A slow DB would then cause kubelet to
   kill healthy processes and add restart load onto the struggling DB itself. Dependency health
   belongs in the readiness probe, which only removes the Pod from traffic.

5. **How do you health-check a service that only speaks gRPC, with no HTTP port at all?**
   The standard gRPC health-checking protocol's `Health`/`Watch` service, probed with
   `grpc_health_probe` as an `exec` probe, or a native `grpc` readiness/liveness probe type on recent
   Kubernetes — a plain HTTP probe cannot speak to a pure gRPC listener.

6. **What does `PYTHONUNBUFFERED=1` actually fix in a containerized Python app?**
   Python buffers stdout when it's not attached to a TTY (always true in a container). Without this,
   log lines can sit in a buffer instead of reaching `kubectl logs` promptly — a real problem when
   you're trying to read logs live during an incident.

7. **In a monorepo, why does changing one service's code sometimes trigger a rebuild of an unrelated
   service's image?**
   A flat build context and Dockerfile (`COPY . .` at the repo root) with no dependency-graph-aware
   build boundary — the naive setup treats every commit anywhere in the repo as relevant to every
   service's image cache.

8. **A feature flag is stored as an environment variable, and picking up a change requires a full
   redeploy. What would you change?**
   Move it to a mounted ConfigMap file instead of an env var — env vars are a one-time snapshot at
   container start, while a mounted file is kept in sync live by the kubelet, letting the app watch
   and reload without a restart.
