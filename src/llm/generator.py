
import json
import re
from pathlib import Path
from typing import Any

from src.llm.client import generate_text
from src.llm.prompts import (
    SYSTEM_PROMPT,
    NARRATIVE_SUMMARY_PROMPT,
    REACTION_ANALYSIS_PROMPT,
    CASE_SUMMARY_PROMPT,
    SERIOUS_CASES_PROMPT,
    TRENDS_PROMPT,
    HISTORY_PROMPT,
    REPORTING_PERIOD_PROMPT,
    CASE_INDEX_PROMPT,
)


# ============================================================
# SECTION CONFIGURATION
# ============================================================

SECTION_PROMPTS = {
    "reporting_period": REPORTING_PERIOD_PROMPT,
    "narrative_summary": NARRATIVE_SUMMARY_PROMPT,
    "case_summary": CASE_SUMMARY_PROMPT,
    "reaction_analysis": REACTION_ANALYSIS_PROMPT,
    "serious_cases": SERIOUS_CASES_PROMPT,
    "trends": TRENDS_PROMPT,
    "history_of_actions": HISTORY_PROMPT,
    "case_index": CASE_INDEX_PROMPT,
}


# ============================================================
# SECTION-SPECIFIC ADDITIONAL RULES
# ============================================================

SECTION_RULES = {
    "narrative_summary": """
IMPORTANT DEMOGRAPHIC RULES:

If demographic evidence is present in APPROVED EVIDENCE,
do NOT state that demographic information is unavailable.

If demographic distributions are provided, they may be
described descriptively.

You may report supplied demographic counts for:
- sex
- age groups
- occurrence country
- primary source country
- reporter country

Do not infer:
- risk factors
- associations
- causality
- clinical significance
- population differences beyond the supplied counts

Do not use the phrase "associated with" unless an exact
association is explicitly stated in APPROVED EVIDENCE.

Use only the supplied demographic counts.
""",

    "case_summary": """
IMPORTANT DEMOGRAPHIC RULES:

If demographic evidence is present, describe it only
using the supplied counts.

Do not say demographics are unavailable when demographic
evidence is present.

Do not infer risk factors, associations, causality,
or clinical significance from demographic distributions.

Do not use the phrase "associated with" unless an exact
association is explicitly stated in APPROVED EVIDENCE.
""",

    "reaction_analysis": """
IMPORTANT REACTION RULES:

Report reactions at the supplied MedDRA Preferred Term
level.

Do not invent System Organ Class groupings.

Reaction counts refer to reaction records unless the
evidence explicitly says otherwise.

Do not infer causality.

Do not state that a reaction was caused by the product.

Do not infer that the product is associated with a
reaction unless that exact association is explicitly
supported by APPROVED EVIDENCE.

Avoid the phrase "associated with" unless the exact
association is explicitly present in APPROVED EVIDENCE.
""",

    "serious_cases": """
IMPORTANT SERIOUSNESS RULES:

Seriousness categories are independent and may overlap.

Do not add seriousness categories to derive a total.

Report the supplied counts exactly.

Do not infer causality or clinical significance.

Do not use the phrase "associated with" unless an exact
association is explicitly stated in APPROVED EVIDENCE.
""",

    "trends": """
IMPORTANT TREND RULES:

Describe temporal observations descriptively.

Do not infer causality from temporal patterns.

Do not call a trend a safety signal unless the supplied
evidence explicitly establishes that.

Do not infer increased or decreased risk.

Do not use the phrase "associated with" unless an exact
association is explicitly stated in APPROVED EVIDENCE.

Use supplied dates and counts exactly.
""",

    "history_of_actions": """
IMPORTANT ACTION RULES:

Only report documented regulatory or company actions.

Do not invent regulatory actions.

Do not infer actions from reactions or seriousness.

If no action information is present in the approved
evidence, state that action information was not available.

Do not use the phrase "associated with" unless an exact
association is explicitly stated in APPROVED EVIDENCE.
""",

    "case_index": """
IMPORTANT CASE INDEX RULES:

Use case identifiers exactly as supplied.

Do not invent case information.

Do not expose unnecessary patient identifying information.

Do not infer causality.

Do not make risk or safety conclusions.

Do not infer associations between the product and reactions.

Do not use the phrase "associated with" unless that exact
association is explicitly supported by APPROVED EVIDENCE.

Use only descriptive case-level information supplied in
the approved evidence.
""",
}


