"""
Tests for src/preprocessing/canonicalizer.py.

This module was singled out for testing because case-level deduplication
is the single easiest place to silently get this dataset's numbers wrong:
1,068 raw rows collapse to 1,024 cases, and picking the wrong row per case
(instead of the latest safetyreportversion) changes every downstream count.
"""
import pandas as pd
import pytest

from src.config import CASE_ID, VERSION
from src.preprocessing.canonicalizer import canonicalize_cases, version_audit


def _df(rows):
    return pd.DataFrame(rows)


def test_canonicalize_keeps_latest_version_per_case():
    df = _df([
        {CASE_ID: "A", VERSION: 1, "value": "old"},
        {CASE_ID: "A", VERSION: 2, "value": "new"},
        {CASE_ID: "B", VERSION: 1, "value": "only"},
    ])
    result = canonicalize_cases(df)

    assert len(result) == 2  # one row per unique case
    a_row = result[result[CASE_ID] == "A"].iloc[0]
    assert a_row["value"] == "new"  # kept version 2, not version 1


def test_canonicalize_is_idempotent_on_single_version_cases():
    df = _df([
        {CASE_ID: "A", VERSION: 1, "value": "x"},
        {CASE_ID: "B", VERSION: 1, "value": "y"},
        {CASE_ID: "C", VERSION: 1, "value": "z"},
    ])
    result = canonicalize_cases(df)
    assert len(result) == 3  # no case had multiple versions, nothing collapses


def test_canonicalize_raises_on_invalid_version_values():
    df = _df([
        {CASE_ID: "A", VERSION: "not-a-number", "value": "x"},
    ])
    with pytest.raises(ValueError):
        canonicalize_cases(df)


def test_version_audit_flags_multi_version_cases_correctly():
    df = _df([
        {CASE_ID: "A", VERSION: 1},
        {CASE_ID: "A", VERSION: 2},
        {CASE_ID: "B", VERSION: 1},
    ])
    audit = version_audit(df)

    a_row = audit[audit[CASE_ID] == "A"].iloc[0]
    b_row = audit[audit[CASE_ID] == "B"].iloc[0]

    assert a_row["multiple_versions"] == True   # noqa: E712
    assert a_row["number_of_versions"] == 2
    assert b_row["multiple_versions"] == False  # noqa: E712
