# Kafka in Scala – Comprehensive Guide

---

## 1 · Dependency Matrix

| Scenario | Library |
|----------|---------|
| Pure FP | **fs2‑kafka** |
| Akka ecosystem | **Alpakka Kafka** |
| Spring Boot | **spring‑kafka** |

Version rule: align with broker’s major (e.g., client 3.6.x ↔ broker 3.x).

---

## 2 · Producer Settings Deep‑Dive

| Setting | Purpose | Recommended |
|---------|---------|-------------|
| `enable.idempotence` | Exactly‑once semantics | `true` |
| `acks` | Replica ack count | `all` |
| `retries` | Auto retry | ≥3 |
| `linger.ms` | Batch window | 5–20 ms for throughput |
| `compression.type` | lz4 / zstd | lz4 for low CPU |

Scala config snippet (fs2‑kafka):

```scala
ProducerSettings[F]
  .withBootstrapServers("broker:9092")
  .withEnableIdempotence(true)
  .withAcks(Acks.All)
  .withLinger(20.millis)
```

---

## 3 · Consumer Settings

* `auto.offset.reset = earliest | latest`.  
* `max.poll.records` tunes batch size.  
* Commit strategy:  
  * **auto** – simple, at‑least‑once.  
  * **manual commitAsync** – custom control.  
  * **exactly‑once** – use **Kafka Streams** or Transactions API.

---

## 4 · Rebalance listeners

In fs2‑kafka:

```scala
val handler = RebalanceListener[F]
  .withPartitionsRevoked { parts => logger.info(s"Revoked $parts") }
settings.withConsumerRebalanceListener(handler)
```

Important for committing offsets before revoke.

---

## 5 · Error Handling & DLQ

```scala
stream.handleErrorWith { e =>
  Producer.dlq(topic = "dlq", record, e) >> Stream.raiseError(e)
}
```

Pattern: push bad message to dead‑letter topic, continue stream.

---

## 6 · Exactly‑Once Transaction Example

```scala
producer.createTransaction
  .flatMap { tx =>
    tx.sendOffsetsToTransaction(offsets, groupId) >>
    tx.commit
  }
```

Requires idempotent producer + **`transactional.id`** config.

---

## 7 · Schema registry integration

```scala
libraryDependencies += "com.github.fd4s" %% "fs2-kafka-vulcan" % "3.3.1"
```

Enables Avro/Protobuf with automatic subject naming.

---

## 8 · Akka Streams Kafka (Alpakka) Example

```scala
Consumer
  .committableSource(settings, Subscriptions.topics("t"))
  .mapAsync(4)(msg => process(msg.record.value) >> msg.committableOffset.commitScaladsl)
  .runWith(Sink.ignore)
```

Back‑pressure driven by stream demand.

---

## 9 · Scaling tips

* Partitions >> consumer instances for rebalancing flexibility.  
* Use **static membership** (`group.instance.id`) to avoid full rebalance on container restarts.  
* Monitor lag via `kafka-consumer-groups.sh`.

---

## 10 · Security quick checklist

| Layer | Setting |
|-------|---------|
| Wire | SSL/TLS |
| Auth | SASL SCRAM / OAUTHBEARER |
| ACL | `Allow: User:app Produce Topic:data` |

---

