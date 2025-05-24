# Delivery Guarantees (QoS), Dead‑Letter Queues & High Availability

This section dives into message delivery assurances, handling failures via DLQs, broker high availability, and batching/asynchronous patterns.

---

## 1. Delivery Guarantees (Quality of Service)

| Guarantee      | Description                                                | Broker Support                            |
|----------------|------------------------------------------------------------|-------------------------------------------|
| **At‑most‑once** | Messages may be lost but never redelivered.              | RabbitMQ: `noAck=true`; Kafka: `acks=0`   |
| **At‑least‑once** | Messages delivered ≥1 time; possible duplicates.        | RabbitMQ default; Kafka: `acks=all`       |
| **Exactly‑once** | Messages delivered precisely once (no loss, no dups).    | Kafka transactions; AWS SNS with FIFO     |

**Analogy**:  
- At‑most‑once: sending postcards (no proof of delivery).  
- At‑least‑once: certified mail (you get duplicate receipts).  
- Exactly‑once: courier with signature and unique tracking.

---

## 2. Dead‑Letter Queues (DLQs)

A DLQ is a special queue/topic where messages that **cannot be processed** (due to errors or retries exceeded) are routed for inspection.

- **RabbitMQ**: Configure via `x-dead-letter-exchange` and TTL or max-length policies.  
- **Kafka**: Use a dedicated topic (e.g., `orders.dlq`) in consumer error handling.  
- **AWS SQS**: Assign a DLQ with `maxReceiveCount` and redrive policy.

**Example (RabbitMQ)**:
```scala
val args = Map("x-dead-letter-exchange" -> "dlx", "x-message-ttl" -> 60000.asInstanceOf[Object])
channel.queueDeclare("primary", true, false, false, args)
```

---

## 3. High Availability Patterns

### RabbitMQ

- **Mirrored Queues** (Classic HA): replicas across nodes, synchronous replication.
- **Quorum Queues**: Raft-based, stronger consistency and auto-healing.

```hocon
# Enable quorum queue policy
rabbitmqctl set_policy ha-all "^" '{"queue-type":"quorum","ha-mode":"all"}'
```

### Apache Kafka

- **Replication Factor** ≥ 2 (ideally 3).
- **In-Sync Replicas (ISR)**: only commit when follower replicas are caught up.
- **Controller & Leader Election**: handles broker failures.

```properties
# Topic with replication and min ISR
replication.factor=3
min.insync.replicas=2
```

### Cloud Brokers

- AWS SQS/SNS: multi-AZ by default.
- GCP Pub/Sub: geo-redundant storage and automatic failover.

---

## 4. Batching & Asynchronous I/O

Batching reduces network overhead:

- **Kafka**:
  - `linger.ms`: wait before sending to batch records.
  - `batch.size`: max batch bytes.
- **RabbitMQ Publisher Confirms**:
  - `confirmSelect()`
  - `waitForConfirmsOrDie()` for batch confirms.
- **AWS SQS**:
  - `SendMessageBatch` API.

**Scala Kafka Example (Asynchronous Send with Batching)**:
```scala
val props = new Properties()
props.put("linger.ms", "100")
props.put("batch.size", "16384")
val producer = new KafkaProducer[String, String](props)

(1 to 50).foreach { i =>
  producer.send(new ProducerRecord("topic", s"key-$i", s"value-$i"), { (md, ex) =>
    if (ex != null) println(s"Error: $ex")
  })
}
producer.flush()
```

---

## 5. Summary & Best Practices

- Choose **ack mode** based on data criticality vs. latency.  
- Always configure **DLQs** to handle poison messages.  
- Use **replication** and **policies** for availability and durability.  
- Tune **batch** settings for throughput, balance latency.  

---

## Further Reading

- RabbitMQ QoS & DLX: https://www.rabbitmq.com/consumer-prefetch.html  
- Kafka Transactions & Exactly-Once: https://kafka.apache.org/documentation/#transactions  
- AWS SQS DLQ & Redrive: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html  
