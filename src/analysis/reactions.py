import pandas as pd


# ============================================================
# REACTION COUNTS
# ============================================================

def reaction_counts(
    reaction_df: pd.DataFrame,
    top_n: int = 10,
) -> dict:

    if reaction_df.empty:
        return {}

    counts = (
        reaction_df["reaction"]
        .dropna()
        .value_counts()
        .head(top_n)
    )

    return {
        str(reaction): int(count)
        for reaction, count in counts.items()
    }


# ============================================================
# OUTCOME COUNTS
# ============================================================

def outcome_counts(
    reaction_df: pd.DataFrame,
) -> dict:

    if reaction_df.empty:
        return {}

    # The raw data already contains a literal lowercase "unknown" as a
    # real reported value, distinct from missing/NaN outcomes. Without
    # normalizing case and whitespace before counting, NaN-filled rows
    # ("Unknown", capital U) and genuinely reported "unknown" rows were
    # being counted as two separate categories in the output.
    counts = (
        reaction_df["outcome"]
        .fillna("unknown")
        .astype(str)
        .str.strip()
        .str.lower()
        .replace("", "unknown")
        .value_counts()
    )

    return {
        str(outcome): int(count)
        for outcome, count in counts.items()
    }


# ============================================================
# SERIOUS REACTION COUNTS
# ============================================================

def serious_reaction_counts(
    reaction_df: pd.DataFrame,
    canonical_df: pd.DataFrame,
    top_n: int = 10,
) -> dict:
    """
    Count reactions belonging to serious canonical cases.

    reaction_df:
        case_id | reaction | outcome | reaction_index

    canonical_df:
        safetyreportid | serious | ...

    Join:
        reaction_df.case_id
            ==
        canonical_df.safetyreportid
    """

    if reaction_df.empty:
        return {}

    if canonical_df.empty:
        return {}

    # --------------------------------------------------------
    # Validate reaction dataframe
    # --------------------------------------------------------

    required_reaction_columns = {
        "case_id",
        "reaction",
    }

    missing_reaction_columns = (
        required_reaction_columns
        - set(reaction_df.columns)
    )

    if missing_reaction_columns:
        raise ValueError(
            "Reaction dataframe is missing required "
            f"columns: {sorted(missing_reaction_columns)}"
        )

    # --------------------------------------------------------
    # Validate canonical dataframe
    # --------------------------------------------------------

    required_case_columns = {
        "safetyreportid",
        "serious",
    }

    missing_case_columns = (
        required_case_columns
        - set(canonical_df.columns)
    )

    if missing_case_columns:
        raise ValueError(
            "Canonical dataframe is missing required "
            f"columns: {sorted(missing_case_columns)}"
        )

    # --------------------------------------------------------
    # Prepare copies
    # --------------------------------------------------------

    reactions = reaction_df.copy()

    cases = canonical_df[
        [
            "safetyreportid",
            "serious",
        ]
    ].copy()

    # --------------------------------------------------------
    # Normalize IDs
    # --------------------------------------------------------

    reactions["case_id"] = (
        reactions["case_id"]
        .astype("string")
        .str.strip()
    )

    cases["safetyreportid"] = (
        cases["safetyreportid"]
        .astype("string")
        .str.strip()
    )

    # --------------------------------------------------------
    # Select serious canonical cases
    # --------------------------------------------------------

    serious_cases = cases[
        cases["serious"]
        .astype("string")
        .str.strip()
        .str.lower()
        == "serious"
    ][
        ["safetyreportid"]
    ].drop_duplicates()

    # --------------------------------------------------------
    # Join reaction records with serious cases
    # --------------------------------------------------------

    serious_reactions = reactions.merge(
        serious_cases,
        left_on="case_id",
        right_on="safetyreportid",
        how="inner",
    )

    # --------------------------------------------------------
    # No serious reactions
    # --------------------------------------------------------

    if serious_reactions.empty:
        return {}

    # --------------------------------------------------------
    # Count serious reactions
    # --------------------------------------------------------

    counts = (
        serious_reactions["reaction"]
        .dropna()
        .value_counts()
        .head(top_n)
    )

    return {
        str(reaction): int(count)
        for reaction, count in counts.items()
    }


# ============================================================
# REACTION SUMMARY
# ============================================================

def reaction_summary(
    reaction_df: pd.DataFrame,
    canonical_df: pd.DataFrame | None = None,
) -> dict:

    result = {

        # ----------------------------------------------------
        # Overall reactions
        # ----------------------------------------------------

        "total_reaction_records": int(
            len(reaction_df)
        ),

        "unique_reactions": (
            int(
                reaction_df["reaction"].nunique()
            )
            if not reaction_df.empty
            else 0
        ),

        "most_common_reactions":
            reaction_counts(
                reaction_df
            ),

        # ----------------------------------------------------
        # Outcomes
        # ----------------------------------------------------

        "outcome_distribution":
            outcome_counts(
                reaction_df
            ),

        # ----------------------------------------------------
        # Serious reactions
        # ----------------------------------------------------

        "most_common_serious_reactions":
            serious_reaction_counts(
                reaction_df,
                canonical_df,
            )
            if canonical_df is not None
            else {},
    }

    return result