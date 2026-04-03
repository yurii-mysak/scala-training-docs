# Partitioning & Rebalancing Strategies – Deep Dive

Combines insights from our April–May 2025 distributed‑systems chats (Cassandra ring math, Kafka rebalance, Dynamo key mapping).

---

## 1 · Goals of Partitioning

1. **Scalability** – distribute data and traffic across nodes.  
2. **Fault isolation** – partition failure only impacts subset.  
3. **Parallelism** – independent processing per shard.

---

## 2 · Consistent Hashing Mechanics

### 2.1 Ring algorithm

```
hash(key) -> 0‒(2^m -1)  (m=128)
Nodes mapped to virtual points
Key stored on first node clockwise
```

* **Virtual nodes** (vnodes) – each physical host owns many tokens to smooth data.

### 2.2 Rebalancing math

* Add node with v tokens ⇒ only keys whose hash falls between new & previous vnode move (≈ 1/v fraction).  
* Removal similarly minimal data migration.

Cassandra default: 256 vnodes per host.

---

## 3 · Range Partitioning

* Split key space into ordered ranges.

| Range | Node |
|-------|------|
| A–M   | n1   |
| N–Z   | n2   |

### 3.1 Pros / Cons

* **Pros** – efficient range scans, natural ordering.  
* **Cons** – **hot spot** if insert pattern skewed (e.g., timestamp prefix). Mitigate by bucketing (`yyyyMMddHH` hash suffix).

---

## 4 · Rendezvous (Highest‑Random‑Weight) Hashing

Score = `hash(nodeID, key)`; pick node with highest score.  
● Avoids ring, simpler to implement.  
● Used in Envoy, Akka Cluster sharding.

---

## 5 · Kafka Consumer Rebalancing

* **Cooperative Sticky** protocol (>= 2.4):  
  * Minimises partition churn; consumers revoke only moved partitions.  
* Static membership (`group.instance.id`) prevents full rebalance on restart.

Rebalance listener pattern (see Kafka chapter) to commit offsets pre‑revoke.

---

## 6 · Cassandra Token Reassignment Workflow

1. `nodetool status` – view ring.  
2. New node bootstrap: `auto_bootstrap: true`.  
3. `nodetool cleanup` on existing nodes to drop moved ranges.

---

## 7 · Data Movement Cost Equation

```
moved_data = total_data * (added_nodes / (current_nodes + added_nodes))
```
With vnodes, moved fraction reduced to ~1%.

---

## 8 · Interview Cheat Cards

* Describe ring vs rendezvous hashing differences.  
* Explain “hot partition” and mitigation tactics (salting, bucketing).  
* Kafka cooperative vs eager rebalance.

