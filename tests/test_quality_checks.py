
import pandas as pd

from datapulse.validation.quality_checks import run_quality_checks


def test_invalid_order_status_detection():
    df = pd.DataFrame({
        "order_status": ["completed", "pending", "unknown"]
    })

    result = run_quality_checks(df)

    assert result["metrics"]["invalid_status_count"] == 1
    assert any(
        alert["metric"] == "invalid_order_status"
        for alert in result["alerts"]
    )


def test_future_timestamp_detection():
    df = pd.DataFrame({
        "order_timestamp": [
            "2099-01-01 10:00:00",
            "2026-01-01 10:00:00",
        ]
    })

    result = run_quality_checks(df)

    assert result["metrics"]["future_timestamp_count"] == 1


def test_amount_outlier_detection():
    df = pd.DataFrame({
        "order_amount": [
            100, 110, 120, 130, 140, 150, 160, 10000
        ]
    })

    result = run_quality_checks(df)

    assert result["metrics"]["amount_outlier_count"] == 1


def test_normal_data_has_no_quality_alerts():
    df = pd.DataFrame({
        "order_status": ["completed", "pending"],
        "order_timestamp": [
            "2026-01-01 10:00:00",
            "2026-01-02 10:00:00",
        ],
        "order_amount": [100, 200],
    })

    result = run_quality_checks(df)

    assert result["alert_count"] == 0


def test_empty_data():
    result = run_quality_checks(pd.DataFrame())

    assert result["status"] == "NO_DATA"
    assert result["alert_count"] == 0
