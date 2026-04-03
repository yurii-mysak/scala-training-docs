# Point-to-Point & Publish-Subscribe Deep Dive

Messaging systems commonly support two primary communication models: **Point-to-Point** and **Publish-Subscribe**.

---

## 1. Point-to-Point Model

- **Definition**: One producer sends messages to a queue; a single consumer receives each message.
- **Guarantee**: Each message processed exactly once (depending on ack mode).
- **Use Cases**: Task distribution, load balancing, work queues.

### RabbitMQ Example

- **Setup**:
  ```scala
  // Declare queue
  channel.queueDeclare("task_queue", true, false, false, null)
  // Publish
  channel.basicPublish("", "task_queue", MessageProperties.PERSISTENT_TEXT_PLAIN, body)
  ```
- **Consumer**:
  ```scala
  channel.basicQos(1)  // fair dispatch
  channel.basicConsume("task_queue", false, (consumerTag, delivery) => {
    // process...
    channel.basicAck(delivery.getEnvelope.getDeliveryTag, false)
  }, _ => {})
  ```
- **Tutorial**: https://www.rabbitmq.com/tutorials/tutorial-one.html

### Kafka Example

- **Single Consumer Group**:
  ```scala
  consumer.subscribe(List("task_topic"))
  while(true){
    val records = consumer.poll(Duration.ofMillis(100))
    records.asScala.foreach { record =>
      // process and commit
      consumer.commitSync()
    }
  }
  ```
- **Concept**: Each partition assigned to only one consumer in the group.

---

## 2. Publish–Subscribe Model

- **Definition**: Producer sends messages to a topic/exchange; multiple subscribers receive copies.
- **Use Cases**: Event broadcasting, notifications, multicasting.

### RabbitMQ Example

- **Fanout Exchange**:
  ```scala
  channel.exchangeDeclare("logs", BuiltinExchangeType.FANOUT)
  // Bind multiple queues
  channel.queueDeclare("logs_queue1", true, false, false, null)
  channel.queueBind("logs_queue1", "logs", "")
  // Consume as usual...
  ```
- **Tutorial**: https://www.rabbitmq.com/tutorials/tutorial-two.html

### Kafka Example

- **Multiple Consumer Groups**:
  ```scala
  // Group "analytics"
  val consumer1 = createConsumer("analytics")
  // Group "alerts"
  val consumer2 = createConsumer("alerts")
  ```
- **Concept**: Each consumer group gets all messages independently.

---

## 3. Acknowledgment Concept

- **Purpose**: Ensure messages are only removed once processed.
- **Modes**:
  - **Manual**: Consumer explicitly acks/nacks.
  - **Automatic**: Broker marks delivered on send or poll.
- **RabbitMQ**: `basic.ack`, `basic.nack`, `basic.reject`.
- **Kafka**: `enable.auto.commit`, `consumer.commitSync()`, `consumer.commitAsync()`.

---

## 4. Cloud Broker Variations

| Broker      | Point-to-Point            | Publish-Subscribe        |
|-------------|---------------------------|--------------------------|
| AWS SQS     | Standard & FIFO queues    | n/a                      |
| AWS SNS     | n/a                       | Topics → SQS, HTTP, SMS  |
| GCP Pub/Sub | Pull & Push subscriptions | Pub/Sub                  |
| Azure SB    | Queues                    | Topics & Subscriptions   |

---

## 5. When to Use Which

- **Point-to-Point**: Distributed tasks, jobs, exactly-once work items.
- **Publish–Subscribe**: Broadcasting events, real-time notifications, fan-out workloads.

---

## 6. Further Reading

- RabbitMQ Tutorials: Point-to-Point & Pub/Sub  
- _Kafka: The Definitive Guide_, Ch. 3–4  
