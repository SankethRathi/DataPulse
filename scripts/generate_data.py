
from pathlib import Path
import argparse

import numpy as np
import pandas as pd


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"

# Fixed seed makes data reproducible
RANDOM_SEED = 42


def generate_orders(
    number_of_rows: int,
    batch_date: str,
    seed: int
) -> pd.DataFrame:
    """
    Generate a synthetic e-commerce orders batch.
    """

    rng = np.random.default_rng(seed)

    order_date = pd.Timestamp(batch_date)

    timestamps = (
        order_date
        + pd.to_timedelta(
            rng.integers(0, 24 * 60 * 60, number_of_rows),
            unit="s"
        )
    )

    data = {
        "order_id": [
            f"ORD{order_date:%Y%m%d}{i:07d}"
            for i in range(1, number_of_rows + 1)
        ],
        "customer_id": [
            f"CUST{value:05d}"
            for value in rng.integers(1, 5001, number_of_rows)
        ],
        "product_id": [
            f"PROD{value:04d}"
            for value in rng.integers(1, 501, number_of_rows)
        ],
        "order_amount": np.round(
            rng.gamma(shape=3.0, scale=300.0, size=number_of_rows),
            2
        ),
        "quantity": rng.integers(1, 6, number_of_rows),
        "order_status": rng.choice(
            ["completed", "pending", "cancelled"],
            size=number_of_rows,
            p=[0.75, 0.15, 0.10]
        ),
        "order_timestamp": timestamps
    }

    return pd.DataFrame(data)


def save_batch(
    dataframe: pd.DataFrame,
    filename: str
) -> None:
    """Save a generated batch as a CSV file."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / filename

    dataframe.to_csv(output_path, index=False)

    print(f"Created: {filename} | Rows: {len(dataframe)}")


def create_batches(number_of_rows: int) -> None:
    """Create historical, normal and anomalous batches."""

    manifest = []

    # Three historical normal batches
    historical_dates = [
        "2026-11-01",
        "2026-11-02",
        "2026-11-03"
    ]

    for index, batch_date in enumerate(historical_dates):
        batch = generate_orders(
            number_of_rows,
            batch_date,
            RANDOM_SEED + index
        )

        filename = f"historical_batch_{index + 1}.csv"
        save_batch(batch, filename)

        manifest.append({
            "filename": filename,
            "scenario": "normal",
            "description": "Historical baseline batch"
        })

    # Normal incoming batch
    normal = generate_orders(
        number_of_rows,
        "2026-11-04",
        RANDOM_SEED + 10
    )

    save_batch(normal, "incoming_normal.csv")

    manifest.append({
        "filename": "incoming_normal.csv",
        "scenario": "normal",
        "description": "Normal incoming batch"
    })

    # Scenario 1: Missing customer IDs
    missing = generate_orders(
        number_of_rows,
        "2026-11-05",
        RANDOM_SEED + 20
    )

    rng = np.random.default_rng(RANDOM_SEED + 21)
    missing_indices = rng.choice(
        missing.index,
        size=int(number_of_rows * 0.20),
        replace=False
    )

    missing.loc[missing_indices, "customer_id"] = None

    save_batch(missing, "incoming_missing_values.csv")

    manifest.append({
        "filename": "incoming_missing_values.csv",
        "scenario": "missing_values",
        "description": "20% of customer IDs are missing"
    })

    # Scenario 2: Duplicate order IDs
    duplicates = generate_orders(
        number_of_rows,
        "2026-11-06",
        RANDOM_SEED + 30
    )

    duplicate_rows = duplicates.sample(
        n=max(1, int(number_of_rows * 0.05)),
        random_state=RANDOM_SEED
    )

    duplicates = pd.concat(
        [duplicates, duplicate_rows],
        ignore_index=True
    )

    save_batch(duplicates, "incoming_duplicates.csv")

    manifest.append({
        "filename": "incoming_duplicates.csv",
        "scenario": "duplicates",
        "description": "5% additional duplicate records"
    })

    # Scenario 3: Shift in order amount distribution
    shifted = generate_orders(
        number_of_rows,
        "2026-11-07",
        RANDOM_SEED + 40
    )

    shifted["order_amount"] = np.round(
        shifted["order_amount"] * 3,
        2
    )

    save_batch(shifted, "incoming_distribution_shift.csv")

    manifest.append({
        "filename": "incoming_distribution_shift.csv",
        "scenario": "distribution_shift",
        "description": "Order amounts increased by a factor of three"
    })

    # Scenario 4: Late-arriving records
    late = generate_orders(
        number_of_rows,
        "2026-11-04",
        RANDOM_SEED + 50
    )

    # These records arrive in a later batch,
    # but their actual event timestamps are older.
    late["order_timestamp"] = (
        late["order_timestamp"] - pd.Timedelta(days=3)
    )

    save_batch(late, "incoming_late_records.csv")

    manifest.append({
        "filename": "incoming_late_records.csv",
        "scenario": "late_records",
        "description": "Records arrive with older event timestamps"
    })

    # Store labels separately from the actual batch data.
    manifest_df = pd.DataFrame(manifest)

    manifest_df.to_csv(
        OUTPUT_DIR / "scenario_manifest.csv",
        index=False
    )

    print("\nAll batches generated successfully!")
    print(f"Total scenarios: {len(manifest_df)}")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate reproducible DataPulse test data"
    )

    parser.add_argument(
        "--rows",
        type=int,
        default=1000,
        help="Number of rows per generated batch"
    )

    args = parser.parse_args()

    if args.rows < 1:
        parser.error("--rows must be greater than zero")

    create_batches(args.rows)
