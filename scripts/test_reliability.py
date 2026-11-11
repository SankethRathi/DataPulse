
from pathlib import Path
import sys
from uuid import uuid4
import tempfile

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from datapulse.pipeline import run_pipeline
import datapulse.transformation.publisher as publisher_module


RAW_DIR = ROOT / "data" / "raw"
SOURCE_PATH = RAW_DIR / "incoming_normal.csv"
BASELINE_PATH = ROOT / "reports" / "baseline.json"


def test_idempotency_and_modified_file():
    print("\nTEST 1: IDEMPOTENCY AND MODIFIED FILE")

    token = uuid4().hex[:8]
    test_file = RAW_DIR / f"reliability_{token}.csv"

    try:
        df = pd.read_csv(SOURCE_PATH)
        df.loc[0, "order_id"] = f"RELIABILITY_{token}"
        df.to_csv(test_file, index=False)

        # First execution
        first = run_pipeline(
            str(test_file),
            str(BASELINE_PATH),
        )

        assert first["pipeline_status"] in (
            "COMPLETED",
            "COMPLETED_WITH_REJECTIONS",
        ), f"Unexpected first status: {first['pipeline_status']}"

        # Second execution: same content
        second = run_pipeline(
            str(test_file),
            str(BASELINE_PATH),
        )

        assert second["pipeline_status"] == "SKIPPED_DUPLICATE", (
            f"Expected duplicate skip, got {second['pipeline_status']}"
        )

        print("PASS: Identical file skipped on second execution")

        # Modify the file content
        df.loc[1, "quantity"] = df.loc[1, "quantity"] + 1
        df.to_csv(test_file, index=False)

        # Third execution: modified content
        third = run_pipeline(
            str(test_file),
            str(BASELINE_PATH),
        )

        assert third["pipeline_status"] in (
            "COMPLETED",
            "COMPLETED_WITH_REJECTIONS",
        ), f"Modified file not processed: {third['pipeline_status']}"

        print("PASS: Modified file processed as a new batch")

    finally:
        test_file.unlink(missing_ok=True)


def test_publishing_failure_rollback():
    print("\nTEST 2: PUBLISHING FAILURE ROLLBACK")

    token = uuid4().hex[:8]

    df = pd.DataFrame({
        "order_id": [f"TEST_{token}"],
        "amount": [100],
    })

    real_replace = publisher_module.os.replace

    with tempfile.TemporaryDirectory() as temp_dir:

        output_dir = Path(temp_dir)
        batch_id = f"rollback_{token}"

        def failing_replace(source, destination):
            destination = Path(destination)

            if destination.name.endswith("_manifest.json"):
                raise OSError("Simulated manifest publishing failure")

            return real_replace(source, destination)

        publisher_module.os.replace = failing_replace

        try:
            try:
                publisher_module.publish_batch(
                    df,
                    batch_id,
                    output_dir=str(output_dir),
                )

                raise AssertionError(
                    "Expected publishing failure did not occur"
                )

            except OSError as exc:
                if "Simulated manifest" not in str(exc):
                    raise

        finally:
            publisher_module.os.replace = real_replace

        csv_path = output_dir / f"{batch_id}.csv"
        manifest_path = output_dir / f"{batch_id}_manifest.json"

        assert not csv_path.exists(), "Partial CSV was left behind"
        assert not manifest_path.exists(), "Partial manifest was left behind"

        remaining_files = list(output_dir.iterdir())

        assert not remaining_files, (
            f"Temporary files were left behind: {remaining_files}"
        )

        print("PASS: Failed publication rolled back all files")


def main():
    print("\nDATAPULSE RELIABILITY TESTS")
    print("=" * 60)

    if not SOURCE_PATH.exists():
        raise FileNotFoundError(SOURCE_PATH)

    if not BASELINE_PATH.exists():
        raise FileNotFoundError(BASELINE_PATH)

    test_idempotency_and_modified_file()
    test_publishing_failure_rollback()

    print("\n" + "=" * 60)
    print("RELIABILITY TEST SUMMARY")
    print("=" * 60)
    print("PASS: Idempotency")
    print("PASS: Modified file processing")
    print("PASS: Publishing failure rollback")
    print("TOTAL: 3/3 PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
