# Akka Streams and Backpressure Guide

## Introduction
Akka Streams is a module within the Akka toolkit that provides a high-level, declarative API for processing streams of data in a reactive, non-blocking, and backpressured manner. It implements the [Reactive Streams](https://www.reactive-streams.org/) specification to ensure interoperability with other stream libraries and promote responsive, resilient, and elastic applications.

---

## Core Concepts of Reactive Streams
Reactive Streams defines a standard for asynchronous stream processing with non-blocking backpressure. The key concepts are:

- **Publisher**: An entity that emits a potentially unbounded sequence of elements to one or more Subscribers.
- **Subscriber**: An entity that consumes elements, reacting to the events emitted by a Publisher.
- **Subscription**: A link between a Publisher and a Subscriber that lets the Subscriber control the rate of data flow by requesting elements.
- **Processor**: A component that acts both as a Subscriber and a Publisher, allowing transformation of the stream.

**Backpressure**: A mechanism by which a Subscriber signals its capacity to process more elements, preventing a fast Publisher from overwhelming a slow Subscriber. This is accomplished through the `request(n)` method in the Subscription, where `n` is the number of elements the Subscriber is ready to handle.

---

## Akka Streams Building Blocks
Akka Streams provides the following abstractions:

1. **Source**  
   - Definition: A starting point of a stream that produces data elements.  
   - Example: `Source(1 to 100)` emits integers from 1 to 100.

2. **Flow**  
   - Definition: A processing stage that accepts input elements, performs transformations, and emits output elements.  
   - Example: `Flow[Int].map(_ * 2)` doubles each incoming integer.

3. **Sink**  
   - Definition: A terminating stage that consumes elements of a stream and produces a materialized value (e.g., completion signal, count).  
   - Example: `Sink.foreach[Int](println)` prints each element.

4. **RunnableGraph**  
   - Definition: A closed graph obtained by connecting Sources, Flows, and Sinks. It can be materialized (run).  
   - Example: `Source(1 to 5).via(Flow[Int].map(_ + 1)).toMat(Sink.seq)(Keep.right)`

5. **Materializer**  
   - Definition: A component responsible for turning the graph blueprint into a running stream, managing actors and execution context.  
   - Usage: `implicit val materializer = Materializer(system)`

---

## Detailed Backpressure Mechanism
Backpressure in Akka Streams is implemented by the following steps:

1. **Downstream Demand**  
   - Each Subscriber requests a number of elements (`request(n)`) from its upstream.  
   - Upstream stages only send elements when there is outstanding demand.

2. **Upstream Throttling**  
   - If a stage finishes processing and still has capacity, it requests more elements from its upstream.  
   - This request propagates back through intermediate stages to the Source.

3. **Buffering and Overflow Strategies**  
   - Each stage can buffer a limited number of elements to absorb bursty traffic.  
   - **Overflow strategies**:
     - `dropHead`: Drops the oldest element in the buffer.
     - `dropTail`: Drops the newest element.
     - `dropBuffer`: Clears the entire buffer.
     - `dropNew`: Drops the incoming element.
     - `fail`: Throws a `BufferOverflowException`.
     - `backpressure` (default): Slows down the upstream by not requesting more.

```scala
// Example of setting buffer and overflow strategy
val bufferedFlow = Flow[Int]
  .buffer(16, OverflowStrategy.dropHead)
  .mapAsync(4)(x => Future(x * 2))
```

---

## Use Case: File Processing Pipeline
Imagine a pipeline that reads lines from a large file, transforms each line to uppercase, and writes them to a database:

```scala
val fileSource: Source[String, Future[IOResult]] =
  FileIO.fromPath(Paths.get("input.txt"))
    .via(Framing.delimiter(ByteString("
"), maximumFrameLength = 256, allowTruncation = true))
    .map(_.utf8String)

val transformFlow: Flow[String, String, NotUsed] =
  Flow[String].map(_.toUpperCase)

val dbSink: Sink[String, Future[Done]] =
  Sink.foreachAsync(parallelism = 4) { line =>
    db.insert(line)  // Assume db.insert returns Future[Unit]
  }

fileSource
  .via(transformFlow)
  .toMat(dbSink)(Keep.right)
  .run()
```

- **Backpressure**: If the database is slow, the sink requests fewer elements, propagating back to slow down file reading.
- **Buffering**: Default buffers hold in-flight elements, smoothing bursts.

---

## Practical Example: Rate Limiting
To protect an external API, you can throttle the rate of requests:

```scala
import scala.concurrent.duration._

val apiRequests = Source(1 to 100)

val rateLimitedRequests = apiRequests.throttle(5, 1.second, 5, ThrottleMode.shaping)

rateLimitedRequests.mapAsync(2)(id => callExternalApi(id)).runWith(Sink.ignore)
```

- **`throttle`** ensures no more than 5 elements per second.
- **`ThrottleMode.shaping`** delays elements to match the rate.

---

## Monitoring and Metrics
- **Stream supervision**: Define `supervisionStrategy` to handle failures (resume, restart, stop).
- **Kamon integration**: Use [Kamon](https://kamon.io/) to collect metrics like processing time, buffer sizes, and throughput.
- **Debugging**: `Log` operator can log events at stages.

```scala
val loggingFlow = Flow[Int]
  .log("processing-element")
  .addAttributes(Attributes.logLevels(onElement = Logging.InfoLevel))
```

---

## Best Practices
- **Non-blocking stages**: Avoid `Thread.sleep` or blocking I/O; use `mapAsync` for asynchronous operations.
- **Controlled parallelism**: Use `mapAsync(parallelism)` to limit concurrent tasks.
- **Appropriate buffer sizes**: Start with default (16), tune based on throughput and memory.
- **Error handling**: Apply `recover` or supervision strategies to handle failures without stopping the entire stream.
- **Graceful shutdown**: On application termination, allow streams to complete:  
  ```scala
  CoordinatedShutdown(system).addTask(PhaseServiceStop, "shutdown-streams") { () =>
    system.terminate()
  }
  ```

---

## Conclusion
Akka Streams simplifies building complex, asynchronous data-processing pipelines by leveraging the Reactive Streams specification. Backpressure and buffering ensure robust, fault-tolerant applications that can handle varying loads gracefully. By following the patterns and best practices outlined, you can implement efficient stream-based solutions for file processing, API integration, real-time analytics, and more.
