import pandas as pd

from src.config import (
    CASE_ID,
    REACTION,
    OUTCOME,
)

from src.preprocessing.normalizers import (
    split_multi_value,
)


def parse_reactions(
    df: pd.DataFrame,
) -> pd.DataFrame:

    records = []

    for _, row in df.iterrows():

        case_id = row[CASE_ID]

        reactions = split_multi_value(
            row.get(REACTION)
        )

        outcomes = split_multi_value(
            row.get(OUTCOME)
        )

        for index, reaction in enumerate(
            reactions
        ):

            outcome = (
                outcomes[index]
                if index < len(outcomes)
                else "Unknown"
            )

            records.append(
                {
                    "case_id": case_id,
                    "reaction": reaction,
                    "outcome": outcome,
                    "reaction_index": index,
                }
            )

    return pd.DataFrame(
        records,
        columns=[
            "case_id",
            "reaction",
            "outcome",
            "reaction_index",
        ],
    )