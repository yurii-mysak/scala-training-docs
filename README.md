# Scala & Backend Engineering — Training & Interview Guide

A comprehensive knowledge base organized by theme and difficulty level.
Each section contains study materials and interview question banks for conducting and preparing for technical interviews.

**Levels**: B = Beginner | I = Intermediate | A = Advanced

---

## Preparing for a specific interview? Start at [00 — Interview Program](00-interview-program/)

Sections **17–23**, and the extensions to 09, 14 and 15, were written as a complete preparation
programme for one named loop: **Staff Software Engineer at Lyft, Global Support & Partnerships**
(Kyiv, remote in Ukraine). They are built from researched evidence about how that loop actually runs
rather than from generic interview advice.

| Start here | What it gives you |
|---|---|
| [00-interview-program/README.md](00-interview-program/README.md) | How the programme works and what the loop tests |
| [00-interview-program/curriculum.md](00-interview-program/curriculum.md) | Every document tagged Required / Recommended / Optional with time estimates |
| [00-interview-program/tracker.md](00-interview-program/tracker.md) | Three paths — 22 h, 48 h or 93 h — as a checklist |
| [00-interview-program/interview-playbook.md](00-interview-program/interview-playbook.md) | How to run each round on the day |
| [00-interview-program/evidence.md](00-interview-program/evidence.md) | The reported question bank, with sourcing marked |
| [00-interview-program/hellointerview-map.md](00-interview-program/hellointerview-map.md) | What to use a HelloInterview subscription for, lesson by lesson |

Sections 01–16 remain the general knowledge base and are re-tagged for this loop in
[curriculum.md, part 2](00-interview-program/curriculum.md).

---

## Daily practice: IT Iaido

Two lessons a day (15–30 min each) arrive by email and on the Dojo dashboard; everything that drives
them lives in [`dojo/`](dojo/): the contract ([SPEC](dojo/SPEC.md)), the six ladders in
[`dojo/curriculum/`](dojo/curriculum/), every lesson ever sent in [`dojo/lessons/`](dojo/lessons/),
progress in [`dojo/progress/`](dojo/progress/) and the scripts in [`dojo/engine/`](dojo/engine/).
Lessons marked *passed* are filed into the numbered sections below (new ones appear as
`24-ai-ml-foundations/`, `25-software-architecture/`, `26-rust/`).

---

## New sections

| Section | Contents |
|---------|----------|
| [00 — Interview Program](00-interview-program/) | The programme: curriculum, tracker, playbook, evidence, HelloInterview map |
| [17 — Lyft Laptop Round](17-lyft-laptop-round/) | The seven recurring problem families, worked in Python with tests |
| [18 — I/O Harness](18-io-harness/) | A runnable skeleton project for the 90-minute round. Clone it, do not write it under time pressure |
| [19 — Observability & On-Call](19-observability-and-oncall/) | SLOs, alerting, on-call health, incident response, debugging distributed systems |
| [20 — LLM & Agent Systems](20-llm-agent-systems/) | Agent architectures, LangGraph patterns, checkpointing, evaluation, LLMOps |
| [21 — Python for Interviews](21-python-for-interviews/) | Python from a Lua/Scala background, stdlib, async, generators, MRO, exceptions, unittest, speed drills |
| [22 — Behavioural & Staff Scope](22-behavioral-and-staff-scope/) | Story bank, CARL, Senior vs Staff framing, metrics for stories |
| [23 — Web & Frontend](23-web-and-frontend/) | Conditional track, only if the role is confirmed as Server + Web |

---

## Core Language & Programming

### [01 — Scala Language](01-scala-language/)
| Level | Topics |
|-------|--------|
| B | [Collections](01-scala-language/Collections.md), [Option](01-scala-language/Option.md), [Pattern Matching](01-scala-language/PatternMatching.md), [Objects & Companions](01-scala-language/ObjectsCompanions.md), [Traits vs Classes](01-scala-language/TraitsClasses.md), [For-Comprehensions](01-scala-language/ForComprehensions.md), [Generics](01-scala-language/GenericClasses.md), [Type Hierarchy](01-scala-language/TypeHierarchy.md), [Value Types & Boxing](01-scala-language/scala_value_types_boxing.md) |
| I | [Advanced Functions](01-scala-language/AdvancedFunctions.md), [Implicits & Type Classes](01-scala-language/ImplicitsTypeClasses.md), [Currying & Type Classes](01-scala-language/currying-typeclass-summary.md), [SBT Advanced](01-scala-language/SBT_Advanced.md) |
| A | [Advanced Type System](01-scala-language/Advanced-TypeSystem.md), [Type Class Hierarchy](01-scala-language/typeclass_hierarchy.md), [Type Classes & Category Theory](01-scala-language/Type-Classes-and-CT.md), [Shapeless & HLists](01-scala-language/Shapeless_HLists.md), [Macros & Metaprogramming](01-scala-language/MacrosMeta.md) |

