
import pandas as pd


def classify_data_type(series: pd.Series) -> str:
    """Return a stable logical data type for a Pandas column."""

    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    if pd.api.types.is_numeric_dtype(series):
        return "numeric"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    return "string"


def profile_schema(df: pd.DataFrame) -> dict:
    """Capture column names and their logical data types."""

    return {
        column: classify_data_type(df[column])
        for column in df.columns
    }


def compare_schemas(
    incoming_schema: dict,
    baseline_schema: dict,
) -> dict:
    """Compare incoming schema with the historical schema."""

    incoming_columns = set(incoming_schema)
    baseline_columns = set(baseline_schema)

    new_columns = sorted(incoming_columns - baseline_columns)
    missing_columns = sorted(baseline_columns - incoming_columns)

    type_changes = []

    for column in sorted(incoming_columns & baseline_columns):
        incoming_type = incoming_schema[column]
        expected_type = baseline_schema[column]

        if incoming_type != expected_type:
            type_changes.append({
                "column": column,
                "expected_type": expected_type,
                "observed_type": incoming_type,
            })

    return {
        "new_columns": new_columns,
        "missing_columns": missing_columns,
        "type_changes": type_changes,
        "passed": (
            not new_columns
            and not missing_columns
            and not type_changes
        ),
    }
