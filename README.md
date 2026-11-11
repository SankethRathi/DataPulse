# DataPulse – Data Quality Monitoring Engine

## 1. Overview

**DataPulse** is a Python-based Data Quality Monitoring Engine designed to monitor incoming data batches, identify data quality issues, detect anomalies, and generate explainable alerts.

It compares incoming data against a historical baseline to identify unexpected changes in data volume, distributions, null values, freshness, and schema.

The system also validates records, quarantines rejected data, transforms valid records, and publishes processed outputs with batch-level traceability.

## 2. Key Features

- **Data ingestion:** Loads incoming CSV batches and calculates SHA-256 content hashes.
- **Idempotency:** Prevents successfully processed identical files from being processed again.
- **Baseline profiling:** Builds historical data profiles using multiple batches.
- **Schema drift detection:** Identifies new columns, missing columns, and data type changes.
- **Anomaly detection:** Detects changes in data volume, null percentages, distributions, and freshness.
- **Data validation:** Checks required fields, duplicates, invalid amounts, quantities, and timestamps.
- **Data quarantine:** Separates rejected records and records their rejection reasons.
- **Data transformation:** Cleans and standardizes valid records and calculates total order value.
- **Data publishing:** Publishes transformed CSV files and associated manifests.
- **Audit logging:** Maintains batch processing history, execution status, and error details.
- **Operational metrics:** Tracks execution time, throughput, valid records, rejected records, and alerts.
- **Explainable alerts:** Generates alerts with severity levels and details about detected issues.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application |
| Pandas | Data processing and transformation |
| NumPy | Numerical operations |
| SQLite | Metadata, audit logs, and pipeline history |
| PyYAML | Configuration management |
| Pytest | Automated testing |
| CSV / JSON | Input data, reports, and published outputs |
| Git / GitHub | Version control |

## 4. Project Architecture

The pipeline follows these stages:

1. **Ingestion:** Load the incoming CSV file and calculate its content hash.
2. **Idempotency check:** Check whether the same content has already been successfully processed.
3. **Schema comparison:** Compare incoming columns and data types against the historical baseline.
4. **Validation:** Identify invalid, missing, and duplicate records.
5. **Quarantine:** Store rejected records separately with rejection reasons.
6. **Profiling:** Calculate data quality statistics for the incoming batch.
7. **Anomaly detection:** Compare the incoming profile with the historical baseline.
8. **Transformation:** Clean and standardize valid records.
9. **Publishing:** Save the transformed data and its manifest.
10. **Monitoring and auditing:** Store pipeline results, alerts, and execution metrics in SQLite.

## 5. Project Structure

```text
DataPulse/
│
├── config/
│   └── settings.yaml
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── quarantine/
│   └── datapulse.db
│
├── reports/
│   ├── baseline.json
│   └── incoming_*_report.json
│
├── scripts/
│   ├── generate_data.py
│   ├── build_baseline.py
│   ├── run_pipeline.py
│   ├── run_e2e_tests.py
│   ├── test_reliability.py
│   └── other utility scripts
│
├── src/
│   └── datapulse/
│       ├── ingestion/
│       ├── profiling/
│       ├── detection/
│       ├── validation/
│       ├── transformation/
│       ├── storage/
│       └── pipeline.py
│
├── tests/
│
├── requirements.txt
├── ARCHITECTURE.md
├── DATA_DICTIONARY.md
└── README.md
```

## 6. Setup and Installation

### Prerequisites

- Python 3.10 or later
- Git
- Windows, Linux, or macOS

### Step 1: Clone the repository

```bash
git clone https://github.com/SankethRathi/DataPulse.git
cd DataPulse
```

### Step 2: Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Step 3: Install dependencies

```powershell
pip install -r requirements.txt
```

### Step 4: Set the Python source path

Windows PowerShell:

```powershell
$env:PYTHONPATH = "src"
```

## 7. Running the Project

### Step 1: Generate synthetic datasets

```powershell
python scripts/generate_data.py
```

This generates historical batches and incoming batches containing different data quality scenarios.

### Step 2: Build the historical baseline

```powershell
python scripts/build_baseline.py
```

The baseline profile is saved in:

```text
reports/baseline.json
```

### Step 3: Run the pipeline

Example:

```powershell
python scripts/run_pipeline.py data/raw/incoming_normal.csv
```

You can also process other scenarios:

```powershell
python scripts/run_pipeline.py data/raw/incoming_missing_values.csv
python scripts/run_pipeline.py data/raw/incoming_duplicates.csv
python scripts/run_pipeline.py data/raw/incoming_distribution_shift.csv
python scripts/run_pipeline.py data/raw/incoming_late_records.csv
python scripts/run_pipeline.py data/raw/incoming_schema_drift.csv
```

The pipeline generates reports, stores processing metadata, quarantines rejected records, and publishes valid transformed data where applicable.

## 8. Supported Data Quality Scenarios

| Scenario | Expected behavior |
|---|---|
| Normal batch | Process successfully |
| Missing values | Detect and reject invalid records |
| Duplicate records | Identify duplicate order IDs |
| Distribution shift | Generate anomaly alerts |
| Late records | Detect freshness issues |
| New column | Generate a schema drift alert |
| Missing column | Fail the batch due to schema incompatibility |
| Data type change | Detect schema type changes and validate affected records |

## 9. Testing

### Run automated unit tests

```powershell
$env:PYTHONPATH = "src"
pytest -v
```

### Run end-to-end scenario tests

```powershell
python scripts/run_e2e_tests.py
```

### Run reliability checks

```powershell
python scripts/test_reliability.py
```

### Verified test results

The current implementation has passed:

- **31 pytest tests**
- **8 end-to-end scenarios**
- **3 reliability checks**

Reliability checks include duplicate-file handling, processing modified file content, and rollback during a simulated publishing failure.

## 10. Database and Monitoring

DataPulse uses SQLite to maintain operational metadata.

The database stores:

- Batch ingestion details
- Pipeline execution history
- Alert information
- Audit history
- Processing status
- Execution time and throughput
- Valid and rejected record counts

Database location:

```text
data/datapulse.db
```

## 11. Output

The project generates:

- Historical baseline profiles in JSON.
- Incoming batch quality reports.
- Anomaly and schema drift alerts.
- Quarantined records with rejection reasons.
- Transformed and published CSV files.
- Publishing manifests.
- SQLite audit and execution history.

## 12. Design Considerations

- Content hashing supports duplicate detection.
- Validation and anomaly detection are separate pipeline stages.
- Schema comparison happens before record validation.
- Rejected records are retained separately for traceability.
- Pipeline outcomes distinguish successful, partially successful, failed, and duplicate-skipped batches.
- Synthetic data makes scenarios reproducible.
- Publishing uses temporary files and rollback handling for simulated publishing failures.

## 13. Future Improvements

- Add concurrent ingestion protection.
- Improve recovery for unexpected process termination during publishing.
- Add large-volume performance and load testing.
- Introduce a monitoring dashboard.
- Expand anomaly detection and configurable quality rules.

## 14. Author

**Developed as a Data Engineering project for the YottaFlex AI Hackathon.**

**Project:** DataPulse – Data Quality Monitoring Engine