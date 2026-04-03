# Reactive Read-Side Guide

This guide covers key concepts and examples for building read-side components in a Scala/Akka/Kafka/Cassandra architecture, including:

1. Akka Persistence Query  
2. Materialized Views  
3. Alpakka Connectors  
4. Projection + HTTP Endpoint Example

---

## 1. Akka Persistence Query

**What is it?**  
Akka Persistence Query is a read-side API for streaming persisted events and snapshots from the Akka Persistence journal. It enables building projections, audit UIs, replay tools, and any event-stream consumer.

**Key Concepts**  
- **ReadJournal**: Plugin-specific entry point (e.g. CassandraReadJournal)  
- **eventsByTag(tag, offset)**: Streams events tagged with a specific tag, starting from a given offset  
- **eventsByPersistenceId(persistenceId, fromSeq, toSeq)**: Streams events for one entity by persistenceId  
- **Offset**: Represents the position in the event stream (e.g., `NoOffset` or a sequence number)  
- **Offset Management**: Store and load offsets to resume projections without missing or reprocessing events

**Configuration (example for Cassandra)**  
```hocon
akka.persistence.query.journal.plugin = "akka.persistence.cassandra.query.journal"
akka.persistence.cassandra {
  query {
    refresh-interval = "250ms"
  }
}
```

**Basic Usage**  
```scala
import akka.persistence.query.PersistenceQuery
import akka.persistence.cassandra.query.scaladsl.CassandraReadJournal

val readJournal = PersistenceQuery(system)
  .readJournalFor[CassandraReadJournal](CassandraReadJournal.Identifier)

// Stream all events tagged "order-events" from the beginning
val eventsSource = readJournal.eventsByTag("order-events", Offset.noOffset)
```

**Example: Streaming by PersistenceId**  
```scala
readJournal
  .eventsByPersistenceId("Invoice-1234", 0L, Long.MaxValue)
  .runForeach { env =>
    println(s"Event ${env.event} at seq ${env.sequenceNr}")
  }
```

---

## 2. Materialized Views

A materialized view is a pre-computed, stored result of a query over base tables. It speeds up read operations by maintaining a physical copy of the view data, refreshed incrementally or on demand.

### Cassandra Example

```cql
-- Base table
CREATE TABLE IF NOT EXISTS orders (
  customer_id uuid,
  order_id    timeuuid,
  amount      decimal,
  PRIMARY KEY (customer_id, order_id)
);

-- Materialized View for top N orders by amount
CREATE MATERIALIZED VIEW IF NOT EXISTS orders_by_amount AS
  SELECT customer_id, order_id, amount
  FROM orders
  WHERE customer_id IS NOT NULL AND order_id IS NOT NULL
  PRIMARY KEY (customer_id, amount, order_id)
  WITH CLUSTERING ORDER BY (amount DESC);
```

**Querying the View**  
```cql
SELECT * FROM orders_by_amount
WHERE customer_id = 123e4567-e89b-12d3-a456-426614174000
LIMIT 10;
```

### PostgreSQL Example

```sql
-- Base table
CREATE TABLE IF NOT EXISTS orders (
  order_id    SERIAL PRIMARY KEY,
  customer_id INT,
  amount      NUMERIC
);

-- Materialized View summarizing total spent
CREATE MATERIALIZED VIEW IF NOT EXISTS customer_order_summary AS
SELECT customer_id,
       COUNT(*)     AS total_orders,
       SUM(amount)  AS total_spent
FROM orders
GROUP BY customer_id;

-- Refresh the view concurrently
REFRESH MATERIALIZED VIEW CONCURRENTLY customer_order_summary;
```

**Querying the View**  
```sql
SELECT * FROM customer_order_summary
WHERE total_spent > 10000;
```

---

## 3. Alpakka Connectors

**What is Alpakka?**  
Alpakka is a Reactive Streams-based connectors library for Akka Streams. It provides out-of-the-box integration ("connectors") for a variety of systems (Kafka, Cassandra, JDBC, S3, MQTT, etc.).

**Core Features**  
- Backpressure-aware: integrates with Akka Streams  
- Pluggable semantics: at-least-once or exactly-once delivery  
- Composable: connectors can be combined via the Streams DSL

**Alternatives**  
- Spring Cloud Stream  
- Kafka Streams  
- fs2-kafka (Scala)  

### Alpakka Kafka Example

