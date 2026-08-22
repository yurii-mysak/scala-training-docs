# Kubernetes Operations: Keeping It Running

> **Priority:** Required
> **Est. time:** 45 min
> **Track:** Both
> **HelloInterview:** none

[Kubernetes Core](kubernetes-core.md) covers the object model; this file covers what happens when
those objects meet real traffic, real node failures, and real capacity limits. Every primitive here
is presented with the specific outage it exists to prevent — that framing is deliberate, because
that's how it gets asked: not "what is an HPA" but "your service fell over during a routine deploy,
what do you check."

---

## 1 · Rollouts & Rollback

- Default strategy is `RollingUpdate`: replace old Pods with new ones incrementally, bounded by two
  knobs — `maxSurge` (how many extra Pods above `replicas` are allowed during the rollout) and
  `maxUnavailable` (how many Pods below `replicas` are tolerated). Defaults are 25%/25%. `Recreate`
  kills all old Pods before creating any new one — simpler, but a guaranteed downtime window.
- **Rollouts and readiness are the same mechanism.** A new Pod only counts as "available" once it
  passes its readiness probe (see below) — if the new version's readiness probe never passes, the
  rollout doesn't fail loudly, it **stalls**: the Deployment controller won't scale down more old
  Pods than `maxUnavailable` allows, so you're stuck part-way rolled out until someone notices. This
  is a safety feature, not a bug, but it reads as "the deploy is hanging" to anyone who expects a
  hard failure.
- `kubectl rollout status deploy/x`, `kubectl rollout history deploy/x`,
  `kubectl rollout undo deploy/x [--to-revision=N]`. `revisionHistoryLimit` bounds how many old
  ReplicaSets (and therefore how far back `undo` can reach) are retained.
