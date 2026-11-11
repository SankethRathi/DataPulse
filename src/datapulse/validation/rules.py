
import pandas as pd


REQUIRED_FIELDS = [
    "order_id",
    "customer_id",
    "product_id",
    "order_amount",
    "quantity",
    "order_status",
    "order_timestamp",
]


def check_missing_values(df: pd.DataFrame) -> pd.Series:
    """Identify records with missing required fields."""
    return df[REQUIRED_FIELDS].isna().any(axis=1)


def check_duplicate_orders(df: pd.DataFrame) -> pd.Series:
    """Identify duplicate order IDs, keeping the first occurrence."""
    return df["order_id"].duplicated(keep="first")


def check_invalid_amounts(df: pd.DataFrame) -> pd.Series:
    """Identify missing, non-numeric, or negative order amounts."""
    amount = pd.to_numeric(df["order_amount"], errors="coerce")
    return amount.isna() | (amount < 0)


def check_invalid_quantities(df: pd.DataFrame) -> pd.Series:
    """Identify missing, non-numeric, or non-positive quantities."""
    quantity = pd.to_numeric(df["quantity"], errors="coerce")
    return quantity.isna() | (quantity <= 0)


def check_invalid_timestamps(df):
    timestamps = pd.to_datetime(
        df["order_timestamp"],
        errors="coerce",
        utc=True,
        format="mixed",
    )
    return timestamps.isna()
