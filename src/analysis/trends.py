import pandas as pd

from src.config import (
    RECEIVED_DATE,
    CASE_ID,
)


def parse_received_date(series: pd.Series) -> pd.Series:
    """
    Parse the ICSR receivedate field safely.

    The supplied dataset stores dates in numeric/string
    YYYYMMDD-style form. We explicitly tell pandas the
    expected format instead of allowing numeric timestamp
    inference.
    """

    # Convert values to strings first.
    values = (
        series
        .astype("string")
        .str.strip()
    )

    # Remove trailing .0 if Excel converted
    # an integer date into a floating-point value.
    values = values.str.replace(
        r"\.0$",
        "",
        regex=True,
    )

    # Parse as YYYYMMDD.
    dates = pd.to_datetime(
        values,
        format="%Y%m%d",
        errors="coerce",
    )

    return dates


def reporting_period(df: pd.DataFrame) -> dict:
    """Return the exact reporting interval supported by receivedate."""

    if df.empty or RECEIVED_DATE not in df.columns:
        return {
            "available": False,
            "start_date": None,
            "end_date": None,
            "start_month": None,
            "end_month": None,
        }

    dates = parse_received_date(df[RECEIVED_DATE]).dropna()

    if dates.empty:
        return {
            "available": False,
            "start_date": None,
            "end_date": None,
            "start_month": None,
            "end_month": None,
        }

    start = dates.min()
    end = dates.max()

    return {
        "available": True,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "start_month": start.strftime("%Y-%m"),
        "end_month": end.strftime("%Y-%m"),
    }


def monthly_trend(
    df: pd.DataFrame,
) -> dict:
    """
    Calculate unique canonical cases per month.
    """

    data = df.copy()

    data["_received_date"] = parse_received_date(
        data[RECEIVED_DATE]
    )

    # Remove records where the reporting date
    # could not be parsed.
    data = data.dropna(
        subset=["_received_date"]
    )

    monthly = (
        data
        .groupby(
            data["_received_date"].dt.to_period("M")
        )[CASE_ID]
        .nunique()
        .sort_index()
    )

    return {
        str(period): int(count)
        for period, count in monthly.items()
    }


def identify_trends(
    monthly_counts: dict,
) -> dict:
    """
    Produce descriptive trend observations.

    This does NOT perform statistical significance testing.
    """

    if not monthly_counts:

        return {
            "observation": (
                "No valid reporting-date data "
                "was available."
            ),
            "peak_month": None,
            "peak_cases": None,
            "lowest_month": None,
            "lowest_cases": None,
            "average_monthly_cases": None,
        }

    series = pd.Series(
        monthly_counts,
        dtype="int64",
    )

    peak_month = str(
        series.idxmax()
    )

    lowest_month = str(
        series.idxmin()
    )

    peak_cases = int(
        series.max()
    )

    lowest_cases = int(
        series.min()
    )

    average_cases = float(
        series.mean()
    )

    observation = (
        f"The highest monthly case count was "
        f"{peak_cases} in {peak_month}, while "
        f"the lowest was {lowest_cases} in "
        f"{lowest_month}."
    )

    return {
        "observation": observation,
        "peak_month": peak_month,
        "peak_cases": peak_cases,
        "lowest_month": lowest_month,
        "lowest_cases": lowest_cases,
        "average_monthly_cases": round(
            average_cases,
            2,
        ),
    }