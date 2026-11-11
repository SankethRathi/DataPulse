# DataPulse – Data Dictionary

## 1. Overview

DataPulse uses synthetic e-commerce order data to demonstrate data ingestion, profiling, validation, anomaly detection, and transformation.

The primary dataset represents customer orders.

## 2. Source Dataset

**Format:** CSV

**Primary dataset:** Historical and incoming order batches.

### Source Columns

| Column | Expected Type | Description |
|---|---|---|
| order_id | String / Identifier | Unique identifier for an order |
| customer_id | String / Identifier | Identifier of the customer who placed the order |
| product_id | String / Identifier | Identifier of the ordered product |
| order_amount | Numeric | Monetary amount associated with the order |
| quantity | Integer | Number of units ordered |
| order_status | String | Current status of the order |
| order_timestamp | Datetime | Timestamp associated with the order |

## 3. Data Quality Rules

| Column | Validation Rule |
|---|---|
| order_id | Must not be missing; duplicate IDs are identified |
| customer_id | Required field; must not be missing |
| product_id | Required field; must not be missing |
| order_amount | Must be numeric and non-negative |
| quantity | Must be numeric and greater than zero |
| order_status | Must be one of completed, pending, or cancelled |
| order_timestamp | Must contain a valid timestamp and must not be in the future |

Additional checks identify missing values, duplicate records, statistical outliers, and unexpected distribution changes.

## 4. Transformed Dataset

The transformation stage standardizes valid records before publishing.

| Column | Expected Type | Description |
|---|---|---|
| order_id | String | Unique order identifier |
| customer_id | String | Customer identifier |
| product_id | String | Product identifier |
| order_amount | Float | Standardized order amount |
| quantity | Integer | Standardized order quantity |
| order_status | String | Normalized lowercase order status |
| order_timestamp | Datetime | Parsed timestamp in UTC |
| total_order_value | Float | Calculated as order_amount multiplied by quantity |

## 5. Processing Metadata

DataPulse maintains batch and pipeline metadata in SQLite.

### Batch Metadata

| Field | Description |
|---|---|
| batch_id | Unique identifier assigned to an ingestion batch |
| source_file | Original source filename |
| content_hash | SHA-256 hash of the source file |
| ingested_at | Time when the batch was ingested |
| row_count | Number of input records |
| column_count | Number of input columns |
| status | Final processing status |
| created_at | Batch record creation timestamp |

### Pipeline Run Metadata

| Field | Description |
|---|---|
| run_id | Unique pipeline execution identifier |
| batch_id | Associated batch identifier |
| pipeline_status | Final pipeline execution status |
| alert_count | Number of generated alerts |
| report_path | Location of the generated report |
| executed_at | Pipeline execution timestamp |
| execution_time_seconds | Total execution duration |
| records_processed | Number of input records processed |
| records_per_second | Processing throughput |
| valid_records | Number of accepted records |
| rejected_records | Number of rejected records |
| schema_alert_count | Number of schema-related alerts |

## 6. Alert Information

DataPulse generates alerts when data quality issues or unexpected changes are detected.

| Attribute | Description |
|---|---|
| Alert Type | Category of detected issue |
| Severity | Priority level such as HIGH or MEDIUM |
| Message | Explanation of the detected issue |
| Details | Additional information about the observation |

## 7. Quarantine Information

Rejected records are stored in quarantine with an additional field:

| Field | Description |
|---|---|
| rejection_reason | Explanation of why the record was rejected |

## 8. Supported Data Quality Scenarios

| Scenario | Description |
|---|---|
| Normal batch | Incoming data follows expected patterns |
| Missing values | Records contain null or missing values |
| Duplicates | Duplicate order identifiers are present |
| Distribution shift | Numeric or categorical distributions change |
| Late records | Incoming records contain old timestamps |
| Schema drift | New columns are introduced |
| Missing column | A required column is absent |
| Type change | An existing column has an unexpected data type |

## 9. Notes and Assumptions

- The project uses synthetic e-commerce order data.
- The historical baseline is generated from multiple historical batches.
- Order IDs are expected to be unique.
- Monetary values must be non-negative.
- Quantities must be positive integers.
- The allowed order status values are completed, pending, and cancelled.
- Timestamps are standardized to UTC during transformation.
- Exact database column definitions and report structures should be verified against the implementation.