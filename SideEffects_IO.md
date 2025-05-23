# Side‑Effects, the IO Monad, and Why It Exists

This chapter pulls together our discussions (2025‑03‑17 and 2025‑05‑14) on **reasoning about side‑effects**, the historical path that led to IO monads in Scala, and how Cats Effect implements them.

---

## 1. Why side‑effects are problematic
| Issue | Impact |
|-------|--------|
| **Hidden state** | Hard to test, unclear dependencies |
| **Non‑determinism** (time, I/O) | Breaks referential transparency |
| **Ordering guarantees** | Re‑ordering code may change behaviour |
| **Exception handling** | Side‑effects can throw unpredictably |

### Real bug from chat
We stepped through a `var balance` example where a concurrent increment lost updates. Wrapping the mutation in `Ref[IO, Int]` fixed it.

---

## 2. Birth of the IO Monad (mini‑history)
* **Haskell (late 1990s)** – isolated effects as `IO a` to keep pure core.  
* **Scalaz 7 (2010)** – first real IO monad in Scala; trampolined to avoid stack overflow.  
* **Cats Effect 1.x (2017)** – **`IO`** with callback‑based run‑loop.  
* **Cats Effect 3 (2021)** – native scheduling, structured concurrency, cancellation.

---

## 3. Anatomy of `IO`
```scala
type IO[A] = IORunLoop => (Either[Throwable,A] => Unit) => Unit
```
Conceptually: a function that, when you provide a callback, performs side‑effects then calls the callback with a result.

### Key properties
* **Lazy** – nothing happens until `unsafeRunSync()` or friends.  
* **Referentially transparent** – `io *> io` duplicates effect, unlike imperative call.  
* **Cancelable** – fiber can be interrupted.

---

## 4. `IO.blocking`
Doc link: <https://typelevel.org/cats-effect/docs/typeclasses/sync>

Use when calling a **blocking API**:
```scala
IO.blocking(scala.io.Source.fromFile("big.csv").mkString)
```
Shifts to the **blocking thread‑pool** so CPU pool isn’t starved (demo 2025‑04‑25).

---

## 5. Clock primitives
```scala
import cats.effect.Clock
Clock[IO].realTime           // returns FiniteDuration
```
Useful for **timed retry** and **metrics** without sticking to `System.nanoTime`.  
We injected fake `Clock` in unit tests.

---

## 6. Cheat‑sheet
| Want | Use |
|------|-----|
| Delay pure computation | `IO.delay` / `IO.apply` |
| Wrap blocking action | `IO.blocking` |
| Timestamp | `Clock[F].realTime` |
| Compose | `io1.flatMap(_ => io2)` or `io1 *> io2` |

