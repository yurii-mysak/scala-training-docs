# SQL Transactions & Locking – Expanded Guide

Merges all Q&A including isolation anomalies, deadlock demos, and 2PC internals.

---

## 1 · MVCC fundamentals

* Each row version has **xmin/xmax** (Postgres).  
* Readers see snapshot at **txStartId**.  
* DELETE sets xmax; VACUUM cleans later.

---

## 2 · Isolation anomalies illustrated

| Isolation | Allowed anomaly |
|-----------|-----------------|
| Read Committed | Non‑repeatable read, phantom |
| Repeatable Read | Phantom (unless predicate lock) |
| Serializable | None |

### 2.1 Example – Phantom under Repeatable Read
```sql
BEGIN;
SELECT COUNT(*) FROM orders WHERE amount > 100;
-- concurrent tx inserts new row
SELECT COUNT(*) ...           -- count changed!
COMMIT;
```

---

## 3 · Row vs Gap locks (InnoDB)

```sql
SELECT * FROM accounts WHERE id BETWEEN 10 AND 20 FOR UPDATE;
```
Locks matching rows **and** gap to prevent phantom insert.

---

## 4 · Deadlock detection

* MySQL: detects cycle ↔ victim rollback (`SHOW ENGINE INNODB STATUS`).  
* Postgres: waits `deadlock_timeout` then aborts one tx.

### Example cycle (chat demo)
1. Tx A locks row 1 → waits for row 2.  
2. Tx B locks row 2 → waits for row 1.

Fix: consistent ordering or `SELECT ... FOR UPDATE NOWAIT`.

---

## 5 · Optimistic vs Pessimistic lock – code snippets

*Optimistic*:
```sql
UPDATE products SET qty = qty-1
WHERE id=1 AND version=10;
```
Row updated only if version matches.

*Pessimistic*:
```sql
BEGIN;
SELECT ... FOR UPDATE;
-- process
COMMIT;
```

---

## 6 · Two‑Phase Commit message flow

```
Coordinator         Participant
    | ---PREPARE-->     |
    | <-- VOTE/ACK ---- |
    | ---COMMIT/ABORT-> |
```
* Prepared state written to redo log.  
* Crash recovery: if coord lost after PREPARE, participants block.

---

## 7 · Serializable snapshot isolation (SSI) – Postgres

* Detects dangerous rw‑conflict graph.  
* May abort tx even without lock conflict.

> Chat 2025‑05‑09: we enabled `default_transaction_isolation = 'serializable'` and got serialization failure under high concurrency.

---

## 8 · Index strategies for locking

* Covering index reduces need for row lock on heap.  
* Partial index + predicate lock smaller scope.  
* `SKIP LOCKED` (Postgres 9.5) for queue tables.

---

## 9 · Checklist quick‑fire

* Explain **phantom read** example.  
* Gap lock only in **RR/Serializable** (InnoDB).  
* 2PC vs Saga reasoning for micro‑services.

