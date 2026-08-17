import pandas as pd


def split_multi_value(value) -> list[str]:
    """
    Convert a comma-separated ICSR field into a list.

    Example:
        "Headache,Nausea,Dizziness"

    becomes:
        ["Headache", "Nausea", "Dizziness"]
    """

    if pd.isna(value):
        return []

    value = str(value).strip()

    if not value:
        return []

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


def normalize_text(value) -> str | None:

    if pd.isna(value):
        return None

    value = str(value).strip()

    return value if value else None