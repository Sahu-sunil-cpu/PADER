import json
import re
from pathlib import Path
from typing import Any


# ============================================================
# CONFIGURATION
# ============================================================

REPORT_SECTIONS = [
    "reporting_period",
    "narrative_summary",
    "case_summary",
    "reaction_analysis",
    "serious_cases",
    "trends",
    "history_of_actions",
    "case_index",
]


# ============================================================
# GENERIC HELPERS
# ============================================================

def load_json(path: Path) -> dict:
    """
    Load a JSON file.
    """

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def read_text(path: Path) -> str:
    """
    Read a text/markdown file.
    """

    return path.read_text(
        encoding="utf-8"
    )


def normalise_number(value: Any) -> str:
    """
    Convert a numeric value to a canonical representation.

    Examples:
        1,024 -> 1024
        1024  -> 1024
        99.9  -> 99.9
    """

    if value is None:
        return ""

    text = str(value).strip()

    text = text.replace(",", "")

    if text.endswith("%"):
        text = text[:-1]

    return text.strip()


# ============================================================
# EXTRACT NUMBERS FROM TEXT
# ============================================================

def extract_numbers(text: str) -> list[str]:
    """
    Extract numeric values from text.

    Dates such as 2025-07 are protected so that:
        2025
        07

    are not incorrectly extracted as independent values.
    """

    if not text:
        return []

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
            f"__DATE_{index}__"
        )

        protected = protected.replace(
            date_value,
            placeholder,
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
            f"__PERCENT_{index}__"
        )

        protected = protected.replace(
            percentage,
            placeholder,
        )

    # --------------------------------------------------------
    # Extract numbers
    # --------------------------------------------------------

    matches = re.findall(
        r"(?<![\w-])"
        r"\d+(?:,\d{3})*"
        r"(?:\.\d+)?"
        r"(?![\w-])",
        protected,
    )

    return [
        normalise_number(value)
        for value in matches
    ]


# ============================================================
# EXTRACT PERCENTAGES
# ============================================================

def extract_percentages(text: str) -> list[str]:
    """
    Extract percentages such as:

        99.9%
        35%
    """

    if not text:
        return []

    matches = re.findall(
        r"\b\d+(?:\.\d+)?\s*%",
        text,
    )

    return [
        normalise_number(value)
        for value in matches
    ]


# ============================================================
# EXTRACT DATES
# ============================================================

def extract_dates(text: str) -> list[str]:
    """
    Extract dates/months/years.
    """

    if not text:
        return []

    return re.findall(
        r"\b\d{4}(?:-\d{2}(?:-\d{2})?)?\b",
        text,
    )


# ============================================================
# EXTRACT EVIDENCE VALUES
# ============================================================

def extract_evidence_numbers(
    evidence: Any,
) -> set[str]:
    """
    Recursively extract numeric values from evidence.
    """

    values: set[str] = set()

    if isinstance(evidence, dict):

        for key, value in evidence.items():

            # Numeric values inside dictionary keys.
            key_text = str(key)

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
                    values.add(
                        normalise_number(match)
                    )

            values.update(
                extract_evidence_numbers(value)
            )

        return values

    if isinstance(evidence, list):

        for item in evidence:

            values.update(
                extract_evidence_numbers(item)
            )

        return values

    if isinstance(evidence, tuple):

        for item in evidence:

            values.update(
                extract_evidence_numbers(item)
            )

        return values

    if isinstance(evidence, (int, float)):

        values.add(
            normalise_number(evidence)
        )

        return values

    if isinstance(evidence, str):

        # Remove dates before extracting standalone numbers.
        protected = re.sub(
            r"\b\d{4}(?:-\d{2}(?:-\d{2})?)?\b",
            "",
            evidence,
        )

        matches = re.findall(
            r"(?<![\w-])"
            r"\d+(?:,\d{3})*"
            r"(?:\.\d+)?"
            r"(?![\w-])",
            protected,
        )

        for match in matches:

            values.add(
                normalise_number(match)
            )

    return values


