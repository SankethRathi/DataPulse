
import pandas as pd
import pytest

from datapulse.transformation.transformer import transform_batch
from datapulse.transformation.publisher import publish_batch


@pytest.fixture
def sample_data():
    return pd.DataFrame({
        "order_id": [" O001 ", "O002"],
        "customer_id": [" C001 ", "C002"],
        "product_id": [" P001 ", "P002"],
        "order_amount": ["500", "600"],
        "quantity": ["2", "3"],
        "order_status": ["COMPLETED", "Pending"],
        "order_timestamp": [
            "2026-11-10 10:00:00",
            "2026-11-10 11:00:00",
        ],
    })


def test_transform_batch(sample_data):
    result = transform_batch(sample_data)

    assert result.loc[0, "order_id"] == "O001"
    assert result.loc[0, "order_status"] == "completed"
    assert result.loc[0, "order_amount"] == 500.0
    assert result.loc[0, "total_order_value"] == 1000.0
    assert str(result["order_timestamp"].dtype).startswith(
        "datetime64"
    )


def test_empty_batch_rejected():
    with pytest.raises(ValueError):
        transform_batch(pd.DataFrame())



def test_publish_batch(sample_data, monkeypatch):
    from pathlib import Path
    from uuid import uuid4

    import pytest

    transformed = transform_batch(sample_data)

    test_dir = Path("tests/test_data/published")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Unique batch ID makes the test independent of previous runs.
    batch_id = f"test-batch-{uuid4().hex}"

    manifest = publish_batch(
        transformed,
        batch_id,
        str(test_dir),
    )

    assert manifest["status"] == "PUBLISHED"
    assert manifest["record_count"] == len(transformed)

    # Verify that publishing the same batch again is rejected.
    with pytest.raises(FileExistsError):
        publish_batch(
            transformed,
            batch_id,
            str(test_dir),
        )

