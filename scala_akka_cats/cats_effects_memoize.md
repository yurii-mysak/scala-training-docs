# Cats Effect: Referential Transparency, Thread Safety & Memoization

## 1. Referential Transparency ⇒ No Hidden State, No Side-Effects

Referential transparency means an expression can be replaced by its value without changing program behavior. In Cats (and Cats Effect), all domain logic is encoded as pure values.

- **Pure functions only depend on their inputs**  
  ```scala
  def add(x: Int, y: Int): Int = x + y
  // You can replace `add(1,2)` with `3` anywhere without changing behavior.
  ```
- **No mutable shared state**  
  Without `var` or global mutation, there’s nothing for concurrent threads to race over.
- **Side effects are isolated**  
  An `IO[A]` is only a description until executed (e.g., via `unsafeRunSync()`), so you can pass around, compose, reorder, or memoize safely.

## 2. Thread Safety by Construction

Pure values can be shared and run on any thread without locks or coordination. Cats provides parallel combinators that work safely under the hood.

```scala
import cats.effect._
import cats.implicits._

// Two independent fetches running in parallel safely:
def fetch(id: Int): IO[String] = IO { /* side-effectful call */ s"User$id" }

val program: IO[(String, String)] =
  (fetch(1), fetch(2)).parTupled   // `parTupled` runs both on multiple threads safely
```

Concurrency primitives in Cats Effect (e.g., `Ref`, `Deferred`, `Semaphore`) themselves enforce atomic operations, avoiding `synchronized` blocks.

## 3. Determinism: Same Inputs → Same Outputs

Pure functions always yield the same result for the same inputs—no hidden clocks, random globals, or counters. Composition of pure functions remains pure.

```scala
def now: IO[Long] = IO(System.currentTimeMillis())

// `now` is a pure description; scheduling or refactoring it won’t change semantics.
val delayed: IO[Unit] =
  now.flatMap(t => IO(println(s"It is $t")))
```

## 4. Memoization (`memoize`)

Memoizing an `IO[A]` turns it into a new `IO[A]` that:

1. Runs the original effect **once**, on first evaluation.  
2. Caches (stores) the resulting `A`.  
3. On subsequent runs, immediately returns the cached `A`.

### Why memoize?

- **Idempotence**: fix non-idempotent effects to a single result.  
- **Determinism**: even volatile effects yield a consistent value.  
- **Performance**: avoid re-running expensive computations.

### Example

```scala
import cats.effect._
import scala.concurrent.duration._

val nowIO: IO[Long] = IO(System.currentTimeMillis())

for {
  memoNow <- nowIO.memoize   // IO[IO[Long]], allocates cache
  getOnce = memoNow          // IO[Long]
  t1     <- getOnce          // executes once
  _      <- IO.sleep(100.millis)
  t2     <- getOnce          // returns same t1
  _      <- IO(println(s"t1 = $t1, t2 = $t2"))
} yield ()
```

## 5. Purity, RT & Thread-Safety with Delayed Side Effects

- The **description** (`IO`) is immutable and thread-safe; you can share it across threads safely.
- **Actual side-effects** occur only when the runtime interprets the description.
- If underlying code mutates unsafe state, use Cats Effect primitives (`Ref`, `Deferred`) to guarantee atomicity and avoid races.

---

*All of the above combines to ensure that your Cats Effect programs are pure, thread-safe, and deterministic.*