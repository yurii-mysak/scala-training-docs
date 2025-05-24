# FS2 Streams Basics

[FS2 (Functional Streams for Scala)](https://fs2.io) provides a purely functional, effect-safe streaming library built on top of Cats Effect. It models streams as **lazy, immutable recipes** for producing and consuming data.

---

## 1. Core Concepts

- **Stream[F, O]**: a sequence of output values `O` in effect `F[_]`.
- **Pull**: the primitive that describes how to get the next chunk or terminate.
- **Chunk**: a collection of elements processed together for efficiency.
- **Pipe[F, I, O]**: alias for `Stream[F, I] => Stream[F, O]`.
- **Context Shift & Concurrency**: integrates with Cats Effect for parallelism and async boundaries.

Analogy: A **water pipeline** where valves and filters (pipes) transform and route water (data) through stages without leaking (no side-effects).

---

## 2. Building Streams

### From Pure Values

```scala
import fs2.Stream

// A finite stream of integers
val s1: Stream[Pure, Int] = Stream(1, 2, 3, 4)
```

### From Effects

```scala
import cats.effect.IO
import fs2.Stream

// Stream that reads lines from console
val consoleLines: Stream[IO, String] =
  Stream.eval(IO.readLine()).repeat.take(5)
```

### From Collections

```scala
val fromList: Stream[Pure, Int] = Stream.emits(List(10, 20, 30))
```

---

## 3. Transformations

- **map / evalMap**: `evalMap(f: O => F[O2])` for effectful mapping.
- **filter**: keep elements satisfying a predicate.
- **flatMap**: expand each element into a sub-stream.
- **through**: apply a `Pipe` transformation.

```scala
val processed: Stream[IO, Int] =
  fromList
    .map(_ * 2)
    .filter(_ % 4 == 0)
    .evalMap(i => IO(println(s"Processed $i")).as(i))
```

---

## 4. Effects & Resource Safety

Use `Stream.resource` to manage resources:

```scala
import cats.effect.{Resource, IO}
import fs2.Stream

def fileResource(path: String): Resource[IO, fs2.io.file.FileHandle[IO]] = ???

val fileLines: Stream[IO, String] =
  Stream.resource(fileResource("data.txt"))
        .flatMap(_.reads(4096))
```

Resources are automatically released when the stream terminates or fails.

---

## 5. Parallelism & Concurrency

- **parEvalMap**: apply effectful function in parallel.
- **merge / parJoin**: combine multiple streams concurrently.

```scala
Stream.emits(1 to 5)
  .covary[IO]
  .parEvalMap(3)(n => IO(n * n))
  .evalMap(sq => IO(println(s"Square: $sq")))
```

---

## 6. Error Handling

- **handleErrorWith**: recover from errors.
- **attempt**: convert to `Either[Throwable, O]`.

```scala
val safe: Stream[IO, Int] =
  consoleLines.evalMap(line =>
    IO(line.toInt).handleErrorWith(_ => IO(0))
  )
```

---

## 7. Further Reading

- Official FS2 Guide – Building Streams: https://fs2.io/#/guide?id=building-streams  
- Concurrency: https://fs2.io/#/guide?id=concurrency  
- Error Handling: https://fs2.io/#/guide?id=error-handling
