import pandas as pd

from src.config import (
    SEX,
    AGE,
    AGE_UNIT,
    COUNTRY,
    PRIMARY_SOURCE_COUNTRY,
    REPORTER_COUNTRY,
    REPORTER_QUALIFICATION,
)


def normalize_age_to_years(
    age,
    unit,
):
    if pd.isna(age):
        return None

    try:
        age = float(age)
    except (ValueError, TypeError):
        return None

    if pd.isna(unit):
        return age

    unit = str(unit).strip().lower()

    if unit in {"year", "years", "yr", "yrs"}:
        return age

    if unit in {"month", "months", "mo", "mos"}:
        return age / 12

    if unit in {"week", "weeks", "wk", "wks"}:
        return age / 52.1775

    if unit in {"day", "days", "d"}:
        return age / 365.25

    if unit in {"hour", "hours", "h"}:
        return age / (365.25 * 24)

    return None


def age_group(age_years):

    if age_years is None:
        return "Unknown"

    if age_years < 18:
        return "<18"

    if age_years < 45:
        return "18-44"

    if age_years < 65:
        return "45-64"

    if age_years < 75:
        return "65-74"

    return "75+"


def age_distribution(df: pd.DataFrame) -> dict:

    groups = []

    for _, row in df.iterrows():

        age = normalize_age_to_years(
            row.get(AGE),
            row.get(AGE_UNIT),
        )

        groups.append(
            age_group(age)
        )

    counts = pd.Series(
        groups
    ).value_counts()

    ordered = [
        "<18",
        "18-44",
        "45-64",
        "65-74",
        "75+",
        "Unknown",
    ]

    return {
        group: int(counts.get(group, 0))
        for group in ordered
    }


def sex_distribution(
    df: pd.DataFrame,
) -> dict:

    counts = (
        df[SEX]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .replace("", "Unknown")
        .value_counts()
    )

    return {
        str(k): int(v)
        for k, v in counts.items()
    }


def country_distribution(
    df: pd.DataFrame,
    column: str,
) -> dict:

    counts = (
        df[column]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .replace("", "Unknown")
        .value_counts()
    )

    return {
        str(k): int(v)
        for k, v in counts.items()
    }


def demographic_summary(
    df: pd.DataFrame,
) -> dict:

    result = {
        "sex": sex_distribution(df),
        "age_groups": age_distribution(df),
    }

    if COUNTRY in df.columns:
        result["occurrence_country"] = (
            country_distribution(
                df,
                COUNTRY,
            )
        )

    if PRIMARY_SOURCE_COUNTRY in df.columns:
        result["primary_source_country"] = country_distribution(
            df,
            PRIMARY_SOURCE_COUNTRY,
        )

    if REPORTER_COUNTRY in df.columns:
        result["reporter_country"] = country_distribution(
            df,
            REPORTER_COUNTRY,
        )

    if REPORTER_QUALIFICATION in df.columns:
        result["reporter_qualification"] = country_distribution(
            df,
            REPORTER_QUALIFICATION,
        )

    return result