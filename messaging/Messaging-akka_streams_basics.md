# Akka Streams Fundamentals

Akka Streams provides a **reactive** and **back-pressured** way to process streams of data, built on top of Akka Actors.

---

## 1. Core Components

- **Source[Out, Mat]**: emits elements; like a producer.
- **Flow[In, Out, Mat]**: processes/transforms elements; like a conveyor belt.
- **Sink[In, Mat]**: consumes elements; like a consumer.
- **RunnableGraph[Mat]**: a blueprint combining Source → Flow → Sink, ready to run (materialize).

![Akka Streams Components](https://doc.akka.io/docs/akka/current/stream/images/stream-components.png)

---

## 2. Working with Flows

A **Flow** defines a processing stage. Common operations:

- `map`: synchronous transformation.  
- `filter`: drop elements not matching a predicate.  
- `via`: insert another Flow.  
- `buffer`: introduce an internal buffer for back-pressure tuning.  

```scala
import akka.actor.ActorSystem
import akka.stream.scaladsl._
import akka.stream.Materializer

implicit val system = ActorSystem("StreamSystem")
implicit val materializer = Materializer(system)

val source = Source(1 to 20)
val flow: Flow[Int, Int, NotUsed] =
  Flow[Int]
    .map(_ * 2)               // multiply each element
    .filter(_ % 3 == 0)       // keep multiples of 3
    .buffer(10, overflowStrategy = OverflowStrategy.dropHead)

val sink = Sink.foreach[Int](x => println(s"Got: $x"))

val graph = source.via(flow).to(sink)
graph.run()
```

---

## 3. Back-Pressure & Demand Signalling

Back-pressure ensures fast producers don’t overwhelm slow consumers:

1. **Demand**: Sink signals how many elements it can handle.
2. **Flow**: propagates demand upstream.
3. **Source**: emits only when requested.

**Analogy**: A restaurant kitchen where waitstaff only bring new orders when chefs indicate they have capacity.

---

## 4. Materialization

Running a graph allocates resources (actors, buffers) and returns materialized values:

```scala
val sumSink: Sink[Int, Future[Int]] = Sink.fold(0)(_ + _)
val sumResult: Future[Int] = source.toMat(sumSink)(Keep.right).run()
```

---

## 5. Error Handling

- **Supervision strategies**: restart, resume, stop on failure.  
- Attach via `withAttributes(ActorAttributes.supervisionStrategy(...))`.

```scala
val safeFlow = flow.withAttributes(
  ActorAttributes.supervisionStrategy {
    case _: ArithmeticException => Supervision.Resume
    case _                      => Supervision.Stop
  }
)
```

---

## 6. Further Reading

- Akka Streams Guide – Flows and Basics: https://doc.akka.io/docs/akka/current/stream/stream-flows-and-basics.html  
- Graph DSL, Substreams, Parallelism sections in official docs.  
