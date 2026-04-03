# Apache Kafka Advanced Patterns

This section covers Kafka’s advanced operational features: consumer rebalancing, retention, cleanup, and replication.

---

## 1. Consumer Partition Rebalance

When consumer group membership changes, Kafka reassigns partitions:

- **Trigger**: consumer join/leave, topic metadata change.
- **Phases**:
  1. **Stop** fetching messages.
  2. **Revoke** current partition assignments.
  3. **Assign** new partitions.
  4. **Resume** consumption.

Implement `ConsumerRebalanceListener`:

```scala
consumer.subscribe(
  List("orders").asJava,
  new ConsumerRebalanceListener {
    override def onPartitionsRevoked(partitions: java.util.Collection[TopicPartition]) = {
      // commit offsets before rebalancing
      consumer.commitSync()
    }
    override def onPartitionsAssigned(partitions: java.util.Collection[TopicPartition]) = {
      // initialize state based on assigned partitions
    }
  }
)
```

**Best Practices**:
- Commit offsets on `onPartitionsRevoked`.
- Minimize downtime by keeping rebalance callbacks fast.
- Prefer **Cooperative Rebalancing** (KIP-429) to reduce disruption.

---

## 2. Log Retention & Cleanup Policies

Control data lifecycle in topics:

- **retention.ms**: time-based retention (default 7 days).
- **retention.bytes**: size-based retention.
- **cleanup.policy**:
  - `delete`: remove old segments past retention.
  - `compact`: keep latest record per key (log compaction).
- **segment.ms** / **segment.bytes**: segment rolling policy.

```bash
# Example: topic config
kafka-topics --alter --topic orders   --add-config retention.ms=86400000,cleanup.policy=compact
```

**Use Cases**:
- Delete for ephemeral event streams.
- Compact for changelog topics (e.g., Kafka Streams state).

---

## 3. Replication & Topic Replication Factor

Ensure fault tolerance via replication:

- **replication.factor**: number of copies of each partition.
- **min.insync.replicas**: minimum ISR for successful writes.
- **unclean.leader.election.enable**: avoid data loss if false.

```bash
# Create topic with replication
kafka-topics --create --topic orders   --partitions 3 --replication-factor 3   --config min.insync.replicas=2
```

- **Leader & Followers**: leader handles reads/writes; followers replicate.
- **In-Sync Replicas (ISR)**: only replicas caught up with leader.
- **Controller**: manages leader election on broker failure.

**Best Practices**:
- Set replication.factor ≥ 3 for production.
- Configure min.insync.replicas to avoid data loss (e.g., 2).
- Monitor ISR size and under-replicated partitions.

---

## 4. Further Reading

- Kafka Consumer Groups & Rebalance: https://kafka.apache.org/documentation/#consumerconfigs  
- Log Compaction & Retention: https://kafka.apache.org/documentation/#basic_ops  
- Replication & Fault Tolerance: https://kafka.apache.org/documentation/#replication  
