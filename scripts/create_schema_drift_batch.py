
from pathlib import Path
import pandas as pd


source = Path("data/raw/incoming_normal.csv")
destination = Path("data/raw/incoming_schema_drift.csv")

df = pd.read_csv(source)

# Introduce a new column that does not exist in the baseline.
df["customer_email"] = [
    f"customer{i}@example.com"
    for i in range(len(df))
]

destination.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(destination, index=False)

print("Schema drift test batch created!")
print("File:", destination)
print("Rows:", len(df))
print("Columns:", list(df.columns))
