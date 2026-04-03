# Cloud Messaging Services Overview

Cloud messaging platforms offer managed, scalable, and durable messaging without maintaining your own brokers.  

---

## 1. AWS Messaging

- **Amazon SQS (Simple Queue Service)**  
  - **Type**: Point-to-Point queue  
  - **Use case**: Decoupling microservices, batch processing  
  - **Delivery**: At-least-once, FIFO queues available  
  - **Analogy**: Bank teller line where customers wait in order  
  - **Example**:  
    ```scala
    import aws.sdk.kotlin.services.sqs.SqsClient
    import aws.sdk.kotlin.services.sqs.model.SendMessageRequest

    val client = SqsClient{ region = "us-east-1" }
    client.sendMessage(SendMessageRequest{
      queueUrl = "https://sqs.us-east-1.amazonaws.com/123456789012/my-queue"
      messageBody = "Hello from Scala!"
    })
    ```  

- **Amazon SNS (Simple Notification Service)**  
  - **Type**: Publish–Subscribe  
  - **Use case**: Fan-out notifications via email, SMS, HTTP endpoints  
  - **Delivery**: Push-based, retries on failure  
  - **Analogy**: Radio station broadcast  
  - **Integration**: Can trigger SQS, Lambda, HTTP, SMS  

- **Amazon MQ**  
  - **Type**: Managed ActiveMQ/RabbitMQ  
  - **Use case**: Lift-and-shift existing AMQP or JMS workloads  
  - **Feature**: Supports AMQP, MQTT, STOMP protocols  

- **Amazon Kinesis Data Streams**  
  - **Type**: Partitioned streaming log  
  - **Use case**: Real-time analytics, event sourcing  
  - **Delivery**: Retention up to days, ordered per shard  
  - **Analogy**: Kafka-like commit log  

---

## 2. Azure Messaging

- **Azure Service Bus**  
  - **Type**: Queue and Topic (Pub-Sub)  
  - **Features**: Sessions, transactions, dead-lettering  
  - **Use case**: Enterprise messaging, workflows  
  - **Delivery**: At-least-once, duplicate detection  

- **Azure Event Hubs**  
  - **Type**: Big data streaming platform  
  - **Use case**: Telemetry ingestion, log streaming  
  - **Analogous to**: Kafka, Kinesis  

- **Azure Event Grid**  
  - **Type**: Managed event routing service  
  - **Use case**: Reactive serverless architectures  
  - **Delivery**: Push events with retry semantics  

---

## 3. GCP Messaging

- **Google Cloud Pub/Sub**  
  - **Type**: Global Pub-Sub messaging  
  - **Features**: Auto-scaling, exactly-once (beta), push/pull models  
  - **Use case**: Event-driven systems, streaming ETL  
  - **Analogy**: Distributed radio broadcast across regions  

- **Google Cloud Pub/Sub Lite**  
  - **Type**: Low-cost, zonal streaming  
  - **Use case**: High-volume, localized workloads  

---

## 4. Common Patterns & Guarantees

| Service       | Model         | Delivery Guarantee | Scalability         |
|---------------|---------------|--------------------|---------------------|
| SQS           | Queue         | At-least-once      | Unlimited queues    |
| SNS / PubSub  | Pub-Sub       | At-least-once      | Massive fan-out     |
| Service Bus   | Queue/Topic   | At-least-once      | Partitioned topics  |
| Event Hubs    | Log           | At-least-once      | Throughput units    |
| Kinesis       | Log           | At-least-once      | Shard-based         |

---

## 5. When to Choose

- **Decoupling with simple queues**: SQS, Service Bus queues  
- **Broadcast to many subscribers**: SNS, Pub/Sub, Event Grid  
- **Stream processing**: Kinesis, Event Hubs, Pub/Sub, Kafka on AWS (MSK)  
- **Legacy lift-and-shift**: Amazon MQ  

---

## 6. Further Reading

- AWS Messaging Overview: https://aws.amazon.com/messaging/  
- Azure Messaging Services: https://azure.microsoft.com/en-us/overview/messaging/  
- GCP Pub/Sub Documentation: https://cloud.google.com/pubsub/docs  
