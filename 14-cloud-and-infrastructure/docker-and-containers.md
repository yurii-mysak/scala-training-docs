# Docker & Containers

> **Priority:** Required
> **Est. time:** 40 min
> **Track:** Both
> **HelloInterview:** none

Kubernetes schedules containers; it doesn't define what one *is*. This file is the mechanism a
level below [Kubernetes Core](kubernetes-core.md) — namespaces and cgroups, images, and the process
model — that every K8s abstraction (resource limits, Pod networking, signal handling during a
rollout) is ultimately built out of.

---

## 1 · What a Container Actually Is

A container is **not** a lightweight VM. There's no hypervisor and no separate kernel — every
container on a host shares that host's kernel. A container is an ordinary Linux process with a
restricted *view* of the system (namespaces) and a restricted *share* of its resources (cgroups).
Weaker isolation than a VM is the direct consequence of sharing one kernel — the reason gVisor and
Kata Containers exist, covered in
[Container Runtimes & cri-o](container-runtimes-cri-o.md#5--alternatives-to-runc).

**Namespaces** — what the process can *see*:

| Namespace | Isolates |
|---|---|
| PID | Its own process tree — PID 1 inside is not PID 1 on the host |
| NET | Its own interfaces, routes, ports |
| MNT | Its own filesystem mount table — this is what makes the image's root look like `/` |
| UTS | Its own hostname |
| IPC | Its own System V IPC / POSIX message queues |
| USER | Maps container UID 0 to an unprivileged host UID (rootless containers) |

**cgroups** — what the process can *use*: CPU shares/quota, memory ceiling, block I/O, PID count.
This is the literal kernel mechanism behind Kubernetes `resources.requests`/`resources.limits` — a
Pod's `limits.memory: 512Mi` becomes, almost directly, a cgroup memory limit on that container's
cgroup; see [Kubernetes Operations](kubernetes-operations.md#3--resource-requests--limits). cgroups
v2 (a single unified hierarchy) is what current kubelet/containerd/cri-o assume by default; v1's
per-controller hierarchies were a long-running source of subtle inconsistencies.

`docker run`, mechanically: pull the image → create a fresh set of namespaces and a cgroup → mount
the image's layers as the root filesystem inside the new MNT namespace → exec the entrypoint as
PID 1 inside that namespace set.

---

## 2 · Image Layers & Caching

- An image is a stack of read-only layers plus a JSON config (env, entrypoint, etc.) and a manifest.
  Each Dockerfile instruction that touches the filesystem produces one new, content-addressed layer.
- **Union filesystem** (overlay2 on Linux): layers stack transparently; a *running* container adds one
  thin writable layer on top (copy-on-write). Writing heavily into that writable layer instead of a
  volume is exactly why a long-running container's disk usage can balloon unexpectedly.
- **Build cache**: a layer is reused only if its instruction *and every preceding layer* are
  byte-identical to a previous build. Practical rule — order instructions least-to-most frequently
  changing:

  ```dockerfile
  COPY requirements.txt .
  RUN pip install -r requirements.txt   # cached until requirements.txt itself changes
  COPY . .                              # changes every commit; stays a cheap, late layer
  ```

- `.dockerignore` keeps the build context small and keeps unrelated changes (docs, `.git`) from
  invalidating layers or leaking into the image.

---

## 3 · Multi-Stage Builds

Compilers, build tools, and full SDKs have no business in a runtime image — bigger attack surface,
bigger pull time, bigger image. `FROM ... AS build` does the compiling; a fresh `FROM` for the
runtime stage `COPY --from=build`s only the finished artifact.

```dockerfile
FROM python:3.11-slim AS build
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=build /root/.local /root/.local
COPY . /app
WORKDIR /app
ENV PATH=/root/.local/bin:$PATH
USER 1000
ENTRYPOINT ["gunicorn", "app:app"]
```

A statically-linked Go binary is the cleanest possible illustration — the runtime stage needs
nothing else at all:

```dockerfile
FROM golang:1.22 AS build
WORKDIR /src
COPY . .
RUN CGO_ENABLED=0 go build -o /app ./cmd/server

FROM gcr.io/distroless/static-debian12
COPY --from=build /app /app
ENTRYPOINT ["/app"]
```

The Python case gets a full production-shaped walkthrough in
[Deploying Python Services](deploying-python-services.md#1--containerizing-a-flaskgrpc-service).

---

## 4 · Image Size & Security

- **Base image choice**: `-slim` variants trim docs and build tooling; Alpine trims further via musl
  libc instead of glibc — smaller, but a real compatibility trap for some Python wheels/native
  extensions that assume glibc and either fail to install or silently misbehave on musl. Distroless
  or `scratch` has no shell and no package manager at all — the smallest attack surface, but nothing
  to `exec` into for debugging (this is exactly why `kubectl debug` ephemeral containers exist — see
  [Kubernetes Debugging Playbook](kubernetes-debugging-playbook.md#10--general-toolkit)).
- **Run as non-root**: `USER` in the Dockerfile, or Kubernetes `securityContext.runAsNonRoot` — a
  container escape is far more dangerous if the escaped process is root.
- **Read-only root filesystem** where possible (`securityContext.readOnlyRootFilesystem: true` plus
  explicit writable volumes only for the paths that genuinely need them) shrinks what a compromised
  process can persist or tamper with.
- **Pin base images by digest** (`@sha256:...`), not just a tag — a tag, even a version tag, can move
  under you; a digest can't.
- **Secrets baked into an early layer are not removed by deleting them in a later one.** The earlier
  layer — and the secret inside it — is still present in the image and extractable directly from the
  layer blobs (`docker history` shows the command; pulling the layer gets you the file). Never `COPY`
  a secret and `RUN rm` it later; use build-time secret mounts (`--mount=type=secret`) or fetch at
  runtime instead.
- Image scanning for known-CVE base packages (Trivy/Grype-class tooling) belongs in CI as a gate, not
  as a manual, skippable step.

---

## 5 · ENTRYPOINT vs. CMD

- **Exec form** — `["executable", "arg"]` — runs the process directly as PID 1.
  **Shell form** — `executable arg`, no brackets — runs it as a child of `/bin/sh -c '...'`, an extra
  process in between.
- `ENTRYPOINT` is the fixed command; `CMD` supplies default arguments to it (or is the whole command
  if no `ENTRYPOINT` is set). `docker run image arg` overrides `CMD` but not `ENTRYPOINT` — the
  standard pattern is a fixed exec-form `ENTRYPOINT` binary with a `CMD` default-args array, so callers
  can override just the arguments.
- Mixing shell-form with the expectation that `docker stop` (or Kubernetes' SIGTERM) reaches your app
  directly is the single most common signal-handling bug — see next section.

---

## 6 · Signal Handling & PID 1

- Linux gives PID 1 special treatment: default signal dispositions (like "terminate on SIGTERM") are
  **not** applied to PID 1 unless the process explicitly installs a handler for it. This is a kernel
  rule, not a container-specific one — containers just happen to be where people run arbitrary
  processes *as* PID 1 and get bitten by it.
- Shell-form `CMD`/`ENTRYPOINT` makes `/bin/sh` PID 1, and `sh` doesn't forward signals to the child
  it exec'd unless written to do so — so `docker stop`'s SIGTERM can go nowhere, the runtime falls
  back to SIGKILL after the grace period, and the app never gets a chance to shut down cleanly.
- PID 1 is also responsible for **reaping zombie processes** (children that exited but whose status
  hasn't been collected) — most application runtimes were never designed to run as PID 1 and never
  implemented this.
- **Fix**: exec-form entrypoint so your real process *is* PID 1 with actual signal handlers installed,
  or front it with a minimal init (`tini`, `dumb-init`, or `docker run --init`) that becomes PID 1,
  forwards signals, and reaps zombies for you.
- The full chain in Kubernetes: kubelet marks the Pod Terminating → sends SIGTERM (optionally after a
  `preStop` hook runs) → the app has `terminationGracePeriodSeconds` (default 30s) to exit cleanly →
  SIGKILL if it hasn't. Getting this right for a real service — including the readiness-vs-SIGTERM
  race — is worked through fully in
  [Deploying Python Services](deploying-python-services.md#3--graceful-shutdown).

---

## 7 · Container Networking Basics

- **Default bridge network**: Docker creates a virtual bridge (`docker0`); each container gets a
  veth pair into it and a private IP. `-p hostPort:containerPort` sets up a host NAT/DNAT rule so
  external traffic can reach an otherwise-private container IP — see
  [NAT, DMZ & VPN](../10-networking/Networking-NAT-DMZ-VPN.md) for the NAT mechanics underneath it.
- **User-defined bridge networks** add an embedded DNS server so containers can resolve each other by
  name — the plain default bridge does not have this.
- This is deliberately simpler than Kubernetes networking, which requires every Pod to get a real,
  cluster-routable IP with **no NAT between Pods** (the "flat network" contract any CNI plugin must
  satisfy). Services and kube-proxy (see [Kubernetes Core](kubernetes-core.md#7--services)) are the
  layer that replaces what `-p` and Docker's embedded DNS do for a single host, at cluster scale.

---

## 8 · Volumes

- **Named volumes**: managed by the runtime, live outside any container's writable layer, survive
  container removal — the recommended default for anything that needs to persist.
- **Bind mounts**: map an exact host path in — great for local dev (mounting live source), risky in
  production (couples the container to a specific host filesystem layout).
- **tmpfs mounts**: RAM-backed, never touch disk, gone when the container stops — for secrets you
  don't want swapped to disk or left behind.
- All three bypass the layered union filesystem's copy-on-write entirely, which is also a performance
  reason to use them for anything write-heavy (databases, logs) instead of the container's own
  writable layer.
- Kubernetes generalizes the same idea into PersistentVolume/PersistentVolumeClaim — a
  StorageClass-driven abstraction over this, decoupled from any single node — see StatefulSets in
  [Kubernetes Core](kubernetes-core.md#4--statefulsets).

---

## Interview questions

1. **What is a container, mechanically — no "lightweight VM" hand-waving?**
   A normal Linux process with a restricted view of the system via namespaces (PID, NET, MNT, UTS,
   IPC, USER) and a restricted resource share via cgroups. No hypervisor, no separate kernel — every
   container on the host shares the host kernel.

2. **Why doesn't deleting a secret in a later Dockerfile layer actually remove it from the image?**
   Layers are immutable and content-addressed; the earlier layer containing the secret still exists
   in the image and is directly extractable from its layer blob regardless of what a later layer does.

3. **Your process ignores `docker stop` (or Kubernetes' SIGTERM) and always gets hard-killed after the
   grace period. Why?**
   Almost always a shell-form `ENTRYPOINT`/`CMD` — `/bin/sh` is PID 1 and doesn't forward the signal
   to the actual application process. Fix with exec form, or a minimal init like `tini`/`dumb-init`.

4. **ENTRYPOINT vs. CMD — why does the distinction matter for how a container image gets reused?**
   `ENTRYPOINT` is the fixed command; `CMD` is overridable default arguments. Exec-form `ENTRYPOINT`
   with a `CMD` args array lets callers override just the arguments (`docker run image --flag`)
   without needing to know or replace the underlying binary.

5. **Why can hitting a CPU limit and hitting a memory limit look completely different from inside the
   container?**
   CPU is compressible — a cgroup CPU limit just throttles the process (CFS quota), so it keeps
   running, only slower. Memory is incompressible — exceeding a memory cgroup limit gets the process
   OOM-killed outright, with no graceful degradation possible.

6. **How would you shrink a Python service's image without breaking native dependency wheels?**
   Prefer `-slim` over Alpine unless every dependency is confirmed musl-compatible — Alpine's smaller
   size can silently break wheels built against glibc; multi-stage build to drop compilers from the
   final image regardless of which base is chosen.

7. **You `COPY` the whole repo and every build reinstalls all dependencies even though only
   application code changed. Why, and how do you fix it?**
   Dependency manifests and source are copied together (or manifests copied *after* source), so any
   source change invalidates the cache from that layer onward. Fix by copying and installing from the
   dependency manifest first, source last.

8. **Why is a compromised root container meaningfully worse than a compromised non-root one, given
   both share the host kernel either way?**
   Root inside the container's user namespace maps to broader capabilities and, without a user
   namespace remapping UID 0, potentially to root on the host if a namespace-escape vulnerability is
   ever exploited — non-root shrinks that specific blast radius even though the shared-kernel
   isolation boundary is the same either way.
