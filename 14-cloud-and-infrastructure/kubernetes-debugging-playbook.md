# Kubernetes Debugging Playbook

> **Priority:** Required
> **Est. time:** 40 min
> **Track:** Both
> **HelloInterview:** none

An on-call reference, not an explanation — [Kubernetes Core](kubernetes-core.md) and
[Kubernetes Operations](kubernetes-operations.md) cover *why* these objects behave this way; this
file is the fast lookup for *what to type* when a symptom shows up. Triage is always top-down:
**status → describe (Events) → logs → exec/debug.** Almost every entry below is really just that
sequence applied to one specific symptom.

---

## 1 · Quick-Reference Table

| Symptom | Most likely cause(s) | First command |
|---|---|---|
| `CrashLoopBackOff` | App exits non-zero at startup; misconfig, missing dependency; or it's actually a repeated OOMKill in disguise | `kubectl logs <pod> --previous` |
| `ImagePullBackOff` / `ErrImagePull` | Wrong tag/registry, missing `imagePullSecrets`, registry auth/rate-limit, wrong architecture | `kubectl describe pod <pod>` |
| `Pending` | Unschedulable: insufficient resources, no node matches affinity/taint, unbound PVC | `kubectl describe pod <pod>` (Events) |
| `OOMKilled` | Memory limit too low for real usage, a genuine leak, or a legitimate burst | `kubectl describe pod <pod>` (Last State) |
| Readiness flapping | Probe too strict, dependency intermittently slow, CPU throttling delaying the check itself | `kubectl describe pod` + `kubectl get events` |
| DNS failures | CoreDNS down/overloaded, NetworkPolicy blocking port 53, `ndots` search-domain overhead | `kubectl exec ... -- nslookup ...` |
| Service has no endpoints | Selector/label mismatch, no Pods Ready, wrong `targetPort` | `kubectl get endpoints <svc>` |
| Node `NotReady` | kubelet down, CNI broken, disk/PID pressure, control-plane network partition | `kubectl describe node <node>` |

---

## 2 · CrashLoopBackOff

`CrashLoopBackOff` describes restart *timing* (kubelet backs off 10s, 20s, 40s... capped at 5m
between attempts) — it is not itself a diagnosis.

```bash
kubectl get pod <pod> -o wide
kubectl describe pod <pod>          # Last State + Reason, Events
kubectl logs <pod>                  # current attempt's stdout/stderr — may be empty if it crashed instantly
kubectl logs <pod> --previous       # the PREVIOUS crashed container's logs — usually the useful one
kubectl get pod <pod> -o jsonpath='{.status.containerStatuses[0].lastState}'
```

