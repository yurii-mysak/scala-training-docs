# Messaging & Streaming

Message brokers, Kafka, RabbitMQ, Akka Streams, FS2, reactive patterns, and high-throughput systems.

## Beginner

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 1 | Messaging fundamentals | [Messaging-Fundamentals.md](Messaging-Fundamentals.md) | Message-oriented middleware, async communication |
| 2 | Point-to-point vs pub/sub | [Messaging-point_to_point_pubsub.md](Messaging-point_to_point_pubsub.md) | Queue vs topic semantics, when to use each |

## Intermediate

### Core Concepts
| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 3 | Delivery, QoS, DLQ, HA | [Messaging-delivery_qos_dlq_ha.md](Messaging-delivery_qos_dlq_ha.md) | At-most/at-least/exactly-once, dead letter queues |
| 4 | Kafka fundamentals | [Messaging-kafka_fundamentals.md](Messaging-kafka_fundamentals.md) | Topics, partitions, offsets, consumer groups |
| 5 | RabbitMQ & AMQP | [Messaging-rabbitmq_amqp_essentials.md](Messaging-rabbitmq_amqp_essentials.md) | Exchanges, bindings, acknowledgments |

### Stream Libraries (Basics)
| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 6 | Akka Streams basics | [Messaging-akka_streams_basics.md](Messaging-akka_streams_basics.md) | Source/Flow/Sink, materialization |
| 7 | FS2 basics | [Messaging-fs2_streams_basics.md](Messaging-fs2_streams_basics.md) | Stream, Pipe, Pull, chunking |

## Advanced

### Kafka & Brokers
| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 8 | Kafka advanced | [Messaging-kafka_advanced.md](Messaging-kafka_advanced.md) | Transactions, idempotent producers, stream processing |

### Stream Libraries (Advanced)
| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 9 | Akka Streams advanced | [Messaging-akka_streams_advanced.md](Messaging-akka_streams_advanced.md) | Custom graph stages, fan-in/fan-out |
| 10 | Akka Streams network | [Messaging-akka_streams_network.md](Messaging-akka_streams_network.md) | TCP/HTTP streaming, framing |
| 11 | FS2 advanced | [Messaging-fs2_streams_advanced.md](Messaging-fs2_streams_advanced.md) | Concurrency, interruption, resource safety |
| 12 | FS2 reactive streams | [Messaging-fs2_reactive_streams.md](Messaging-fs2_reactive_streams.md) | Interop with reactive streams spec |

### Architecture & Performance
| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 13 | Async boundaries & reactive streams | [Messaging-AsyncBoundariesReactiveStreams.md](Messaging-AsyncBoundariesReactiveStreams.md) | Backpressure across async boundaries |
| 14 | High-throughput, low-latency systems | [Messaging-high_throughput_low_latency_systems_expanded.md](Messaging-high_throughput_low_latency_systems_expanded.md) | Batching, compression, zero-copy, kernel bypass |

## Key Interview Questions by Level

**Beginner**: What is the difference between a message queue and pub/sub? When would you use asynchronous messaging?

**Intermediate**: How do Kafka consumer groups work? What is the difference between at-least-once and exactly-once delivery? Explain backpressure.

**Advanced**: How would you design a system for exactly-once processing with Kafka? Compare Akka Streams vs FS2 for a streaming ETL pipeline. How do you achieve low-latency at high throughput?
