
import pandas as pd


ALLOWED_ORDER_STATUSES = {
    "completed",
    "pending",
    "cancelled",
}


def run_quality_checks(df: pd.DataFrame) -> dict:
    """Run additional business-level data quality checks."""

    alerts = []
    metrics = {}

    if df.empty:
        return {
            "status": "NO_DATA",
            "metrics": {},
            "alerts": [],
            "alert_count": 0,
        }

    # 1. Invalid order statuses
    if "order_status" in df.columns:
        statuses = df["order_status"].astype("string").str.strip().str.lower()

        invalid_statuses = statuses[
            statuses.notna()
            & ~statuses.isin(ALLOWED_ORDER_STATUSES)
        ]

        metrics["invalid_status_count"] = len(invalid_statuses)

        if len(invalid_statuses) > 0:
            examples = sorted(invalid_statuses.unique().tolist())[:10]

            alerts.append({
                "metric": "invalid_order_status",
                "severity": "HIGH",
                "observed": len(invalid_statuses),
                "expected": 0,
                "message": (
                    f"{len(invalid_statuses)} records contain "
                    f"unsupported order statuses: {examples}."
                ),
            })

    # 2. Future order timestamps
    if "order_timestamp" in df.columns:
        timestamps = pd.to_datetime(
            df["order_timestamp"],
            errors="coerce",
            utc=True,
            format="mixed",
        )

        future_count = int(
            (timestamps > pd.Timestamp.now(tz="UTC")).sum()
        )

        metrics["future_timestamp_count"] = future_count

        if future_count > 0:
            alerts.append({
                "metric": "future_order_timestamps",
                "severity": "MEDIUM",
                "observed": future_count,
                "expected": 0,
                "message": (
                    f"{future_count} orders have timestamps "
                    "in the future."
                ),
            })

    # 3. Extreme order amounts using the IQR method
    if "order_amount" in df.columns:
        amounts = pd.to_numeric(
            df["order_amount"],
            errors="coerce",
        ).dropna()

        if len(amounts) >= 4:
            q1 = float(amounts.quantile(0.25))
            q3 = float(amounts.quantile(0.75))
            iqr = q3 - q1

            upper_limit = q3 + (1.5 * iqr)
            lower_limit = q1 - (1.5 * iqr)

            outlier_count = int(
                ((amounts < lower_limit) | (amounts > upper_limit)).sum()
            )

            metrics["amount_outlier_count"] = outlier_count
            metrics["amount_iqr_lower_limit"] = round(lower_limit, 2)
            metrics["amount_iqr_upper_limit"] = round(upper_limit, 2)

            if outlier_count > 0:
                alerts.append({
                    "metric": "order_amount_outliers",
                    "severity": "MEDIUM",
                    "observed": outlier_count,
                    "expected": 0,
                    "message": (
                        f"{outlier_count} order amounts fall outside "
                        f"the IQR range ({lower_limit:.2f}, "
                        f"{upper_limit:.2f})."
                    ),
                })

    return {
        "status": "COMPLETED",
        "metrics": metrics,
        "alerts": alerts,
        "alert_count": len(alerts),
    }