Read `Last State: Terminated: Reason:` in `describe` first: `OOMKilled` sends you to
[resource limits](kubernetes-operations.md#3--resource-requests--limits); `Error` with a non-zero
exit code sends you to `--previous` logs and the app itself; `Completed` (exit 0) on something meant
to run forever usually means a wrong `ENTRYPOINT`/`CMD` or a process that daemonizes instead of
running in the foreground — see
[Docker & Containers](docker-and-containers.md#5--entrypoint-vs-cmd).

---

## 3 · ImagePullBackOff / ErrImagePull

```bash
kubectl describe pod <pod>     # Events line has the literal registry error string
kubectl get pod <pod> -o jsonpath='{.spec.containers[0].image}'
kubectl get sa <serviceaccount> -o yaml | grep -A3 imagePullSecrets
```

Causes: a typo'd tag, an image that doesn't exist for the node's architecture (arm64 vs. amd64), a
private registry needing `imagePullSecrets` not attached to the Pod's ServiceAccount, anonymous
registry rate-limiting, or — as often as not — the node's own IAM role lacking ECR pull permission,
which is an AWS problem wearing a Kubernetes symptom; see
[Terraform & AWS](terraform_aws_overview.md). The `Events` block in `describe` almost always contains
the exact registry error (`401`, `manifest unknown`, `toomanyrequests`) — read it before guessing.

---

## 4 · Pending

`Pending` means the scheduler has not bound the Pod to any node **at all** yet.

```bash
kubectl describe pod <pod>               # Events: "0/6 nodes are available: 3 Insufficient cpu, ..."
kubectl get nodes -o wide
kubectl describe node <candidate-node>   # Allocatable vs. Allocated, Taints
kubectl get pvc                          # STATUS column — Pending PVC blocks the Pod that mounts it
kubectl get resourcequota -n <ns>
```

The scheduler explains itself: `Events` gives a per-predicate rejection count, e.g.
*"2 node(s) had taint that the pod didn't tolerate, 4 Insufficient memory"* — that line names the
exact knob to turn (add capacity, fix a toleration, raise a quota, or wait on a PVC/StorageClass).

---

## 5 · OOMKilled

```bash
kubectl describe pod <pod>     # Last State: Terminated, Reason: OOMKilled, Exit Code: 137
kubectl top pod <pod>          # needs metrics-server — current usage vs. limit
kubectl get pod <pod> -o jsonpath='{.spec.containers[0].resources}'
```

Exit code **137 = 128 + SIGKILL(9)** — the same arithmetic whether Kubernetes or plain Docker did the
killing. Distinguish "limit too low for legitimate peak usage" (raise the limit, or fix the
request/limit ratio — see [Kubernetes Operations](kubernetes-operations.md#4--qos-classes--eviction))
from "an actual leak" (a profiling problem inside the app, not a YAML fix): if OOMKills correlate with
traffic spikes, it's sizing; if usage climbs monotonically with Pod age regardless of traffic, it's a
leak.

---

## 6 · Readiness Flapping

```bash
kubectl get events --sort-by=.lastTimestamp | grep <pod>
kubectl describe pod <pod>            # "Readiness probe failed: ..." with the actual status/timeout
kubectl get endpoints <svc> -o yaml   # watch the Pod's IP appear and disappear
```

Widen `failureThreshold`/`periodSeconds` before assuming an app bug — real jitter (GC pause,
connection-pool contention, a downstream's own p99, or CPU throttling from an undersized limit
delaying the probe handler itself) can trip an overly tight threshold. If the readiness endpoint does
real dependency checks, give it its own short internal timeout separate from the probe's, so a slow
dependency fails fast and predictably instead of eating the whole probe window.

---

## 7 · DNS Failures

```bash
kubectl -n kube-system get pods -l k8s-app=kube-dns
kubectl -n kube-system logs -l k8s-app=kube-dns
kubectl run -it --rm dnsdebug --image=busybox:1.36 --restart=Never -- nslookup <service>.<namespace>.svc.cluster.local
kubectl exec -it <pod> -- cat /etc/resolv.conf
```

If `nslookup` from a **fresh debug Pod** works but the actual app Pod can't resolve anything, suspect
a `NetworkPolicy` scoped to that app's namespace/labels blocking egress to CoreDNS on port 53 —
rather than CoreDNS itself. Also worth knowing: default `ndots:5` search-domain expansion means an
external hostname can generate up to 5x the DNS queries you'd expect before it falls through to the
real answer — a latency/quota issue that looks like "DNS is slow," not "DNS is broken."

---

## 8 · Service Has No Endpoints

```bash
kubectl get endpoints <svc>              # empty ADDRESSES column is the smoking gun
kubectl get svc <svc> -o yaml | grep -A3 selector
kubectl get pods --show-labels -l <same-selector-as-svc>
kubectl get pods -o wide                 # are the matching pods even Ready?
```

An empty `Endpoints` object with Pods that *look* like they should match means one of two things:
the selector doesn't actually match (compare the Service's `Selector` line against `--show-labels`
character-by-character — a stray typo or a template that changed is the usual culprit) or every
matching Pod is simply not Ready — check readiness (see
[Kubernetes Operations](kubernetes-operations.md#2--probes-readiness-vs-liveness-vs-startup)) before
assuming the Service itself is broken; a Service with correct config and zero Ready Pods is working
exactly as designed.

---

## 9 · Node NotReady

```bash
kubectl get nodes
kubectl describe node <node>       # Conditions: Ready / MemoryPressure / DiskPressure / PIDPressure / NetworkUnavailable
kubectl get pods -A -o wide --field-selector spec.nodeName=<node>
# on the node itself, if reachable:
systemctl status kubelet
systemctl status containerd        # or crio
crictl ps                          # CRI-level view — see Container Runtimes & cri-o
journalctl -u kubelet -n 200
```

`describe node`'s `Conditions` block names which pressure signal tripped. If the node isn't
reporting at all (no recent lease renewal), the fix is at the infrastructure layer — instance health,
autoscaling group replacement — not inside Kubernetes; see
[Terraform & AWS](terraform_aws_overview.md). `crictl` (see
[Container Runtimes & cri-o](container-runtimes-cri-o.md#6--debugging-at-the-cri-layer)) is the tool
when even the container runtime, not just kubelet, is suspect.

---

## 10 · General Toolkit

- `kubectl get events --sort-by=.lastTimestamp -A` — cluster-wide chronological event feed; the
  single best "what just happened" command, and the first thing to run on almost anything.
- `kubectl exec -it <pod> -- sh` — only works if the container image has a shell. For distroless or
  `scratch` images (see [Docker & Containers](docker-and-containers.md#4--image-size--security)),
  use `kubectl debug <pod> -it --image=busybox --target=<container>` to attach an ephemeral debug
  container sharing the target's process namespace instead.
- `kubectl port-forward <pod> 8080:8080` — reach a Pod directly, bypassing Service/Ingress entirely,
  to isolate "is this the app or the routing in front of it."
- `kubectl top pod` / `kubectl top node` — requires `metrics-server`; an error here is itself a
  finding, not a dead end.
- `crictl` — the CRI-level equivalent of the `docker` CLI, for when `kubectl` can't reach a node at
  all — see [Container Runtimes & cri-o](container-runtimes-cri-o.md).

---

## Interview questions

1. **A Pod is stuck `CrashLoopBackOff` — walk through your first three commands.**
   `kubectl describe pod` for Last State/Reason and Events, `kubectl logs <pod> --previous` for the
   crashed attempt's actual output, then branch on the reason: OOMKilled → resource limits; non-zero
   exit → application logs; exit 0 → entrypoint/foreground-process mismatch.

2. **Exit code 137 — what does it mean, and what are the two different things that commonly cause it?**
   128 + signal 9 (SIGKILL). Either the kubelet's OOM path killed the container for exceeding its
   memory limit, or the process ignored SIGTERM (a PID 1/signal-handling bug) and got hard-killed
   after `terminationGracePeriodSeconds` expired — see
   [Docker & Containers](docker-and-containers.md#6--signal-handling--pid-1).

3. **`kubectl get svc` shows the Service, but curling it times out. Where do you look?**
   `kubectl get endpoints <svc>` first — an empty result means either the selector doesn't match any
   Pod's labels or no matching Pod is Ready. If Endpoints looks populated, check `targetPort` against
   the container's actual listening port next.

4. **A node shows `NotReady` — how do you tell whether it's a Kubernetes problem or an infrastructure
   problem?**
   `kubectl describe node` — a specific pressure Condition (Disk/Memory/PID) points inside the node;
   no recent status update at all (stale lease) points at the node being unreachable from the control
   plane, which is an infrastructure-layer question (instance health, networking, autoscaling group).

5. **Why might `kubectl logs` show nothing useful for a crash-looping Pod, and what do you run
   instead?**
   The current attempt may not have logged anything before dying, or may have just restarted with a
   fresh, empty log stream. `kubectl logs --previous` gets the terminated container's own logs, which
   is usually where the actual error is.

6. **DNS resolution works from a fresh debug Pod but fails from the app Pod in the same namespace —
   what's your hypothesis?**
   A `NetworkPolicy` scoped to the app's labels blocking egress to CoreDNS on port 53, rather than
   CoreDNS itself being down — CoreDNS being genuinely unhealthy would break the fresh debug Pod too.

7. **What's the practical difference between a Pod stuck `Pending` and one stuck `CrashLoopBackOff`,
   in terms of what phase failed?**
   `Pending` means the scheduler never bound it to a node — a placement/capacity problem, before the
   container ever ran. `CrashLoopBackOff` means it *was* scheduled and started, and the container
   process itself keeps exiting — a runtime/application problem.

8. **A rollout looks stuck, not failed — new Pods exist but traffic never seems to shift to them. What
   do you check?**
   Readiness on the new ReplicaSet's Pods specifically — an unpassing readiness probe on the new
   version freezes the Deployment controller's progression by design; see
   [Kubernetes Operations](kubernetes-operations.md#1--rollouts--rollback).
