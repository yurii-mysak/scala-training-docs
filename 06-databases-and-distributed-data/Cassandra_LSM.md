# Cassandra Internals – LSM, Read/Write Path, and Compaction

All insights from April & May 2025 sessions.

---

## 1 · Write Path in detail

1. **Client → Coordinator** via token aware driver.  
2. **Coordinator** replicates mutation to replicas (based on RF) with `CL`.  
3. Each replica:  
   * Append to **commit‑log** (sequential fsync).  
   * Update **memtable** (skiplist).  
   * Respond `ACK`.

**Hinted hand‑off**: if replica down, coordinator stores hint row for later.

---

### 1.1 Durable writes config
`commitlog_sync_period_in_ms`; trade‑off latency vs durability.

---

## 2 · Memtable flush & SSTable format

* Memtable size threshold triggers flush.  
* Flush produces SSTable components:  
  * `Data.db` – rows  
  * `Index.db` – primary index every 128 KB  
  * `Summary.db` – sparse index  
  * `Filter.db` – Bloom filter

---

## 3 · Read Path trace (chat 2025‑05‑23)

```plaintext
BloomFilter  --miss--> skip SSTable
Summaries    --binary search-->
PrimaryIndex --points to--> Data row
```

If row appears in multiple SSTables, **most recent (by timestamp)** wins.

---

## 4 · Compaction strategies

| Strategy | Best for | How |
|----------|----------|-----|
| Size‑Tiered (STCS) | Write heavy, time‑series | Merge similar‑sized files |
| Leveled (LCS) | Read heavy, small rows | Size by exponential levels |
| Time‑Window (TWCS) | TTL data, logs | Merge only same time window |

Config:
```yaml
compaction = {'class':'LeveledCompactionStrategy', 'sstable_size_in_mb':160}
```

---

## 5 · Anti‑entropy & repair

* `nodetool repair` merges divergent replicas.  
* **Read repair** occurs if replicas differ beyond `read_repair_chance`.

---

## 6 · LSM vs B‑Tree Bench results (chat lab)

Test: 1 M writes then 1 M reads.

| Engine | Write TPS | Read TPS |
|--------|-----------|----------|
| Cassandra (LSM) | 105 k | 45 k |
| MySQL (B‑tree)  | 30 k  | 110 k |

Observation: LSM shines in write, B‑tree in point reads.

---

## 7 · Tombstones & GCGrace

Deletes create tombstone rows; purged after `gc_grace_seconds` + compaction.  
Keep low (e.g., 24 h) only if no replica downtime > grace.

---

## 8 · Troubleshooting commands

```bash
nodetool status          # ring view
nodetool cfstats keyspace.table
sstabledump file.db | jq '.'
```

Cassandra data model - https://medium.com/code-zen/cassandra-schemas-for-beginners-like-me-9714cee9236a
