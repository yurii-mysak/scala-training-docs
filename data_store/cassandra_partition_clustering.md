# Cassandra Partition vs Clustering Keys

## Partition Key
- The **partition key** is the first element (or set of elements) of the `PRIMARY KEY` in a Cassandra table. It determines **which node** in the cluster stores a given row by hashing the key to a token range.
- Physically, all rows sharing the same partition key are stored together in the same “partition,” the unit of distribution and replication.
- **Design reasoning:**
  - Choose a partition key with **high cardinality** to spread load evenly and avoid “hot” partitions.
  - Ensure your most common query patterns include the full partition key, because you **cannot** query by clustering columns alone.

## Clustering Key
- The **clustering key** consists of one or more columns listed *after* the partition key in the `PRIMARY KEY` definition. These columns **sort** the rows within each partition.
- Cassandra physically orders data on disk according to the clustering columns, supporting efficient range scans and ordered retrieval (e.g., time series data).
- **Design reasoning:**
  - Use clustering keys to model **query-specific ordering** (e.g., `ORDER BY timestamp DESC`).
  - Keep the number of clustering columns modest; excessive clustering can bloat partition size and complicate reads.

## Composite (Compound) Keys
A **composite primary key** combines partition and clustering components:

```sql
PRIMARY KEY ((a, b), c, d)
```

- **Composite partition key** `(a, b)`: data is sharded by the hash of both `a` and `b`.
- **Composite clustering key** `(c, d)`: rows within each `(a,b)` partition are ordered first by `c`, then by `d`.

## Examples

```sql
-- Simple primary key: only partition key
CREATE TABLE example1 (
  user_id   UUID,
  data      text,
  PRIMARY KEY (user_id)
);

-- Single clustering key
CREATE TABLE example2 (
  user_id     UUID,
  event_time  timestamp,
  info        text,
  PRIMARY KEY (user_id, event_time)
);

-- Composite partition + clustering
CREATE TABLE example3 (
  region      text,
  device_id   text,
  metric_time timestamp,
  value       double,
  PRIMARY KEY ((region, device_id), metric_time)
);
```

- In **example2**, `user_id` is the partition key (distribution), and `event_time` is the clustering key (sorted order).
- In **example3**, each `(region,device_id)` pair maps to one partition; events are retrieved in time order within that partition.

## Reasoning & Best Practices
1. **Query-Driven Modeling:** Start by enumerating your queries. Ensure every query’s `WHERE` clause includes the full partition key, and any ordering or range scans use clustering columns.
2. **Partition Size:** Keep partitions under a few hundred megabytes. Very wide partitions can lead to read timeouts and compaction pressure.
3. **Avoid Hotspots:** Don’t use a monotonically increasing key (e.g., timestamp) *alone* as the partition key—this will overload a single node.
4. **Clustering Order:** Define clustering columns in the order that matches your most frequent range queries. Cassandra only supports ordering in the order declared by the schema.
5. **Composite Keys for Flexibility:** Use composite partition keys when you need to shard by multiple dimensions (e.g., tenant + device), but remember this constrains queries to always include *all* partition components.

By understanding that **partition keys** control *distribution* and **clustering keys** control *ordering*, you can design Cassandra tables that scale horizontally while serving your application’s access patterns efficiently.
