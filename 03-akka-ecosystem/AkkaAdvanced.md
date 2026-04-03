# Akka Advanced: Fault Tolerance, Streams, Futures, and Clustering

---

## 1. Fault tolerance

### 1.1 Supervision strategies
* **Resume** – skip faulty message.
* **Restart** – stop & start actor, clears state.
* **BackoffSupervisor** for exponential restart delays.

HOCON example:
```hocon
akka.actor.deployment {
  /worker {
    supervisor-strategy = "akka.actor.DefaultSupervisorStrategy"
  }
}
```

### 1.2 Death watch
`context.watch(child)` to receive `Terminated(child)`.

---

## 2. Futures integration
Actors return `Future` via `ask`; use `pipeTo` to send result back without blocking.

---

## 3. Akka Streams quick tour
* **Source → Flow → Sink** graph.  
* Materialisation returns a `Future` (e.g., stream completion).  
* Back‑pressure via demand signalling.

Simple:
```scala
Source(1 to 10).map(_ * 2).runWith(Sink.foreach(println))(system)
```

---

## 4. Dispatchers revisited
`Dispatcher` is a `ThreadPoolExecutor` + mailbox.  
Configure parallelism:
```hocon
blocking-dispatcher {
  type = Dispatcher
  executor = "thread-pool-executor"
  thread-pool-executor {
    fixed-pool-size = 8
  }
}
```

---

## 5. Clustering (overview)
* **Seed nodes**, gossip, membership.  
* `ClusterSingleton` ensures one instance across cluster.  
* `ShardRegion` for entity distribution.

---

## 6. Streams vs Futures
* Streams = pull‑based, back‑pressured pipelines.  
* Futures = one‑shot async value.

Use `Source.future(fut)` to bridge.

---

## 7. Testing probes & streams
`TestSink` & `TestSource` allow deterministic assertions in streams DSL.

---

## 8. Interview nuggets
* Restart vs Resume.  
* back‑pressure signals (`Request(n)`).  
* Remoting uses Akka TCP artery.

