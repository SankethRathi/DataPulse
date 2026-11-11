
import pandas as pd

from datapulse.profiling.schema import compare_schemas


VOLUME_CHANGE_THRESHOLD = 20.0
NULL_INCREASE_THRESHOLD = 5.0
AMOUNT_CHANGE_THRESHOLD = 30.0
STATUS_CHANGE_THRESHOLD = 10.0
FRESHNESS_LAG_HOURS = 24.0


def create_alert(metric, severity, observed, expected, message):
    return {
        "metric": metric,
        "severity": severity,
        "observed": observed,
        "expected": expected,
        "message": message,
    }


def detect_anomalies(
    profile: dict,
    baseline: dict,
    check_schema: bool = True,
) -> list[dict]:

    alerts = []

    # 1. Schema drift detection
    # Can be disabled when schema comparison has already
    # been performed earlier in the pipeline.
    if check_schema:
        incoming_schema = profile.get("schema", {})
        baseline_schema = baseline.get("schema", {})

        if baseline_schema:
            schema_result = compare_schemas(
                incoming_schema,
                baseline_schema,
            )

            for column in schema_result["new_columns"]:
                alerts.append(create_alert(
                    "schema_new_column",
                    "MEDIUM",
                    column,
                    None,
                    f"Unexpected column '{column}' was introduced.",
                ))

            for column in schema_result["missing_columns"]:
                alerts.append(create_alert(
                    "schema_missing_column",
                    "HIGH",
                    None,
                    column,
                    f"Expected column '{column}' is missing.",
                ))

            for change in schema_result["type_changes"]:
                alerts.append(create_alert(
                    "schema_type_change",
                    "HIGH",
                    change["observed_type"],
                    change["expected_type"],
                    (
                        f"Column '{change['column']}' changed type "
                        f"from '{change['expected_type']}' to "
                        f"'{change['observed_type']}'."
                    ),
                ))

    # 2. Volume anomaly
    observed_rows = profile["row_count"]
    expected_rows = baseline["row_count"]["median"]

    if expected_rows:
        volume_change = (
            abs(observed_rows - expected_rows)
            / expected_rows
            * 100
        )

        if volume_change > VOLUME_CHANGE_THRESHOLD:
            alerts.append(create_alert(
                "row_count",
                "HIGH",
                observed_rows,
                expected_rows,
                (
                    f"Batch volume changed by {volume_change:.2f}% "
                    f"from the historical median of {expected_rows} rows."
                ),
            ))

    # 3. Null percentage anomaly
    for column, details in profile["columns"].items():
        observed_nulls = details["null_percentage"]
        expected_nulls = baseline["null_percentages"].get(column, 0)

        increase = observed_nulls - expected_nulls

        if increase > NULL_INCREASE_THRESHOLD:
            alerts.append(create_alert(
                f"null_percentage:{column}",
                "HIGH",
                observed_nulls,
                expected_nulls,
                (
                    f"Null percentage in '{column}' increased by "
                    f"{increase:.2f} percentage points."
                ),
            ))

    # 4. Numeric distribution anomaly
    amount_stats = profile["columns"]["order_amount"]["statistics"]

    for metric in ["mean", "median"]:
        observed = amount_stats.get(metric)
        expected = baseline["order_amount"].get(metric)

        if observed is None or expected is None or expected == 0:
            continue

        change = (
            abs(observed - expected) / abs(expected) * 100
        )

        if change > AMOUNT_CHANGE_THRESHOLD:
            alerts.append(create_alert(
                f"order_amount_{metric}",
                "HIGH",
                observed,
                expected,
                (
                    f"Order amount {metric} changed by {change:.2f}% "
                    f"from its historical baseline."
                ),
            ))

    # 5. Categorical distribution anomaly
    observed_status = (
        profile["columns"]["order_status"].get("distribution", {})
    )

    expected_status = baseline["order_status_distribution"]

    all_statuses = set(observed_status) | set(expected_status)

    for status in all_statuses:
        observed = observed_status.get(status, 0)
        expected = expected_status.get(status, 0)

        difference = abs(observed - expected)

        if difference > STATUS_CHANGE_THRESHOLD:
            alerts.append(create_alert(
                f"order_status_distribution:{status}",
                "MEDIUM",
                observed,
                expected,
                (
                    f"'{status}' order share changed by "
                    f"{difference:.2f} percentage points."
                ),
            ))

    # 6. Freshness anomaly
    incoming_timestamp = (
        profile.get("freshness", {}).get("latest_event_timestamp")
    )

    historical_timestamp = baseline.get(
        "latest_historical_event_timestamp"
    )

    if incoming_timestamp and historical_timestamp:
        incoming_time = pd.to_datetime(
            incoming_timestamp,
            utc=True,
        )

        historical_time = pd.to_datetime(
            historical_timestamp,
            utc=True,
        )

        lag_hours = (
            historical_time - incoming_time
        ).total_seconds() / 3600

        if lag_hours > FRESHNESS_LAG_HOURS:
            alerts.append(create_alert(
                "data_freshness",
                "HIGH",
                incoming_timestamp,
                historical_timestamp,
                (
                    f"Incoming batch's latest event is "
                    f"{lag_hours:.2f} hours older than the "
                    "latest historical event."
                ),
            ))

    # 7. Invalid timestamp anomaly
    invalid_count = (
        profile.get("freshness", {}).get(
            "invalid_timestamp_count",
            0,
        )
    )

    if invalid_count > 0:
        alerts.append(create_alert(
            "invalid_timestamps",
            "HIGH",
            invalid_count,
            0,
            f"{invalid_count} invalid timestamps were found during profiling.",
        ))

    return alerts
