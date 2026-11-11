
import argparse
from pathlib import Path

from datapulse.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Run the DataPulse data quality pipeline."
    )

    parser.add_argument(
        "batch_path",
        help="Path to the incoming CSV batch."
    )

    parser.add_argument(
        "--baseline",
        default="reports/baseline.json",
        help="Path to the baseline JSON file."
    )

    args = parser.parse_args()

    if not Path(args.batch_path).is_file():
        parser.error(f"Batch file not found: {args.batch_path}")

    if not Path(args.baseline).is_file():
        parser.error(f"Baseline file not found: {args.baseline}")

    run_pipeline(
        batch_path=args.batch_path,
        baseline_path=args.baseline,
    )


if __name__ == "__main__":
    main()
