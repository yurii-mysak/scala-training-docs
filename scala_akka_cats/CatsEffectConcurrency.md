# Cats Effect: Sync, Async, Concurrent, and Concurrency Primitives

This chapter groups the questions we had about **typeclasses hierarchy** and the standard primitives (`Ref`, `Deferred`, `Semaphore`, STM).

---

## 1. Type‑class hierarchy

```
        Monad
          ▲
        Sync     (suspend side‑effects)
          ▲
        Async    (register callbacks)
          ▲
     Concurrent  (fibers, race, cancellation)
```

### 1.1 `Sync`
* `delay`, `blocking`, and **`bracket`** for resource safety.

### 1.2 `Async`
* Model callback‑based APIs:
  ```scala
  Async[F].async_[A] { cb =>
    client.call(a => cb(Right(a)))
  }
  ```

### 1.3 `Concurrent`
* `start`, `racePair`, `parTraverse`.

---

## 2. Standard primitives

| Primitive | Category | Example use |
|-----------|----------|-------------|
| `Ref[F,A]` | Atomic mutable cell | counters, caching |
| `Deferred[F,A]` | One‑shot promise | result hand‑off between fibers |
| `Semaphore[F]` | Permit control | DB connection pool |
| `MVar` (cats‑mtl) | Take/put synchronous queue | Producer/consumer |

### 2.1 Ref demo (chat 2025‑03‑20)
```scala
for
  ref <- Ref.of[IO](0)
  _   <- List.fill(100)(ref.update(_+1)).parSequence
  n   <- ref.get
yield n            // 100
```

---

## 3. Software Transactional Memory (STM) – `Ref` & `Atom`
Cats‑Effect 3 provides `Ref` but full STM is via **`cats-stm`** (external).  
Basic idea: optimistic retries until invariants hold.

---

## 4. Thread model

* **Compute pool** – fixed, CPUs × 2.  
* **Blocking pool** – cached, unbounded.  
* **Scheduler** – single thread for timers.

Guideline: never busy‑spin; always use `Temporal.sleep` or `Deferred`.

---

## 5. Resource management (`Resource`)

```scala
Resource.make(open)(close).use { file =>
  // do work
}
```
Guarantees release even on error or cancellation.

---

## 6. Interview checklist
* Differences between `Ref` and `AtomicReference`.  
* When to pick `Deferred` vs `Semaphore`.  
* How `start` returns a **`Fiber`** handle.  
* `Resource` is just `Kleisli` under the hood.

