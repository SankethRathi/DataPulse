
from datetime import datetime, timezone

import pandas as pd


MAX_CATEGORY_VALUES = 10


def profile_batch(df: pd.DataFrame) -> dict:
    """Generate a concise data quality profile."""

    if df.empty:
        raise ValueError("Cannot profile an empty batch")

    profile = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": {},
    }

    for column in df.columns:
        series = df[column]

        column_profile = {
            "null_count": int(series.isna().sum()),
            "null_percentage": round(series.isna().mean() * 100, 2),
            "distinct_count": int(series.nunique()),
        }

        if pd.api.types.is_numeric_dtype(series):
            valid = series.dropna()

            column_profile["statistics"] = {
                "mean": round(float(valid.mean()), 2) if not valid.empty else None,
                "median": round(float(valid.median()), 2) if not valid.empty else None,
                "min": float(valid.min()) if not valid.empty else None,
                "max": float(valid.max()) if not valid.empty else None,
                "std": round(float(valid.std()), 2) if not valid.empty else None,
            }

        elif column != "order_timestamp":
            # Avoid enormous distributions for ID-like columns.
            if series.nunique() <= MAX_CATEGORY_VALUES:
                counts = series.value_counts(normalize=True)

                column_profile["distribution"] = {
                    str(key): round(float(value * 100), 2)
                    for key, value in counts.head(MAX_CATEGORY_VALUES).items()
                }
            else:
                column_profile["distribution"] = (
                    "Skipped: high-cardinality column"
                )

        profile["columns"][column] = column_profile

    if "order_timestamp" in df.columns:
        timestamps = pd.to_datetime(
            df["order_timestamp"],
            errors="coerce",
            utc=True
        )

        valid = timestamps.dropna()

        profile["freshness"] = {
            "latest_event_timestamp": (
                valid.max().isoformat() if not valid.empty else None
            ),
            "age_hours_at_profile_time": (
                round(
                    (datetime.now(timezone.utc) - valid.max()).total_seconds() / 3600,
                    2
                )
                if not valid.empty else None
            ),
            "invalid_timestamp_count": int(timestamps.isna().sum()),
        }

    return profile
