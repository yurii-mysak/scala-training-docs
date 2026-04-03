# Stream Processing in Scala – Expanded Handbook

---

## 1 · Motivation

Stream processing lets you model **unbounded, back‑pressured** data pipelines with resource safety, contrasting with one‑shot `Future` or in‑memory collections.

---

## 2 · FS2 Core Concepts

| Term | Meaning |
|------|---------|
| `Stream[F, A]` | Pull‑based sequence of `A` in effect `F` |
| Chunk | Vector batch to reduce overhead |
| Pull | Low‑level step to build complex operators |

### 2.1 Resource safety

```scala
Stream.bracket(IO(open))(close).flatMap(use)
```
Automatically releases even on error or cancel (uses Cats `Resource` under hood).

### 2.2 Concurrency combinators

* `parEvalMap(n)(f)` – parallel map with `n` fibers.  
* `merge`: interleave two streams.  
* `interruptWhen(signal)` – stop on Boolean stream.

### 2.3 Error handling

```scala
stream.handleErrorWith(e => Stream.eval(log(e)) >> Stream.empty)
```

---

## 3 · Akka Streams Deep Dive

### 3.1 Graph DSL

```
Source -> Flow1 -> Flow2 -> Sink
```

* Materialized value: `Future[Done]` or custom.  
* Stages backed by Actors; each boundary has mailbox.

### 3.2 Back‑pressure protocol

* Downstream sends `Request(n)` to upstream.  
* Overflow strategies: `dropHead`, `buffer`, `fail`.

### 3.3 Supervision

```scala
.flowWithContext
  .withAttributes(ActorAttributes.supervisionStrategy {
      case _: ArithmeticException => Supervision.Resume
  })
```

---

## 4 · Comparison Table

| Feature | **FS2** | **Akka Streams** |
|---------|---------|------------------|
| Paradigm | Pure FP, no mutation | Actor model |
| Error model | FP `raiseError` | Supervision directives |
| Back‑pressure | Pull, demand driven | Reactive Streams |
| Integration | Cats Effect ecosystem | Akka HTTP, Akka Actors |
| Hot vs cold | Cold by default | Cold |

---

## 5 · Kafka Bridges

### 5.1 FS2‑Kafka

```scala
KafkaConsumer.stream(...)
  .evalMap(process)
  .through(commitBatch(500, 15.seconds))
```

### 5.2 Alpakka Kafka

`Consumer.committableSource` + `Committer.sink`.

---

## 6 · Checkpointing & State

* FS2: maintain state via `scan`/`evalScan`.  
* Akka Streams: `statefulMapConcat` or use Alpakka `AlpakkaKafka.commitWithMetadata`.

---

## 7 · Testing streams

* FS2: pure streams test with `compile.toList` inside `IOTest`.  
* Akka: `TestSink` and `Source.tick`.

---

## 8 · Performance gotchas

| Gotcha | Solution |
|--------|----------|
| Unbounded queue in Akka | Use `buffer` + overflow strategy |
| Synchronous boundary excess | Combine flows where possible |
| Blocking calls in stage | Use `mapAsync` with blocking dispatcher |

---

