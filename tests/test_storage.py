from uuid import uuid4
import sqlite3
from pathlib import Path

import datapulse.storage.database as database
from datapulse.storage.database import initialize_database
from datapulse.storage.repository import save_pipeline_result


TEST_DIR = Path("tests/test_data")


def setup_test_database(monkeypatch, filename):
    TEST_DIR.mkdir(parents=True, exist_ok=True)

    db_path = TEST_DIR / filename

    monkeypatch.setattr(database, "DATABASE_PATH", db_path)
    initialize_database()

    return db_path


def test_database_initialization(monkeypatch):
    db_path = setup_test_database(
        monkeypatch, "initialization_test.db"
    )

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

    assert {"batches", "pipeline_runs", "alerts"}.issubset(tables)


def test_save_pipeline_result(monkeypatch):
    db_path = setup_test_database(
    monkeypatch,
    f"repository_test_{uuid4().hex}.db"
)

    report = {
        "batch_metadata": {
            "batch_id": "test-batch-001",
            "source_file": "test.csv",
            "ingested_at": "2026-11-11T10:00:00+00:00",
        },
        "validation": {
            "total_records": 100,
            "valid_records": 95,
            "rejected_records": 5,
        },
        "pipeline_status": "COMPLETED",
        "alert_count": 1,
        "report_path": "reports/test_report.json",
        "alerts": [{
            "metric": "order_amount_mean",
            "severity": "HIGH",
            "observed": 2000,
            "expected": 900,
            "message": "Order amount increased unexpectedly.",
        }],
    }

    run_id = save_pipeline_result(report)

    with sqlite3.connect(db_path) as connection:
        batch_count = connection.execute(
            "SELECT COUNT(*) FROM batches"
        ).fetchone()[0]

        run_count = connection.execute(
            "SELECT COUNT(*) FROM pipeline_runs"
        ).fetchone()[0]

        alert_count = connection.execute(
            "SELECT COUNT(*) FROM alerts WHERE run_id = ?",
            (run_id,),
        ).fetchone()[0]

    assert batch_count == 1
    assert run_count == 1
    assert alert_count == 1
