# Purely Functional Parallelism & Concurrency

Scala’s Cats Effect and ZIO provide lightweight fibers, structured concurrency, and deterministic resource management—all without exposing low‑level threads.

---

## 1 · Parallel Combinators

* `parTraverse` / `parSequence` run independent effects in parallel using the compute thread‑pool.citeturn0search2turn0search8  
* `racePair` returns the winner & loser fiber.  
* `Fiber` handle supports `join`, `cancel`.

```scala
IO.parTraverse(List(1,2,3))(heavy)
```

---

## 2 · Thread Model

Cats‑Effect 3 uses three pools: *compute*, *blocking*, *scheduler*. Fibers are user‑mode tasks multiplexed onto worker threads.citeturn0search8

---

## 3 · Parallelism vs Concurrency

* **Concurrency** – structure overlapping tasks (fibers).  
* **Parallelism** – execute simultaneously on different cores; runtime schedules fibers fairly.

---

## 4 · Functional Parallelism à la *FP‑in‑Scala*

The book’s `Par[A]` wraps `ExecutorService` and provides `parMap`, `parFilter`, illustrating parallel algorithms in a pure API.citeturn0search2

---

## 5 · Best Practices

| Scenario | Operator |
|----------|----------|
| Independent API calls | `parTraverse` |
| First response wins | `race` / `racePair` |
| Timeout | `IO.race(io, IO.sleep(5.s))` |
| CPU‑heavy | wrap in `IO.blocking` to avoid starving compute pool |

---

