import pandas as pd

from src.config import (
    CASE_ID,
    SERIOUS,
    EXPEDITED,
    RECEIVED_DATE,
    REACTION,
    COUNTRY,
    OUTCOME,
    OUTPUT_DIR,
)


SERIOUSNESS_FLAGS = {
    "death": "seriousnessdeath",
    "life_threatening": "seriousnesslifethreatening",
    "hospitalization": "seriousnesshospitalization",
    "disabling": "seriousnessdisabling",
    "congenital_anomaly": "seriousnesscongenitalanomali",
    "other": "seriousnessother",
}


AFFIRMATIVE_VALUES = {"1", "true", "yes"}


def _is_affirmative(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .isin(AFFIRMATIVE_VALUES)
    )


def total_cases(df: pd.DataFrame) -> int:
    return int(df[CASE_ID].nunique())


def serious_cases(df: pd.DataFrame) -> int:
    values = (
        df[SERIOUS]
        .astype(str)
        .str.strip()
        .str.lower()
    )
    return int((values == "serious").sum())


def seriousness_breakdown(df: pd.DataFrame) -> dict:
    result = {}

    for name, column in SERIOUSNESS_FLAGS.items():
        if column not in df.columns:
            result[name] = {"count": 0, "available": False}
            continue

        result[name] = {
            "count": int(_is_affirmative(df[column]).sum()),
            "available": True,
        }

    return result


def alert_case_summary(
    canonical_df: pd.DataFrame,
    reaction_df: pd.DataFrame | None = None,
    top_n: int = 10,
) -> dict:
    """
    Summarize cases explicitly flagged by fulfillexpeditecriteria.

    For this exercise, the dataset's expedited flag is the deterministic
    basis used for the 15-day Alert analysis. Seriousness is reported
    separately rather than inferred from the flag.
    """
    if EXPEDITED not in canonical_df.columns:
        return {
            "available": False,
            "alert_cases": 0,
            "serious_alert_cases": 0,
            "non_serious_alert_cases": 0,
            "alert_reaction_records": 0,
            "top_alert_reactions": {},
            "alert_outcome_distribution": {},
        }

    alert_mask = _is_affirmative(canonical_df[EXPEDITED])
    alerts = canonical_df.loc[alert_mask].copy()

    serious_mask = (
        alerts[SERIOUS]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("serious")
    ) if not alerts.empty else pd.Series(dtype=bool)

    result = {
        "available": True,
        "alert_cases": int(len(alerts)),
        "serious_alert_cases": int(serious_mask.sum()) if not alerts.empty else 0,
        "non_serious_alert_cases": int((~serious_mask).sum()) if not alerts.empty else 0,
        "alert_reaction_records": 0,
        "top_alert_reactions": {},
        "alert_outcome_distribution": {},
    }

    if reaction_df is None or reaction_df.empty or alerts.empty:
        return result

    alert_ids = set(alerts[CASE_ID].astype(str).str.strip())
    reactions = reaction_df.copy()
    reactions["case_id"] = reactions["case_id"].astype(str).str.strip()
    alert_reactions = reactions[reactions["case_id"].isin(alert_ids)].copy()

    result["alert_reaction_records"] = int(len(alert_reactions))

    if not alert_reactions.empty:
        result["top_alert_reactions"] = {
            str(k): int(v)
            for k, v in (
                alert_reactions["reaction"]
                .dropna()
                .value_counts()
                .head(top_n)
                .items()
            )
        }

        result["alert_outcome_distribution"] = {
            str(k): int(v)
            for k, v in (
                alert_reactions["outcome"]
                .fillna("unknown")
                .astype(str)
                .str.strip()
                .str.lower()
                .replace("", "unknown")
                .value_counts()
                .items()
            )
        }

    return result


def case_summary(df: pd.DataFrame) -> dict:
    total = total_cases(df)
    serious = serious_cases(df)

    return {
        "total_cases": total,
        "serious_cases": serious,
        "non_serious_cases": total - serious,
        "serious_percentage": round(serious / total * 100, 2) if total else 0,
        "seriousness_breakdown": seriousness_breakdown(df),
    }


def export_case_listing(
    canonical_df: pd.DataFrame,
    reaction_df: pd.DataFrame | None = None,
) -> dict:
    """
    Export a traceable case/reaction listing.

    When reaction_df is supplied, the listing contains one row per
    parsed reaction record while case-level attributes come from the
    canonical case record. This preserves all reaction-level detail
    while avoiding stale case versions for seriousness/date/country.
    """
    listing_path = OUTPUT_DIR / "case_listing.csv"

    canonical = canonical_df.copy()
    canonical[CASE_ID] = canonical[CASE_ID].astype(str).str.strip()

    case_columns = [c for c in [CASE_ID, SERIOUS, RECEIVED_DATE, COUNTRY] if c in canonical.columns]
    case_data = canonical[case_columns].drop_duplicates(subset=[CASE_ID]).copy()
    case_data = case_data.rename(
        columns={
            CASE_ID: "case_id",
            SERIOUS: "seriousness",
            RECEIVED_DATE: "reporting_date",
            COUNTRY: "country",
        }
    )

    if reaction_df is not None and not reaction_df.empty:
        reactions = reaction_df.copy()
        reactions["case_id"] = reactions["case_id"].astype(str).str.strip()
        listing = reactions.merge(
            case_data,
            on="case_id",
            how="inner",
            validate="many_to_one",
        )
        listing = listing[
            [
                "case_id",
                "reaction",
                "seriousness",
                "reporting_date",
                "country",
                "outcome",
            ]
        ]
        granularity = "reaction_record"
    else:
        listing = case_data.copy()
        if REACTION in canonical.columns:
            listing["reaction"] = canonical[REACTION].astype(str)
        else:
            listing["reaction"] = ""
        if OUTCOME in canonical.columns:
            listing["outcome"] = canonical[OUTCOME].astype(str)
        else:
            listing["outcome"] = ""
        listing = listing[
            [
                "case_id",
                "reaction",
                "seriousness",
                "reporting_date",
                "country",
                "outcome",
            ]
        ]
        granularity = "case"

    listing.to_csv(listing_path, index=False)

    return {
        "total_cases": int(canonical_df[CASE_ID].nunique()),
        "listing_rows": int(len(listing)),
        "unique_case_ids": int(listing["case_id"].nunique()),
        "granularity": granularity,
        "export_path": str(listing_path.name),
        "fields_included": list(listing.columns),
    }
