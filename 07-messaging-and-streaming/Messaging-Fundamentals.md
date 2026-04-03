# Messaging Fundamentals

Modern distributed systems often rely on **asynchronous messaging** to let independent
components talk to each other **without having to be online, healthy, or aware of each
other’s implementation details at the same time**.  
Think of a postal service: the sender drops a letter in a mailbox and leaves; the
post‑office stores, routes, and eventually delivers it, while the receiver picks it up
when convenient.  

---

## 1. What *is* a Message ?

A *message* is a self‑contained data package that travels over a network
via a **Message‑Oriented Middleware** (MOM, _message broker_).  
Typical elements (field names differ per broker):

| Section | Purpose | Examples |
|---------|---------|----------|
| **Header / Metadata** | Routing & protocol‑level data | *timestamp*, *content‑type*, *key*, *partition*, *delivery‑mode* |
| **Properties** | Application‑level attributes | *user‑id*, *tenant*, *trace‑id*, custom tags |
| **Body / Payload** | Business data (JSON, Avro, Protobuf, bytes) | `{ "orderId": 42, "total": 19.99 }` |

![Generic message envelope](https://raw.githubusercontent.com/ymysak/static-assets/main/images/message-envelope.png)

---

## 2. Why Use Messaging ?

1. **Loose coupling** – services need only agree on the *contract* (schema), not each
   other’s location or uptime.
2. **Load leveling (buffering)** – queues absorb bursts, smoothing traffic spikes.
3. **Resilience & graceful degradation** – if recipients are down, messages persist.
4. **Scalability** – horizontal consumers can be added without touching producers.
5. **Observability** – brokers expose metrics, tracing, DLQs for troubleshooting.

Analogies:  
*Email* (store‑and‑forward), *parcel lockers* (pick‑up later), *restaurant kitchen
ticket rail* (orders printed, chefs pick up independently).

---

## 3. Messaging Patterns

| Pattern | Broker Primitive | Analogy | When to Use |
|---------|------------------|---------|-------------|
| **Point‑to‑Point** | *queue* (RabbitMQ), *partition* (Kafka with single consumer group), *SQS Standard* | Single counter queue at a bank | One consumer receives each message, tasks, job queues |
| **Publish–Subscribe** | *fanout/topic exchange* (RabbitMQ), *Kafka topic with many consumer groups*, *SNS* | Radio broadcast | Fan‑out events to many independent listeners |
| **Request / Reply** | Temporary queues, correlation ids | Phone call with caller‑ID | Workflows needing a response |
| **Competing Consumers** | Multiple consumers in same group | Taxi stand – first grabs job | Throughput with ordered processing per partition |

---

## 4. Acknowledgements & Delivery Guarantees (QoS)

| Guarantee | Broker Support | What it Means | Trade‑Off |
|-----------|---------------|---------------|-----------|
| **At‑most‑once** | Fire‑and‑forget send (`acks=0` in Kafka) | No duplicate, but possible loss | Fastest, risky |
| **At‑least‑once** | Default for RabbitMQ, Kafka (`acks=all`) | No loss, but duplicates possible | Requires idempotent consumer |
| **Exactly‑once** | Kafka transactional APIs, Cloud Pub/Sub with *ordering keys* | No loss *and* no duplicates | Extra coordination & storage |

Ack types (RabbitMQ): `basic.ack`, `basic.nack`, `basic.reject` (requeue or DLQ).  
Kafka offset commit: **auto**, **sync**, **async** (store offset in broker to mark ack).

---

## 5. Dead‑Letter Queues (DLQ)

Messages that cannot be processed after *N* attempts or due to
validation errors are rerouted to a *dead‑letter queue* for inspection.
DLQs prevent poison messages from blocking critical flows.

---

## 6. High Availability

* **RabbitMQ mirrored queues / quorum queues** (Raft)  
* **Kafka replication factor ≥ 3**, leader election via Raft / ZooKeeper (legacy)  
* **Cloud brokers**: SQS, Pub/Sub are multi‑AZ by default.

![Cluster vs single broker](https://raw.githubusercontent.com/ymysak/static-assets/main/images/broker-ha.svg)

---

## 7. Batch & Asynchronous I/O

Batching amortises the network round‑trip cost: Kafka producer `linger.ms` +
`batch.size`; RabbitMQ publisher confirm *batch* vs *individual* vs *async* confirms.  
Asynchronous send returns `Future[RecordMetadata]` (Kafka) or unit and a confirm
callback (RabbitMQ).

---

## 8. Quick Scala Examples

<details>
<summary>Kafka Producer (asynchronous, at‑least‑once)</summary>

```scala
import org.apache.kafka.clients.producer.*
import org.apache.kafka.common.serialization.StringSerializer
import java.util.Properties
import scala.jdk.FutureConverters.*

val props = Properties()
props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092")
props.put(ProducerConfig.ACKS_CONFIG, "all")          // at‑least‑once
props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, classOf[StringSerializer].getName)
props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, classOf[StringSerializer].getName)

val producer = KafkaProducer[String, String](props)
val record   = ProducerRecord("orders", "42", """{ "total": 19.99 }""")

producer.send(record).asScala
  .foreach(md => println(s"Stored at offset ${md.offset()} in partition ${md.partition()}"))
```
</details>

<details>
<summary>RabbitMQ basic publish (fanout exchange)</summary>

```scala
import com.rabbitmq.client.*
val factory = ConnectionFactory()
factory.setHost("localhost")
val conn  = factory.newConnection()
val chan  = conn.createChannel()

chan.exchangeDeclare("logs", BuiltinExchangeType.FANOUT)
val msg = "server started @ " + java.time.Instant.now
chan.basicPublish("logs", "", null, msg.getBytes("UTF-8"))
println(" [x] Sent '" + msg + "'")
```
</details>

---

## 9. Further Reading

* RabbitMQ AMQP Concepts – Exchanges, Queues, Bindings, Ack
* _Kafka: The Definitive Guide_ (Ch. 1–4)
* FS2 & Akka Streams Guides – back‑pressure and reactive principles
* AWS Messaging Services Overview – SQS, SNS, Kinesis, MQ
