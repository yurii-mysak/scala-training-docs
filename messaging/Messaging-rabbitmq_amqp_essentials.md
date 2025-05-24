# RabbitMQ AMQP Essentials

RabbitMQ is an open-source message broker implementing the AMQP 0-9-1 protocol. It decouples producers and consumers through exchanges, queues, and bindings.

---

## 1. Exchange Types

AMQP defines four built-in exchange types:

- **direct**: routes messages with a routing key exactly matching the binding key.
- **fanout**: broadcasts all messages to every queue bound, ignoring routing keys.
- **topic**: routes using pattern matching on routing keys; `*` matches one word, `#` matches zero or more.
- **headers**: routes based on matching message header attributes instead of routing key values.

![AMQP Exchange Types](https://raw.githubusercontent.com/ymysak/static-assets/main/images/rabbitmq-exchanges.png)

---

## 2. Queues and Bindings

- **Queue**: durable buffer storing messages until acknowledged.
- **Binding**: rule that tells an exchange to route messages to a queue based on a key or headers.

```scala
// Declare a durable queue and bind to a direct exchange
channel.queueDeclare("task_queue", true, false, false, null)
channel.queueBind("task_queue", "task_exchange", "task_key")
```

---

## 3. Routing & Message Flow

1. Producer publishes to an **exchange**.
2. Exchange evaluates all **bindings**.
3. Routes message to appropriate **queues**.
4. Consumers fetch from queues in FIFO order.

---

## 4. Point-to-Point & Publish-Subscribe Models

- **Point-to-Point**: direct exchange + single consumer queue  
  Tutorial: https://www.rabbitmq.com/tutorials/tutorial-one.html
- **Publish/Subscribe**: fanout exchange + multiple queues bound  
  Tutorial: https://www.rabbitmq.com/tutorials/tutorial-two.html
- **Fair Dispatch**: prefetch count + manual ack for load balancing  
  Tutorial: https://www.rabbitmq.com/tutorials/tutorial-three.html

---

## 5. Message Acknowledgements

- **basic.ack**: acknowledge successful processing.
- **basic.nack** / **basic.reject**: reject and optionally requeue or dead-letter.

```scala
val delivery =  // from consumer callback
channel.basicAck(delivery.getEnvelope.getDeliveryTag, false)
```

---

## 6. Publisher Confirms

Enable confirms on a channel:

```scala
channel.confirmSelect()
// Individual confirm
channel.basicPublish(...); channel.waitForConfirms()
// Batch confirm
channel.basicPublish(...); channel.waitForConfirmsOrDie()
// Async confirm
channel.addConfirmListener { (seqNo, multiple) => /* callback */ }
```

- **Individual**: confirm per message.
- **Batch**: group confirmations for efficiency.
- **Asynchronous**: non-blocking listeners for high throughput.

---

## 7. Persistence & Durability

- Mark **exchanges** and **queues** as durable.
- Set messages persistent: `props.builder().deliveryMode(2).build()`.
- Ensures survival across broker restarts.

---

## 8. Selective Consumption

Bind queues with specific routing keys or patterns:

```scala
channel.queueDeclare("errors", true, false, false, null)
channel.queueBind("errors", "logs", "error.*")
```

---

## 9. Further Reading

- RabbitMQ AMQP Concepts – Exchanges, Queues, Bindings, Acks  
- Tutorials:  
  - Point-to-Point: https://www.rabbitmq.com/tutorials/tutorial-one.html  
  - Publish/Subscribe: https://www.rabbitmq.com/tutorials/tutorial-two.html  
  - Fair Dispatch: https://www.rabbitmq.com/tutorials/tutorial-three.html
