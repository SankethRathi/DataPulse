
import sqlite3
from pathlib import Path


DATABASE_PATH = Path("data/datapulse.db")


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def _add_missing_columns(connection, table_name, columns):
    existing_columns = {
        row["name"]
        for row in connection.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()
    }

    for column_name, column_type in columns.items():
        if column_name not in existing_columns:
            connection.execute(
                f"ALTER TABLE {table_name} "
                f"ADD COLUMN {column_name} {column_type}"
            )


def initialize_database():
    with get_connection() as connection:

        # 1. Batch information
        connection.execute("""
            CREATE TABLE IF NOT EXISTS batches (
                batch_id TEXT PRIMARY KEY,
                source_file TEXT NOT NULL,
                ingested_at TEXT,
                total_records INTEGER,
                valid_records INTEGER,
                rejected_records INTEGER,
                status TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        _add_missing_columns(
            connection,
            "batches",
            {
                "content_hash": "TEXT",
            },
        )

        connection.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_batches_content_hash
            ON batches(content_hash)
            WHERE content_hash IS NOT NULL
        """)

        # 2. Pipeline execution results
        connection.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id TEXT PRIMARY KEY,
                batch_id TEXT NOT NULL,
                pipeline_status TEXT,
                alert_count INTEGER,
                report_path TEXT,
                executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (batch_id) REFERENCES batches(batch_id)
            )
        """)

        # Add operational metrics to existing databases safely.
        _add_missing_columns(
            connection,
            "pipeline_runs",
            {
                "execution_time_seconds": "REAL",
                "records_processed": "INTEGER",
                "records_per_second": "REAL",
                "valid_records": "INTEGER",
                "rejected_records": "INTEGER",
                "schema_alert_count": "INTEGER",
            },
        )

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_pipeline_runs_executed_at
            ON pipeline_runs(executed_at)
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status
            ON pipeline_runs(pipeline_status)
        """)

        # 3. Individual alerts
        connection.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                metric TEXT,
                severity TEXT,
                observed_value TEXT,
                expected_value TEXT,
                message TEXT,
                FOREIGN KEY (run_id) REFERENCES pipeline_runs(run_id)
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_run_id
            ON alerts(run_id)
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_severity
            ON alerts(severity)
        """)

        # 4. Independent execution audit
        connection.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_audit (
                audit_id TEXT PRIMARY KEY,
                source_file TEXT NOT NULL,
                content_hash TEXT,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                duration_seconds REAL,
                error_message TEXT,
                run_id TEXT
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_status
            ON pipeline_audit(status)
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_started_at
            ON pipeline_audit(started_at)
        """)

    print("SQLite database initialized successfully.")
