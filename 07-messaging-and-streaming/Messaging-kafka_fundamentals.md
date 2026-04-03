# Apache Kafka Fundamentals

Apache Kafka is a distributed streaming platform for building real-time data pipelines and applications.

---

## 1. Topics, Partitions, Logs, Offsets

- **Topic**: a named category/feed to which messages are published.
- **Partition**: an ordered, immutable sequence of messages within a topic.
- **Log**: the physical commit log storing the messages of a partition.
- **Offset**: a sequential ID uniquely identifying each message in a partition.

| Term       | Definition                                             | Analogy               |
|------------|--------------------------------------------------------|-----------------------|
| Topic      | Named stream of records                                | Radio station         |
| Partition  | Sub-stream enabling parallelism                        | Channel on a radio    |
| Log        | Immutable sequence of records                          | Message tape          |
| Offset     | Position of a record in the log                        | Timestamp on tape     |

![Kafka Topic and Partition](https://raw.githubusercontent.com/ymysak/static-assets/main/images/kafka-topic-partition.png)

---

## 2. Messages

A Kafka *record* consists of:
- **Key** (optional): for partitioning.
- **Value**: payload (bytes, JSON, Avro, etc.).
- **Timestamp**: event or ingestion time.
- **Headers** (optional): metadata key-value pairs.

---

## 3. Producers, Consumers, and Consumer Groups

- **Producer**: publishes records to topics.
- **Consumer**: reads records from topics.
- **Consumer Group**: a set of consumers sharing a `group.id`; each partition is consumed by only one member in the group, enabling scaling and fault-tolerance.

---

## 4. Messaging Models

| Model            | Description                                           | Kafka Example                 |
|------------------|-------------------------------------------------------|-------------------------------|
| Point-to-Point   | One consumer per group processes each message         | Single consumer group         |
| Publish–Subscribe| Multiple groups each receive all messages             | Reporting, analytics services |

---

## 5. Producing Messages

- **Synchronous**:
  ```scala
  val metadata = producer.send(record).get() // blocks until acknowledged
  ```
- **Asynchronous**:
  ```scala
  producer.send(record, (metadata, exception) => {
    if (exception != null) println("Error: " + exception)
    else println(s"Offset: ${metadata.offset()}")
  })
  ```

---

## 6. Producer Configuration

- `acks`: `0` (no wait), `1` (leader), `all` (all ISR).
- `retries`: number of resend attempts on failure.
- `linger.ms`, `batch.size`: control batching.

---

## 7. Partitioning

- **By Key**: default partitioner hashes the key.
- **Explicit**: specify partition in `new ProducerRecord(topic, partition, key, value)`.

---

## 8. Consuming Messages

```scala
consumer.subscribe(List("orders"))
while (true) {
  val records = consumer.poll(Duration.ofMillis(100))
  for (record <- records.asScala) {
    println(s"Received ${record.value()} at offset ${record.offset()}")
  }
}
```

---

## 9. Offset Management

- **Auto-commit**: `enable.auto.commit=true`
- **Manual Sync**: `consumer.commitSync()`
- **Manual Async**: `consumer.commitAsync()`
- **Specific Offset**: `consumer.commitSync(Map(partition -> offset+1))`

---

## 10. Consumer Rebalance

Partitions are re-assigned on group membership changes. Implement `ConsumerRebalanceListener` to handle `onPartitionsAssigned` and `onPartitionsRevoked`.

---

## 11. Retention & Cleanup Policies

- **retention.ms**: max time to keep logs.
- **cleanup.policy**: `delete` (remove old), `compact` (keep latest per key).

---

## 12. Replication & Fault Tolerance

- **Replication Factor**: number of copies across brokers.
- **ISR**: in-sync replicas for durability.
- Leader election ensures availability on failure.

---

## 13. Dead-Letter Queues

Kafka doesn’t have built-in DLQs. Common pattern: route failed messages to a dedicated topic (e.g., `orders.dlq`).

---

## 14. Further Reading

- _Kafka: The Definitive Guide_ (Ch. 1–4)
- Apache Kafka Documentation: https://kafka.apache.org/documentation
