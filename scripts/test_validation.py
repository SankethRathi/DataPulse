
from datapulse.ingestion.loader import load_batch
from datapulse.validation.validator import validate_batch
from datapulse.validation.quarantine import save_quarantine


batch_path = "data/raw/incoming_duplicates.csv"

batch = load_batch(batch_path)

valid, rejected = validate_batch(batch["data"])

quarantine_path = save_quarantine(rejected)

print("\nVALIDATION RESULTS")
print("------------------")
print("Batch ID:", batch["metadata"]["batch_id"])
print("Total records:", len(batch["data"]))
print("Valid records:", len(valid))
print("Rejected records:", len(rejected))
print("Quarantine file:", quarantine_path)

if not rejected.empty:
    print("\nRejection reasons:")
    print(rejected["rejection_reason"].value_counts())
