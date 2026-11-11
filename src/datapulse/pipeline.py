
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

from datapulse.ingestion.loader import load_batch, calculate_file_hash

from datapulse.profiling.profiler import profile_batch
from datapulse.profiling.schema import profile_schema, compare_schemas

from datapulse.detection.detector import detect_anomalies

from datapulse.validation.validator import validate_batch
from datapulse.validation.quarantine import save_quarantine
from datapulse.validation.quality_checks import run_quality_checks

from datapulse.transformation.transformer import transform_batch
from datapulse.transformation.publisher import publish_batch

from datapulse.storage.database import initialize_database

from datapulse.storage.repository import (
    save_pipeline_result,
    find_batch_by_hash,
    start_pipeline_audit,
    finish_pipeline_audit,
)


def _save_report(report, batch_path):
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_path = (
        reports_dir / f"{Path(batch_path).stem}_report.json"
    )

    report["report_path"] = str(report_path)

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    return report_path


def _run_pipeline(
    batch_path: str,
    baseline_path: str = "reports/baseline.json",
):
    start_time = time.perf_counter()

    print("\nStarting DataPulse pipeline...")

    initialize_database()

    # 1. Ingestion
    batch = load_batch(batch_path, validate_schema=False)

    metadata = batch["metadata"]
    source_df = batch["data"]
    total_records = len(source_df)

    print("1. Ingestion completed")

    # 2. Idempotency
    existing_batch = find_batch_by_hash(metadata["content_hash"])

    if existing_batch:
        print("Duplicate batch detected. Skipping.")

        return {
            "pipeline_status": "SKIPPED_DUPLICATE",
            "source_file": metadata["source_file"],
            "content_hash": metadata["content_hash"],
            "existing_batch_id": existing_batch["batch_id"],
            "previous_run_id": existing_batch["previous_run_id"],
        }

    # 3. Load baseline and compare schema BEFORE validation
    with open(baseline_path, "r", encoding="utf-8") as file:
        baseline = json.load(file)

    incoming_schema = profile_schema(source_df)
    baseline_schema = baseline.get("schema", {})

    schema_result = compare_schemas(
        incoming_schema,
        baseline_schema,
    )

    schema_alerts = []

    for column in schema_result["new_columns"]:
        schema_alerts.append({
            "metric": "schema_new_column",
            "severity": "MEDIUM",
            "observed": column,
            "expected": None,
            "message": f"Unexpected column '{column}' was introduced.",
        })

    for column in schema_result["missing_columns"]:
        schema_alerts.append({
            "metric": "schema_missing_column",
            "severity": "HIGH",
            "observed": None,
            "expected": column,
            "message": f"Expected column '{column}' is missing.",
        })

    for change in schema_result["type_changes"]:
        schema_alerts.append({
            "metric": "schema_type_change",
            "severity": "HIGH",
            "observed": change["observed_type"],
            "expected": change["expected_type"],
            "message": (
                f"Column '{change['column']}' changed from "
                f"{change['expected_type']} to "
                f"{change['observed_type']}."
            ),
        })

    print("2. Schema comparison completed")

    # Missing required columns make safe processing impossible.
    if schema_result["missing_columns"]:
        report = {
            "batch_metadata": metadata,
            "schema_comparison": schema_result,
            "alerts": schema_alerts,
            "alert_count": len(schema_alerts),
            "pipeline_status": "FAILED",
            "failure_reason": "Required columns are missing.",
        }

        _save_report(report, batch_path)

        print("Schema validation failed.")
        print("Missing columns:", schema_result["missing_columns"])

        return report

    # 4. Validation
    valid_df, rejected_df = validate_batch(source_df)

    valid_records = len(valid_df)
    rejected_records = len(rejected_df)

    print("3. Validation completed")

    # 5. Quarantine
    quarantine_path = (
        Path("data/quarantine")
        / f"{Path(batch_path).stem}_rejected.csv"
    )

    if not rejected_df.empty:
        save_quarantine(rejected_df, str(quarantine_path))

    print("4. Quarantine completed")

    # 6. Reconciliation
    reconciled_records = valid_records + rejected_records

    reconciliation = {
        "input_records": total_records,
        "valid_records": valid_records,
        "rejected_records": rejected_records,
        "reconciled_records": reconciled_records,
        "difference": total_records - reconciled_records,
        "passed": reconciled_records == total_records,
    }

    if not reconciliation["passed"]:
        raise RuntimeError("Record reconciliation failed")

    print("5. Reconciliation completed")

    # 7. Profiling and anomaly detection
    profile = {}
    alerts = list(schema_alerts)

    if not valid_df.empty:
        profile = profile_batch(valid_df)
        profile["schema"] = profile_schema(valid_df)

        alerts.extend(
            detect_anomalies(
                profile,
                baseline,
                check_schema=False,
            )
        )

    print("6. Profiling completed")

    # 8. Business quality checks
    quality_result = run_quality_checks(valid_df)
    alerts.extend(quality_result["alerts"])

    print("7. Business quality checks completed")

    # 9. Transformation and publishing
    transformation_info = None
    publishing_info = None

    if not valid_df.empty:
        transformed_df = transform_batch(valid_df)

        publishing_info = publish_batch(
            transformed_df,
            metadata["batch_id"],
        )

        transformation_info = {
            "input_records": len(valid_df),
            "output_records": len(transformed_df),
            "input_columns": len(valid_df.columns),
            "output_columns": len(transformed_df.columns),
            "status": "COMPLETED",
        }

    print("8. Transformation and publishing completed")

    # 10. Operational metrics
    execution_time = round(
        time.perf_counter() - start_time, 4
    )

    throughput = (
        round(total_records / execution_time, 2)
        if execution_time > 0 else 0
    )

    # 11. Determine final pipeline status
    if total_records > 0 and valid_records == 0:
        pipeline_status = "FAILED_VALIDATION"
    elif rejected_records > 0:
        pipeline_status = "COMPLETED_WITH_REJECTIONS"
    else:
        pipeline_status = "COMPLETED"

    # 12. Final report
    report = {
        "batch_metadata": metadata,
        "schema_comparison": schema_result,

        "validation": {
            "total_records": total_records,
            "valid_records": valid_records,
            "rejected_records": rejected_records,
            "quarantine_file": (
                str(quarantine_path)
                if rejected_records else None
            ),
        },

        "reconciliation": reconciliation,
        "profile": profile,
        "quality_checks": quality_result,
        "alerts": alerts,
        "alert_count": len(alerts),
        "transformation": transformation_info,
        "publishing": publishing_info,

        "operational_metrics": {
            "execution_time_seconds": execution_time,
            "records_processed": total_records,
            "records_per_second": throughput,
        },

        "pipeline_status": pipeline_status,
    }

    _save_report(report, batch_path)

    # 13. SQLite persistence
    run_id = save_pipeline_result(report)

    report["run_id"] = run_id

    _save_report(report, batch_path)

    print("\n========== DATAPULSE RESULTS ==========")
    print("Total records:", total_records)
    print("Valid records:", valid_records)
    print("Rejected records:", rejected_records)
    print("Schema alerts:", len(schema_alerts))
    print("Total alerts:", len(alerts))
    print("Reconciliation:", reconciliation["passed"])
    print("Execution time:", execution_time)
    print("Throughput:", throughput)
    print(
        "Published:",
        publishing_info["published_file"]
        if publishing_info else "No valid records",
    )
    print("Report:", report["report_path"])
    print("SQLite Run ID:", run_id)
    print("Pipeline status:", report["pipeline_status"])

    return report


