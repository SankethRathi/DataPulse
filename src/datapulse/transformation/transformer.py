
import pandas as pd


def transform_batch(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize validated records."""

    if df.empty:
        raise ValueError("Cannot transform an empty batch")

    transformed = df.copy()

    # Standardize text columns
    text_columns = [
        "order_id",
        "customer_id",
        "product_id",
        "order_status",
    ]

    for column in text_columns:
        transformed[column] = (
            transformed[column]
            .astype("string")
            .str.strip()
        )

    # Standardize numeric columns
    transformed["order_amount"] = pd.to_numeric(
        transformed["order_amount"], errors="raise"
    ).astype(float)

    transformed["quantity"] = pd.to_numeric(
        transformed["quantity"], errors="raise"
    ).astype(int)

    # Standardize order status
    transformed["order_status"] = (
        transformed["order_status"].str.lower()
    )

    # Standardize timestamps to UTC
    transformed["order_timestamp"] = pd.to_datetime(
        transformed["order_timestamp"],
        errors="raise",
        utc=True,
    )

    # Add derived business column
    transformed["total_order_value"] = (
        transformed["order_amount"] * transformed["quantity"]
    ).round(2)

    return transformed
