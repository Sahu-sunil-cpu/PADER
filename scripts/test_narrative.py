import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pathlib import Path

from src.llm.generator import (
    generate_section,
)


def main():

    context_path = Path(
        "outputs/report_context/narrative_summary.json"
    )

    generated_text = generate_section(
        section_name="narrative_summary",
        context_path=context_path,
    )

    print()
    print("=" * 70)
    print("GENERATED NARRATIVE SUMMARY")
    print("=" * 70)
    print()
    print(generated_text)


if __name__ == "__main__":
    main()