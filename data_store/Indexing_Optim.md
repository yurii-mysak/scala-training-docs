# Indexing & Query Optimisation – Expanded Playbook

---

## 1 · Index Taxonomy

| Engine | Index type | Typical use |
|--------|------------|-------------|
| Postgres | **B‑tree** (default) | Equality/range on most types |
|          | **BRIN** | Huge append‑only tables; stores min/max per block |
|          | **GiST** | Geospatial & full‑text |
| MySQL/InnoDB | **B‑tree clustered** | Primary key, keeps row data inline |
|             | **Secondary** | Non‑PK columns; leaf stores PK pointer |
| SQL Server | **Non‑clustered** | Multiple per table; include columns |

---

## 2 · Index Fragmentation Explained

### 2.1 Page split diagram

```
Before insert
[30,40,50,60,70]
↓ insert 65 causes split
[30,40,50] | [60,65,70]
```
*50 % full pages cause bloat and longer scans.*

Check in Postgres:

```sql
SELECT * FROM pgstattuple('public.orders');
```

### 2.2 Defrag strategies
* **Postgres**: `REINDEX`, `VACUUM (FULL)`, or `pg_repack`.  
* **MySQL**: `OPTIMIZE TABLE`.  
* **Online rebuild**: create new index concurrently then drop old.

---

## 3 · Reading `EXPLAIN`

```sql
EXPLAIN ANALYZE
SELECT o.* FROM orders o
JOIN customers c ON c.id = o.cust_id
WHERE c.country = 'US' AND o.amount > 100;
```

| Node | Key points |
|------|------------|
| `Nested Loop` | Good if inner side indexed & small |
| `Hash Join` | Large joins; watch hash mem |
| `Seq Scan` | Table scan; maybe missing index |
| `Bitmap Index Scan` | Multiple index conditions combined |

Tip: check **actual time** vs **rows** to spot misestimates.

---

## 4 · Covering & Included Indexes

Postgres `INCLUDE`:

```sql
CREATE INDEX idx_order_status_incl
ON orders(status)
INCLUDE (amount, created_at);
```
Planner can satisfy query without heap fetch.

SQL Server non‑clustered:

```sql
CREATE INDEX ix_email_inc ON users(email) INCLUDE(name, created);
```

---

## 5 · Partial & Conditional Indexes

```sql
CREATE INDEX idx_active ON users(id)
WHERE status = 'ACTIVE';
```
Reduces size, locks predicate rows only.

---

## 6 · Statistics & Planner

* **ANALYZE** updates histograms; autovacuum triggers based on `autovacuum_analyze_scale_factor`.  
* MySQL: `innodb_stats_persistent` keeps stats on disk.

---

## 7 · Join Optimisation Tricks

| Pattern | Improvement |
|---------|-------------|
| Push predicates before join | Reduces row count |
| Choose proper join order | Use hints (`/*+ Leading(c) */`) |
| Break huge OR into UNION ALL | Lets planner use indexes |

---

## 8 · Materialized Views & Caching

Postgres:

```sql
CREATE MATERIALIZED VIEW sales_mv AS
SELECT date_trunc('day', created) d, SUM(amount)
FROM orders GROUP BY d;
REFRESH MATERIALIZED VIEW sales_mv;
```

Use for heavy aggregation refreshed nightly.

---

## 9 · CTE vs Inline View

Postgres optimises non‑`WITH RECURSIVE` CTE as inline (since v12). Older versions treat as optimisation barrier—inline manually if plan bad.

---

## 10 · Indexing Cheat Sheet

* Narrow index first; keep row width small.  
* Don’t index low‑cardinality booleans.  
* Combine leading equality + trailing range: `(user_id, created_at)` good for `user_id = ? AND created_at > ?`.

