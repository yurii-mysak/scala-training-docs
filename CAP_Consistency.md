# CAP Theorem & Consistency – Expanded Reference

---

## 1 · Formal Statement

In an asynchronous network with partitions, you can guarantee at most **two** of:

* **Consistency (C)** – every node sees same data at same time.  
* **Availability (A)** – every request receives (non‑error) response.  
* **Partition tolerance (P)** – system continues despite dropped messages.

---

## 2 · System Classification Examples

| System | CAP bias |
|--------|----------|
| Etcd / ZooKeeper | **CP** (leader stops accepting writes on partition) |
| DynamoDB / Cassandra | **AP** (choose tunable R/W quorum) |
| Spanner | Attempts CA via GPS clock but still P by design |

> *Chat note:* Spanner uses TrueTime to bound uncertainty → “externally consistent” but not synchronous network.

---

## 3 · BASE & Eventual Consistency

* **Basically Available** – system responds.  
* **Soft‑state** – data may change without input.  
* **Eventual consistency** – state converges given no new writes.

### 3.1 Convergence mechanisms
* Read repair (Cassandra).  
* Anti‑entropy Merkle trees.  
* CRDTs (Riak, Redis‑Gears).

---

## 4 · Quorum math

Requirement: `R + W > N`

| Example | N | W | R | Guarantees |
|---------|---|---|---|------------|
| Strong (Cassandra) | 3 | 2 | 2 | Latest read |
| Fast reads | 3 | 3 | 1 | High write consistency |
| Eventual | 3 | 1 | 1 | AP focus |

---

## 5 · PACELC

“If no partition (P) – trade **Latency** vs **Consistency**.”

| System | If Partition | Else |
|--------|--------------|------|
| Cassandra | A over C | L over C (quorum) |
| Spanner | C over A | E => L (TrueTime adds latency) |

---

## 6 · Design Patterns

* **Leader/follower** (CP) – Raft, Paxos.  
* **Multi‑leader** (AP) – Dynamo style with conflict resolution (vector clocks).  
* **Leaderless quorum** – writes to N replicas, read repair.

---

## 7 · Real‑world incidents discussed

* Partition in AWS us‑east‑1 (chat 2025‑03) → Service chose to degrade writes to keep availability → stale reads 3 min.

---

## 8 · Interview rapid‑fire

* Explain CAP in one sentence.  
* Why network partitions unavoidable in distributed systems.  
* How quorum formula ensures read freshness.  
* Difference between **linearizability** and **serializability** (linearizable includes time order across nodes).

