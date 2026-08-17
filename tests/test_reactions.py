"""
Tests for src/preprocessing/reaction_parser.py.

This is the other high-risk spot in the pipeline: the raw data stores
multiple reactions and their outcomes comma-separated in a single cell
(e.g. "Rectal haemorrhage,Deficiency anaemia"), positionally paired with
outcomes in the same row. A naive .value_counts() on the raw column
silently treats a multi-reaction cell as one combined "reaction" and
produces wrong top-reaction counts -- exactly the bug this project hit
and fixed during development.
"""
import pandas as pd

from src.config import CASE_ID, REACTION, OUTCOME
from src.preprocessing.reaction_parser import parse_reactions


def _df(rows):
    return pd.DataFrame(rows)


def test_single_reaction_single_outcome():
    df = _df([
        {CASE_ID: "A", REACTION: "Headache", OUTCOME: "recovered"},
    ])
    result = parse_reactions(df)

    assert len(result) == 1
    assert result.iloc[0]["reaction"] == "Headache"
    assert result.iloc[0]["outcome"] == "recovered"


def test_multi_reaction_splits_into_separate_records():
    df = _df([
        {CASE_ID: "A", REACTION: "Headache,Nausea,Dizziness", OUTCOME: "recovered,unknown,recovering"},
    ])
    result = parse_reactions(df)

    assert len(result) == 3
    assert list(result["reaction"]) == ["Headache", "Nausea", "Dizziness"]
    # outcomes must stay positionally paired with their reaction, not
    # independently exploded
    assert list(result["outcome"]) == ["recovered", "unknown", "recovering"]


def test_multi_reaction_pads_missing_outcomes_rather_than_crashing():
    df = _df([
        {CASE_ID: "A", REACTION: "Headache,Nausea", OUTCOME: "recovered"},
    ])
    result = parse_reactions(df)

    assert len(result) == 2
    assert result.iloc[0]["outcome"] == "recovered"
    assert result.iloc[1]["outcome"] == "Unknown"  # padded, not dropped or crashed


def test_missing_reaction_produces_no_records():
    df = _df([
        {CASE_ID: "A", REACTION: None, OUTCOME: None},
    ])
    result = parse_reactions(df)
    assert len(result) == 0


def test_whitespace_around_values_is_stripped():
    df = _df([
        {CASE_ID: "A", REACTION: " Headache , Nausea ", OUTCOME: "recovered, unknown"},
    ])
    result = parse_reactions(df)
    assert list(result["reaction"]) == ["Headache", "Nausea"]
    assert list(result["outcome"]) == ["recovered", "unknown"]
