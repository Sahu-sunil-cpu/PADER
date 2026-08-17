from pathlib import Path

import pandas as pd


class DataLoader:

    def load(self, file_path: str | Path) -> pd.DataFrame:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Dataset not found: {path}"
            )

        suffix = path.suffix.lower()

        if suffix == ".csv":
            df = pd.read_csv(path)

        elif suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(path)

        else:
            raise ValueError(
                f"Unsupported file type: {suffix}"
            )

        if df.empty:
            raise ValueError("Dataset is empty.")

        # Keep every column.
        df.columns = (
            df.columns
            .str.strip()
        )

        return df