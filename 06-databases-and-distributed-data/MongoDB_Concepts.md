# MongoDB Deep Concepts – Expanded

Synthesises all chats (May 2025) on replication, sharding, aggregation pipeline, consistency, and schema patterns.

---

## 1 · Architecture at a glance

```
 clients
    │
mongos router  <-- sharded cluster entry
    │
config servers (CSRS)  — metadata
    │
shard replica sets   ── primary + secondaries
```

* **Router (mongos)** – scatter‑gathers queries to shards.  
* **Config server** – stores chunk map; needs majority.

---

## 2 · Replica set internals

| Role | Responsibility |
|------|----------------|
| Primary | Accept writes, oplog source |
| Secondary | Pull oplog, apply ops |
| Arbiter | Votes only, no data |

**Election** – Raft‑like, majority. Chat note: “network partition with 3 nodes → primary + secondary keep majority, old primary becomes secondary”.

---

### 2.1 Majority vs Linearizable recap

| Concern | Majority | Linearizable |
|---------|----------|--------------|
| Write concern | `w: "majority"` | same |
| Read concern  | `local/majority` | `linearizable` |
| Guarantee | Durable after quorum | Read sees last committed |
| Latency | Lower | Higher (extra round trip) |

---

## 3 · Sharding Mechanics

* **Hash shard key** – uniform but no range query.  
* **Range shard key** – good for time‑series (`ts`), must handle chunk splits.

Chunk migration triggered at 64 MB (default); balancer moves hottest chunks off overloaded shard.

---

## 4 · Aggregation Pipeline Cheatsheet

| Stage | Use |
|-------|-----|
| `$match` | Filter early (index) |
| `$project` | Shape document |
| `$group` | Aggregation, `_id` key |
| `$lookup` | Left outer join |
| `$facet` | Multi‑facet in one pass |
| `$bucketAuto` | Histograms |

Performance tip (chat): put `$match` / `$project` before `$lookup` to minimise docs.

---

```javascript
db.orders.aggregate([
  {$match: {status:"PAID"}},
  {$lookup:{
     from: "customers",
     localField: "custId",
     foreignField:"_id",
     as: "cust"
  }},
  {$unwind:"$cust"},
  {$group:{_id:"$cust.country", revenue:{$sum:"$amount"}}}
])
```

---

## 5 · Schema Design Patterns

| Pattern | When to use |
|---------|-------------|
| **Bucket** | Time‑series (group events per hour) |
| **Outlier** | 90 % small docs inline, large in separate collection |
| **Subset** | Embed Top N comments, store rest separate |
| **Extended Reference** | Keep frequently‑read fields duplicated |

---

## 6 · Index cookbook

* **Compound prefix** rule: only leftmost fields usable.  
* **Partial index** – `status:"ACTIVE"` subset.  
* **TTL index** on date field for auto‑expire logs.  
* Hidden index (v4.4) for performance testing.

---

## 7 · Multi‑document ACID Transactions (since 4.0)

```javascript
session.startTransaction()
try {
  acc.updateOne({...})
  ledger.insertOne({...})
  session.commitTransaction()
} catch(e){
  session.abortTransaction()
}
```
* Limit: 60 seconds, 16 MB oplog, touch ≤1000 docs.  
* Use sparingly; impacts oplog & perf.

---

## 8 · Performance tips & anti‑patterns

| Anti‑pattern | Fix |
|--------------|-----|
| `$in` with 10 k values | Split into batches |
| Unbounded array growth | Use bucket + pagination |
| Large documents > 2 MB | Store blob in GridFS or S3 |

---

