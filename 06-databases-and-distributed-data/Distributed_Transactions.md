# Distributed Transactions – Expanded (2PC, Saga, Outbox)

---

## 1 · Two‑Phase Commit (2PC) Deep Flow

```
Client → Coordinator: BEGIN
Coordinator → Participants: PREPARE
Participants ↔ fsync WAL, respond VOTE_COMMIT / VOTE_ABORT
Coordinator: if all commit → writes COMMIT, notifies
Else writes ABORT
Participants: upon COMMIT msg, release locks
```

### 1.1 Failure Scenarios

| Failure | Recovery |
|---------|----------|
| Coordinator crash after PREPARE | Participants in *prepared* block; wait until coord recovers or timeout for manual intervention |
| Participant crash before VOTE | Coordinator aborts | 
| Network partition | Risk of **blocking** until partition heals |

*Chat 2025‑05‑22*: observed pending prepared records in MySQL `information_schema.innodb_trx`.

---

## 2 · 3PC & Paxos Commit (mention)

3‑Phase Commit reduces blocking but needs synchronous network; rarely used in practice vs Paxos/Raft replicated log.

---

## 3 · Saga Pattern Variants

### 3.1 Orchestrated (central saga)

```plaintext
Order Service  → Payment  → Inventory →  Shipping
        ←cancelPayment ← restockInventory (on failure)
```

Saga log table stores step status; orchestrator sends compensating commands.

### 3.2 Choreographed

* Each service publishes **event**; next service listens.  
* Compensations triggered by timeout or negative event.

---

## 4 · Transactional Outbox & CDC

* Service writes domain event into **outbox** table in same local DB tx.  
* Debezium reads binlog → Kafka topic.  
* Guarantees ordering & atomic persistence without XA.

Diagram (from our chat sketch):

```
Service → DB (table + outbox)  --binlog--> Kafka
```

---

## 5 · Idempotency & Exactly‑Once

* Use **deduplication keys** or **UPSERT** to ensure repeated saga step safe.  
* Kafka exactly‑once producer + idempotent consumer via transaction boundary.

---

## 6 · gRPC / HTTP timeout handling

Saga orchestrator chooses **compensation** if child service does not ACK within SLA; avoids indefinite locks.

---

## 7 · Cost Driver Breakdown

| Factor | Adds latency |
|--------|--------------|
| Round‑trip count | 2 (prepare + commit) | 
| fsync per participant | WAL durability |
| Log growth | Prepared entries stay until resolved |
| Lock duration | Held through both phases |

---

## 8 · Decision Matrix

| Requirement | Recommendation |
|-------------|----------------|
| Same DB engine, same cluster | DB local tx sufficient |
| Cross‑service invariants | Saga or outbox |
| Absolute atomicity over micro‑services | 2PC / XA, accept blocking |
| High throughput, compensable | Saga |