def run_pipeline(
    batch_path: str,
    baseline_path: str = "reports/baseline.json",
):
    """Execute DataPulse with persistent audit tracking."""

    audit_id = str(uuid4())
    started_at = datetime.now(timezone.utc)
    start_clock = time.perf_counter()

    source_file = Path(batch_path).name

    try:
        content_hash = calculate_file_hash(batch_path)
    except Exception:
        content_hash = None

    initialize_database()

    start_pipeline_audit(
        audit_id=audit_id,
        source_file=source_file,
        content_hash=content_hash,
        started_at=started_at.isoformat(),
    )

    try:
        result = _run_pipeline(batch_path, baseline_path)

        status = result.get("pipeline_status", "COMPLETED")

        finish_pipeline_audit(
            audit_id=audit_id,
            status=status,
            completed_at=datetime.now(timezone.utc).isoformat(),
            duration_seconds=round(
                time.perf_counter() - start_clock, 4
            ),
            run_id=(
                result.get("previous_run_id")
                if status == "SKIPPED_DUPLICATE"
                else result.get("run_id")
            ),
            error_message=result.get("failure_reason"),
        )

        result["audit_id"] = audit_id

        print("\nAudit ID:", audit_id)
        print("Audit status:", status)

        return result

    except Exception as exc:
        finish_pipeline_audit(
            audit_id=audit_id,
            status="FAILED",
            completed_at=datetime.now(timezone.utc).isoformat(),
            duration_seconds=round(
                time.perf_counter() - start_clock, 4
            ),
            error_message=f"{type(exc).__name__}: {exc}",
        )

        print("Pipeline failed:", exc)
        raise