- Kubernetes has **no native canary or blue-green primitive** — a rolling update always eventually
  replaces 100% of Pods. Real percentage-based traffic splitting is either faked with replica-count
  ratios (crude: 1 canary Pod out of 20 is *roughly* 5% of traffic, not exactly, and only if all Pods
  get equal load) or done properly at L7 via a service mesh — see
  [Service Mesh & Envoy](service-mesh-and-envoy.md#4--l7-proxying-and-traffic-shifting) — or a
  progressive-delivery controller (Argo Rollouts, Flagger) layered on top.
- **Real failure prevented:** a rolling update with `maxUnavailable` set too high and no
  PodDisruptionBudget can take down more capacity than the system can absorb during an entirely
  routine, low-risk-looking deploy.

---

## 2 · Probes: Readiness vs. Liveness vs. Startup

| Probe | Failure means | Kubernetes does |
|---|---|---|
| **Startup** | App is still starting up | Suppresses liveness/readiness checks until it passes once |
| **Readiness** | Can't serve traffic *right now* | Removes the Pod from Service Endpoints — no restart |
| **Liveness** | Process is wedged/stuck | Kills and restarts the container |

Getting the *intent* backwards is the single most common probe mistake:

- **Liveness checking a downstream dependency** (e.g. pinging the database) is the classic
  self-inflicted outage: the DB gets slow under load → liveness times out → kubelet restarts an
  otherwise perfectly healthy process → the restart adds load to an already-struggling DB and briefly
  drops capacity further → more timeouts → restart storm. Liveness should answer "is *this process*
  alive," never "are my dependencies healthy." Dependency health belongs in readiness.
- **No readiness probe (or one that passes immediately)** means a brand-new Pod gets real traffic
  before its connection pools are warm or caches are populated — a visible error spike at exactly the
  moment of every rollout.
- **A borderline/too-strict readiness probe** causes flapping: the Pod cycles in and out of Endpoints,
  causing connection resets and retry storms on callers, and — worse — can stall a rolling update
  indefinitely if it flaps at the wrong instant (see §1).
- **No startup probe on a slow-booting app** means liveness's own `initialDelaySeconds` has to be set
  pessimistically long for the worst-case boot time, which then also slows down detecting a genuinely
  wedged process later in the Pod's life. A startup probe lets you tune the two independently: patient
  during boot, fast to react once running.
- Tuning fields: `initialDelaySeconds`, `periodSeconds`, `timeoutSeconds`, `failureThreshold`,
  `successThreshold`. `failureThreshold × periodSeconds` is your real detection latency for an actual
  outage — worth having as a concrete number, not just the field names, given this loop's emphasis on
  live napkin math.

---

## 3 · Resource Requests & Limits

- **Requests** are what the scheduler reserves — a node is only eligible for a Pod if its unreserved
  capacity covers the Pod's requests. This is a scheduling-time decision, not a runtime cap.
- **Limits** are the runtime ceiling, enforced via cgroups (the same mechanism described in
  [Docker & Containers](docker-and-containers.md#1--what-a-container-actually-is)) by the kubelet
  and container runtime.
- **CPU is compressible**: exceeding the limit gets you throttled (CFS quota) — the process keeps
  running, just slower. This can silently spike p99 latency with no crash, no event, no obvious
  signal short of checking throttling metrics directly.
- **Memory is incompressible**: exceeding the limit gets the container OOMKilled immediately, no
  warning, no drain — see the OOMKilled entry in
  [Kubernetes Debugging Playbook](kubernetes-debugging-playbook.md#5--oomkilled).
- **Real failure prevented:** no limits set at all lets one noisy Pod starve every other Pod
  scheduled on the same node ("noisy neighbor"); no requests set lets the scheduler bin-pack blind
  and overcommit a node, so it runs hot the moment real traffic isn't perfectly even across Pods.

---

## 4 · QoS Classes & Eviction

| Class | Condition | Evicted |
|---|---|---|
| **Guaranteed** | requests == limits, for every resource, every container | Last |
| **Burstable** | at least one request set, doesn't qualify as Guaranteed | Middle |
| **BestEffort** | no requests/limits at all | First |

- Under node memory pressure, the kubelet watches eviction signals (`memory.available`,
  `nodefs.available`, `imagefs.available`) against thresholds and, on breach, evicts Pods ranked by:
  is usage over its request? → then QoS class → then priority.
- BestEffort existing at all, and being evicted first, is deliberate — it's how you run genuinely
  low-priority/batch work that soaks up whatever capacity is left without an SLA, instead of pretending
  everything needs the same guarantees.
- **Real failure prevented:** a low-traffic but genuinely important Pod, run as BestEffort next to
  noisy BestEffort neighbors, gets evicted first during a shared node's memory pressure event —
  despite having done nothing wrong itself.

---

## 5 · HPA & VPA

- **HorizontalPodAutoscaler**: watches a metric (CPU/memory via `metrics-server`, or a custom/external
  metric) and adjusts **replica count** to drive utilization toward a target. Utilization is measured
  as a percentage of the Pod's *request*, not an absolute number — HPA is meaningless without requests
  set (§3).
- Scale-up reacts fast by default; scale-down has a stabilization window specifically to avoid
  flapping replica count on noisy short-term dips.
- **VerticalPodAutoscaler**: recommends or sets `requests`/`limits` per Pod based on observed usage.
  Modes: `Off` (recommend only), `Initial` (set once at Pod creation), `Auto`/`Recreate` (evicts and
  recreates running Pods with new sizing — itself a disruption event, not free).
- **Don't drive HPA and VPA off the same resource on the same workload.** VPA resizing a Pod's request
  changes the denominator HPA's utilization percentage is computed against, so each can trigger the
  other — a genuinely common, easy-to-miss misconfiguration.

---

## 6 · PodDisruptionBudgets

- A PDB constrains **voluntary** disruptions only — a node drain for an upgrade, cluster-autoscaler
  scaling a node down, an explicit `kubectl drain`/evict. It does **not**, and cannot, stop
  **involuntary** disruption — a node crashing, an OOM kill, the kubelet dying.
- Set `minAvailable` or `maxUnavailable` (mutually exclusive) against a label selector.
- **Real failure prevented:** a node-pool upgrade (voluntary drain) landing in the same window as a
  Deployment's own rollout (also voluntary, from the Deployment's perspective) — with 3 replicas and
  no PDB, both operations independently think they're allowed to take a Pod down "voluntarily" at the
  same time, and you can transiently hit zero Ready replicas even though each operation, evaluated
  alone, looked completely safe.
- A PDB that's *too* strict (e.g. `minAvailable: 100%` on a single-replica workload) can permanently
  block a drain — cluster-autoscaler or upgrade tooling stalls indefinitely waiting on a budget that
  can never be satisfied. Alert on stuck drains, not just on PDB violations.

---

## 7 · Node Affinity, Taints/Tolerations, and Scheduling

- **nodeSelector**: exact-label match, blunt.
- **nodeAffinity**: `requiredDuringSchedulingIgnoredDuringExecution` (hard filter) vs.
  `preferredDuringSchedulingIgnoredDuringExecution` (soft, weighted). "IgnoredDuringExecution" is the
  detail worth remembering: it's evaluated only at scheduling time, so relabeling a node later does
  **not** evict Pods that no longer match.
- **podAffinity / podAntiAffinity**: schedule relative to *other Pods*, not nodes — the standard way
  to spread replicas across a failure domain via `topologyKey: topology.kubernetes.io/zone`.
- **Taints** (on nodes) are the inverse of affinity — they repel Pods unless explicitly tolerated.
  `NoSchedule` (block new placements), `PreferNoSchedule` (soft), `NoExecute` (evict Pods already
  there that don't tolerate it, optionally after `tolerationSeconds`).
- Scheduling runs in two phases: **filtering** (which nodes are even legal — resources, taints,
  affinity, port conflicts) then **scoring** (which legal node is best — spreading, image-already-
  present, resource balance).
- **Real failure prevented:** 3 replicas with no anti-affinity or topology spread constraint can all
  land on the same node — or the same AZ — simply because that's where the scheduler found room. One
  node or AZ failure then takes down a service that looked safe on paper at "3 replicas."
  `topologySpreadConstraints` is the more precise modern tool for this versus `podAntiAffinity`.

---

## 8 · Failure → Primitive Reference

| Failure scenario | Primitive that prevents it |
|---|---|
| Traffic sent to a Pod that can't serve it yet | Readiness probe |
| A wedged process that never self-recovers | Liveness probe |
| Liveness killing a slow-booting app before it's up | Startup probe |
| Scheduler overcommitting a node | Resource requests |
| One Pod starving its neighbors | Resource limits |
| A drain/rollout coincidence dropping every replica at once | PodDisruptionBudget |
| Correlated failure from replicas sharing one node/AZ | Anti-affinity / topology spread |
| Under-provisioning for real traffic | HPA |
| Chronic over- or under-requesting drift | VPA |

---

## Interview questions

1. **Your rollout is stuck at 2/5 new Pods and hasn't progressed in ten minutes — what's your first
   check?**
   Readiness on the new ReplicaSet's Pods — `kubectl describe pod` on one of them and
   `kubectl rollout status`. A rollout stalls, it doesn't hard-fail, when new Pods never become Ready.

2. **Why must a liveness probe never check a downstream dependency?**
   Because failing liveness triggers a restart, not a traffic pull. If liveness depends on a slow DB,
   a struggling DB causes kubelet to kill healthy processes and add restart load onto the very
   dependency that's already failing — turning a slowdown into an outage.

3. **Explain QoS classes, and why BestEffort is allowed to exist if it's evicted first.**
   Guaranteed (requests==limits), Burstable (partial requests), BestEffort (none) — ranked in that
   order for eviction priority under node pressure. BestEffort exists on purpose: it's how low-value
   batch work absorbs spare capacity without an SLA, accepting first-to-go as the tradeoff.

4. **Why can HPA and VPA fight each other on the same workload?**
   HPA's target is a percentage of the Pod's resource *request*; VPA changes that request. Resize the
   request and you change what "100% utilization" means to HPA, so the two can each trigger a reaction
   to the other's last action.

5. **A node drain during a routine deploy took a 3-replica service to zero Ready Pods. Root cause?**
   No PodDisruptionBudget (or one too permissive) meant the drain's voluntary evictions and the
   Deployment's own rolling update were each individually "allowed," but uncoordinated — nothing
   stopped both from removing available replicas in the same window.

6. **Why does exceeding a CPU limit look completely different from exceeding a memory limit?**
   CPU is compressible — the kernel just throttles the process's CFS quota, so it runs slower with no
   crash and often no obvious signal beyond a latency spike. Memory is incompressible — exceeding the
   limit gets the container OOMKilled outright, with a clear signal in `kubectl describe pod`.

7. **How do you stop replicas of a critical service from landing on the same node or AZ?**
   `podAntiAffinity` or, preferably, `topologySpreadConstraints` keyed on
   `topology.kubernetes.io/zone` (or `hostname` for per-node spreading) — scheduling-time guarantees,
   not something you can retrofit after Pods are already placed.

8. **What does `maxSurge`/`maxUnavailable` actually control, and what's the risk of setting
   `maxUnavailable` high to make deploys "faster"?**
   They bound how many extra Pods above, or how many fewer Pods below, `replicas` are tolerated
   mid-rollout. A high `maxUnavailable` speeds up the rollout by removing more old capacity at once —
   which is exactly the mechanism behind "a routine deploy took down more capacity than the system
   could absorb" if there's no PodDisruptionBudget backstopping it.
