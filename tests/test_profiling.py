
import pandas as pd
import pytest

from datapulse.profiling.profiler import profile_batch


def test_profile_row_count():
    df = pd.DataFrame({
        "customer_id": ["C1", "C2", "C3"]
    })

    result = profile_batch(df)

    assert result["row_count"] == 3


def test_profile_null_percentage():
    df = pd.DataFrame({
        "customer_id": ["C1", None, "C3", None]
    })

    result = profile_batch(df)

    assert result["columns"]["customer_id"]["null_percentage"] == 50.0


def test_profile_numeric_statistics():
    df = pd.DataFrame({
        "order_amount": [100, 200, 300]
    })

    result = profile_batch(df)

    stats = result["columns"]["order_amount"]["statistics"]

    assert stats["mean"] == 200
    assert stats["min"] == 100
    assert stats["max"] == 300


def test_empty_batch():
    df = pd.DataFrame()

    with pytest.raises(ValueError):
        profile_batch(df)
