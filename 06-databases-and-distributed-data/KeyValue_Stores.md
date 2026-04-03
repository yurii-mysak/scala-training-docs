# Key‑Value Stores – Expanded Reference

—

## 1 · Architecture Internals

### 1.1 In‑memory dict + append‑only log (Redis AOF)
* Write: `SET k v` → append to AOF, update hash table.  
* Compaction: `BGREWRITEAOF`.

### 1.2 Slab allocator (Memcached)
* Pre‑allocates slabs by size class to avoid fragmentation.

---

## 2 · Redis Advanced Data Types

| Type | Commands | Real use |
|------|----------|----------|
| **Hash** | `HSET`, `HGETALL` | User profile bucket |
| **List** | `RPUSH`, `BLPOP` | Job queue |
| **Sorted Set** | `ZADD`, `ZRANGE` | Leaderboard |
| **Stream** | `XADD`, `XREADGROUP` | Event log with consumer groups |

> **Chat 2025‑05‑09**: we coded a Lua script to atomically `INCR` quota & publish event.

```lua
redis.call('INCR', KEYS[1])
redis.call('XADD', 'quota_stream', '*', 'user', ARGV[1])
```

---

## 3 · Distributed deployment patterns

| Pattern | Description |
|---------|-------------|
| **Client‑side sharding** (Ketama) | Hash key → server; simple but no rebalancing. |
| **Redis Cluster** | 16384 hash slots auto‑migrated. |
| **Proxy layer** (Twemproxy) | Central proxy manages shards; reduces client logic. |

---

## 4 · Cache‑Aside algorithm (diagram)

```
         miss
Client ---------> Cache
   |               |
   |               | miss
   |               v
   +-----------> Database
                   |
                 result
                   |
                   v
             Cache SET + TTL
```

TTL strategy from chat: **randomised expiry** to prevent stampede.

---

## 5 · Consistency & durability spectrum

| Setting | Redis | Effect |
|---------|-------|--------|
| `AOF everysec` | fsync each sec | Lose ≤1 s data on crash |
| `appendfsync always` | every write | Durable but slower |
| Replication | async | May lose acked writes if primary fails |

---

## 6 · Gotchas

| Pitfall | Mitigation |
|---------|------------|
| Hot key → shard imbalance | Add userId prefix or pipeline MSET |
| Large value (>512 MB) in Redis | Use external object store + indirection |
| Memcached eviction (LRU) race | Add namespace versioning |

---



---

## 7 · Why is Redis fast?

* **Event‑loop + single‑thread** avoids context switch.  
* Data in RAM; optional disk persistence async.  
* Optimised data structures (ziplist, intset) pick compact reps based on length.  
* Syscall batching via `writev` and pipeline.

---

## 8 · Key design guidelines

* Keep key short (<64 B).  
* Use colon hierarchy (`user:123:profile`).  
* Include version prefix for cache bust (`v2:user:123`).

### Aggregation boundary (value):

* Pack up to 512 KB per value for atomic get/set.  
* Avoid storing huge blobs; use pointer to S3.

---

## 9 · Memcached vs Redis deep points

| Dimension | Memcached | Redis |
|-----------|-----------|-------|
| Eviction | LRU slab | LRU/TTL per key |
| Persistence | none | RDB/AOF |
| Data types | Strings only | Rich |
| Cluster mode | client‑side | built‑in |
| TLS auth | Not native | Yes |

