import pandas as pd

from src.config import (
    CASE_ID,
    VERSION,
    RECEIVED_DATE,
)


class DataValidator:

    REQUIRED_COLUMNS = {
        CASE_ID,
        VERSION,
        RECEIVED_DATE,
    }

    def validate(self, df: pd.DataFrame) -> None:

        missing = self.REQUIRED_COLUMNS - set(df.columns)

        if missing:
            raise ValueError(
                "Required columns are missing:\n"
                + "\n".join(sorted(missing))
            )

        if df.empty:
            raise ValueError("Dataset is empty.")

        if df[CASE_ID].isna().any():
            raise ValueError(
                f"{CASE_ID} contains missing values."
            )

        if df[VERSION].isna().any():
            raise ValueError(
                f"{VERSION} contains missing values."
            )

        print("Schema validation: PASSED")

    def quality_summary(self, df: pd.DataFrame) -> dict:

        return {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "missing_values": int(df.isna().sum().sum()),
            "unique_cases": int(df[CASE_ID].nunique()),
        }