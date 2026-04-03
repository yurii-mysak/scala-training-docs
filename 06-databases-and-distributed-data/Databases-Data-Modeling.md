# Databases & Data Modeling Interview Preparation (Expanded)

## 1. Cassandra Partitioning vs. Clustering Keys

### Overview
Cassandra is a distributed NoSQL database designed for high availability and scalability. Data is distributed across multiple nodes in a cluster to handle large volumes of reads and writes.

### Partition Key
- **Definition**: Part of the primary key that determines which node stores the data.
- **Role**:  
  - Distributes data evenly across the cluster.  
  - Routes client requests to the correct node.
- **Characteristics**:  
  - High-cardinality values (many unique values) are ideal to avoid “hot” partitions.  
  - Example: In a `users_by_country` table:
  ```cql
  CREATE TABLE users_by_country (
    country_code text,
    user_id uuid,
    name text,
    PRIMARY KEY (country_code, user_id)
  );
  ```
  Here, `country_code` is the partition key, so all users from the same country are stored together.

### Clustering Keys
- **Definition**: The remaining part of the primary key that determines ordering within a partition.
- **Role**:  
  - Sorts rows inside a partition.  
  - Enables efficient range queries.
- **Characteristics**:  
  - Order is ascending by default, but can be customized.  
  - Example: In an `events_by_user` table:
  ```cql
  CREATE TABLE events_by_user (
    user_id uuid,
    event_time timestamp,
    event_type text,
    details text,
    PRIMARY KEY (user_id, event_time)
  ) WITH CLUSTERING ORDER BY (event_time DESC);
  ```
  Here, `user_id` is the partition key, `event_time` is the clustering key sorted in descending order, so you retrieve the latest events first.

### Best Practices
- **Partition Key Selection**:  
  - Choose a key that evenly distributes load.  
  - Avoid using timestamps or monotonically increasing IDs alone.
- **Composite Keys**: Combine multiple columns for better distribution, e.g., `(country_code, user_id)`.
- **Clustering Depth**: Limit number of clustering columns to keep partitions manageable.
- **Avoid Tombstone Overload**: Design schema to prevent large numbers of deleted rows within a partition.

---

## 2. B-Tree vs. LSM Tree (for NoSQL)

### Data Structures
| Feature         | B-Tree                                         | LSM Tree                                               |
|-----------------|-------------------------------------------------|--------------------------------------------------------|
| **Structure**   | Balanced tree with nodes and pages             | Log-structured merge tree with in-memory and disk layers |
| **Write Path**  | Update in place, splitting pages when full     | Append-only write to commit log and memtable, then flushed to SSTables |
| **Read Path**   | Traversal down tree nodes to find key          | Read from in-memory memtable and multiple SSTables, may require merging |
| **Use Cases**   | OLTP, point lookups, range scans               | High write throughput, time-series data, write-heavy workloads |
| **Examples**    | MySQL InnoDB, PostgreSQL, SQLite                | Cassandra, RocksDB, LevelDB                             |

### How LSM Tree Works
1. **Write-Ahead Log (WAL)**: Ensures durability by logging writes.  
2. **Memtable**: An in-memory sorted structure (e.g., a TreeMap).  
3. **SSTables**: Immutable sorted files on disk.  
4. **Compaction**: Periodically merges SSTables to reduce files and reclaim space.

#### LSM Tree Flow (ASCII)
```
Client Write -> WAL -> Memtable
When Memtable is full -> Flush Memtable -> SSTable0
Later writes -> SSTable1, SSTable2...
Compaction merges SSTable0+1 -> SSTableMerged
```

### Pros & Cons
- **B-Tree**  
  - Pros: Fast reads, consistent lookup times.  
  - Cons: Slower writes under high concurrency; page splits can cause I/O spikes.
- **LSM Tree**  
  - Pros: High write throughput, sequential disk I/O.  
  - Cons: Read amplification, compaction I/O overhead.

### Best Practices
- **LSM Compaction Tuning**:  
  - **Size-Tiered**: Better for write-heavy with less read pressure.  
  - **Leveled**: Balances read/write by organizing SSTables into levels.
