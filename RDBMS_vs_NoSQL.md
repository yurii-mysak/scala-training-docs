# RDBMS vs NoSQL – Expanded Guide

This file fuses **all** discussion threads from May 2025 (SQL isolation, NoSQL access‑patterns, CAP) into a single, interview‑ready reference.

---

## 1&nbsp;· Core Philosophies

| Aspect | **RDBMS** (Postgres, MySQL) | **NoSQL** |
|--------|----------------------------|-----------|
| Data shape | Fixed schema (DDL) | Schema‑on‑read / flexible |
| Integrity | ACID constraints, FK, CHECK | Application‑level |
| Scaling model | Vertical + read replicas | Horizontal, auto‑shard |
| Query | Declarative SQL | API‑driven, limited joins |
| Consistency | Strong (per tx) | Tunable (eventual → strong) |

> **Chat 2025‑05‑09**: we noted that RDBMS = *“single source of truth, relational math”* whereas NoSQL = *“ease of evolution & scale‑out”*.

---

## 2&nbsp;· NoSQL taxonomies

| Family | Example | Optimised for |
|--------|---------|--------------|
| Key‑value | Redis, DynamoDB | <1 ms lookups |
| Document | MongoDB, Couchbase | Flexible JSON |
| Wide‑column | Cassandra, HBase | Time‑series, logs |
| Graph | Neo4j, JanusGraph | Relationship traversal |

---

## 3&nbsp;· Detailed Strength / Weakness Matrix

### 3.1 RDBMS Deep Strengths
* **Complex joins** – multi‑way, window functions, CTEs.  
* **Rich indexing** – B‑tree, hash, GiST, BRIN.  
* **Mature tooling** – query planner, WAL replication, backup.

### 3.2 RDBMS Weaknesses
* **Schema migrations** can lock tables.  
* **Single‑primary** write bottleneck (unless advanced multi‑master).  
* **Costly sharding** – app logic or Citus‑style extension.

### 3.3 NoSQL Strengths
* **Polyglot APIs** – binary JSON (BSON), thrift.  
* **Elastic throughput** – online resharding (Cassandra `nodetool`).  
* **Built‑in TTL** per row/doc.

### 3.4 NoSQL Weaknesses
* **Eventual consistency headaches** – need upserts/idempotent ops.  
* **Cross‑entity transactions absent** (except Mongo multi‑doc since 4.0).  
* **Limited ad‑hoc analytics**, push to Spark/Presto.

---

## 4&nbsp;· Practical decision tree

```
                      +-- Need complex multi-table JOIN? -> RDBMS
Start --> Data shape? |
                      +-- JSON w/ unknown fields? ------> Document
             \-- Write throughput > 50k/s, append-only? ------> Wide-column
```

---

## 5&nbsp;· Concrete Examples from Chats

### 5.1 Authentication service (chat 05‑09)
```sql
BEGIN;
SELECT * FROM users WHERE email = 'me@host';
-- check password hash
INSERT INTO login_audit(...);
COMMIT;
```
*Requires multi‑row tx → choose Postgres.*

### 5.2 Event logging pipeline (chat 05‑22)
* 200 k events/s, partition key = userId.  
* Chose **Cassandra** with `QUORUM` writes for safety, then Spark SQL for batch analytics.

---

## 6&nbsp;· Polyglot Co‑existence Pattern
* **System of record** → Postgres.  
* **High‑volume read cache** → Redis (`cache‑aside`).  
* **Search & analytics** → Elasticsearch.  
* CDC via Debezium streams into Kafka (see chapter 25).

---

## 7&nbsp;· Interview Flashcards
* *Vertical* vs *horizontal* scaling; define **sharding key** pitfalls.  
* Explain **BASE** in one sentence (“always returns but may be stale”).  
* Why **foreign keys** are impossible in DynamoDB (single partition).  
* Trade‑offs of **multi‑doc txn** in Mongo (global lock → throughput hit).



---

## 8 · NoSQL Families Cheat‑Sheet

| Type | Example Engines | Ideal workload |
|------|-----------------|----------------|
| **Key‑Value** | Redis, DynamoDB | Session cache, config |
| **Document** | MongoDB, Couchbase | Product catalogs, CMS |
| **Wide‑Column** | Cassandra, HBase | High‑write time‑series |
| **Graph** | Neo4j, Amazon Neptune | Social networks, fraud path |

---

## 9 · Choosing the Right Database (Decision Heuristics)

1. **Access pattern first** – Are most operations key lookup, hierarchical doc, analytic scan?  
2. **Consistency need** – Strong invariants → RDBMS / CP store.  
3. **Growth projection** – Horizontal scale early if dataset > single node.  
4. **Latency target** – <5 ms? In‑memory KV (Redis).  
5. **Query flexibility** – If ad‑hoc joins indispensable, prefer RDBMS or DWH.  

*Rule from chat: “pick the DB that solves 90 % of queries with primary key”.*