# ============================================================
# LOAD CONTEXT
# ============================================================

def load_context(context_path: Path) -> dict:
    """
    Load a report-context JSON file.
    """

    with open(
        context_path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ============================================================
# BUILD USER PROMPT
# ============================================================

def build_user_prompt(
    section_name: str,
    context: dict,
) -> str:

    if section_name not in SECTION_PROMPTS:
        raise ValueError(
            f"Unknown report section: {section_name}"
        )

    section_instruction = SECTION_PROMPTS[
        section_name
    ]

    additional_rules = SECTION_RULES.get(
        section_name,
        "",
    )

    evidence_json = json.dumps(
        context,
        indent=2,
        ensure_ascii=False,
    )

    return f"""
SECTION INSTRUCTIONS
====================

{section_instruction}


SECTION-SPECIFIC RULES
======================

{additional_rules}


APPROVED EVIDENCE
=================

The following evidence is the ONLY source of factual
information that may be used in the generated section.

{evidence_json}


GROUNDING REQUIREMENTS
======================

1. Use only facts present in APPROVED EVIDENCE.

2. Do not invent numbers, dates, percentages, reactions,
   demographics, countries, outcomes, or case information.

3. Do not perform new arithmetic.

4. Do not derive new statistics.

5. Do not infer causality.

6. Do not state that the product caused a reaction.

7. Do not infer risk factors.

8. Do not infer clinical significance.

9. Do not describe a finding as a safety signal unless
   the supplied evidence explicitly establishes it.

10. Seriousness categories may overlap.

11. Distinguish reaction-record counts from unique case
    counts where relevant.

12. If a category is present in APPROVED EVIDENCE, do not
    claim that the category is unavailable.

13. Dates such as 2025-07 and 2024-12 are approved values
    when they appear in the evidence.

14. Percentages such as 99.9% are approved only when the
    corresponding percentage is present in the evidence.

15. Preserve the meaning of the supplied evidence.

16. Do not use numbered Markdown lists if possible.
    Prefer bullet lists for enumerating factual items.

17. Do not use the phrase "associated with" unless the
    exact association is explicitly stated in APPROVED
    EVIDENCE.

18. Prefer neutral descriptive language such as:
    - "reported"
    - "observed"
    - "identified"
    - "included in the reported data"
    - "was reported"

19. Do not replace an unsupported association with another
    implied association.

20. Do not use language implying that a reaction, demographic
    group, country, outcome, or temporal pattern represents
    increased risk, decreased risk, safety concern, or
    clinical significance unless explicitly supported by
    APPROVED EVIDENCE.

TASK
====

Write the requested report section.

Return only the report section text.

Do not include analysis of these instructions.
Do not include JSON.
Do not mention that you are an AI.
"""


# ============================================================
# VALUE NORMALIZATION
# ============================================================

def _normalise_number(value: Any) -> str:
    """
    Convert numeric values to a canonical string.

    Examples:
        1024      -> "1024"
        "1,024"   -> "1024"
        99.9      -> "99.9"
        "99.9%"   -> "99.9"
    """

    if value is None:
        return ""

    text = str(value).strip()

    text = text.replace(",", "")

    if text.endswith("%"):
        text = text[:-1]

    return text.strip()


# ============================================================
# EXTRACT APPROVED VALUES
# ============================================================

def _extract_approved_values(
    evidence: Any,
) -> set[str]:
    """
    Recursively extract approved scalar values.
    """

    approved_values: set[str] = set()

    if isinstance(evidence, dict):

        for key, value in evidence.items():

            if isinstance(key, str):

                approved_values.add(
                    key.strip()
                )

            approved_values.update(
                _extract_approved_values(value)
            )

        return approved_values

    if isinstance(evidence, list):

        for item in evidence:

            approved_values.update(
                _extract_approved_values(item)
            )

        return approved_values

    if isinstance(evidence, tuple):

        for item in evidence:

            approved_values.update(
                _extract_approved_values(item)
            )

        return approved_values

    if isinstance(evidence, (int, float)):

        approved_values.add(
            _normalise_number(evidence)
        )

        return approved_values

    if isinstance(evidence, str):

        value = evidence.strip()

        if value:

            approved_values.add(
                value
            )

            normalised = _normalise_number(
                value
            )

            if normalised:

                approved_values.add(
                    normalised
                )

        return approved_values

    return approved_values


# ============================================================
# EXTRACT APPROVED PERCENTAGES
# ============================================================

def _extract_approved_percentages(
    evidence: Any,
) -> set[str]:
    """
    Extract explicitly approved percentages.

    A numeric value such as 99.9 is NOT automatically
    treated as 99.9%.

    The percentage must explicitly appear in the evidence
    or be represented by a percentage-related field.
    """

    percentages: set[str] = set()

    if isinstance(evidence, dict):

        for key, value in evidence.items():

            key_lower = str(key).lower()

            if (
                "percentage" in key_lower
                or "percent" in key_lower
            ):

                if isinstance(
                    value,
                    (int, float),
                ):

                    percentages.add(
                        _normalise_number(value)
                    )

                elif isinstance(
                    value,
                    str,
                ):

                    matches = re.findall(
                        r"\d+(?:\.\d+)?\s*%",
                        value,
                    )

                    for match in matches:

                        percentages.add(
                            _normalise_number(match)
                        )

            percentages.update(
                _extract_approved_percentages(value)
            )

        return percentages

    if isinstance(evidence, list):

        for item in evidence:

            percentages.update(
                _extract_approved_percentages(item)
            )

        return percentages

    if isinstance(evidence, str):

        matches = re.findall(
            r"\d+(?:\.\d+)?\s*%",
            evidence,
        )

        for match in matches:

            percentages.add(
                _normalise_number(match)
            )

    return percentages


# ============================================================
# EXTRACT APPROVED DATES
# ============================================================

def _extract_approved_dates(
    evidence: Any,
) -> set[str]:
    """
    Extract date/month values such as:

        2025-07
        2024-12
        2025
    """

    dates: set[str] = set()

    if isinstance(evidence, dict):

        for key, value in evidence.items():

            key_text = str(key).strip()

            if re.fullmatch(
                r"\d{4}-\d{2}",
                key_text,
            ):

                dates.add(key_text)

            if re.fullmatch(
                r"\d{4}",
                key_text,
            ):

                dates.add(key_text)

            dates.update(
                _extract_approved_dates(value)
            )

        return dates

    if isinstance(evidence, list):

        for item in evidence:

            dates.update(
                _extract_approved_dates(item)
            )

        return dates

    if isinstance(evidence, str):

        matches = re.findall(
            r"\b\d{4}(?:-\d{2}(?:-\d{2})?)?\b",
            evidence,
        )

        dates.update(matches)

    return dates


# ============================================================
# EXTRACT APPROVED NUMERIC VALUES
# ============================================================

def _extract_approved_numbers(
    evidence: Any,
) -> set[str]:
    """
    Extract numeric values from approved evidence.

    Handles:

        1024
        1,024
        99.9
        109
        21

    Date components are not treated as independent values.
    """

    numbers: set[str] = set()

    if isinstance(evidence, dict):

        for key, value in evidence.items():

            key_text = str(key)

            # ------------------------------------------------
            # Do not extract components of date keys.
            # ------------------------------------------------

            if not re.fullmatch(
                r"\d{4}(?:-\d{2})?(?:-\d{2})?",
                key_text,
            ):

                matches = re.findall(
                    r"(?<![\w-])"
                    r"\d+(?:,\d{3})*"
                    r"(?:\.\d+)?"
                    r"(?![\w-])",
                    key_text,
                )

                for match in matches:

                    numbers.add(
                        _normalise_number(match)
                    )

            numbers.update(
                _extract_approved_numbers(value)
            )

        return numbers

    if isinstance(evidence, list):

        for item in evidence:

            numbers.update(
                _extract_approved_numbers(item)
            )

        return numbers

    if isinstance(evidence, (int, float)):

        numbers.add(
            _normalise_number(evidence)
        )

        return numbers

    if isinstance(evidence, str):

        # ----------------------------------------------------
        # Protect complete dates.
        # ----------------------------------------------------

        date_matches = re.findall(
            r"\b\d{4}-\d{2}(?:-\d{2})?\b",
            evidence,
        )

        protected = evidence

        for date_value in date_matches:

            protected = protected.replace(
                date_value,
                "",
            )

        # ----------------------------------------------------
        # Extract numeric values.
        # ----------------------------------------------------

        matches = re.findall(
            r"(?<![\w-])"
            r"\d+(?:,\d{3})*"
            r"(?:\.\d+)?"
            r"(?![\w-])",
            protected,
        )

        for match in matches:

            numbers.add(
                _normalise_number(match)
            )

    return numbers


# ============================================================
# EXTRACT GENERATED DATES
# ============================================================

def _extract_text_dates(
    text: str,
) -> set[str]:
    """
    Extract dates/months from generated text.
    """

    return set(
        re.findall(
            r"\b\d{4}(?:-\d{2}(?:-\d{2})?)?\b",
            text,
        )
    )


# ============================================================
# EXTRACT GENERATED PERCENTAGES
# ============================================================

def _extract_text_percentages(
    text: str,
) -> list[str]:
    """
    Extract percentages such as 99.9%.
    """

    return re.findall(
        r"\b\d+(?:\.\d+)?\s*%",
        text,
    )


# ============================================================
# EXTRACT GENERATED NUMBERS
# ============================================================

def _extract_text_numbers(
    text: str,
) -> list[str]:
    """
    Extract numeric claims from generated text.

    Numbers that are clearly editorial/structural rather than
    factual evidence values are ignored.

    Examples ignored:
        top 10 reactions
        first 10 cases
        10 most common reactions

    Examples retained:
        1024 cases
        99.9%
        81 records
        2025-07
    """

    # --------------------------------------------------------
    # Protect dates
    # --------------------------------------------------------

    date_pattern = re.compile(
        r"\b\d{4}(?:-\d{2}(?:-\d{2})?)?\b"
    )

    dates = date_pattern.findall(text)

    protected = text

    for index, date_value in enumerate(dates):

        placeholder = (
            f"__DATE_PLACEHOLDER_{index}__"
        )

        protected = protected.replace(
            date_value,
            placeholder,
            1,
        )

    # --------------------------------------------------------
    # Protect percentages
    # --------------------------------------------------------

    percentage_pattern = re.compile(
        r"\b\d+(?:\.\d+)?\s*%"
    )

    percentages = percentage_pattern.findall(
        protected
    )

    for index, percentage in enumerate(percentages):

        placeholder = (
            f"__PERCENT_PLACEHOLDER_{index}__"
        )

        protected = protected.replace(
            percentage,
            placeholder,
            1,
        )

    # --------------------------------------------------------
    # Find numeric values
    # --------------------------------------------------------

    matches = re.findall(
        r"(?<![\w-])"
        r"\d+(?:,\d{3})*"
        r"(?:\.\d+)?"
        r"(?![\w-])",
        protected,
    )

    # --------------------------------------------------------
    # Remove clearly editorial numbers
    # --------------------------------------------------------

    editorial_patterns = [

        # "top 10 reactions"
        r"\btop\s+\d+\b",

        # "top 10 reported reactions"
        r"\btop\s+\d+\s+\w+",

        # "first 10 cases"
        r"\bfirst\s+\d+\b",

        # "last 10 cases"
        r"\blast\s+\d+\b",

        # "10 most common reactions"
        r"\b\d+\s+most\s+common\b",

        # "10 most frequently reported"
        r"\b\d+\s+most\s+frequently\b",

        # "10 leading reactions"
        r"\b\d+\s+leading\b",

        # "10 highest"
        r"\b\d+\s+highest\b",

        # "10 lowest"
        r"\b\d+\s+lowest\b",
    ]

    editorial_numbers = set()

    for pattern in editorial_patterns:

        for match in re.finditer(
            pattern,
            protected,
            flags=re.IGNORECASE,
        ):

            number_match = re.search(
                r"\d+(?:,\d{3})*(?:\.\d+)?",
                match.group(),
            )

            if number_match:

                editorial_numbers.add(
                    _normalise_number(
                        number_match.group()
                    )
                )

    # --------------------------------------------------------
    # Return factual numbers only
    # --------------------------------------------------------

    factual_numbers = []

    for number in matches:

        normalised = _normalise_number(
            number
        )

        if normalised in editorial_numbers:
            continue

        factual_numbers.append(number)

    return factual_numbers


# ============================================================
# CAUSALITY VALIDATION
# ============================================================

CAUSALITY_PATTERNS = [
    r"\bcaused by\b",
    r"\bcaused\b",
    r"\bcauses\b",
    r"\bcause\b",
    r"\bdue to\b",
    r"\bresulted from\b",
    r"\bresulting from\b",
    r"\battributed to\b",
    r"\bcausally related\b",
    r"\bcausal relationship\b",
]


# ============================================================
# RISK / SAFETY CLAIM VALIDATION
# ============================================================

RISK_PATTERNS = [
    r"\bhigher risk\b",
    r"\blower risk\b",
    r"\bincreased risk\b",
    r"\bdecreased risk\b",
    r"\brisk factor\b",
    r"\bsafety signal\b",
    r"\bsafety concern\b",
    r"\bunsafe\b",
    r"\bsafe\b",
    r"\bhigh risk\b",
    r"\blow risk\b",
    r"\bincreased incidence\b",
    r"\bassociated with\b",
]


# ============================================================
# TEXT VALIDATION
# ============================================================

def validate_generated_text(
    text: str,
    approved_evidence: dict,
) -> dict:
    """
    Validate generated text against approved evidence.

    Checks:

    1. Unsupported percentages
    2. Unsupported dates
    3. Unsupported numeric claims
    4. Unsupported causality
    5. Unsupported risk/safety claims
    """

    issues: list[str] = []

    approved_numbers = (
        _extract_approved_numbers(
            approved_evidence
        )
    )

    approved_percentages = (
        _extract_approved_percentages(
            approved_evidence
        )
    )

    approved_dates = (
        _extract_approved_dates(
            approved_evidence
        )
    )

    evidence_text = json.dumps(
        approved_evidence,
        ensure_ascii=False,
    )

    # --------------------------------------------------------
    # Percentages
    # --------------------------------------------------------

    generated_percentages = (
        _extract_text_percentages(text)
    )

    for percentage in generated_percentages:

        normalised = _normalise_number(
            percentage
        )

        if normalised not in approved_percentages:

            issues.append(
                f"Unsupported percentage: "
                f"{percentage}"
            )

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    generated_dates = (
        _extract_text_dates(text)
    )

    for date_value in generated_dates:

        if date_value in approved_dates:
            continue

        if date_value in evidence_text:
            continue

        issues.append(
            f"Unsupported year/date: "
            f"{date_value}"
        )

    # --------------------------------------------------------
    # Numeric claims
    # --------------------------------------------------------

    generated_numbers = (
        _extract_text_numbers(text)
    )

    approved_years = {
        date[:4]
        for date in approved_dates
        if date
    }

    for number in generated_numbers:

        normalised = _normalise_number(
            number
        )

        if not normalised:
            continue

        # ----------------------------------------------------
        # Explicitly approved numeric value.
        # ----------------------------------------------------

        if normalised in approved_numbers:
            continue

        # ----------------------------------------------------
        # Approved year.
        # ----------------------------------------------------

        if normalised in approved_years:
            continue

        # ----------------------------------------------------
        # Numeric value exists inside approved evidence.
        # ----------------------------------------------------

        if normalised in evidence_text:
            continue

        issues.append(
            f"Unsupported numeric claim: "
            f"{number}"
        )

    # --------------------------------------------------------
    # Causality
    # --------------------------------------------------------

    lower_text = text.lower()

    for pattern in CAUSALITY_PATTERNS:

        if re.search(
            pattern,
            lower_text,
        ):

            issues.append(
                "Potential unsupported causality "
                f"statement: {pattern}"
            )

    # --------------------------------------------------------
    # Risk / Safety conclusions
    # --------------------------------------------------------

    for pattern in RISK_PATTERNS:

        if re.search(
            pattern,
            lower_text,
        ):

            issues.append(
                "Potential unsupported "
                f"risk/safety conclusion: {pattern}"
            )

    return {
        "passed": len(issues) == 0,
        "issues": issues,
    }


# ============================================================
# VALIDATE SECTION
# ============================================================

def validate_section(
    generated_text: str,
    context: dict,
) -> dict:
    """
    Validate a generated section against its context.
    """

    approved_evidence = context.get(
        "approved_evidence",
        {},
    )

    return validate_generated_text(
        generated_text,
        approved_evidence,
    )


# ============================================================
# GENERATE SECTION
# ============================================================

def generate_section(
    section_name: str,
    context_path: Path,
) -> str:
    """
    Generate one report section and validate it.

    The generated text is returned only if grounding
    validation passes.
    """

    if section_name not in SECTION_PROMPTS:

        raise ValueError(
            f"Unknown report section: "
            f"{section_name}"
        )

    context = load_context(
        context_path
    )

    user_prompt = build_user_prompt(
        section_name,
        context,
    )

    generated_text = generate_text(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    if not generated_text:

        raise ValueError(
            f"LLM returned empty text for section: "
            f"{section_name}"
        )

    validation = validate_section(
        generated_text,
        context,
    )

    if not validation["passed"]:

        issues_text = "\n".join(
            f"- {issue}"
            for issue in validation["issues"]
        )

        raise ValueError(
            "\n"
            "GROUNDING VALIDATION FAILED\n"
            f"Section: {section_name}\n\n"
            "Validation issues:\n"
            f"{issues_text}\n\n"
            "The generated section was rejected."
        )

    return generated_text


# ============================================================
# OPTIONAL HELPER
# ============================================================

def generate_section_with_result(
    section_name: str,
    context_path: Path,
) -> dict:
    """
    Optional helper for debugging/testing.

    Unlike generate_section(), this returns the generated
    text and validation result without raising an exception.
    """

    if section_name not in SECTION_PROMPTS:

        raise ValueError(
            f"Unknown report section: "
            f"{section_name}"
        )

    context = load_context(
        context_path
    )

    user_prompt = build_user_prompt(
        section_name,
        context,
    )

    generated_text = generate_text(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    validation = validate_section(
        generated_text,
        context,
    )

    return {
        "section": section_name,
        "generated_text": generated_text,
        "validation": validation,
    }