```scala
import akka.kafka.scaladsl.{Consumer, Producer}
import akka.kafka.{ConsumerSettings, ProducerSettings, Subscriptions}
import org.apache.kafka.clients.producer.ProducerRecord
import io.circe.syntax._

val consumerSettings = ConsumerSettings(system, new StringDeserializer, new StringDeserializer)
  .withBootstrapServers("kafka:9092")
  .withGroupId("order-service")

// Consume and process
Consumer
  .plainSource(consumerSettings, Subscriptions.topics("orders"))
  .map { msg =>
    // parse, process...
    msg
  }
  .mapAsync(commit = true)(_.committableOffset.commitScaladsl())
  .runWith(Sink.ignore)

// Produce
val producerSettings = ProducerSettings(system, new StringSerializer, new StringSerializer)
  .withBootstrapServers("kafka:9092")

Source(List(order))
  .map(o => new ProducerRecord[String, String]("orders", o.id.toString, o.asJson.noSpaces))
  .runWith(Producer.plainSink(producerSettings))
```

### Alpakka Cassandra Example

```scala
import akka.stream.alpakka.cassandra.scaladsl.CassandraSessionRegistry

val session = CassandraSessionRegistry.get(system).sessionFor("alpakka.cassandra")

// Write
Source(events)
  .mapAsync(1)(e =>
    session.executeWrite(
      "INSERT INTO events_by_tag(tag, offset, data) VALUES (?, ?, ?)",
      e.tag, e.offset, e.data
    )
  )
  .runWith(Sink.ignore)

// Read
session
  .select("SELECT * FROM events_by_tag WHERE tag = 'order-events'")
  .runWith(Sink.foreach(row => println(row.getString("data"))))
```

---

## 4. Projection + HTTP Endpoint Example

This example shows a full flow: project events, update a Cassandra read table, and serve it via Akka HTTP + Circe.

```scala
import akka.actor.typed.ActorSystem
import akka.actor.typed.scaladsl.Behaviors
import akka.persistence.query.{EventEnvelope, Offset, PersistenceQuery}
import akka.persistence.cassandra.query.scaladsl.CassandraReadJournal
import akka.stream.scaladsl.{Keep, Sink}
import akka.stream.alpakka.cassandra.scaladsl.CassandraSessionRegistry
import akka.http.scaladsl.Http
import akka.http.scaladsl.server.Directives._
import akka.http.scaladsl.model._
import io.circe.generic.auto._
import io.circe.syntax._
import scala.jdk.CollectionConverters._

object ReadSideApp {
  // Domain event
  sealed trait ApplicationEvent { def applicationId: String }
  case class ApplicationReceived(applicationId: String, timestamp: Long) extends ApplicationEvent
  case class ConditionUpdated(applicationId: String, conditions: List[String]) extends ApplicationEvent

  // Read model
  case class ApplicationView(applicationId: String, receivedAt: Long, conditions: List[String])

  def main(args: Array[String]): Unit = {
    implicit val system = ActorSystem(Behaviors.empty, "read-side")
    implicit val ec     = system.executionContext

    // Cassandra session & DDL
    val session = CassandraSessionRegistry.get(system).sessionFor("alpakka.cassandra")
    session.executeDDL(
      """CREATE KEYSPACE IF NOT EXISTS underwriting
         WITH replication = {'class':'SimpleStrategy','replication_factor':'1'};
         CREATE TABLE IF NOT EXISTS underwriting.application_view (
           application_id text PRIMARY KEY, received_at bigint, conditions list<text>);
      """
    )

    // Projection: stream events and upsert view
    val readJournal = PersistenceQuery(system.toClassic)
      .readJournalFor[CassandraReadJournal](CassandraReadJournal.Identifier)
    readJournal.eventsByTag("application-events", Offset.noOffset)
      .mapAsync(1) {
        case EventEnvelope(_, _, _, ev: ApplicationEvent) =>
          val view = ev match {
            case ApplicationReceived(id, ts) => ApplicationView(id, ts, Nil)
            case ConditionUpdated(id, cs)    => ApplicationView(id, 0L, cs)
          }
          session.executeWrite(
            "INSERT INTO underwriting.application_view(application_id, received_at, conditions) VALUES (?, ?, ?)",
            view.applicationId, view.receivedAt: java.lang.Long, view.conditions.asJava
          )
        case _ => Future.unit
      }
      .toMat(Sink.ignore)(Keep.right).run()

    // HTTP route: read view and return JSON
    val route = path("applications" / Segment) { appId =>
      get {
        val fView = session.selectOne(
          "SELECT application_id, received_at, conditions FROM underwriting.application_view WHERE application_id = ?",
          appId
        ).map(_.map(row => ApplicationView(
          row.getString("application_id"), row.getLong("received_at"),
          row.getList("conditions", classOf[String]).asScala.toList
        )))
        onSuccess(fView) {
          case Some(view) => complete(HttpEntity(ContentTypes.`application/json`, view.asJson.noSpaces))
          case None       => complete(StatusCodes.NotFound, s"Application $appId not found")
        }
      }
    }

    Http().newServerAt("0.0.0.0", 8080).bind(route)
  }
}
```

---

*End of Guide.*
