import json
from pathlib import Path


class EvidenceRegistry:

    def __init__(self):
        self.evidence = []

    def add(
        self,
        evidence_id: str,
        metric: str,
        value,
        source_columns: list[str],
        calculation: str,
    ) -> None:

        self.evidence.append(
            {
                "evidence_id": evidence_id,
                "metric": metric,
                "value": value,
                "source_columns": source_columns,
                "calculation": calculation,
            }
        )

    def get_all(self) -> list:

        return self.evidence

    def save(self, path: str | Path) -> None:

        path = Path(path)
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                self.evidence,
                f,
                indent=2,
                ensure_ascii=False,
            )