### [02 — Functional Programming](02-functional-programming/)
| Level | Topics |
|-------|--------|
| B | [FP Foundations](02-functional-programming/Functional-Programming-Foundations.md) |
| I | [Functional Data Structures](02-functional-programming/Functional-Data-Structures.md), [Functional Design Patterns](02-functional-programming/Functional-Design-Patterns.md), [Side Effects & IO](02-functional-programming/SideEffects_IO.md), [Purely Functional State](02-functional-programming/Purely-Functional-State.md) |
| A | [Purely Functional Concurrency](02-functional-programming/Purely-Functional-Concurrency.md) |

---

## Frameworks & Runtime

### [03 — Akka Ecosystem](03-akka-ecosystem/)
| Level | Topics |
|-------|--------|
| B | [Actors Core](03-akka-ecosystem/AkkaActorsCore.md), [Ask & Pipe](03-akka-ecosystem/akka-ask-pipe-summary.md) |
| I | [Advanced Actors](03-akka-ecosystem/AkkaAdvanced.md), [Akka Cluster](03-akka-ecosystem/Akka_Cluster.md), [Stream Processing](03-akka-ecosystem/Stream_Processing.md), [Streaming & Backpressure](03-akka-ecosystem/akka_streaming_and_backpressure_detailed_guide.md) |
| A | [Cluster Deep Dive](03-akka-ecosystem/Akka_Cluster_UltraDeepDive.md), [Reactive Read-Side](03-akka-ecosystem/reactive_readside.md), [Kafka + Scala](03-akka-ecosystem/Kafka_Scala.md) |

### [04 — Concurrency & Async](04-concurrency-and-async/)
| Level | Topics |
|-------|--------|
| B | [Futures Basics](04-concurrency-and-async/scala_akka_futures.md) |
| I | [Multiple Futures](04-concurrency-and-async/multiple_futures.md), [Cats Effect Concurrency](04-concurrency-and-async/CatsEffectConcurrency.md) |
| A | [Cats Effect Memoize](04-concurrency-and-async/cats_effects_memoize.md) |

### [05 — JVM Internals](05-jvm-internals/)
| Level | Topics |
|-------|--------|
| B | [JVM & Tooling](05-jvm-internals/JVM-JVM_and_Tooling.md), [Memory: Stack & Heap](05-jvm-internals/JVM-Memory_Stack_Heap.md) |
| I | [Classloaders](05-jvm-internals/JVM-Classloaders.md), [Garbage Collection](05-jvm-internals/JVM-Garbage_Collection.md), [AOT vs JIT](05-jvm-internals/JVM-AOT_vs_JIT.md) |
| A | [Performance Tuning](05-jvm-internals/JVM-PerformanceTuning.md), [GC Profiling & Tuning](05-jvm-internals/JVM-GC_Profiling_and_Tuning.md), [Scala App Profiling](05-jvm-internals/scala_app_profiling.md) |

---

## Data & Storage

