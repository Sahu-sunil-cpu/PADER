import pandas as pd

from src.config import CASE_ID, VERSION


def canonicalize_cases(df: pd.DataFrame) -> pd.DataFrame:

    data = df.copy()

    data[VERSION] = pd.to_numeric(
        data[VERSION],
        errors="coerce"
    )

    if data[VERSION].isna().any():
        raise ValueError(
            f"{VERSION} contains invalid values."
        )

    # Keep the latest version of every case.
    data = data.sort_values(
        [CASE_ID, VERSION]
    )

    canonical = (
        data
        .groupby(CASE_ID, as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )

    return canonical


def version_audit(df: pd.DataFrame) -> pd.DataFrame:

    audit = (
        df.groupby(CASE_ID)
        .agg(
            number_of_versions=(VERSION, "nunique"),
            latest_version=(VERSION, "max"),
        )
        .reset_index()
    )

    audit["multiple_versions"] = (
        audit["number_of_versions"] > 1
    )

    return audit