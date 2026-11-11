
import json
from uuid import uuid4

from datapulse.storage.database import get_connection


def find_batch_by_hash(content_hash: str):
    """Find an already completed batch with identical contents."""

    with get_connection() as connection:
        row = connection.execute("""
            SELECT
                b.batch_id,
                b.source_file,
                b.status,
                b.content_hash,
                (
                    SELECT pr.run_id
                    FROM pipeline_runs pr
                    WHERE pr.batch_id = b.batch_id
                    ORDER BY pr.executed_at DESC
                    LIMIT 1
                ) AS previous_run_id
            FROM batches b
            WHERE b.content_hash = ?
              AND b.status = 'COMPLETED'
            LIMIT 1
        """, (content_hash,)).fetchone()

    return dict(row) if row else None


def save_pipeline_result(report: dict) -> str:
    """Persist batch, execution metrics, and alerts."""

    metadata = report["batch_metadata"]
    validation = report["validation"]
    operational = report.get("operational_metrics", {})

    run_id = str(uuid4())

    alerts = report.get("alerts", [])

    schema_alert_count = sum(
        1 for alert in alerts
        if str(alert.get("metric", "")).startswith("schema_")
    )

    with get_connection() as connection:

        connection.execute("""
            INSERT INTO batches (
                batch_id,
                source_file,
                ingested_at,
                total_records,
                valid_records,
                rejected_records,
                status,
                content_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metadata["batch_id"],
            metadata["source_file"],
            metadata["ingested_at"],
            validation["total_records"],
            validation["valid_records"],
            validation["rejected_records"],
            "COMPLETED",
            metadata.get("content_hash"),
        ))

        connection.execute("""
            INSERT INTO pipeline_runs (
                run_id,
                batch_id,
                pipeline_status,
                alert_count,
                report_path,
                execution_time_seconds,
                records_processed,
                records_per_second,
                valid_records,
                rejected_records,
                schema_alert_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            metadata["batch_id"],
            report["pipeline_status"],
            report.get("alert_count", len(alerts)),
            report.get("report_path"),
            operational.get("execution_time_seconds"),
            operational.get("records_processed"),
            operational.get("records_per_second"),
            validation["valid_records"],
            validation["rejected_records"],
            schema_alert_count,
        ))

        for alert in alerts:
            connection.execute("""
                INSERT INTO alerts (
                    run_id,
                    metric,
                    severity,
                    observed_value,
                    expected_value,
                    message
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                alert.get("metric"),
                alert.get("severity"),
                json.dumps(alert.get("observed")),
                json.dumps(alert.get("expected")),
                alert.get("message"),
            ))

    return run_id


def start_pipeline_audit(
    audit_id: str,
    source_file: str,
    content_hash: str | None,
    started_at: str,
):
    """Record that a pipeline execution has started."""

    with get_connection() as connection:
        connection.execute("""
            INSERT INTO pipeline_audit (
                audit_id,
                source_file,
                content_hash,
                status,
                started_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            audit_id,
            source_file,
            content_hash,
            "RUNNING",
            started_at,
        ))


def finish_pipeline_audit(
    audit_id: str,
    status: str,
    completed_at: str,
    duration_seconds: float,
    error_message: str = None,
    run_id: str = None,
):
    """Record the final result of a pipeline execution."""

    with get_connection() as connection:
        cursor = connection.execute("""
            UPDATE pipeline_audit
            SET
                status = ?,
                completed_at = ?,
                duration_seconds = ?,
                error_message = ?,
                run_id = ?
            WHERE audit_id = ?
        """, (
            status,
            completed_at,
            duration_seconds,
            error_message,
            run_id,
            audit_id,
        ))

        if cursor.rowcount != 1:
            raise ValueError(
                f"Audit record not found: {audit_id}"
            )


def get_pipeline_audit_history(limit: int = 20) -> list[dict]:
    """Retrieve recent pipeline executions, including failures."""

    limit = max(1, min(int(limit), 500))

    with get_connection() as connection:
        rows = connection.execute("""
            SELECT *
            FROM pipeline_audit
            ORDER BY started_at DESC
            LIMIT ?
        """, (limit,)).fetchall()

    return [dict(row) for row in rows]


def get_pipeline_run_history(limit: int = 20) -> list[dict]:
    """Retrieve completed pipeline runs with their batch metrics."""

    limit = max(1, min(int(limit), 500))

    with get_connection() as connection:
        rows = connection.execute("""
            SELECT
                pr.run_id,
                pr.batch_id,
                b.source_file,
                pr.pipeline_status,
                pr.alert_count,
                pr.schema_alert_count,
                pr.execution_time_seconds,
                pr.records_processed,
                pr.records_per_second,
                pr.valid_records,
                pr.rejected_records,
                pr.report_path,
                pr.executed_at
            FROM pipeline_runs pr
            JOIN batches b
                ON b.batch_id = pr.batch_id
            ORDER BY pr.executed_at DESC
            LIMIT ?
        """, (limit,)).fetchall()

    return [dict(row) for row in rows]


def get_dashboard_summary() -> dict:
    """Return aggregate metrics for a monitoring dashboard."""

    with get_connection() as connection:

        run_summary = connection.execute("""
            SELECT
                COUNT(*) AS total_runs,
                SUM(CASE
                    WHEN status = 'COMPLETED' THEN 1 ELSE 0
                END) AS completed_runs,
                SUM(CASE
                    WHEN status = 'FAILED' THEN 1 ELSE 0
                END) AS failed_runs,
                SUM(CASE
                    WHEN status = 'SKIPPED_DUPLICATE' THEN 1 ELSE 0
                END) AS skipped_runs,
                AVG(duration_seconds) AS average_duration_seconds
            FROM pipeline_audit
        """).fetchone()

        batch_summary = connection.execute("""
            SELECT
                COALESCE(SUM(total_records), 0) AS total_records,
                COALESCE(SUM(valid_records), 0) AS valid_records,
                COALESCE(SUM(rejected_records), 0) AS rejected_records
            FROM batches
        """).fetchone()

        performance_summary = connection.execute("""
            SELECT
                AVG(execution_time_seconds) AS average_execution_seconds,
                AVG(records_per_second) AS average_throughput
            FROM pipeline_runs
        """).fetchone()

        severity_rows = connection.execute("""
            SELECT
                severity,
                COUNT(*) AS alert_count
            FROM alerts
            GROUP BY severity
        """).fetchall()

        alert_counts = {
            row["severity"]: row["alert_count"]
            for row in severity_rows
        }

    return {
        "runs": dict(run_summary),
        "records": dict(batch_summary),
        "performance": dict(performance_summary),
        "alerts_by_severity": alert_counts,
    }
