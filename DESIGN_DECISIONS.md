# DataPulse – Design Decisions and Trade-offs

## 1. Architecture

DataPulse uses a modular Python pipeline with separate components for ingestion, profiling, anomaly detection, validation, transformation, publishing and storage.

This separation makes individual stages easier to test and maintain.

## 2. Technology Choices

- **Python:** Core implementation and pipeline orchestration.
- **Pandas and NumPy:** Data profiling, validation and transformation.
- **SQLite:** Lightweight persistent storage for batch metadata, alerts and audit history.
- **CSV and JSON:** Input data, published datasets and quality reports.
- **Pytest:** Automated testing.

## 3. Important Design Decisions

### Content-based idempotency

SHA-256 content hashing is used to identify previously processed files. This avoids processing identical successfully completed batches again.

Trade-off: Hashing requires reading the file, and concurrent submissions would require additional protection against race conditions.

### Historical baseline

The system builds a baseline using historical batches and compares incoming batches against it.

Trade-off: A small historical sample may not represent every legitimate business variation.

### Validation and quarantine

Invalid records are separated from valid records and retained with rejection reasons.

Trade-off: Quarantining records requires additional storage and operational review.

### Schema drift handling

New columns, missing columns and data type changes are detected before normal record validation.

Trade-off: New columns can be accepted with an alert, while missing required columns prevent normal processing.

### SQLite storage

SQLite provides persistent operational metadata without requiring a separate database server.

Trade-off: It is suitable for this local demonstration but is not a replacement for a distributed production database.

### File publishing

Temporary files and rollback handling are used to reduce the risk of incomplete publishing.

Trade-off: Publishing multiple files is not a single atomic transaction across all files.

## 4. Known Limitations

- Concurrent duplicate submissions are not fully protected against race conditions.
- Large-volume performance needs further benchmarking.
- Recovery after unexpected process termination during multi-file publishing needs improvement.
- The historical baseline is based on a limited synthetic dataset.

## 5. Future Improvements

- Concurrency-safe ingestion.
- Stronger crash recovery.
- Configurable anomaly thresholds.
- Large-volume performance testing.
- Expanded monitoring and reporting.