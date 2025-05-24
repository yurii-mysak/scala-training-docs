# FS2 Streams: Reactive Streams Interop

FS2 offers full compliance with the Reactive Streams specification via the `fs2-reactive-streams` module, enabling interoperability with other Reactive Streams libraries (e.g., Akka Streams, RxJava).

---

## 1. Reactive Streams Primer

Reactive Streams defines four interfaces:
- **Publisher[T]**: emits items to **Subscribers**.
- **Subscriber[T]**: consumes items from **Publishers**.
- **Subscription**: manages back-pressure, request(n) and cancel().
- **Processor[I, O]**: a hybrid of Subscriber and Publisher.

Back-pressure is built-in: subscribers signal demand via `request(n)`.

---

## 2. FS2 Publisher & Subscriber

FS2 provides extension methods:

- **`Stream[F, O].toUnicastPublisher`**: convert FS2 Stream to a Reactive Streams Publisher.
- **`Stream.fromPublisher[F, O](publisher)`**: consume from a Reactive Streams Publisher as FS2 Stream.

### Example: FS2 → Reactive Streams Publisher

```scala
import cats.effect.IO
import fs2.Stream
import fs2.interop.reactivestreams._

val fs2Stream: Stream[IO, Int] = Stream.iterate(1)(_ + 1).take(5)
val publisher = fs2Stream.toUnicastPublisher
// publisher: org.reactivestreams.Publisher[Int]
```

### Example: Reactive Streams Publisher → FS2

```scala
import fs2.Stream
import fs2.interop.reactivestreams._

val externalPublisher: org.reactivestreams.Publisher[String] = ???
val fs2FromPub: Stream[IO, String] = Stream.fromPublisher[IO, String](externalPublisher)
```

---

## 3. Back-Pressure in FS2 Interop

- FS2 honors `request(n)` from subscribers.
- Upstream FS2 stream will only produce as many elements as requested, ensuring no resource exhaustion.

---

## 4. Use Cases

- **Integrate FS2 with Akka Streams**: bridge between two streaming libraries in a microservice architecture.
- **Leverage JMS or Pulsar clients**: wrap their Reactive Streams Publisher output into FS2.
- **Test harnesses**: easily supply test data via FS2 and feed into Reactive Streams-based components.

---

## 5. Further Reading

- FS2 Reactive Streams Guide: https://fs2.io/#/guide?id=reactive-streams  
- Project: https://github.com/typelevel/fs2-reactive-streams  
