# High-Throughput, Low-Latency Systems Interview Prep

## Introduction
In modern distributed systems, two key performance metrics are **throughput** (how many tasks can be processed per unit time) and **latency** (how quickly an individual task is completed). High-throughput, low-latency systems are critical in domains like financial trading, online advertising, and real-time analytics, where every millisecond matters.

---

## 1. Message Brokers & Event Streaming

### What Is a Message Broker?
A **message broker** is middleware that routes messages from producers (senders) to consumers (receivers). It decouples components, allowing them to evolve independently.

### Common Example: Apache Kafka
- **Topic**: A named stream of records (e.g., `bid_requests`).
- **Partition**: A slice of a topic; each holds an ordered, immutable sequence of messages.
- **Producer**: Writes messages to a topic.
- **Consumer**: Reads messages from one or more partitions.

```text
Producer -> [Topic: bid_requests (Partitions: 0,1,2)] -> Broker -> Consumer Group
```

### Key Concepts
- **Partitioning** allows parallelism: each partition can be processed by a separate consumer.
- **Replication** ensures resilience: each partition is copied to multiple broker nodes.
- **Offset**: The index of a message within a partition; consumers track offsets to know which messages they’ve processed.

### Best Practices for Beginners
- Start with **3 brokers** and **3 replicas** for fault tolerance.
- Choose a **partition key** (e.g., auction ID) to distribute load evenly.
- Set **`acks=all`** so the producer waits until all replicas acknowledge a write, trading a bit of latency for durability.

---

## 2. Backpressure Management

### Why Backpressure Matters
Imagine a busy highway: if cars (data) enter faster than they can exit, a traffic jam forms. Similarly, if your producer is faster than your consumer, you risk memory exhaustion, delays, or crashes.

### Techniques

#### a) Kafka Consumer Throttling
- Each consumer **polls** at its own pace. If it can’t keep up, metrics show increased **lag**.
- You can **scale out** by adding more consumers to the group.

#### b) Reactive Streams (e.g., Akka Streams)
- Implement a **demand-driven** model: consumers signal how many messages they can handle.
- **Buffer** and **overflow** strategies let you drop or delay excess messages when overwhelmed.

### Simple Example in Pseudocode
```scala
// Signal-based flow
source
  .buffer(100)         // hold up to 100 messages
  .map(process)
  .run()
```

### Best Practices
- Monitor lag and set alerts when it exceeds thresholds.
- Use **bounded queues** with clear overflow policies (e.g., drop oldest).
- Introduce **retry with exponential backoff** to handle transient errors.

---

## 3. In-Memory Caches & Data Locality

### What Is a Cache?
A **cache** temporarily stores data in fast-access memory to reduce access times for frequently used information.

### Why Use Redis for Bidding?
- **Low latency**: sub-millisecond lookups.
- **Data structures**: hashes, sorted sets, and bitmaps suit various use cases.
- **Atomic operations**: through Lua scripting.

### Designing for Data Locality
1. **Partition by Key**  
   Use the same key (e.g., bidder ID) for both cache and service so requests hit the same node.
2. **Co-location**  
   Deploy cache nodes in the same data center or availability zone as your app servers.
3. **Redis Cluster**  
   - Splits key space into **16,384 hash slots**.
   - Nodes own ranges of slots, redistributing when scaling.

### Example Workflow
```scala
// Fetch bidder budget
val budget = redisClient.hget("bidder:" + bidderId, "budget")

if (budget < bidAmount) {
  rejectBid()
} else {
  placeBid()
}
```

### Best Practices
- Use **TTL (time-to-live)** to clear stale entries.
- **Pre-warm** cache on startup for critical keys.
- Avoid **hot keys**: design cache keys to spread load evenly.

---

## 4. Horizontal Scaling

### What Is Horizontal Scaling?
Scaling **horizontally** means adding more machines (nodes) to handle increased load, rather than upgrading a single machine (vertical scaling).

### 4.1 Sharding
- **Definition**: Splitting data by a shard key (e.g., user ID mod N) across multiple instances.
- **Example**: User sessions on 4 servers: userID % 4 selects the server.

### 4.2 Consistent Hashing
- **Problem**: Rehashing all keys when nodes change is costly.
- **Solution**: Map both data and nodes onto a **hash ring**; only affected keys need relocation when nodes join/leave.

```text
[Node A]---10---[Key X]---25---[Node B]---50---[Key Y]---75---[Node C]
```

### 4.3 Stateless vs. Stateful Services
- **Stateless**  
  - No local session state; any instance can serve any request.
  - Easier to autoscale and replace.
- **Stateful**  
  - Maintains in-memory state or sessions.
  - Requires **sticky sessions** or external state store (Redis, database).

### Best Practices
- Prefer **stateless** whenever possible; move state to dedicated stores.
- Automate **node discovery** and **rebalance** (e.g., using Kubernetes).
- Test **failure scenarios**: simulate node crashes and ensure smooth failover.

---

## 5. Simple Diagrams

### Message Flow
```text
[Producer] --> [Broker Cluster (Topic: bids)] --> [Consumer Group] --> [Processing Service]
```

### Consistent Hash Ring
```text
(0)A----X----B----Y----C----Z----A(100)
```

---

*This expanded guide is designed to help both technical and non-expert interviewers or candidates quickly grasp core concepts and best practices in designing high-throughput, low-latency systems.*