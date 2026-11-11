
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import hashlib

import pandas as pd


REQUIRED_COLUMNS = {
    "order_id",
    "customer_id",
    "product_id",
    "order_amount",
    "quantity",
    "order_status",
    "order_timestamp",
}


class IngestionError(Exception):
    """Raised when a batch cannot be ingested."""


def calculate_file_hash(file_path: str | Path) -> str:
    sha256 = hashlib.sha256()

    with Path(file_path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def load_batch(
    file_path: str | Path,
    validate_schema: bool = True,
) -> dict:
    path = Path(file_path)

    if not path.exists():
        raise IngestionError(f"File not found: {path}")

    if path.suffix.lower() != ".csv":
        raise IngestionError("Only CSV files are supported")

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError as exc:
        raise IngestionError(
            "CSV file is empty or has no header"
        ) from exc
    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise IngestionError(
            f"Unable to parse CSV: {exc}"
        ) from exc

    if len(df.columns) == 0:
        raise IngestionError("CSV has no columns")

    if df.columns.duplicated().any():
        raise IngestionError("CSV contains duplicate column names")

    if validate_schema:
        missing_columns = REQUIRED_COLUMNS - set(df.columns)

        if missing_columns:
            raise IngestionError(
                f"Missing required columns: {sorted(missing_columns)}"
            )

    return {
        "data": df,
        "metadata": {
            "batch_id": str(uuid4()),
            "content_hash": calculate_file_hash(path),
            "source_file": path.name,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "row_count": len(df),
            "column_count": len(df.columns),
            "status": "INGESTED",
        },
    }
