# Concurrency with Scala Futures

Scala’s `Future` abstraction allows you to run asynchronous computations and compose them. By default, creating a `Future` starts its execution immediately on an `ExecutionContext`. This document explores various patterns for launching and coordinating multiple futures **truly in parallel**, common pitfalls, and best practices.

---

## 1. Eager Execution and `ExecutionContext`

```scala
import scala.concurrent.{Future, ExecutionContext}
import ExecutionContext.Implicits.global

// This starts immediately when constructed:
val f: Future[Int] = Future {
  // some heavy computation
  Thread.sleep(1000)
  42
}
```

- **Eager**: A `Future` begins running as soon as it’s created.
- **ExecutionContext**: Underlying thread pool.  
  - Default: `global` fork-join pool, sized to CPU cores.  
  - For blocking I/O: wrap in `blocking { … }` or use a separate thread pool.

---

## 2. `Future.sequence`

Collect many futures into one:

```scala
val futures: List[Future[Int]] = List(1,2,3).map(i ⇒ Future { heavyComputation(i) })
val all: Future[List[Int]] = Future.sequence(futures)

all.onComplete {
  case Success(results) ⇒ println(s"All done: $results")
  case Failure(e) ⇒ println(s"Error: $e")
}
```

- **Use-case**: Run N independent tasks and await all.
- **Failure**: Fails fast—if any future fails, the combined future fails.

---

## 3. `Future.traverse`

Map + sequence in one step:

```scala
val ids = List("A","B","C")
val fetched: Future[List[Data]] =
  Future.traverse(ids)(id ⇒ Future { fetchFromDb(id) })
```

Equivalent to `Future.sequence(ids.map(...))`.

---

## 4. Pairwise Combination: `zip` / `zipWith`

For exactly two futures:

```scala
val f1 = Future { computeA() }
val f2 = Future { computeB() }

// Pair results
val pair: Future[(A,B)] = f1.zip(f2)

// Combine via function
val sum: Future[Int] = f1.zipWith(f2)(_ + _)
```

---

## 5. For-Comprehension Pitfall

A naïve for-comprehension **sequences** creation, not execution:

```scala
for {
  a ← Future { heavyComputation(1) }
  b ← Future { heavyComputation(2) }
  c ← Future { heavyComputation(3) }
} yield (a, b, c)
```

Under the hood:

```scala
Future { heavyComputation(1) }
  .flatMap(a ⇒ Future { heavyComputation(2) }
  .flatMap(b ⇒ Future { heavyComputation(3) }
    .map(c ⇒ (a, b, c))))
```

- **Problem**: `b` doesn’t start until `a` finishes, and `c` after `b`.
- **Result**: Sequential, not parallel.

### True Concurrency with For-Comprehension

```scala
// 1. Start futures immediately:
val f1 = Future { heavyComputation(1) }
val f2 = Future { heavyComputation(2) }
val f3 = Future { heavyComputation(3) }

// 2. Compose them:
val combined: Future[(Int, Int, Int)] = for {
  a ← f1  // all are already running
  b ← f2
  c ← f3
} yield (a, b, c)
```

---

## 6. “First One Wins”: `Future.firstCompletedOf`

```scala
val fastest: Future[Int] = Future.firstCompletedOf(List(f1, f2, f3))
```

- **Use-case**: Race conditions or fallback strategies.

---

## 7. Parallel Collections

For CPU-bound work on collections:

```scala
import scala.collection.parallel.CollectionConverters._

val results = (1 to 1000000).toList.par.map(i ⇒ heavyComputation(i))
```

- Uses a fork-join pool.
- No `Future` wrapping needed.

---

## 8. Functional Libraries: Cats Effect & ZIO

Purely functional alternatives:

```scala
import cats.effect.IO
import cats.implicits._

// List[IO[Int]]
val tasks: List[IO[Int]] = List(
  IO(heavyComputation(1)),
  IO(heavyComputation(2)),
  IO(heavyComputation(3))
)

// Run in parallel, get List[Int]
val parallel: IO[List[Int]] = tasks.parSequence
```

- **Benefits**: Resource safety, fiber-based concurrency, rich error handling.

---

## 9. Error Handling & Timeouts

- **Recover**: provide a fallback value.
  ```scala
  future.recover { case _: TimeoutException ⇒ defaultValue }
  ```
- **onComplete** / **onFailure** / **onSuccess**: side-effects.
- **Await.result**: blocking wait (avoid in non-test code).
- **withTimeout**: custom combinator.
  ```scala
  val withTimeout = Future.firstCompletedOf(Seq(future, timeoutFuture))
  ```

---

## 10. Summary Table

| Pattern                          | Description                                  |
|----------------------------------|----------------------------------------------|
| `Future.sequence`                | N futures → `Future[List[T]]`, fail-fast     |
| `Future.traverse`                | Map + sequence                              |
| `zip` / `zipWith`                | Pair/combine two futures                    |
| Naïve `for`-comprehension        | Sequential launch and composition (avoid)    |
| For-comprehension (pre-started)  | Concurrent composition of already-running    |
| `firstCompletedOf`               | Race, take fastest                           |
| Parallel Collections             | `Seq.par.map(..)` for CPU-bound             |
| Cats/ZIO `parSequence`, `zipPar` | Functional-style parallelism                |

---

*Authored on June 24, 2025.*
