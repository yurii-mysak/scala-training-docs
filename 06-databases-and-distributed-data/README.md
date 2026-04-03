# Databases & Distributed Data

Relational and NoSQL databases, transactions, indexing, storage engines, distributed consistency, partitioning, and event sourcing.

---

## Beginner

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 1 | RDBMS vs NoSQL | [RDBMS_vs_NoSQL.md](RDBMS_vs_NoSQL.md) | When to use relational vs NoSQL, trade-offs |
| 2 | Key-value stores | [KeyValue_Stores.md](KeyValue_Stores.md) | Redis, Memcached, use cases |
| 3 | Wide-column vs document | [WideColumn_vs_Document.md](WideColumn_vs_Document.md) | Cassandra vs MongoDB model comparison |
| 4 | Data modeling | [Databases-Data-Modeling.md](Databases-Data-Modeling.md) | Normalization, denormalization, schema design |

## Intermediate

### Transactions & Query Optimization
| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 5 | SQL transactions | [SQL_Transactions.md](SQL_Transactions.md) | ACID, isolation levels, locks, deadlocks |
| 6 | Indexing & optimization | [Indexing_Optim.md](Indexing_Optim.md) | B-tree indexes, composite indexes, EXPLAIN |
| 7 | Query optimization | [db_query_optimization_approaches.md](db_query_optimization_approaches.md) | Query plans, N+1 problem, join strategies |

### Storage Engines
| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 8 | B-tree vs LSM | [btree_lsm_comparison.md](btree_lsm_comparison.md) | Read vs write optimization, compaction |
| 9 | Storage persistence | [Data_Storage_Persistence_Strategies.md](Data_Storage_Persistence_Strategies.md) | WAL, snapshots, append-only logs |

### Specific Databases
| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 10 | Elasticsearch | [Elasticsearch_Basics.md](Elasticsearch_Basics.md) | Inverted index, full-text search, mappings |
| 11 | MongoDB | [MongoDB_Concepts.md](MongoDB_Concepts.md) | Document model, aggregation pipeline, sharding |

## Advanced

### Distributed Theory
| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 12 | CAP theorem & consistency | [CAP_Consistency.md](CAP_Consistency.md) | CAP trade-offs, eventual vs strong consistency |
| 13 | Linearizability vs serializability | [linearizability_vs_serializability.md](linearizability_vs_serializability.md) | Consistency guarantees, real-time ordering |
| 14 | Distributed transactions | [Distributed_Transactions.md](Distributed_Transactions.md) | 2PC, 3PC, Saga pattern, consensus protocols |

### Partitioning & Replication
| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 15 | Partitioning & rebalancing | [Partitioning_Rebalancing.md](Partitioning_Rebalancing.md) | Hash vs range partitioning, consistent hashing |
| 16 | Partition strategies | [partition_strategies.md](partition_strategies.md) | Hot spots, rebalancing strategies |

### Cassandra & DynamoDB
| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 17 | Cassandra partitioning | [cassandra_partition_clustering.md](cassandra_partition_clustering.md) | Partition keys, clustering keys, data distribution |
| 18 | Cassandra LSM & read/write path | [Cassandra_LSM.md](Cassandra_LSM.md) | Memtable, SSTable, compaction strategies |
| 19 | Cassandra + Doobie indexing | [Cassandra_Doobie_Indexing_Guide.md](Cassandra_Doobie_Indexing_Guide.md) | Secondary indexes, materialized views |
| 20 | DynamoDB | [dynamodb_refresher.md](dynamodb_refresher.md) | Partition key design, RCU/WCU, GSI/LSI |

### Event-Driven Data
| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 21 | Event sourcing | [Event-Sourcing-Guide.md](Event-Sourcing-Guide.md) | Event store, snapshots, projections, replay |

## Key Interview Questions by Level

**Beginner**: When would you choose NoSQL over RDBMS? What is normalization and when would you denormalize?

**Intermediate**: Explain ACID properties. What are the SQL isolation levels and what anomalies does each prevent? How does a B-tree index speed up queries?

**Advanced**: Explain CAP theorem with a real-world example. How does consistent hashing work? Design a partition strategy for a high-write-throughput system. What is the difference between linearizability and serializability?
