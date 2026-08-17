"""
Generate the final DOCX deliverable -- but only from a report that has
actually been approved by a human reviewer.

This is the human-review gate in practice: this script refuses to run
unless outputs/generated_report/review_status.json says status ==
"approved". Until that happens, no file named final_report.md exists
at all -- only draft_report.md, the unreviewed auto-generated output.
review_report.py's `approve` command is the only thing that ever
creates final_report.md, by copying draft_report.md at the moment of
approval. This script then builds the DOCX from that file.

Run order:
    python scripts/generate_report.py     # generates final_report.md
    python scripts/validate_report.py     # writes validation_result.json
    python scripts/review_report.py status
    python scripts/review_report.py approve --reviewer "your name"
    python scripts/generate_docx.py       # only works after approval
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json

from src.config import GENERATED_REPORT_DIR, REVIEW_STATUS_OUTPUT
from src.report.docx_generator import generate_docx


def main() -> None:
    print("=" * 70)
    print("PADER DOCX GENERATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Human review gate
    # --------------------------------------------------------
    if not REVIEW_STATUS_OUTPUT.exists():
        raise SystemExit(
            "No review status found.\n"
            "Run `python scripts/validate_report.py` then "
            "`python scripts/review_report.py approve --reviewer <name>` "
            "before generating the DOCX."
        )

    review_status = json.loads(REVIEW_STATUS_OUTPUT.read_text(encoding="utf-8"))

    if review_status.get("status") != "approved":
        raise SystemExit(
            f"Report is not approved (current status: "
            f"{review_status.get('status', 'unknown')}).\n"
            "DOCX generation is blocked until a human reviewer runs:\n"
            "  python scripts/review_report.py approve --reviewer <name>"
        )

    print(f"Review status : approved")
    print(f"Reviewer      : {review_status.get('reviewer')}")
    print(f"Reviewed at   : {review_status.get('reviewed_at_utc')}")

    # --------------------------------------------------------
    # Build the DOCX from FINAL_REPORT, which only exists at all
    # because the approve step above created it. Its existence is
    # itself part of the gate, not just the status field.
    # --------------------------------------------------------
    final_path_str = review_status.get("final_report_path")
    if not final_path_str:
        raise SystemExit(
            "review_status.json is marked approved but has no "
            "final_report_path. Re-run the approve command."
        )

    markdown_path = Path(final_path_str)
    docx_path = GENERATED_REPORT_DIR / "final_report.docx"

    print(f"\nSource (approved, final): {markdown_path}")
    print(f"Output                  : {docx_path}")

    if not markdown_path.exists():
        raise FileNotFoundError(
            f"final_report.md not found even though review_status.json "
            f"says approved: {markdown_path}"
        )

    print("\nGenerating DOCX...")
    generated_path = generate_docx(
        markdown_path=markdown_path,
        output_path=docx_path,
    )

    if not generated_path.exists() or generated_path.stat().st_size == 0:
        raise RuntimeError("DOCX generation reported success but output is missing or empty.")

    print(f"\nDOCX generated: {generated_path}")
    print(f"Size: {generated_path.stat().st_size:,} bytes")
    print("\n" + "=" * 70)
    print("DOCX GENERATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
