# Container Runtimes & cri-o

> **Priority:** Recommended
> **Est. time:** 20 min
> **Track:** Both
> **HelloInterview:** none

The layer between kubelet and the actual `namespaces`/`cgroups` work in
[Docker & Containers](docker-and-containers.md#1--what-a-container-actually-is). Short by design —
this is precise plumbing knowledge, not a topic with much surface area, but the job description names
cri-o specifically, so the vocabulary needs to be exact.

---

## 1 · Why This Layer Exists

kubelet does not run containers itself. It delegates to a pluggable runtime over a stable API, so
Kubernetes isn't hard-wired to one container engine. That API is the **CRI**.

---

## 2 · The Container Runtime Interface (CRI)

A gRPC API between kubelet and the runtime — fittingly the same RPC framework in heavy use
elsewhere in a Python/Go backend — with two services:

- **RuntimeService**: pod sandbox lifecycle (create/start/stop/remove the shared network namespace a
  Pod's containers live in) and container lifecycle within it, plus `exec`/`attach`/`port-forward`
  plumbing.
- **ImageService**: pull, list, and remove images.

kubelet is the CRI **client**; containerd and CRI-O are CRI **servers**.

---

## 3 · containerd vs. CRI-O vs. the dockershim Removal

- Docker predates both Kubernetes and the CRI. Early Kubernetes talked to the full Docker Engine
  through an in-tree translation layer (**dockershim**) that converted kubelet's CRI-shaped calls into
  Docker Engine's own, non-CRI API.
- Dockershim was **removed in Kubernetes 1.24** (2022) — not because Docker-built images stopped
  working (a common misconception; standard OCI images from `docker build` run unmodified on any CRI
  runtime), but because maintaining a translation layer to an engine that was never CRI-native was
  ongoing maintenance cost for no upside once CRI-native runtimes had matured.
- **containerd**: originally extracted *from* Docker Engine as its core runtime component, donated to
  the CNCF, graduated. General-purpose and CRI-native; used directly by most managed Kubernetes node
  images (EKS, GKE, AKS) — and still sits underneath Docker Engine itself today.
- **CRI-O**: built by Red Hat specifically, and only, to implement the CRI — no non-Kubernetes use
  case, deliberately minimal, versioned in lockstep with Kubernetes releases, the default runtime on
  OpenShift.
- The practical interview-level distinction is **scope**, not capability: both are thin and both shell
  out to an OCI-level runtime for the actual namespace/cgroup work (§4) — containerd is a more
  general-purpose daemon with its own broader plugin/client ecosystem, CRI-O is deliberately just the
  CRI implementation and nothing else.

---

## 4 · OCI Runtime Spec & runc

Two separate OCI specs get conflated in casual conversation:

- **Image Spec** — layer format, manifest, config; what `docker build` produces.
- **Runtime Spec** — the on-disk `config.json` describing namespaces/cgroups/mounts for one container
  instance; what actually gets executed.

**runc** is the reference implementation of the OCI Runtime Spec: given a bundle (a root filesystem +
`config.json`), it performs the actual `clone()`/`unshare()`/cgroup setup described in
[Docker & Containers](docker-and-containers.md#1--what-a-container-actually-is) and then execs the
process. Both containerd and CRI-O call an OCI runtime — runc, by default — as their last step.

---

## 5 · Alternatives to runc

| Runtime | Approach | Trade-off |
|---|---|---|
| **crun** | C reimplementation of the same OCI spec | Lower memory/startup overhead than Go-based runc; CRI-O's default on some distros |
| **gVisor** (`runsc`) | Intercepts syscalls in userspace, implements its own kernel-like layer | Much stronger isolation for untrusted workloads, at a syscall-latency cost |
| **Kata Containers** | Runs each container/Pod inside its own lightweight VM | Real hardware-virtualization isolation, still speaks the same OCI/CRI interface |

Reach for gVisor or Kata specifically when tenant isolation matters more than raw shared-kernel
performance — running arbitrary or untrusted user code is the textbook case. Default to runc/crun
otherwise; the shared-kernel isolation namespaces/cgroups provide is sufficient for your own trusted
services.

---

## 6 · Debugging at the CRI Layer

`crictl` is the CRI-level analogue of the `docker` CLI — it talks directly to whatever CRI socket is
configured (containerd or CRI-O), which makes it the right tool exactly when `kubectl` itself can't
reach a node; see [Kubernetes Debugging Playbook](kubernetes-debugging-playbook.md#9--node-notready).

```bash
crictl ps                  # running containers, CRI-level view
crictl pods                 # pod sandboxes
crictl images
crictl logs <container-id>
crictl inspect <container-id>
```

---

## 7 · The Stack, Summarized

| Layer | Example | Talks to |
|---|---|---|
| Orchestrator | kubelet | CRI (gRPC) |
| CRI implementation | containerd, CRI-O | An OCI runtime |
| OCI runtime | runc, crun, runsc, kata-runtime | Kernel namespaces/cgroups (or a VM) |

---

## Interview questions

1. **What problem does the CRI actually solve, in one sentence?**
   It's a stable, pluggable API between kubelet and the container runtime, so Kubernetes isn't
   hard-wired to one specific engine.

2. **Why was dockershim removed, and did that break running Docker-built images on Kubernetes?**
   It was removed for the ongoing maintenance cost of translating to a non-CRI-native engine once
   CRI-native alternatives had matured — it did not break anything for users, since standard OCI
   images produced by `docker build` run unmodified on any CRI runtime.

3. **What's the practical difference between containerd and CRI-O?**
   Scope, not raw capability — containerd is a general-purpose daemon with a broader ecosystem beyond
   just Kubernetes; CRI-O is deliberately minimal and built only to implement the CRI. Both are
   CRI-native and both ultimately call an OCI runtime for the real work.

4. **Where does runc actually fit relative to containerd/CRI-O?**
   One layer down — it's the OCI runtime both shell out to for the actual `clone()`/cgroup-setup work
   that creates the container; containerd/CRI-O handle the CRI-facing lifecycle and image management
   above it.

5. **When would you reach for gVisor or Kata Containers instead of runc?**
   When tenant isolation matters more than shared-kernel performance — running arbitrary or untrusted
   user code is the clearest case, since both provide stronger isolation than namespaces/cgroups alone
   at the cost of overhead runc doesn't have.

6. **What does `crictl` give you that `kubectl` can't?**
   Node-local, CRI-level visibility when the problem is below or outside kubectl's own reach — e.g.
   the kubelet-to-API-server path is itself broken, or you need to see exactly what the runtime thinks
   is running on a specific node.
