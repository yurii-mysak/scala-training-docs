# Akka Streams Advanced Configuration & Patterns

This covers deeper Akka Streams topics: configuration, design principles, substreams, pipelining, parallelism, and robust error handling.

---

## 1. Configuration

Akka Streams runs on top of Akka Actors; adjust settings in `application.conf`:

```hocon
# application.conf
akka {
  actor {
    default-dispatcher {
      fork-join-executor {
        parallelism-min = 2
        parallelism-factor = 2.0
        parallelism-max = 4
      }
    }
  }
  stream {
    materializer {
      # Max buffer size before back-pressure
      max-input-buffer-size = 16
      # Dispatcher for stream actors
      dispatcher = "akka.actor.default-dispatcher"
    }
    # Attributes propagation
    output-burst-limit = 50
  }
}
```

- **Dispatcher**: threads for stream actors.
- **Buffer sizes**: control back-pressure thresholds.
- **Dispatcher per stream**: override via `.withAttributes(ActorAttributes.dispatcher("custom"))`.

---

## 2. Design Principles

Akka Streams embodies **Reactive Streams**:
1. **Asynchronous**: non-blocking.
2. **Back-pressure**: consumer dictates rate.
3. **Bounded buffers**: avoid unlimited memory use.
4. **Location transparency**: via StreamRefs, networks.

Analogous to an assembly line with control points (async boundaries).

---

## 3. Substreams

Split and process logical sub-streams:

```scala
val source: Source[Int, NotUsed] = Source(1 to 100)

// group by even/odd keys
val sub = source
  .groupBy(2, _ % 2)
  .mapAsync(4)(n => Future(n * 2))
  .mergeSubstreams

sub.runWith(Sink.foreach(println))
```

- `groupBy`: splits into substreams by key.
- `splitWhen` / `splitAfter`: split on predicate.
- `mergeSubstreams`: reassemble.

---

## 4. Pipelining & Parallelism

### mapAsync / mapAsyncUnordered

```scala
val flow = Flow[Int]
  .mapAsync(parallelism = 4)(n => Future {
    Thread.sleep(100); n * n
  })
```

- **Ordered**: `mapAsync` preserves order.
- **Unordered**: `mapAsyncUnordered` emits as ready.

### Balancing & Merging

```scala
val balancer = Flow[Int].balance(3)
val merger   = Flow[Int].merge(3)

val graph = GraphDSL.create() { implicit b =>
  import GraphDSL.Implicits._

  val in = b.add(Source(1 to 100))
  val out = b.add(Sink.foreach(println))

  val bal = b.add(balancer)
  val mer = b.add(merger)

  in ~> bal
  for (_ <- 1 to 3) bal.out ~> Flow[Int].mapAsync(2)(heavyWork) ~> mer
  mer ~> out

  ClosedShape
}
RunnableGraph.fromGraph(graph).run()
```

- **balance**: split load across outlets.
- **merge**: combine multiple streams.

---

## 5. Error Handling & Supervision

Define a **supervision strategy** to resume or restart on failure:

```scala
val decider: Supervision.Decider = {
  case _: IOException         => Supervision.Resume
  case _: ArithmeticException => Supervision.Restart
  case _                      => Supervision.Stop
}

val safeFlow = flow.withAttributes(
  ActorAttributes.supervisionStrategy(decider)
)
```

- **Resume**: skip faulty element.
- **Restart**: clear operator state, flow continues.
- **Stop**: terminate the stream.

Attach at any stage:

```scala
val robustGraph = source
  .via(safeFlow)
  .toMat(sink)(Keep.right)
  .withAttributes(ActorAttributes.supervisionStrategy(decider))
  .run()
```

---

## 6. Further Reading

- Configuration Reference: https://doc.akka.io/docs/akka/current/stream/index.html  
- Design Principles: https://doc.akka.io/docs/akka/current/general/stream/stream-design.html  
- Substreams: https://doc.akka.io/docs/akka/current/stream/stream-substream.html  
- Parallelism: https://doc.akka.io/docs/akka/current/stream/stream-parallelism.html  
- Error Handling: https://doc.akka.io/docs/akka/current/stream/stream-error.html  