### [06 — Databases & Distributed Data](06-databases-and-distributed-data/)
| Level | Topics |
|-------|--------|
| B | [RDBMS vs NoSQL](06-databases-and-distributed-data/RDBMS_vs_NoSQL.md), [Key-Value Stores](06-databases-and-distributed-data/KeyValue_Stores.md), [Wide-Column vs Document](06-databases-and-distributed-data/WideColumn_vs_Document.md), [Data Modeling](06-databases-and-distributed-data/Databases-Data-Modeling.md) |
| I | [SQL Transactions](06-databases-and-distributed-data/SQL_Transactions.md), [Indexing & Optimization](06-databases-and-distributed-data/Indexing_Optim.md), [Query Optimization](06-databases-and-distributed-data/db_query_optimization_approaches.md), [B-tree vs LSM](06-databases-and-distributed-data/btree_lsm_comparison.md), [Storage Persistence](06-databases-and-distributed-data/Data_Storage_Persistence_Strategies.md), [Elasticsearch](06-databases-and-distributed-data/Elasticsearch_Basics.md), [MongoDB](06-databases-and-distributed-data/MongoDB_Concepts.md) |
| A | [CAP & Consistency](06-databases-and-distributed-data/CAP_Consistency.md), [Linearizability vs Serializability](06-databases-and-distributed-data/linearizability_vs_serializability.md), [Distributed Transactions](06-databases-and-distributed-data/Distributed_Transactions.md), [Partitioning & Rebalancing](06-databases-and-distributed-data/Partitioning_Rebalancing.md), [Partition Strategies](06-databases-and-distributed-data/partition_strategies.md), [Cassandra Partitioning](06-databases-and-distributed-data/cassandra_partition_clustering.md), [Cassandra LSM](06-databases-and-distributed-data/Cassandra_LSM.md), [Cassandra + Doobie](06-databases-and-distributed-data/Cassandra_Doobie_Indexing_Guide.md), [DynamoDB](06-databases-and-distributed-data/dynamodb_refresher.md), [Event Sourcing](06-databases-and-distributed-data/Event-Sourcing-Guide.md) |

### [07 — Messaging & Streaming](07-messaging-and-streaming/)
| Level | Topics |
|-------|--------|
| B | [Messaging Fundamentals](07-messaging-and-streaming/Messaging-Fundamentals.md), [Point-to-Point vs Pub/Sub](07-messaging-and-streaming/Messaging-point_to_point_pubsub.md) |
| I | [Delivery, QoS, DLQ](07-messaging-and-streaming/Messaging-delivery_qos_dlq_ha.md), [Kafka Fundamentals](07-messaging-and-streaming/Messaging-kafka_fundamentals.md), [RabbitMQ & AMQP](07-messaging-and-streaming/Messaging-rabbitmq_amqp_essentials.md), [Akka Streams Basics](07-messaging-and-streaming/Messaging-akka_streams_basics.md), [FS2 Basics](07-messaging-and-streaming/Messaging-fs2_streams_basics.md) |
| A | [Kafka Advanced](07-messaging-and-streaming/Messaging-kafka_advanced.md), [Akka Streams Advanced](07-messaging-and-streaming/Messaging-akka_streams_advanced.md), [Akka Streams Network](07-messaging-and-streaming/Messaging-akka_streams_network.md), [FS2 Advanced](07-messaging-and-streaming/Messaging-fs2_streams_advanced.md), [FS2 Reactive Streams](07-messaging-and-streaming/Messaging-fs2_reactive_streams.md), [Async Boundaries](07-messaging-and-streaming/Messaging-AsyncBoundariesReactiveStreams.md), [High-Throughput Systems](07-messaging-and-streaming/Messaging-high_throughput_low_latency_systems_expanded.md) |

### [13 — Data Engineering](13-data-engineering/)
| Level | Topics |
|-------|--------|
| B | [Data Concepts](13-data-engineering/Data_concepts.md) |
| I | [Data Concepts (Extended)](13-data-engineering/Data_concepts_2.md), [Delta & Parquet](13-data-engineering/delta_parquet_guide.md) |
| A | [Lakehouse Architecture](13-data-engineering/lakehouse_unified_platform_and_migration.md) |

---

## Algorithms & Practice

