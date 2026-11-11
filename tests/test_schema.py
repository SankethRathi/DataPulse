
import pandas as pd

from datapulse.profiling.schema import (
    profile_schema,
    compare_schemas,
)


def test_new_column_detection():
    baseline = {
        "order_id": "string",
        "order_amount": "numeric",
    }

    incoming = {
        "order_id": "string",
        "order_amount": "numeric",
        "customer_email": "string",
    }

    result = compare_schemas(incoming, baseline)

    assert result["new_columns"] == ["customer_email"]
    assert result["missing_columns"] == []
    assert result["passed"] is False


def test_missing_column_detection():
    baseline = {
        "order_id": "string",
        "order_amount": "numeric",
    }

    incoming = {
        "order_id": "string",
    }

    result = compare_schemas(incoming, baseline)

    assert result["missing_columns"] == ["order_amount"]
    assert result["new_columns"] == []


def test_data_type_change_detection():
    baseline = {
        "order_id": "string",
        "order_amount": "numeric",
    }

    incoming = {
        "order_id": "string",
        "order_amount": "string",
    }

    result = compare_schemas(incoming, baseline)

    assert len(result["type_changes"]) == 1
    assert result["type_changes"][0]["column"] == "order_amount"
    assert result["type_changes"][0]["expected_type"] == "numeric"
    assert result["type_changes"][0]["observed_type"] == "string"


def test_matching_schema():
    schema = {
        "order_id": "string",
        "order_amount": "numeric",
    }

    result = compare_schemas(schema, schema)

    assert result["passed"] is True
    assert result["new_columns"] == []
    assert result["missing_columns"] == []
    assert result["type_changes"] == []


def test_profile_schema():
    df = pd.DataFrame({
        "order_id": ["O1", "O2"],
        "order_amount": [100.0, 200.0],
        "quantity": [1, 2],
    })

    schema = profile_schema(df)

    assert schema["order_id"] == "string"
    assert schema["order_amount"] == "numeric"
    assert schema["quantity"] == "numeric"