# ============================================================
# EXTRACT EVIDENCE PERCENTAGES
# ============================================================

def extract_evidence_percentages(
    evidence: Any,
) -> set[str]:
    """
    Extract explicitly approved percentages.

    A numeric value such as 99.9 is NOT automatically
    interpreted as 99.9%.
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
                        normalise_number(value)
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
                            normalise_number(match)
                        )

            percentages.update(
                extract_evidence_percentages(
                    value
                )
            )

        return percentages

    if isinstance(evidence, list):

        for item in evidence:

            percentages.update(
                extract_evidence_percentages(
                    item
                )
            )

    return percentages


# ============================================================
# EXTRACT EVIDENCE DATES
# ============================================================

def extract_evidence_dates(
    evidence: Any,
) -> set[str]:
    """
    Extract approved dates from evidence.
    """

    dates: set[str] = set()

    if isinstance(evidence, dict):

        for key, value in evidence.items():

            key_text = str(key).strip()

            if re.fullmatch(
                r"\d{4}",
                key_text,
            ):

                dates.add(key_text)

            elif re.fullmatch(
                r"\d{4}-\d{2}",
                key_text,
            ):

                dates.add(key_text)

            elif re.fullmatch(
                r"\d{4}-\d{2}-\d{2}",
                key_text,
            ):

                dates.add(key_text)

            dates.update(
                extract_evidence_dates(value)
            )

        return dates

    if isinstance(evidence, list):

        for item in evidence:

            dates.update(
                extract_evidence_dates(item)
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
# LOAD ALL APPROVED EVIDENCE
# ============================================================

def load_all_approved_evidence(
    context_dir: Path,
) -> dict:
    """
    Load approved evidence from all section context files.

    Returns one combined dictionary.
    """

    combined: dict[str, Any] = {}

    for section_name in REPORT_SECTIONS:

        possible_paths = [
            context_dir
            / f"{section_name}.json",

            context_dir
            / f"{section_name}_context.json",
        ]

        context_path = None

        for path in possible_paths:

            if path.exists():

                context_path = path
                break

        if context_path is None:
            continue

        context = load_json(
            context_path
        )

        approved_evidence = context.get(
            "approved_evidence",
            context,
        )

        combined[
            section_name
        ] = approved_evidence

    return combined


# ============================================================
# COMBINE EVIDENCE
# ============================================================

def combine_evidence(
    evidence: dict,
) -> dict:
    """
    Return a combined evidence structure.

    Keeping section boundaries allows future validators
    to perform section-specific checks.
    """

    return {
        "sections": evidence,
    }


# ============================================================
# CHECK SECTION FILES
# ============================================================

def validate_section_files(
    sections_dir: Path,
) -> list[str]:
    """
    Check that all expected generated sections exist.
    """

    issues: list[str] = []

    for section_name in REPORT_SECTIONS:

        path = (
            sections_dir
            / f"{section_name}.md"
        )

        if not path.exists():

            issues.append(
                f"Missing generated section: "
                f"{section_name}"
            )

            continue

        content = path.read_text(
            encoding="utf-8"
        ).strip()

        if not content:

            issues.append(
                f"Empty generated section: "
                f"{section_name}"
            )

    return issues


# ============================================================
# CHECK NUMERIC GROUNDING
# ============================================================

def validate_report_numbers(
    report_text: str,
    approved_evidence: dict,
) -> list[str]:
    """
    Validate numeric values in the final report.

    This is intentionally conservative.

    A number is considered valid if it occurs somewhere in
    the approved evidence.
    """

    issues: list[str] = []

    evidence_numbers = (
        extract_evidence_numbers(
            approved_evidence
        )
    )

    generated_numbers = (
        extract_numbers(
            report_text
        )
    )

    for number in generated_numbers:

        if not number:
            continue

        if number in evidence_numbers:
            continue

        issues.append(
            f"Report contains numeric value not "
            f"found in approved evidence: {number}"
        )

    return sorted(
        set(issues)
    )


# ============================================================
# CHECK PERCENTAGES
# ============================================================

def validate_report_percentages(
    report_text: str,
    approved_evidence: dict,
) -> list[str]:
    """
    Validate percentages in the final report.
    """

    issues: list[str] = []

    approved_percentages = (
        extract_evidence_percentages(
            approved_evidence
        )
    )

    generated_percentages = (
        extract_percentages(
            report_text
        )
    )

    for percentage in generated_percentages:

        if percentage not in approved_percentages:

            issues.append(
                "Report contains unsupported "
                f"percentage: {percentage}%"
            )

    return sorted(
        set(issues)
    )


# ============================================================
# CHECK DATES
# ============================================================

def validate_report_dates(
    report_text: str,
    approved_evidence: dict,
) -> list[str]:
    """
    Validate dates/months/years in final report.
    """

    issues: list[str] = []

    approved_dates = (
        extract_evidence_dates(
            approved_evidence
        )
    )

    evidence_text = json.dumps(
        approved_evidence,
        ensure_ascii=False,
    )

    generated_dates = (
        extract_dates(
            report_text
        )
    )

    for date_value in generated_dates:

        if date_value in approved_dates:
            continue

        # Allow a date if it is explicitly present somewhere
        # in the serialized evidence.
        if date_value in evidence_text:
            continue

        issues.append(
            "Report contains unsupported "
            f"date/year: {date_value}"
        )

    return sorted(
        set(issues)
    )


# ============================================================
# CHECK FOR UNSUPPORTED CAUSALITY
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


def validate_causality(
    report_text: str,
) -> list[str]:
    """
    Detect unsupported causal language.
    """

    issues: list[str] = []

    lower_text = report_text.lower()

    for pattern in CAUSALITY_PATTERNS:

        if re.search(
            pattern,
            lower_text,
        ):

            issues.append(
                "Potential unsupported causality "
                f"statement: {pattern}"
            )

    return sorted(
        set(issues)
    )


# ============================================================
# CHECK RISK / SAFETY LANGUAGE
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


def validate_risk_language(
    report_text: str,
) -> list[str]:
    """
    Detect unsupported risk/safety conclusions.
    """

    issues: list[str] = []

    lower_text = report_text.lower()

    for pattern in RISK_PATTERNS:

        if re.search(
            pattern,
            lower_text,
        ):

            issues.append(
                "Potential unsupported "
                f"risk/safety conclusion: {pattern}"
            )

    return sorted(
        set(issues)
    )


# ============================================================
# CHECK REQUIRED REPORT SECTIONS
# ============================================================

def validate_required_sections(
    report_text: str,
) -> list[str]:
    """
    Ensure the final report contains the expected headings.
    """

    issues: list[str] = []

    required_headings = [
        "Reporting Period",
        "Narrative Summary",
        "Case Summary",
        "Reaction Analysis",
        "Serious Cases",
        "Trends",
        "History of Actions",
        "Case Index",
    ]

    for heading in required_headings:

        if heading.lower() not in report_text.lower():

            issues.append(
                f"Missing required report section: "
                f"{heading}"
            )

    return issues


# ============================================================
# CHECK EMPTY REPORT
# ============================================================

def validate_report_not_empty(
    report_text: str,
) -> list[str]:
    """
    Basic report sanity check.
    """

    if not report_text.strip():

        return [
            "Final report is empty."
        ]

    return []


# ============================================================
# FINAL REPORT VALIDATION
# ============================================================

def validate_final_report(
    report_path: Path,
    context_dir: Path,
    sections_dir: Path | None = None,
) -> dict:
    """
    Validate the assembled final report.

    Checks:

    1. Report exists
    2. Required sections exist
    3. Generated section files exist
    4. Numeric grounding
    5. Percentage grounding
    6. Date grounding
    7. Causality
    8. Risk/safety language
    """

    issues: list[str] = []

    # --------------------------------------------------------
    # Check report existence
    # --------------------------------------------------------

    if not report_path.exists():

        return {
            "passed": False,
            "issues": [
                f"Final report not found: {report_path}"
            ],
        }

    report_text = read_text(
        report_path
    )

    # --------------------------------------------------------
    # Load evidence
    # --------------------------------------------------------

    evidence_by_section = (
        load_all_approved_evidence(
            context_dir
        )
    )

    approved_evidence = combine_evidence(
        evidence_by_section
    )

    # --------------------------------------------------------
    # Basic checks
    # --------------------------------------------------------

    issues.extend(
        validate_report_not_empty(
            report_text
        )
    )

    issues.extend(
        validate_required_sections(
            report_text
        )
    )

    # --------------------------------------------------------
    # Section file checks
    # --------------------------------------------------------

    if sections_dir is not None:

        issues.extend(
            validate_section_files(
                sections_dir
            )
        )

    # --------------------------------------------------------
    # Grounding checks
    # --------------------------------------------------------

    issues.extend(
        validate_report_numbers(
            report_text,
            approved_evidence,
        )
    )

    issues.extend(
        validate_report_percentages(
            report_text,
            approved_evidence,
        )
    )

    issues.extend(
        validate_report_dates(
            report_text,
            approved_evidence,
        )
    )

    # --------------------------------------------------------
    # Safety checks
    # --------------------------------------------------------

    issues.extend(
        validate_causality(
            report_text
        )
    )

    issues.extend(
        validate_risk_language(
            report_text
        )
    )

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    issues = sorted(
        set(issues)
    )

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "report_path": str(report_path),
        "sections_checked": len(
            REPORT_SECTIONS
        ),
    }


# ============================================================
# SAVE VALIDATION RESULT
# ============================================================

def save_validation_result(
    result: dict,
    output_path: Path,
) -> Path:
    """
    Save validation result as JSON.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            result,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return output_path


