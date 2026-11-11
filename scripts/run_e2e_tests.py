
from pathlib import Path
import sys
from uuid import uuid4

import pandas as pd

# Make the src package available when running this script directly.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from datapulse.pipeline import run_pipeline


RAW_DIR = ROOT / "data" / "raw"
BASELINE_PATH = ROOT / "reports" / "baseline.json"
SOURCE_PATH = RAW_DIR / "incoming_normal.csv"

TOKEN = uuid4().hex[:8]

results = []


def create_batch(name, modify):
    """Create an independent test batch from the normal dataset."""

    df = pd.read_csv(SOURCE_PATH)

    # Ensure every test file has a unique content hash.
    df.loc[0, "order_id"] = f"E2E_{name}_{TOKEN}"

    df = modify(df)

    path = RAW_DIR / f"e2e_{name}_{TOKEN}.csv"
    df.to_csv(path, index=False)

    return path


def check_scenario(name, modify, verify):
    """Execute the real pipeline and verify its report."""

    print(f"\n{'=' * 65}")
    print(f"TESTING: {name.upper()}")
    print("=" * 65)

    try:
        batch_path = create_batch(name, modify)

        report = run_pipeline(
            batch_path=str(batch_path),
            baseline_path=str(BASELINE_PATH),
        )

        verify(report)

        results.append((name, "PASS", "Expected behaviour verified"))
        print(f"\nRESULT: PASS - {name}")

    except Exception as exc:
        results.append((name, "FAIL", str(exc)))
        print(f"\nRESULT: FAIL - {name}: {exc}")


def normal_batch(df):
    return df


def missing_values_batch(df):
    df.loc[:29, "customer_id"] = None
    return df


def duplicate_batch(df):
    duplicates = df.iloc[:50].copy()
    return pd.concat([df, duplicates], ignore_index=True)


def distribution_shift_batch(df):
    df["order_amount"] = df["order_amount"] * 3
    return df


def late_records_batch(df):
    df["order_timestamp"] = "2026-09-01 10:00:00"
    return df


def new_column_batch(df):
    df["e2e_source"] = "integration_test"
    return df


def missing_column_batch(df):
    return df.drop(columns=["customer_id"])


def type_change_batch(df):
    df["order_amount"] = "not-a-number"
    return df


def verify_normal(report):
    assert report["pipeline_status"] == "COMPLETED"
    assert report["reconciliation"]["passed"] is True
    assert report["publishing"]["status"] == "PUBLISHED"


def verify_missing_values(report):
    assert report["pipeline_status"] == "COMPLETED_WITH_REJECTIONS"
    assert report["validation"]["rejected_records"] > 0
    assert report["reconciliation"]["passed"] is True
    assert report["publishing"]["status"] == "PUBLISHED"


def verify_duplicates(report):
    assert report["pipeline_status"] == "COMPLETED_WITH_REJECTIONS"
    assert report["validation"]["rejected_records"] >= 50
    assert report["reconciliation"]["passed"] is True
    assert report["publishing"]["status"] == "PUBLISHED"


def verify_distribution_shift(report):
    assert report["pipeline_status"] == "COMPLETED"

    metrics = {
        alert["metric"]
        for alert in report["alerts"]
    }

    assert (
        "order_amount_mean" in metrics
        or "order_amount_median" in metrics
    ), "Numeric distribution shift was not detected"


def verify_late_records(report):
    assert report["pipeline_status"] == "COMPLETED"

    assert any(
        alert["metric"] == "data_freshness"
        for alert in report["alerts"]
    ), "Freshness alert was not generated"


def verify_new_column(report):
    assert report["pipeline_status"] == "COMPLETED"

    assert "e2e_source" in report["schema_comparison"]["new_columns"]

    schema_alerts = [
        alert for alert in report["alerts"]
        if alert["metric"] == "schema_new_column"
    ]

    assert len(schema_alerts) == 1, (
        f"Expected one new-column alert, got {len(schema_alerts)}"
    )


def verify_missing_column(report):
    assert report["pipeline_status"] == "FAILED"

    assert "customer_id" in report["schema_comparison"]["missing_columns"]

    assert any(
        alert["metric"] == "schema_missing_column"
        and alert["severity"] == "HIGH"
        for alert in report["alerts"]
    )


def verify_type_change(report):
    assert report["pipeline_status"] == "FAILED_VALIDATION"

    assert any(
        change["column"] == "order_amount"
        for change in report["schema_comparison"]["type_changes"]
    ), "Data type change was not detected"

    assert report["validation"]["valid_records"] == 0
    assert report["validation"]["rejected_records"] > 0
    assert report["reconciliation"]["passed"] is True

    assert report["publishing"] is None, (
        "Invalid records were unexpectedly published"
    )


def main():
    print("\nDATAPULSE END-TO-END TEST SUITE")
    print("Using:", SOURCE_PATH)
    print("Baseline:", BASELINE_PATH)

    if not SOURCE_PATH.exists():
        raise FileNotFoundError(SOURCE_PATH)

    if not BASELINE_PATH.exists():
        raise FileNotFoundError(BASELINE_PATH)

    scenarios = [
        ("normal", normal_batch, verify_normal),
        ("missing_values", missing_values_batch, verify_missing_values),
        ("duplicates", duplicate_batch, verify_duplicates),
        ("distribution_shift", distribution_shift_batch, verify_distribution_shift),
        ("late_records", late_records_batch, verify_late_records),
        ("new_column", new_column_batch, verify_new_column),
        ("missing_column", missing_column_batch, verify_missing_column),
        ("type_change", type_change_batch, verify_type_change),
    ]

    for name, modify, verify in scenarios:
        check_scenario(name, modify, verify)

    print("\n" + "=" * 65)
    print("DATAPULSE END-TO-END TEST SUMMARY")
    print("=" * 65)

    for name, status, details in results:
        print(f"{status:5} | {name:22} | {details}")

    passed = sum(1 for _, status, _ in results if status == "PASS")
    failed = len(results) - passed

    print("-" * 65)
    print(f"TOTAL: {len(results)} | PASSED: {passed} | FAILED: {failed}")
    print("=" * 65)

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
