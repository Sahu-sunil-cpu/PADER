import json
import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORT CURRENT VALIDATOR
# ============================================================

from src.config import (
    REPORT_CONTEXT_DIR,
    GENERATED_REPORT_DIR,
    DRAFT_REPORT,
    VALIDATION_OUTPUT,
)
from src.report.report_validator import (
    validate_final_report,
    save_validation_result,
)


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    # --------------------------------------------------------
    # Project paths (from src.config, so every script agrees on
    # the same filenames - a local hardcoded path here previously
    # diverged from what review_report.py expected to read)
    # --------------------------------------------------------

    context_dir = REPORT_CONTEXT_DIR

    generated_report_dir = GENERATED_REPORT_DIR

    report_path = DRAFT_REPORT

    sections_dir = (
        generated_report_dir
        / "sections"
    )

    validation_path = VALIDATION_OUTPUT

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
    # Check required paths before validation
    # --------------------------------------------------------

    if not context_dir.exists():

        print(
            "\nERROR: Report context directory does not exist:"
        )

        print(context_dir)

        print(
            "\nRun the data/context generation pipeline first."
        )

        raise SystemExit(1)

    if not report_path.exists():

        print(
            "\nERROR: Final report does not exist:"
        )

        print(report_path)

        print(
            "\nRun report generation first."
        )

        raise SystemExit(1)

    # --------------------------------------------------------
    # Validate final report
    # --------------------------------------------------------

    result = validate_final_report(
        report_path=report_path,
        context_dir=context_dir,
        sections_dir=sections_dir,
    )

    # --------------------------------------------------------
    # Save validation result
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

        print(
            f"\nValidation result saved to:"
        )

        print(validation_path)

    else:

        print(
            "FINAL REPORT VALIDATION FAILED"
        )

        print(
            "=" * 70
        )

        print(
            f"\nValidation result saved to:"
        )

        print(validation_path)

        raise SystemExit(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()