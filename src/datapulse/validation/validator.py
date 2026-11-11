
from datapulse.validation.rules import (
    REQUIRED_FIELDS,
    check_missing_values,
    check_duplicate_orders,
    check_invalid_amounts,
    check_invalid_quantities,
    check_invalid_timestamps,
)


def validate_batch(df):
    """Separate valid and rejected records with rejection reasons."""

    missing_columns = set(REQUIRED_FIELDS) - set(df.columns)
    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    data = df.copy()
    rejection_reasons = [[] for _ in range(len(data))]

    validation_checks = {
        "Missing required fields": check_missing_values(data),
        "Duplicate order ID": check_duplicate_orders(data),
        "Invalid order amount": check_invalid_amounts(data),
        "Invalid quantity": check_invalid_quantities(data),
        "Invalid timestamp": check_invalid_timestamps(data),
    }

    for reason, mask in validation_checks.items():
        for position, is_invalid in enumerate(mask.tolist()):
            if is_invalid:
                rejection_reasons[position].append(reason)

    data["rejection_reason"] = [
        "; ".join(reasons) for reasons in rejection_reasons
    ]

    rejected_mask = data["rejection_reason"] != ""

    valid = data.loc[~rejected_mask].drop(
        columns=["rejection_reason"]
    ).copy()

    rejected = data.loc[rejected_mask].copy()

    return valid, rejected