# ============================================================
# COMMAND-LINE ENTRY POINT
# ============================================================

def main() -> None:

    # --------------------------------------------------------
    # Project paths
    # --------------------------------------------------------

    project_root = (
        Path(__file__)
        .resolve()
        .parents[2]
    )

    context_dir = (
        project_root
        / "outputs"
        / "report_context"
    )

    generated_report_dir = (
        project_root
        / "outputs"
        / "generated_report"
    )

    report_path = (
        generated_report_dir
        / "draft_report.md"
    )

    sections_dir = (
        generated_report_dir
        / "sections"
    )

    validation_path = (
        generated_report_dir
        / "validation_report.json"
    )

    # --------------------------------------------------------
    # Print configuration
    # --------------------------------------------------------

    print(
        "\n"
        + "=" * 70
    )

    print(
        "PADER FINAL REPORT VALIDATION"
    )

    print(
        "=" * 70
    )

    print(
        f"Report   : {report_path}"
    )

    print(
        f"Evidence : {context_dir}"
    )

    print(
        f"Sections : {sections_dir}"
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    result = validate_final_report(
        report_path=report_path,
        context_dir=context_dir,
        sections_dir=sections_dir,
    )

    # --------------------------------------------------------
    # Save result
    # --------------------------------------------------------

    save_validation_result(
        result,
        validation_path,
    )

    # --------------------------------------------------------
    # Print result
    # --------------------------------------------------------

    print(
        "\n"
        + "=" * 70
    )

    print(
        "VALIDATION RESULT"
    )

    print(
        "=" * 70
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )

    print(
        "\n"
        + "=" * 70
    )

    if result["passed"]:

        print(
            "FINAL REPORT VALIDATION PASSED"
        )

        print(
            "=" * 70
        )

    else:

        print(
            "FINAL REPORT VALIDATION FAILED"
        )

        print(
            "=" * 70
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()