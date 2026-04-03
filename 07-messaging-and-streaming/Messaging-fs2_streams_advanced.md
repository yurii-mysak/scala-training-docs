# FS2 Streams Advanced Patterns

This covers more advanced FS2 topics: configuration, concurrency, reactive streams interop, and robust error handling.

---

## 1. Configuration

FS2 is purely functional and configurable via pure code and Cats Effect integration:

```scala
import fs2.Stream
import cats.effect.{IO, Resource}
import fs2.io.file.{Files, Path}

// Example: read file with custom chunk size
val fileStream: Stream[IO, String] =
  Files[IO]
    .readAll(Path("data.txt"), chunkSize = 8192)
    .through(fs2.text.utf8.decode)
    .through(fs2.text.lines)
```

- **Chunk Size**: tune memory vs. I/O trade-off.
- **Through Pipes**: chain transformations declaratively.
- **Resource Safety**: use `Stream.resource` for managed resources.

---

## 2. Concurrency

FS2 provides several primitives for parallelism:

- **parEvalMap**: effectful mapping with bounded parallelism.
- **parJoin**: merge multiple streams concurrently.

```scala
// Parallel map with up to 4 fibers
Stream.emits(1 to 10)
  .covary[IO]
  .parEvalMap(4)(n => IO(n * n))
  .evalMap(result => IO(println(s"Squared: $result")))
  .compile
  .drain
```

- **maxConcurrentOps**: control fiber usage.
- **Async Boundaries**: `.evalMap` introduces asynchronous boundaries automatically.

---

## 3. Reactive Streams Interop

FS2 can interoperate with Reactive Streams using the `fs2-reactive-streams` module:

```scala
import cats.effect.IO
import fs2.Stream
import fs2.interop.reactivestreams._

val rsPublisher = Stream.emits(1 to 5).covary[IO].toUnicastPublisher
val fs2FromRS: Stream[IO, Int] = Stream.fromPublisher[IO, Int](rsPublisher)
```

- Conform to Reactive Streams spec with back-pressure.
- Integrate FS2 with Akka Streams or other Reactive Streams libraries.

---

## 4. Error Handling

Handle errors declaratively in FS2:

- **handleErrorWith**: recover from errors.
- **attempt**: convert stream to `Either[Throwable, A]`.
- **onError**: execute cleanup on failure.

```scala
val safeStream: Stream[IO, Int] =
  Stream.eval(IO(throw new RuntimeException("fail")))
    .handleErrorWith { e => 
      Stream.eval(IO(println(s"Error: ${e.getMessage}"))).as(-1)
    }
    .compile
    .toList
```

- Use **`Stream.bracket`** for safe acquisition and release:
  ```scala
  Stream.bracket(IO(openConn()))(conn => IO(conn.close())).flatMap { conn =>
    Stream.eval(IO(conn.read()))
  }
  ```

---

## 5. Further Reading

- FS2 Guide – Configuration: https://fs2.io/#/guide  
- Concurrency: https://fs2.io/#/guide?id=concurrency  
- Error Handling: https://fs2.io/#/guide?id=error-handling  
- Reactive Streams Interop: https://github.com/typelevel/fs2-reactive-streams  
