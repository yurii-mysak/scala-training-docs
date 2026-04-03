# DynamoDB Refresher: Interview Prep Guide

## Introduction
Amazon DynamoDB is a fully managed NoSQL database service provided by AWS. Unlike traditional relational databases (RDBMS), which use tables, rows, and columns, DynamoDB is designed as a key-value and document database. This means:

- **Key-Value**: Each item is stored and accessed by a unique key.
- **Document**: Items can contain nested attributes (similar to JSON objects).

This design allows DynamoDB to scale horizontally, offering single-digit millisecond latency at any scale. It is ideal for:
- **Gaming**: Tracking player state and leaderboards.
- **Internet of Things (IoT)**: Collecting time-series sensor data.
- **E-commerce**: Handling shopping carts, orders, and user profiles.

---

## Table Fundamentals

A DynamoDB table consists of:

- **Items**: Equivalent to rows in an RDBMS.
- **Attributes**: Equivalent to columns, but items in the same table can have different sets of attributes.

### Primary Key Types
1. **Partition Key (PK) Only**  
   - A simple primary key.
   - DynamoDB uses the PK to determine the partition (storage internal shard) where an item is stored.
2. **Composite Primary Key**  
   - Combines a **Partition Key** and a **Sort Key (SK)**.
   - SK allows multiple items to share the same PK but be distinguished by the SK, enabling richer query patterns such as time-ordered data.

#### Example Table Definition
```json
{
  "TableName": "Orders",
  "AttributeDefinitions": [
    { "AttributeName": "UserId", "AttributeType": "S" },
    { "AttributeName": "OrderDate", "AttributeType": "S" }
  ],
  "KeySchema": [
    { "AttributeName": "UserId", "KeyType": "HASH" },
    { "AttributeName": "OrderDate", "KeyType": "RANGE" }
  ],
  "BillingMode": "PAY_PER_REQUEST"
}
```
- **AttributeType**: "S" for string, "N" for number, "B" for binary.
- **BillingMode**: PAY_PER_REQUEST (on-demand) or PROVISIONED (manual capacity).

---

## Secondary Indexes

Indexes let you query data in ways other than the primary key. There are two types:

1. **Local Secondary Index (LSI)**  
   - Shares the same Partition Key as the base table.
   - Defines a different Sort Key.
   - Created only at the time of table creation.
   - **Use case**: Query the same item group with different sort orders.

2. **Global Secondary Index (GSI)**  
   - Can have a different Partition Key and Sort Key from the base table.
   - Created at any time.
   - Supports eventual consistency only.
   - **Use case**: Query data by non-primary attributes (e.g., find orders by status).

#### Example GSI Creation
```json
{
  "UpdateTable": {
    "TableName": "Orders",
    "AttributeDefinitions": [
      { "AttributeName": "Status", "AttributeType": "S" }
    ],
    "GlobalSecondaryIndexUpdates": [
      {
        "Create": {
          "IndexName": "StatusIndex",
          "KeySchema": [
            { "AttributeName": "Status", "KeyType": "HASH" },
            { "AttributeName": "OrderDate", "KeyType": "RANGE" }
          ],
          "Projection": {
            "ProjectionType": "ALL"
          },
          "ProvisionedThroughput": {
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5
          }
        }
      }
    ]
  }
}
```

---

## Data Modeling Patterns

### Single-Table Design
Instead of multiple tables, store all entities in one table, differentiating them by attribute patterns:
- **Partition Key**: Prefix with entity type (e.g., `USER#123`, `ORDER#123`).
- **Sort Key**: Encodes relationships and ordering (e.g., `PROFILE#`, `ORDER#date`).

**Benefits**:
- Efficient single-query retrievals.
- Fewer cross-table joins (DynamoDB does not support joins).

#### Single-Table Example
| PK            | SK                    | EntityType | Additional Attributes             |
|---------------|-----------------------|------------|-----------------------------------|
| `USER#123`    | `PROFILE#123`         | User       | name, email                       |
| `USER#123`    | `ORDER#2025-06-11#001`| Order      | totalAmount, status               |
| `PRODUCT#X7A` | `DETAILS`             | Product    | name, category, price             |