- **Bloom Filters**: Use to skip SSTables that do not contain a key.
- **Tunable Consistency**: In Cassandra, set QUORUM or LOCAL_QUORUM for consistency/performance trade-offs.

---

## 3. Doobie as a Functional JDBC Wrapper in Scala

### What is Doobie?
- A pure functional library for interacting with relational databases in Scala.  
- Wraps JDBC in a type-safe, composable API using Cats Effect.

### Key Concepts
1. **Transactor**  
   - Responsible for acquiring and releasing connections.  
   ```scala
   import doobie._
   import doobie.implicits._
   import cats.effect.IO

   val xa = Transactor.fromDriverManager[IO](
     "org.postgresql.Driver",
     "jdbc:postgresql://localhost/world",
     "user",
     "pass"
   )
   ```
2. **ConnectionIO[A]**  
   - A description of a database action returning `A`.  
   - Built with SQL interpolator:
   ```scala
   case class User(id: Int, name: String)

   def findUser(id: Int): ConnectionIO[User] =
     sql"SELECT id, name FROM users WHERE id = $id"
       .query[User]
       .unique
   ```
3. **Transact**  
   - Converts a `ConnectionIO` into an effect (`IO`) that runs the action:
   ```scala
   val userIO: IO[User] = findUser(42).transact(xa)
   ```
4. **Batch Operations**  
   - Use `Update` for bulk writes:
   ```scala
   val users = List(User(1, "Alice"), User(2, "Bob"))
   val insert = Update[User]("INSERT INTO users (id, name) VALUES (?, ?)")
     .updateMany(users)
   ```

### Benefits
- **Type Safety**: Compile-time verification of SQL fragments.  
- **Composability**: Build complex workflows by combining `ConnectionIO` monads.  
- **Resource Safety**: Automatic connection cleanup.

### Best Practices
- **SQL Interpolator**: Always use to avoid injection.  
- **Small Transactions**: Keep transactions short to reduce lock contention.  
- **Specify Fetch Size**: For large result sets, tune with `.withFetchSize(n)`.

---

## 4. Query Optimization

### Common Techniques
1. **Indexing**  
   - Create indexes on columns used in `WHERE`, `JOIN`, and `ORDER BY`.  
   - Beware of over-indexing; each index slows `INSERT/UPDATE/DELETE`.
2. **Predicate Pushdown**  
   - Apply filters as early as possible, ideally at the database level.
3. **EXPLAIN Plans**  
   - Use `EXPLAIN` (PostgreSQL) or `EXPLAIN ANALYZE` to inspect query execution.
4. **Batching & Pagination**  
   - Use batched operations for bulk writes.  
   - Page large result sets to avoid memory spikes.
5. **Connection Pooling**  
   - Use HikariCP or similar to reuse connections.

### Example: EXPLAIN ANALYZE
```sql
EXPLAIN ANALYZE
SELECT * FROM orders
WHERE customer_id = 123
ORDER BY order_date DESC
LIMIT 10;
```

---

## 5. Migration Best Practices

### Versioning Tools
- **Flyway**  
  - Simple, SQL-based migrations.  
  - Place files in `resources/db/migration`.
- **Liquibase**  
  - XML/JSON/YAML-based changelogs.  
  - Supports rollbacks explicitly.

### Migration Workflow
1. **Incremental Scripts**  
   - One change per file named with version prefix (e.g., `V1__create_users.sql`).
2. **Idempotency**  
   - Write scripts so re-running doesn’t break. Use `IF NOT EXISTS`.
3. **Rollback Strategies**  
   - Provide `DOWN` scripts or backups for critical tables.
4. **Staging Tests**  
   - Run migrations in a mirror of production before deployment.

### Example Flyway Command
```bash
flyway -url=jdbc:postgresql://db/prod -user=app -password=pass migrate
```

---

> This expanded guide uses clear definitions, diagrams, and examples to make advanced topics accessible to those without deep NoSQL or Scala backgrounds.
