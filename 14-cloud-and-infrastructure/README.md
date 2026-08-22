# Cloud & Infrastructure

Cloud providers, managed services, Infrastructure as Code, and — the core of this section —
containers and container orchestration: Docker, the OCI/CRI runtime stack, Kubernetes, and the
Envoy-based service mesh model. The job description for this loop names Kubernetes, Docker, and
cri-o explicitly, so this is where most of this section's prep weight sits; the candidate already
has real depth in AWS and Terraform, so that material stays lean by comparison — a refresher, not a
ramp.

---

## Read in this order

### Containers & runtimes — the mechanism underneath everything else

| # | File | Priority | Est. time | Description |
|---|---|---|---|---|
| 1 | [docker-and-containers.md](docker-and-containers.md) | Required | 40 min | Namespaces and cgroups as the actual isolation mechanism, image layers/caching, multi-stage builds, image size and security, ENTRYPOINT vs. CMD, signal handling and the PID 1 problem, container networking, volumes |
| 2 | [container-runtimes-cri-o.md](container-runtimes-cri-o.md) | Recommended | 20 min | The CRI interface, containerd vs. cri-o vs. the dockershim removal, the OCI runtime spec, runc and its alternatives (crun, gVisor, Kata) |

### Kubernetes — the object model, operating it, and debugging it

| # | File | Priority | Est. time | Description |
|---|---|---|---|---|
| 3 | [kubernetes-core.md](kubernetes-core.md) | Required | 45 min | The object model as a working mental model, not a glossary: Pods through Ingress, ConfigMaps/Secrets, and the desired-state control loop that explains almost everything else |
| 4 | [kubernetes-operations.md](kubernetes-operations.md) | Required | 45 min | Rollouts and rollback, readiness/liveness/startup probes, resource requests/limits, QoS and eviction, HPA/VPA, PodDisruptionBudgets, affinity/taints/scheduling — each tied to the real outage it prevents |
| 5 | [kubernetes-debugging-playbook.md](kubernetes-debugging-playbook.md) | Required | 40 min | The on-call reference: a symptom-to-cause table and exact `kubectl` commands for CrashLoopBackOff, ImagePullBackOff, Pending, OOMKilled, readiness flapping, DNS failures, no-endpoints Services, and NotReady nodes |

### Service mesh and applying it to a real service

| # | File | Priority | Est. time | Description |
|---|---|---|---|---|
| 6 | [service-mesh-and-envoy.md](service-mesh-and-envoy.md) | Recommended | 30 min | Sidecar model, Envoy's L7/xDS design, traffic shifting, retries/timeouts/circuit breaking, observability signals, mTLS — Lyft built Envoy and donated it to the CNCF |
| 7 | [deploying-python-services.md](deploying-python-services.md) | Recommended | 35 min | Containerizing a Flask/gRPC Python service, gunicorn/uvicorn worker models, graceful shutdown, health endpoints, twelve-factor config, monorepo image builds |

### AWS & Infrastructure as Code — existing depth, quick refresher

| # | File | Priority | Est. time | Description |
|---|---|---|---|---|
| 8 | [terraform_aws_overview.md](terraform_aws_overview.md) | Recommended | 20 min | Terraform workflow and commands, core AWS services (EC2, S3, IAM), remote state and locking, modules and workspaces |
| 9 | [Messaging-cloud_messaging_services.md](Messaging-cloud_messaging_services.md) | Optional | 15 min | AWS SQS/SNS/Kinesis vs. Azure Service Bus/Event Hubs vs. GCP Pub/Sub — managed messaging comparison |

---

## If you only have twenty minutes

Read [kubernetes-debugging-playbook.md](kubernetes-debugging-playbook.md). It's the single most
interview-useful file in this section — a real on-call engineer's symptom-to-command reference, and
the fastest way to sound fluent rather than textbook when a "what would you check" question lands.

## Key interview questions by level

**Beginner**: What is a container, mechanically? What's the difference between a Docker image and a
container? What are the main cloud messaging services and how do they compare?

**Intermediate**: What is Infrastructure as Code? What's the difference between a Deployment and a
StatefulSet? Why does Kubernetes separate readiness from liveness probes? What is the CRI, and why
does it exist?

**Advanced**: Walk through what happens between `kubectl apply` and a running Pod. Why would a
company build its own L7 proxy instead of adopting an existing one? How would you protect a service
that depends on several third-party APIs with a variety of failure modes? How do resource requests,
limits, and QoS classes interact under node memory pressure?
