import json
import sys
from pathlib import Path


# ============================================================
# ADD PROJECT ROOT TO PYTHON PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from src.report.report_generator import (
    ReportGenerator,
)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CONTEXT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "report_context"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "generated_report"
)


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=" * 70
    )

    print(
        "PADER AI ENGINE - REPORT GENERATION"
    )

    print(
        "=" * 70
    )

    print(
        f"Context directory : {CONTEXT_DIR}"
    )

    print(
        f"Output directory  : {OUTPUT_DIR}"
    )

    generator = ReportGenerator(
        context_dir=CONTEXT_DIR,
        output_dir=OUTPUT_DIR,
    )

    sections = generator.generate_report()

    print(
        "\n"
        + "=" * 70
    )

    print(
        "GENERATED SECTIONS"
    )

    print(
        "=" * 70
    )

    for section_name in sections:

        print(
            f"  ✓ {section_name}"
        )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "REPORT GENERATION COMPLETED"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()