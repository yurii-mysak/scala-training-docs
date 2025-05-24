# Akka Streams: Reactive Streams Over Network (StreamRefs)

Akka Streams' **StreamRefs** allow **Reactive Streams** data flows to cross **actor boundaries** and network nodes, preserving back-pressure semantics end-to-end.

---

## 1. Overview of StreamRefs

- **SourceRef[T]**: a remote publisher; a `Source[T, NotUsed]` that streams elements from a remote actor.
- **SinkRef[T]**: a remote subscriber; a `Sink[T, NotUsed]` that sends elements to a remote actor.
- **Transport**: uses Akka Remoting or Cluster to ferry messages.
- **Back-pressure**: demand signals travel from SinkRef back to SourceRef.

Analogy: a hose (SourceRef) connected via a coupling (network) to a water tank (SinkRef): flow rate adapts to tank's intake capacity.

---

## 2. Enabling StreamRefs

Add settings in `application.conf`:

```hocon
akka {
  actor.provider = "cluster"
  remote.artery {
    canonical.hostname = "127.0.0.1"
    canonical.port = 25520
  }
}
```

Include dependency:

```scala
libraryDependencies += "com.typesafe.akka" %% "akka-stream" % "2.6.x"
```

---

## 3. Example Usage

### 3.1 Server: Expose SourceRef

```scala
import akka.actor.typed.{ActorSystem, Behavior}
import akka.actor.typed.scaladsl.Behaviors
import akka.stream.typed.scaladsl.{ActorMaterializer, StreamRefs}
import akka.stream.scaladsl.Source

object StreamServer {
  def apply(): Behavior[Any] = Behaviors.receive { (context, _) =>
    implicit val system = context.system
    import akka.actor.typed.scaladsl.adapter._
    implicit val classicSystem = system.toClassic
    implicit val mat = ActorMaterializer()

    // Create a SourceRef from a local Source
    val numbers: Source[Int, NotUsed] = Source(1 to 100).throttle(1, 1.second)
    val sourceRefFuture = numbers.runWith(StreamRefs.sourceRef[Int]())
    sourceRefFuture.foreach { sourceRef =>
      // Send the SourceRef to client via actor/message
      context.log.info(s"SourceRef ready: $sourceRef")
      // context.messageAdapter(...)(...)
    }
    Behaviors.same
  }
}
```

### 3.2 Client: Consume SourceRef

```scala
import akka.actor.typed.ActorSystem
import akka.stream.scaladsl.Source
import akka.stream.typed.scaladsl.StreamRefs
import scala.concurrent.duration._

val system = ActorSystem(Behaviors.empty[Any], "client")
implicit val classicSystem = system.toClassic
implicit val mat = ActorMaterializer()
import system.executionContext

// Assume sourceRef is received from server actor
val sourceRef: SourceRef[Int] = /* obtained from server */
// Run the remote stream as local Source
val remoteSource: Source[Int, NotUsed] = Source.fromGraph(sourceRef)
remoteSource.runForeach { n =>
  println(s"Received $n")
}
```

---

## 4. Flow Through SinkRef

Reverse direction: send elements to a remote SinkRef:

```scala
// Acquire SinkRef on server
val sinkRefFuture = StreamRefs.sinkRef[Int]().runWith(Sink.asPublisher(false))
// Provide SinkRef to client actor

// Client side
val sinkRef: SinkRef[Int] = /* from server */
Source(1 to 50).runWith(sinkRef)
```

---

## 5. Considerations

- **Lifecycle**: StreamRefs close on completion or failure.
- **Serialization**: ensure element types are serializable.
- **Timeouts**: configure handshake timeouts in `StreamRefs`.

---

## 6. Further Reading

- Akka Docs: StreamRefs – https://doc.akka.io/docs/akka/current/stream/stream-refs.html  
- Reactive Streams: https://www.reactive-streams.org/  
- Akka Distributed Data & Streams integration  
