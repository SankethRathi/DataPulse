
import json
import os
from pathlib import Path
from uuid import uuid4

import pandas as pd


def publish_batch(
    df: pd.DataFrame,
    batch_id: str,
    output_dir: str = "data/processed",
) -> dict:
    """Safely publish transformed data and its metadata."""

    if df.empty:
        raise ValueError("Cannot publish an empty dataset")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    safe_batch_id = "".join(
        character if character.isalnum() or character in "-_"
        else "_"
        for character in batch_id
    )

    csv_path = output_path / f"{safe_batch_id}.csv"
    manifest_path = output_path / f"{safe_batch_id}_manifest.json"

    if csv_path.exists() or manifest_path.exists():
        raise FileExistsError(
            f"Batch {batch_id} has already been published"
        )

    token = uuid4().hex

    temp_csv = output_path / f".{safe_batch_id}_{token}.tmp.csv"
    temp_manifest = output_path / f".{safe_batch_id}_{token}.tmp.json"

    csv_published = False

    try:
        # Write CSV to a temporary file first.
        df.to_csv(temp_csv, index=False)

        manifest = {
            "batch_id": batch_id,
            "published_file": str(csv_path),
            "record_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "status": "PUBLISHED",
        }

        # Write manifest to a temporary file.
        with temp_manifest.open("w", encoding="utf-8") as file:
            json.dump(manifest, file, indent=4)

        # Move completed files into their final locations.
        os.replace(temp_csv, csv_path)
        csv_published = True

        os.replace(temp_manifest, manifest_path)

        return manifest

    except Exception:
        # Roll back files created by this publication attempt.
        if csv_published:
            csv_path.unlink(missing_ok=True)

        manifest_path.unlink(missing_ok=True)

        raise

    finally:
        temp_csv.unlink(missing_ok=True)
        temp_manifest.unlink(missing_ok=True)