---

## Capacity Modes

1. **On-Demand (Pay-Per-Request)**
   - Automatically scales up/down.
   - Billed per read/write request.
   - Ideal for unpredictable or spiky workloads.

2. **Provisioned**
   - Specify Read Capacity Units (RCU) and Write Capacity Units (WCU).
   - Use Auto Scaling to adjust based on traffic patterns.
   - More cost-effective for steady high throughput.

- **RCU**: One strongly consistent read per second of up to 4 KB.
- **WCU**: One write per second of up to 1 KB.

---

## Consistency Models

- **Eventually Consistent Read** (default)
  - Data may not reflect the results of a recently completed write.
  -  - Consistency across all copies usually within a second.
- **Strongly Consistent Read**
  - Returns the most up-to-date data, reflecting all prior writes.
  - Consumes twice the RCU of eventually consistent reads.

**Example**:
- Use strong consistency for user account balances to ensure correctness.
- Use eventual consistency for analytics dashboards where slight delay is acceptable.

---

## Transactions

DynamoDB supports ACID transactions across multiple items and tables:
- **TransactGetItems**: Retrieve multiple items atomically.
- **TransactWriteItems**: Write multiple items atomically.

**Use Cases**:
- Transferring funds between user accounts.
- Ensuring order placement and inventory deduction happen together.

---

## DynamoDB Streams

Streams capture a time-ordered sequence of item-level changes:
- **Stream Records**: Insert, modify, or remove events.
- **Retention**: 24 hours.
- **Integration**: Process stream events with AWS Lambda, Kinesis Data Streams, or custom consumers.

**Example**: Update an Elasticsearch index whenever data changes.

---

## Security

- **IAM Policies**: Grant least-privilege access to specific tables and actions.
- **Encryption at Rest**:
  - AWS-managed key (default).
  - Customer-managed key (CMK) via AWS KMS.
- **TLS in Transit**: All communication is encrypted with HTTPS.
- **VPC Endpoints**: Access DynamoDB through private network paths.

---

## Best Practices

1. **Distribute Workload**  
   - Avoid “hot” keys by adding random suffixes or using hierarchical keys.
2. **Efficient Queries**  
   - Use Query operations over Scan for better performance.
3. **Sparse Indexes**  
   - Only index items that need the GSI to reduce storage.
4. **Time To Live (TTL)**  
   - Automatically delete expired items to save space.
5. **Error Handling & Retries**  
   - Implement exponential backoff on throttling errors (HTTP 400/ProvisionedThroughputExceededException).
6. **Monitoring**  
   - Use CloudWatch alarms for throttled requests and high latency.
7. **Backup & Restore**  
   - Enable point-in-time recovery (PITR) for protection against accidental deletes.

---

## Example Queries

### Query by Partition and Sort Key
Fetch orders for user `123` between Jan–Dec 2025:
```python
from boto3.dynamodb.conditions import Key
response = table.query(
    KeyConditionExpression=Key('UserId').eq('123') & Key('OrderDate').between('2025-01-01','2025-12-31'),
    ConsistentRead=False
)
```

### Scan with Filter
Find all orders above $100:
```python
response = table.scan(
    FilterExpression=Key('totalAmount').gt(100)
)
```

---

## Diagrams

### Composite Key & Single-Table Design
```mermaid
erDiagram
    USER_TABLE ||--o{ ITEM : contains
    ITEM {
        string PK "Partition Key"
        string SK "Sort Key"
        map Attributes
    }
```

### Data Partitioning Across Storage Nodes
```
+-----------+     +-----------+     +-----------+
|  Node A   |     |  Node B   |     |  Node C   |
| (Hash 0-9)|     |(Hash 10-19)|    |(Hash 20-29)|
+-----------+     +-----------+     +-----------+
     |                |                 |
   Items            Items             Items
```
