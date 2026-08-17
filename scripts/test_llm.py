import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.llm.client import generate_text


def main():

    response = generate_text(
        system_prompt=(
            "You are a helpful assistant. "
            "Respond briefly."
        ),
        user_prompt=(
            "Explain what a pharmacovigilance report is "
            "in one sentence."
        ),
    )

    print("\nLLM RESPONSE")
    print("=" * 60)
    print(response)


if __name__ == "__main__":
    main()