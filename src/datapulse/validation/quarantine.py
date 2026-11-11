
from pathlib import Path
import pandas as pd


def save_quarantine(
    rejected_df: pd.DataFrame,
    output_path: str = "data/quarantine/rejected_records.csv",
) -> str:
    """Save rejected records for investigation."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rejected_df.empty:
        if "rejection_reason" not in rejected_df.columns:
            raise ValueError("Rejected records must contain rejection_reason")

        rejected_df.to_csv(path, index=False)

    return str(path)
