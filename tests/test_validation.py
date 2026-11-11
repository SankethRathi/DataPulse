
import pandas as pd
import pytest

from datapulse.validation.validator import validate_batch


@pytest.fixture
def sample_data():
    return pd.DataFrame({
        "order_id": [1, 2, 3, 4],
        "customer_id": [101, 102, 103, 104],
        "product_id": [201, 202, 203, 204],
        "order_amount": [500, 600, 700, 800],
        "quantity": [1, 2, 3, 4],
        "order_status": ["completed", "pending", "completed", "cancelled"],
        "order_timestamp": [
            "2026-11-01",
            "2026-11-02",
            "2026-11-03",
            "2026-11-04",
        ],
    })


def test_all_records_valid(sample_data):
    valid, rejected = validate_batch(sample_data)

    assert len(valid) == 4
    assert len(rejected) == 0


def test_duplicate_order_rejected(sample_data):
    sample_data.loc[3, "order_id"] = 1

    valid, rejected = validate_batch(sample_data)

    assert len(rejected) == 1
    assert "Duplicate order ID" in rejected.iloc[0]["rejection_reason"]


def test_negative_amount_rejected(sample_data):
    sample_data.loc[0, "order_amount"] = -100

    valid, rejected = validate_batch(sample_data)

    assert len(rejected) == 1
    assert "Invalid order amount" in rejected.iloc[0]["rejection_reason"]


def test_invalid_quantity_rejected(sample_data):
    sample_data.loc[0, "quantity"] = 0

    valid, rejected = validate_batch(sample_data)

    assert len(rejected) == 1
    assert "Invalid quantity" in rejected.iloc[0]["rejection_reason"]


def test_invalid_timestamp_rejected(sample_data):
    sample_data.loc[0, "order_timestamp"] = "invalid-date"

    valid, rejected = validate_batch(sample_data)

    assert len(rejected) == 1
    assert "Invalid timestamp" in rejected.iloc[0]["rejection_reason"]


def test_missing_required_column_rejected_by_schema(sample_data):
    sample_data = sample_data.drop(columns=["order_id"])

    with pytest.raises(ValueError):
        validate_batch(sample_data)
