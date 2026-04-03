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
  * AtomicReference is a low-level, eager, side-effecting tool for lock-free mutable references in the JVM. 
  * Ref[F, T] wraps that same power in a pure, lazy, composable effect, fitting neatly into functional-effect programs (and forming the foundation for higher-level, safe concurrency primitives).
* When to pick `Deferred` vs `Semaphore`. 
  * | Feature           | Deferred                                                                     | Semaphore                                                                                      |
    | ----------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
    | Core concept      | A one-shot, write-once “promise” or “latch”                                  | A mutable counter of permits for controlling concurrency                                       |
    | State transitions | Starts empty; can be completed **exactly once**, then never changes          | Starts with N permits; can be **acquired** (decrement) and **released** (increment) repeatedly |
    | Waiting behavior  | Any number of fibers can **wait** on it; they all resume once it’s completed | Fibers wait only if no permits are available; otherwise acquire immediately                    |
    | Data carried      | Holds a single value of type `A`                                             | Carries no payload; it only tracks permit counts                                               |
  * Use Deferred when you need a one-time signal or to publish a single result to many consumers:
    * Initialization barrier 
      * One fiber performs setup (e.g. loading config), then completes the Deferred. Other fibers .get on it and suspend until setup is done.
  
    * Promise/future
      * You want to hand out a “promise” to consumers and have exactly one producer fill it.
  
    * Single event coordination
      * E.g. signal shutdown, trigger a cleanup, or broadcast that a resource is ready.
  * Use Semaphore when you need to limit or gate the number of concurrent operations:
    * Connection pools
      * Limit to N simultaneous database connections or HTTP clients.

    * Backpressure
      * Ensure only M fibers can enter a critical section (e.g. writing to a file).

    * Rate limiting
      * Combined with a refill strategy, you can build simple rate limiters.
  
* How `start` returns a **`Fiber`** handle.  
* `Resource` is just `Kleisli` under the hood.

