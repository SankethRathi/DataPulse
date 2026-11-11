
from pathlib import Path

import pytest

from datapulse.ingestion.loader import load_batch, IngestionError


DATA_DIR = Path("data/raw")
TEMP_DIR = Path("tests/temp")


@pytest.fixture
def local_tmp_path():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    yield TEMP_DIR

    # Clean up temporary test files
    for file in TEMP_DIR.iterdir():
        if file.is_file():
            file.unlink()


def test_load_normal_batch():
    result = load_batch(DATA_DIR / "incoming_normal.csv")

    assert len(result["data"]) == 1000
    assert result["metadata"]["status"] == "INGESTED"
    assert result["metadata"]["row_count"] == 1000


def test_missing_file():
    with pytest.raises(IngestionError):
        load_batch(DATA_DIR / "does_not_exist.csv")


def test_missing_required_column(local_tmp_path):
    file_path = local_tmp_path / "invalid.csv"
    file_path.write_text(
        "order_id,customer_id\nORD1,CUST1",
        encoding="utf-8"
    )

    with pytest.raises(
        IngestionError,
        match="Missing required columns"
    ):
        load_batch(file_path)


def test_empty_file(local_tmp_path):
    file_path = local_tmp_path / "empty.csv"
    file_path.write_text("", encoding="utf-8")

    with pytest.raises(IngestionError):
        load_batch(file_path)
