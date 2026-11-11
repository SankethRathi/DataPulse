
from pathlib import Path

from datapulse.profiling.baseline import build_baseline, save_baseline


historical_batches = [
    "data/raw/historical_batch_1.csv",
    "data/raw/historical_batch_2.csv",
    "data/raw/historical_batch_3.csv",
]

baseline = build_baseline(historical_batches)

output_path = "reports/baseline.json"
save_baseline(baseline, output_path)

print("Baseline created successfully!")
print(f"Saved to: {output_path}")
print(baseline)
