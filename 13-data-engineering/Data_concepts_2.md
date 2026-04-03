# Data Platform Interview Prep – Extended Explanations

This guide provides beginner-friendly, detailed explanations for key data platform interview topics: layered medallion architecture, securing data lakes, ETL orchestration with late-arriving data handling, and ensuring data quality in operational pipelines.

## 1. Layered Architecture: Bronze / Silver / Gold Zones
A medallion (or layered) architecture organizes data through successive refinement stages:

- **Bronze (Raw Zone)**: Ingests data exactly as received, preserving original structure and all attributes for future reprocessing if needed.
- **Silver (Cleansed Zone)**: Applies basic cleaning—removing duplicates, filling missing values, enforcing data types—and standardizes schemas across sources to create a reliable intermediate dataset.
- **Gold (Curated Zone)**: Produces business-ready tables or views—often star or snowflake schemas—optimized for reporting, dashboards, and analytics with high performance SLAs.

**Implementation Tips**
1. **Bronze Layer**: Store raw files in object storage (S3, ADLS) or as Delta/Iceberg tables without transformations.
2. **Silver Layer**: Use Spark jobs or dbt incremental models to validate schemas, handle nulls, and join related streams into unified tables.
3. **Gold Layer**: Materialize aggregated views and dimensional tables; automate promotions with CI/CD pipelines gated on data quality tests.

---

## 2. Securing Sensitive Data in a Data Lake
Protecting sensitive data involves multiple layers:

1. **Classification & Cataloging**: Tag datasets by sensitivity (e.g., PII, PHI) in a metadata catalog like Azure Purview or AWS Glue Data Catalog to drive access policies.
2. **Encryption**:
   - **At Rest**: Enable server-side encryption (SSE-S3, SSE-KMS) or client-side encryption using customer-managed keys.
   - **In Transit**: Enforce TLS/SSL for all data transfers, including API calls and service-to-service communication.
3. **Access Control**:
   - **IAM Policies**: Apply the principle of least privilege—grant minimal permissions scoped to buckets, prefixes, or tables.
   - **Fine-Grained ACLs**: Use AWS Lake Formation or Azure RBAC to define table- and column-level access rules.
4. **Auditing & Monitoring**:
   - Enable storage access logs (S3 server logs, Azure Monitor) and cloud audit trails (CloudTrail).
   - Set up alerting on anomalous patterns, such as bulk downloads or unauthorized IAM changes.

---

## 3. ETL Orchestration & Late-Arriving Data
Effective pipelines are reliable and resilient to timing variability:

- **Orchestration Strategy**:
  - Use Apache Airflow to define DAGs, keeping scheduling separate from transformation logic and storing code in version control.
  - Enable CI/CD for DAG validations, unit tests, and automated deployments.

- **Handling Late-Arriving Data**:
  1. **Idempotent Designs**: Implement upserts or merge logic (e.g., MERGE in Spark/SQL) to ingest late data without duplications.
  2. **Windowing & Watermarks**: In streaming frameworks (Spark Structured Streaming, Beam), define watermarks and allowed lateness to reopen windows for straggler events.
  3. **Bi-Temporal Tables**: Track both event and ingestion timestamps to backfill and reconcile historical corrections.
  4. **Reprocessing Pipelines**: Retain raw Bronze data to trigger selective backfills or full reprocessing when late data is detected.

---

## 4. Ensuring Data Quality in Operational Pipelines
Maintain trust in data through continuous validation:

- **Quality Dimensions**: Accuracy, completeness, consistency, timeliness, and uniqueness are core attributes to enforce.
- **Enforcement Strategies**:
  1. **Automated Checks**: Embed tests using frameworks like Great Expectations for schema conformity, null thresholds, and custom expectations.
  2. **Data Contracts & SLAs**: Define producer-consumer agreements specifying schemas, value ranges, and freshness requirements; validate in CI pipelines.
  3. **Metadata & Lineage**: Use catalogs to track dataset versions, ownership, and transformation history for traceability.
  4. **Monitoring & Alerts**: Stream metrics (row counts, error rates) to Prometheus or cloud monitoring; trigger alerts on threshold breaches.
  5. **Reconciliation & Backfill**: Periodically compare aggregates with source systems; use archived raw data for corrections.

---

## 5. Interview Talking Points
- **Medallion Architecture**: Sketch each layer, explain purpose and transformations.
- **Security**: Describe encryption setup, IAM roles, and audit configurations.
- **Orchestration**: Walk through an Airflow DAG, highlighting how you handle failures and late data.
- **Data Quality**: Share a real example where automated tests caught an issue and how you remediated it.
