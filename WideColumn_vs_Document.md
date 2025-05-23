# Wide‑Column vs Document Stores – Deep Dive

Combines our 2025‑05‑02 access‑pattern chat, Cassandra data‑model notes, and Mongo schema design Q&A.

---

## 1 · Data Model Comparison

| Feature | Wide‑Column (Cassandra) | Document (MongoDB) |
|---------|-------------------------|--------------------|
| Row key | `(partition, clustering)` composite | `_id` (ObjectId or custom) |
| Column granularity | Millions of sparse columns | Entire document blob |
| Query unit | Partition slice | Whole document |
| Storage engine | LSM‑tree SSTables | WiredTiger B‑Tree + write‑ahead |
| Schema flexibility | Add new columns on write | Add new fields anytime |

---

## 2 · Cassandra table anatomy (chat snippet)

```cql
CREATE TABLE sensor_data (
  device_id  text,
  ts         timestamp,
  reading    double,
  PRIMARY KEY ((device_id), ts)
) WITH CLUSTERING ORDER BY (ts DESC);
```
*Partition key* = `device_id`; *clustering* = `ts DESC` for recent‑first reads.

---

### 2.1 Partition size rule
* ≤ 100 MB or 10,000 rows to avoid hotspot (per 2025‑05‑02 advice).*

---

## 3 · MongoDB document schema example

```json
{
  "_id": "p123",
  "title": "Hoodie",
  "variants": [
    {"size": "M", "sku": "p123-M", "qty": 4},
    {"size": "L", "sku": "p123-L", "qty": 1}
  ],
  "tags": ["apparel","winter"]
}
```

Indexes:
```javascript
db.products.createIndex({"variants.sku":1})
```

---

## 4 · Query patterns mapping

| Use case | Wide‑Column | Document |
|----------|-------------|----------|
| Time‑series per device | Partition per id | Bucket pattern with time field |
| Product catalog search | ALLOW FILTERING costly | Single doc lookup by `_id` |
| User feed timeline | Partition by userId & day | Embed posts or use separate collection + `$lookup` |

---

## 5 · Consistency and replication

| Aspect | Cassandra | MongoDB |
|--------|-----------|---------|
| Tunable read/write CL | `QUORUM`, `LOCAL_ONE` | `majority`, `linearizable` |
| Replication | Multi‑DC, gossip | Replica sets, election |
| Failure handling | Hinted hand‑off, read repair | Rollback / op‑log |

---

## 6 · Schema evolution strategies

*Wide‑Column*: new columns coexist; reads of old rows return `null`.

*Document*:
1. Version field in doc.
2. Lazy migration on read (`$setOnInsert`).
3. Background script.

---

## 7 · Anti‑patterns gathered

| DB | Anti‑pattern | Reason |
|----|--------------|--------|
| Cassandra | Using `IN` over large key list | Scatter‑gather to every replica |
| MongoDB | Large arrays updated per element | Causes doc moves & oplog bloat |
| Both | Hot partition key (country=US) | Skews load |

---

