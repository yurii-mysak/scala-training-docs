
# Event Sourcing & CQRS, Sagas, and Distributed Transactions Guide

This guide provides clear, non-expert-friendly explanations, concrete examples, and best practices for key patterns in modern distributed systems.

---

## 1. Event Sourcing & CQRS (Command Query Responsibility Segregation)

### 1.1 What is Event Sourcing?

- **Simple Explanation**: Rather than storing only the current state (e.g., "Account balance is $100"), you store every change that led to that state (e.g., "Deposited $50", "Withdrew $20").  
- **Why It Matters**: You get a complete audit log, can rebuild state at any point in time, and easily reason about "what happened when".

#### Everyday Analogy
Imagine tracking a person’s weight by logging every meal and workout, instead of just writing down the final weight. You know exactly what caused each change.

### 1.2 What is CQRS?

- **Simple Explanation**: Split your system’s operations into two parts:
  - **Commands**: Actions that change data (writes), like "CreateOrder" or "UpdateProfile".  
  - **Queries**: Actions that read data, like "GetOrderDetails".
- **Why It Matters**: You can optimize reads and writes separately—scaling, database technology, and even data models can differ.

#### Example Flow
1. **User** sends a **CreateOrder** command.  
2. **Command Model** validates and records an **OrderCreated** event.  
3. **Event Handlers** update one or more **Read Databases** optimized for reporting.

### 1.3 Basic Scala Example

```scala
// Command
case class CreateOrder(id: UUID, items: List[String]) extends Command

// Event
case class OrderCreated(id: UUID, items: List[String], timestamp: Instant) extends Event

// Aggregate handling writes
class OrderAggregate extends PersistentActor {
  override def receiveCommand: Receive = {
    case cmd: CreateOrder =>
      // Validate
      if (cmd.items.nonEmpty)
        persist(OrderCreated(cmd.id, cmd.items, Instant.now)) { evt =>
          // Inform success
          sender() ! Right("Order created")
        }
      else
        sender() ! Left("No items in order")
  }

  override def receiveRecover: Receive = {
    case evt: OrderCreated => // rebuild state if needed
  }
}
```

**Key Best Practices**  
- Use **append-only** logs for events.  
- Regularly create **snapshots** to speed up recovery.  
- Ensure **events are immutable** and versioned.

---

## 2. Microservice Patterns

### 2.1 API Gateway

- **Purpose**: Single endpoint for all client requests.  
- **Benefits**: Centralized security (authentication, rate limiting), request routing, and aggregation of multiple services.

### 2.2 Service Discovery

- **Purpose**: Let services find and communicate without hard-coded addresses.  
- **Examples**: Consul, Netflix Eureka, Kubernetes DNS.

### 2.3 Resilience Patterns

- **Circuit Breaker**  
  - **What**: Temporarily stop calls to a failing service to prevent cascading failures.  
  - **Tools**: Resilience4j, Hystrix.
- **Bulkhead**  
  - **What**: Isolate resources so one service failure doesn’t exhaust shared resources.
- **Retry with Backoff**  
  - **What**: Retry failed calls, but wait longer each time (e.g., 100ms, 200ms, 400ms).

---

## 3. Distributed Transactions

### 3.1 Two-Phase Commit (2PC)

1. **Prepare Phase**  
   - Coordinator asks all participants, “Can you commit?”  
   - Each participant votes “Yes” or “No”.
2. **Commit/Rollback Phase**  
   - If **all** say Yes → Coordinator tells everyone to **commit**.  
   - If **any** say No → Coordinator tells everyone to **rollback**.

**Drawbacks**  
- Global locks held until commit → **Blocking**.  
- Single coordinator can become a **bottleneck** or single point of failure.

### 3.2 Saga Pattern

- A sequence of smaller local transactions with **compensating actions** instead of global locks.

#### 3.2.1 Orchestration vs. Choreography

| Category        | Orchestration                                           | Choreography                                            |
|-----------------|---------------------------------------------------------|---------------------------------------------------------|
| Control Flow    | Central **Saga Orchestrator** sends commands            | Services react to events emitted by previous steps      |
| Visibility      | Clear, centralized view of saga progress                | Distributed; each service only knows its own part       |

#### 3.2.2 Real-World Example: Order Processing

1. **Start Saga**: User places an order → Saga Orchestrator.  
2. **Create Order**: Orders service reserves items → emits `OrderCreated`.  
3. **Reserve Payment**: Payments service attempts payment → emits `PaymentReserved` or `PaymentFailed`.  
   - If failed → orchestrator issues `CancelOrder` (compensate).  
4. **Ship Items**: Inventory service ships items → emits `ItemsShipped`.  
5. **Complete Saga**: Orchestrator marks saga complete.

```text
[Client]
   |
   v
[Saga Orchestrator]
   |
   +--> [Orders Service] --(OrderCreated)--> 
   |                                       |
   +--> [Payments Service] --(PaymentReserved)--> 
   |                                       |
   +--> [Inventory Service] --(ItemsShipped)--> 
   |
Success!
```

**Compensations**:  
- For `PaymentFailed`, call `CancelOrder`.  
- For `ShippingFailed`, call `RefundPayment`.

**Sagas Best Practices**  
- Define clear **compensating actions**.  
- Implement **timeouts** and **dead-letter** handling for stuck sagas.  
- Keep steps **idempotent** for safe retries.

---

## 4. Saga vs. 2PC Comparison

| Aspect            | Saga                                   | 2PC                                     |
|-------------------|----------------------------------------|-----------------------------------------|
| Locks             | No global locks; uses compensations    | Global locks until final commit         |
| Failure Handling  | Local compensations on failure         | Rollback all or block until recovery    |
| Scalability       | High (distributed participants)        | Limited by coordinator bottleneck       |
| Complexity        | Must design compensations              | Protocol complexity, but transactional  |

---

## 5. Visual Diagrams

### 5.1 Event Sourcing & CQRS Flow

```
[Commands] --> [Write Model] --> [Event Store] --> [Projections] --> [Read Model]
```

### 5.2 Saga Orchestration

```
 Client
   |
   v
Orchestrator --> Service A --> Service B --> Service C
   ^             |             |             |
   |             v             v             v
Compensation <-- Compensation <-- Compensation
```

---

## 6. Additional Tips

- **Logging & Monitoring**: Use centralized tracing (e.g., Zipkin, Jaeger) to follow saga across services.  
- **Data Consistency**: Understand that eventual consistency is common; inform users when data may be slightly stale.  
- **Choosing Patterns**: Use **2PC** only when strong consistency is mandated and the cost of blocking is acceptable. Use **Sagas** for long-lived, business-level workflows.

---

*This expanded guide provides approachable explanations, step-by-step examples, and practical advice for interview preparation around Event Sourcing, CQRS, microservice resilience, and distributed transaction patterns.*
