# Akka Ecosystem

Actor model, clustering, streaming, backpressure, and Kafka integration.

## Beginner

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 1 | Actors core | [AkkaActorsCore.md](AkkaActorsCore.md) | Actor lifecycle, message passing, tell vs ask |
| 2 | Ask & pipe patterns | [akka-ask-pipe-summary.md](akka-ask-pipe-summary.md) | Ask pattern pitfalls, pipe pattern for futures |

## Intermediate

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 3 | Advanced actors | [AkkaAdvanced.md](AkkaAdvanced.md) | Supervision strategies, stashing, FSM, routers |
| 4 | Akka Cluster | [Akka_Cluster.md](Akka_Cluster.md) | Cluster membership, seed nodes, split brain |
| 5 | Stream processing | [Stream_Processing.md](Stream_Processing.md) | Source/Flow/Sink, materialization, graph DSL |
| 6 | Streaming & backpressure | [akka_streaming_and_backpressure_detailed_guide.md](akka_streaming_and_backpressure_detailed_guide.md) | Backpressure mechanics, buffer strategies |

## Advanced

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 7 | Cluster deep dive | [Akka_Cluster_UltraDeepDive.md](Akka_Cluster_UltraDeepDive.md) | CRDT, cluster sharding, ddata, consistency |
| 8 | Reactive read-side | [reactive_readside.md](reactive_readside.md) | Read-side projections, event processors |
| 9 | Kafka + Scala | [Kafka_Scala.md](Kafka_Scala.md) | Alpakka Kafka, consumer/producer patterns, exactly-once |

## Key Interview Questions by Level

**Beginner**: What is the actor model? How does message passing differ from shared memory concurrency? What is tell vs ask?

**Intermediate**: How does Akka handle failure (supervision)? Explain backpressure in Akka Streams. What is materialization?

**Advanced**: How does cluster sharding work? How would you design an event-sourced system with Akka? Explain exactly-once semantics with Kafka.
