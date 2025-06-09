# Delta Lake & Parquet Guide

This guide covers two essential topics for modern data platforms: how Delta Lake ensures ACID transactions on Parquet files, and an overview of the Parquet file format itself.

## 1. Delta Lake ACID on Parquet

Delta Lake brings ACID (Atomicity, Consistency, Isolation, Durability) guarantees to data lakes built on Parquet by layering a transaction log and metadata management on top of raw files.

### Transaction Log
Delta Lake maintains a `_delta_log` directory alongside data files. Every write, update, or delete operation is recorded as an atomic JSON log entry. Periodically, these log entries are compacted into Parquet checkpoints for efficient snapshot reconstruction.

### Atomicity
Writes are atomic: data files are written first, and only after a complete write does Delta Lake append a corresponding log entry. If a job fails mid-write, the absence of a log update means the operation is rolled back, leaving data in a consistent prior state.

### Consistency
Delta enforces schema checks on each write. Any operation that violates the table schema—such as type mismatches or missing fields—is rejected, ensuring that all committed data conforms to a single, agreed structure.

### Isolation
Using optimistic concurrency control, Delta Lake ensures that concurrent operations do not interfere. Each writer checks that no conflicting transactions have been committed before appending its own log entry. If a conflict is detected, the write is retried, guaranteeing serializable isolation without heavy locking.

### Durability
Once a transaction log entry is written, it is stored on durable object storage (e.g., S3, ADLS). Combined with periodic Parquet checkpoints, this ensures that tables can be fully restored even after system failures or crashes.

### Why It Matters
- **Data Integrity**: Prevents partial writes and table corruption.  
- **Concurrent Workloads**: Supports simultaneous batch and streaming writes without exposing intermediate states.  
- **Time Travel**: Enables querying historical snapshots of data for debugging and auditing.  
- **Schema Evolution**: Allows safe addition or modification of columns over time.  
- **Performance**: Checkpoints and metadata caching reduce the overhead of reading large directories of Parquet files.

---

## 2. Parquet File Format

Apache Parquet is a columnar storage format optimized for analytics and big data processing.

### File Structure
- **File Footer & Metadata**: Stores the schema, column statistics, and pointers to row groups.  
- **Row Groups**: Horizontal partitions of data, each containing data for a subset of rows.  
- **Column Chunks**: Within each row group, data is stored column-by-column, allowing individual columns to be compressed and encoded independently.

### Key Features
- **Columnar Layout**: Only columns needed for a query are read, minimizing I/O.  
- **Efficient Compression**: Supports codecs like Snappy, GZIP, and LZO, plus encodings such as dictionary and run-length encoding.  
- **Schema Evolution**: New columns can be added, and compatible schemas can be merged without rewriting existing data.  
- **Nested Types**: Supports complex data structures (maps, lists, structs) through efficient serialization.

### Common Use Cases
- **Analytical Queries**: Ideal for large-scale aggregations and filters in engines like Spark and Presto.  
- **Data Lakes and Lakehouses**: Acts as the storage layer for Delta Lake, Apache Iceberg, and Hudi.  
- **Interoperability**: Widely supported across ecosystems (Java, Python, C++), making it a de facto standard for big data.

### Comparison with Other Formats
| Format  | Storage Model | Best Use Case                    |
|---------|---------------|----------------------------------|
| Parquet | Columnar      | Analytics and data lakes         |
| ORC     | Columnar      | Hive-based workloads             |
| Avro    | Row           | Event streaming and messaging    |
| CSV/JSON| Row           | Simple interchange, low volume   |
