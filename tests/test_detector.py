
import json

from datapulse.ingestion.loader import load_batch
from datapulse.profiling.profiler import profile_batch
from datapulse.detection.detector import detect_anomalies


with open("reports/baseline.json", encoding="utf-8") as file:
    baseline = json.load(file)

batch_path = "data/raw/incoming_distribution_shift.csv"

result = load_batch(batch_path)
profile = profile_batch(result["data"])

alerts = detect_anomalies(profile, baseline)

print("Batch:", batch_path)
print("Alerts detected:", len(alerts))

for alert in alerts:
    print("\n", alert["severity"], "-", alert["metric"])
    print(alert["message"])