### [08 — Algorithms & Data Structures](08-algorithms-and-data-structures/)
| Level | Topics |
|-------|--------|
| B | [Base Data Structures](08-algorithms-and-data-structures/Base_Data_Structures.md), [Algorithmic Complexity](08-algorithms-and-data-structures/Algorithmic_Complexity.md), [HashSet & HashMap](08-algorithms-and-data-structures/hashset_hashmap.md), [Binary Heap](08-algorithms-and-data-structures/binary_heap_summary.md) |
| I | [Sorting & Searching](08-algorithms-and-data-structures/Sorting_Searching.md), [Trees & Graphs](08-algorithms-and-data-structures/Trees_and_Graphs.md), [BFS & DFS](08-algorithms-and-data-structures/bfs_dfs_summary.md), [Graph Traversal](08-algorithms-and-data-structures/Traversal_Graph_Search.md), [Recursion & DP](08-algorithms-and-data-structures/Recursion_Dynamic_Programming.md), [String Searching](08-algorithms-and-data-structures/String_Searching_Algorithms.md) |
| A | [Dijkstra's Algorithm](08-algorithms-and-data-structures/Dijkstras_Algorithm.md), [Advanced DP & Hash Collisions](08-algorithms-and-data-structures/Advanced_DP_Hash_Collision.md) |

### [09 — Coding Challenges](09-coding-challenges/)
40 LeetCode problems in Scala, organized by difficulty and pattern.
| Level | Count | Examples |
|-------|-------|---------|
| Easy | 20 | Two Sum, Valid Parentheses, Reverse Linked List, Climbing Stairs |
| Medium | 17 | Number of Islands, LRU Cache, Course Schedule, Generate Parentheses |
| Hard | 3 | Trapping Rain Water, Sliding Window Maximum, Serialize Binary Tree |

---

## Infrastructure & Operations

### [10 — Networking](10-networking/)
| Level | Topics |
|-------|--------|
| B | [Network Models](10-networking/Networking-Network-Models.md), [IP Addressing](10-networking/Networking-IP-Addressing.md), [Network Tools](10-networking/Networking-Network-Tools.md) |
| I | [DNS & DHCP](10-networking/Networking-DNS-DHCP.md), [IPv4 vs IPv6](10-networking/Networking-IPV4-vs-IPV6.md), [NAT, DMZ, VPN](10-networking/Networking-NAT-DMZ-VPN.md) |
| A | [Routing & Reverse Proxy](10-networking/Networking-Routing-Reverse-Proxy.md), [HTTPS & TLS](10-networking/Networking-HTTPS-TLS.md) |

### [11 — Security](11-security/)
| Level | Topics |
|-------|--------|
| B | [Authentication](11-security/Security-authentication.md), [Common Threats](11-security/Security-threats.md) |
| I | [Cryptography](11-security/Security-cryptography.md), [Transport Security](11-security/Security-transport_protocol.md) |
| A | [Penetration Testing](11-security/Security-pentesting.md) |

### [12 — Testing](12-testing/)
| Level | Topics |
|-------|--------|
| B | [Test Types & Levels](12-testing/Testing-types_levels.md), [Unit Testing](12-testing/Testing-unit_testing.md), [TDD & BDD](12-testing/Testing-tdd_bdd.md) |
| I | [Test Frameworks](12-testing/Testing-frameworks.md), [Mocks & Stubs](12-testing/Testing-mocks_stubs.md), [Mock Frameworks](12-testing/Testing-mock_frameworks.md) |
| A | [Property-Based Testing](12-testing/Testing-property_based.md), [Load Testing](12-testing/Testing-load_testing.md), [Microbenchmarking](12-testing/Testing-microbenchmarking.md) |

### [14 — Cloud & Infrastructure](14-cloud-and-infrastructure/)
| Level | Topics |
|-------|--------|
| B | [Cloud Messaging Services](14-cloud-and-infrastructure/Messaging-cloud_messaging_services.md) |
| I | [Terraform & AWS](14-cloud-and-infrastructure/terraform_aws_overview.md) |

### [15 — System Design](15-system-design/)
| Level | Topics |
|-------|--------|
| B | [Architecture & Dev Process](15-system-design/Architecture-Dev-Process.md) |
| I | [gRPC & Protobuf](15-system-design/grpc_protobuf_schema_design.md), [Event Sourcing, CQRS & Sagas](15-system-design/event_sourcing_cqrs_sagas_guide.md) |
| A | [Payment Systems Design](15-system-design/payments_interview_prep_expanded.md) |

---


## AI & Machine Learning

### [24 — AI / ML Foundations](24-ai-ml-foundations/)
| Level | Topics |
|-------|--------|
| B | [What machine learning actually optimises](24-ai-ml-foundations/what-machine-learning-actually-optimises.md) |
| I | [Decision models: when an LLM answers with probabilities, not text](24-ai-ml-foundations/decision-models-when-an-llm-answers-with-probabilities-not.md) |
## Domain-Specific

### [16 — AdTech](16-adtech/)
| Level | Topics |
|-------|--------|
| I | [OpenRTB Protocol](16-adtech/openrtb.md), [RTB Fundamentals](16-adtech/AdTech_RTB_Fundamentals_Expanded.md) |
| A | [High-Scale Bidding Engine](16-adtech/High-Scale-Bidding-Engine-Architecture-Expanded.md) |
