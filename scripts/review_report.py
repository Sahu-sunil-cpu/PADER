import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DRAFT_REPORT, FINAL_REPORT, REVIEW_STATUS_OUTPUT, VALIDATION_OUTPUT


def load_status() -> dict:
    if REVIEW_STATUS_OUTPUT.exists():
        return json.loads(REVIEW_STATUS_OUTPUT.read_text(encoding="utf-8"))
    return {
        "status": "not_generated",
        # Before any review has happened, there is no final_report.md at
        # all -- only the unreviewed draft. FINAL_REPORT is created for
        # the first time by `approve`, below.
        "draft_report_path": str(DRAFT_REPORT),
        "final_report_path": None,
        "validation_path": str(VALIDATION_OUTPUT),
        "reviewer": None,
        "reason": None,
    }


def save_status(status: dict) -> None:
    REVIEW_STATUS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_STATUS_OUTPUT.write_text(
        json.dumps(status, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Approve or flag the generated PADER report.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status")

    approve = sub.add_parser("approve")
    approve.add_argument("--reviewer", required=True)

    flag = sub.add_parser("flag")
    flag.add_argument("--reviewer", required=True)
    flag.add_argument("--reason", required=True)

    args = parser.parse_args()
    status = load_status()

    if args.command == "status":
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return

    if not DRAFT_REPORT.exists():
        raise SystemExit(
            "No draft report found. Run `python scripts/generate_report.py` first."
        )

    if not VALIDATION_OUTPUT.exists():
        raise SystemExit(
            "Validation result not found. Run `python scripts/validate_report.py` first."
        )

    validation = json.loads(VALIDATION_OUTPUT.read_text(encoding="utf-8"))
    if args.command == "approve" and not validation.get("passed", False):
        raise SystemExit("Report cannot be approved because validation failed.")

    status.update(
        {
            "status": "approved" if args.command == "approve" else "flagged",
            "reviewer": args.reviewer,
            "reason": getattr(args, "reason", None),
            "reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
            "draft_report_path": str(DRAFT_REPORT),
            "validation_path": str(VALIDATION_OUTPUT),
        }
    )

    if args.command == "approve":
        # This is the moment FINAL_REPORT is created for the first time.
        # Before this line, no file named "final" exists anywhere on
        # disk for this run -- only the unreviewed draft did.
        shutil.copyfile(DRAFT_REPORT, FINAL_REPORT)
        status["final_report_path"] = str(FINAL_REPORT)
        save_status(status)
        print(f"Approved. Final report written to: {FINAL_REPORT}")
    else:
        status["final_report_path"] = None
        save_status(status)
        print("Report flagged for review. No final_report.md was created.")


if __name__ == "__main__":
    main()

