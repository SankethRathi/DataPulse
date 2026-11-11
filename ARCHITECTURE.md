# DataPulse – System Architecture

## 1. Overview

DataPulse is a Python-based Data Quality Monitoring Engine that processes incoming CSV batches, validates records, detects anomalies, and publishes cleaned datasets.

The system follows a modular pipeline architecture. Each stage has a separate responsibility, making the application easier to maintain, test, and extend.

## 2. Architecture Flow

```text
              Incoming CSV Batch
                      |
                      v
               Data Ingestion
                      |
                      v
             Content Hash Check
                      |
                      v
             Schema Comparison
                      |
                      v
              Data Validation
                      |
             +--------+--------+
             |                 |
             v                 v
         Valid Data       Rejected Data
             |                 |
             |                 v
             |             Quarantine
             |
             v
         Data Profiling
             |
             v
       Anomaly Detection
             |
             v
         Transformation
             |
             v
           Publishing
             |
             v
       Reports and Audit
             |
             v
         SQLite Storage
```

## 3. Main Components

### 3.1 Data Ingestion

**Location:** `src/datapulse/ingestion/loader.py`

Responsibilities:
- Read incoming CSV files.
- Calculate SHA-256 content hashes.
- Capture batch metadata.
- Identify previously processed identical files.

### 3.2 Data Profiling

**Location:** `src/datapulse/profiling/`

Responsibilities:
- Calculate row and column counts.
- Measure null values and percentages.
- Calculate distinct values.
- Generate numerical statistics.
- Analyze categorical distributions.
- Evaluate data freshness.

Historical batches are used to build the baseline profile.

### 3.3 Schema Drift Detection

**Location:** `src/datapulse/profiling/schema.py`

Responsibilities:
- Identify new columns.
- Identify missing columns.
- Detect data type changes.
- Compare incoming schema with the baseline schema.

### 3.4 Anomaly Detection

**Location:** `src/datapulse/detection/detector.py`

Responsibilities:
- Compare incoming profiles with historical baseline values.
- Detect unexpected changes in data volume.
- Identify changes in null percentages.
- Detect distribution shifts.
- Identify freshness-related issues.
- Generate alerts with severity levels.

### 3.5 Data Validation

**Location:** `src/datapulse/validation/`

Responsibilities:
- Check required fields.
- Identify missing values.
- Detect duplicate order IDs.
- Validate order amounts and quantities.
- Check timestamp validity.
- Perform additional data quality checks.

Invalid records are separated from valid records.

### 3.6 Quarantine

**Location:** `src/datapulse/validation/quarantine.py`

Rejected records are stored separately with rejection reasons to support investigation and traceability.

### 3.7 Transformation

**Location:** `src/datapulse/transformation/transformer.py`

Responsibilities:
- Standardize text fields.
- Convert numeric fields to appropriate types.
- Normalize order status values.
- Parse timestamps.
- Calculate total order value.

### 3.8 Publishing

**Location:** `src/datapulse/transformation/publisher.py`

Responsibilities:
- Publish transformed CSV files.
- Generate publishing manifests.
- Use temporary files and replacement operations.
- Perform rollback handling when a simulated publishing failure occurs.

### 3.9 Storage and Auditing

**Location:** `src/datapulse/storage/`

SQLite stores:
- Batch metadata.
- Pipeline execution history.
- Alerts.
- Audit records.
- Processing metrics.

### 3.10 Pipeline Orchestration

**Location:** `src/datapulse/pipeline.py`

The pipeline coordinates all the individual components and records the final processing status.

## 4. Data Flow

1. An incoming CSV batch is submitted.
2. The ingestion component calculates its content hash.
3. Previously completed identical content is skipped.
4. The incoming schema is compared against the historical baseline.
5. Records are validated and separated into valid and rejected datasets.
6. Rejected records are written to quarantine.
7. The incoming dataset is profiled and compared with the baseline.
8. Anomaly and quality alerts are generated.
9. Valid records are transformed.
10. Transformed data and publishing manifests are generated.
11. Processing results and audit information are stored in SQLite.

## 5. Storage Design

| Storage | Purpose |
|---|---|
| CSV | Raw input and published datasets |
| JSON | Baseline profiles and quality reports |
| SQLite | Batch metadata, alerts, audit and pipeline history |
| Quarantine CSV | Rejected records and rejection reasons |

## 6. Reliability Considerations

- SHA-256 hashing supports content-based duplicate detection.
- Validation separates invalid records from valid records.
- Reconciliation checks that input records equal valid plus rejected records.
- Audit records capture pipeline execution outcomes.
- Publishing uses temporary files and rollback handling.
- Automated tests cover normal, invalid, and schema-drift scenarios.

## 7. Current Limitations

- Concurrent duplicate submissions are not fully protected against race conditions.
- Multi-file publishing is not a single atomic transaction.
- Large-volume performance requires additional benchmarking.
- Unexpected process termination during publishing requires stronger recovery handling.

## 8. Future Enhancements

- Concurrency-safe ingestion.
- Improved crash recovery.
- Configurable quality thresholds.
- Large-scale performance testing.
- Additional monitoring and visualization capabilities.