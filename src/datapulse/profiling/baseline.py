
import json
from pathlib import Path

import pandas as pd

from datapulse.ingestion.loader import load_batch
from datapulse.profiling.profiler import profile_batch
from datapulse.profiling.schema import profile_schema


def build_baseline(batch_paths: list[str]) -> dict:
    if not batch_paths:
        raise ValueError("At least one historical batch is required")

    profiles = []
    schemas = []

    for path in batch_paths:
        result = load_batch(path)
        df = result["data"]

        if df.empty:
            raise ValueError(f"Historical batch is empty: {path}")

        profiles.append(profile_batch(df))
        schemas.append(profile_schema(df))

    row_counts = [p["row_count"] for p in profiles]

    amount_means = [
        p["columns"]["order_amount"]["statistics"]["mean"]
        for p in profiles
    ]

    amount_medians = [
        p["columns"]["order_amount"]["statistics"]["median"]
        for p in profiles
    ]

    null_percentages = {
        column: [
            p["columns"][column]["null_percentage"]
            for p in profiles
        ]
        for column in profiles[0]["columns"]
    }

    all_statuses = set()

    for profile in profiles:
        all_statuses.update(
            profile["columns"]["order_status"]
            .get("distribution", {})
            .keys()
        )

    status_distributions = {
        status: [
            p["columns"]["order_status"]
            .get("distribution", {})
            .get(status, 0)
            for p in profiles
        ]
        for status in all_statuses
    }

    timestamps = [
        p.get("freshness", {}).get("latest_event_timestamp")
        for p in profiles
        if p.get("freshness", {}).get("latest_event_timestamp")
    ]

    latest_historical_timestamp = (
        max(pd.to_datetime(timestamps, utc=True)).isoformat()
        if timestamps else None
    )

    # Use the first historical batch as the canonical schema.
    canonical_schema = schemas[0]

    # Historical batches should have a consistent schema.
    for index, schema in enumerate(schemas[1:], start=2):
        comparison = {
            "new_columns": sorted(set(schema) - set(canonical_schema)),
            "missing_columns": sorted(set(canonical_schema) - set(schema)),
            "type_changes": [
                column
                for column in set(schema) & set(canonical_schema)
                if schema[column] != canonical_schema[column]
            ],
        }

        if (
            comparison["new_columns"]
            or comparison["missing_columns"]
            or comparison["type_changes"]
        ):
            raise ValueError(
                f"Historical schema mismatch in batch {index}: "
                f"{comparison}"
            )

    baseline = {
        "baseline_version": 3,
        "historical_batch_count": len(profiles),

        "schema": canonical_schema,

        "row_count": {
            "median": float(pd.Series(row_counts).median()),
            "min": int(min(row_counts)),
            "max": int(max(row_counts)),
        },

        "order_amount": {
            "mean": round(
                float(pd.Series(amount_means).median()), 2
            ),
            "median": round(
                float(pd.Series(amount_medians).median()), 2
            ),
        },

        "null_percentages": {
            column: round(
                float(pd.Series(values).median()), 2
            )
            for column, values in null_percentages.items()
        },

        "order_status_distribution": {
            status: round(
                float(pd.Series(values).median()), 2
            )
            for status, values in status_distributions.items()
        },

        "latest_historical_event_timestamp": (
            latest_historical_timestamp
        ),
    }

    return baseline


def save_baseline(baseline: dict, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(baseline, file, indent=4)
