import json
from pathlib import Path
from typing import Any

from src.config import OUTPUT_DIR


class ReportContextBuilder:
    """
    Converts deterministic analysis + evidence registry into
    section-specific context packets.

    The LLM receives only the scoped evidence required by a section;
    it never receives the raw dataset.
    """

    def __init__(
        self,
        analysis_results_path: Path,
        evidence_registry_path: Path,
        output_dir: Path = OUTPUT_DIR / "report_context",
    ):
        self.analysis_results_path = Path(analysis_results_path)
        self.evidence_registry_path = Path(evidence_registry_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.analysis_results = self._load_json(self.analysis_results_path)
        self.evidence_registry = self._load_json(self.evidence_registry_path)
        self.evidence_map = {
            item["evidence_id"]: item
            for item in self.evidence_registry
            if "evidence_id" in item
        }

    @staticmethod
    def _load_json(path: Path) -> Any:
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _get_analysis(self, key: str, default: Any = None) -> Any:
        return self.analysis_results.get(key, default)

    def _get_evidence(self, evidence_id: str) -> dict:
        return self.evidence_map.get(evidence_id, {})

    def _save_context(self, section_name: str, context: dict) -> Path:
        path = self.output_dir / f"{section_name}.json"
        with open(path, "w", encoding="utf-8") as file:
            json.dump(context, file, indent=2, ensure_ascii=False)
        return path

    # ========================================================
    # REPORTING PERIOD
    # ========================================================

    def build_reporting_period(self) -> dict:
        period = self._get_analysis("reporting_period", {})
        monthly = self._get_analysis("monthly_trend", {})

        return {
            "section": "Reporting Period",
            "approved_evidence": {
                "start_date": period.get("start_date"),
                "end_date": period.get("end_date"),
                "start_month": period.get("start_month"),
                "end_month": period.get("end_month"),
                "months_with_data": list(monthly.keys()),
                "monthly_case_counts": monthly,
            },
            "evidence_ids": ["E010", "E008"],
            "instructions": [
                "State the exact reporting period only when supported by receivedate.",
                "Do not invent an NDA/application identifier because none is supplied.",
                "Do not infer a reporting frequency beyond the supplied dates.",
            ],
        }

    # ========================================================
    # NARRATIVE SUMMARY
    # ========================================================

    def build_narrative_summary(self) -> dict:
        cases = self._get_analysis("case_summary", {})
        alerts = self._get_analysis("alert_summary", {})
        demographics = self._get_analysis("demographics", {})
        reactions = self._get_analysis("reactions", {})
        period = self._get_analysis("reporting_period", {})
        trends = self._get_analysis("trend_observations", {})

        return {
            "section": "Narrative Summary and Analysis",
            "approved_evidence": {
                "reporting_period": period,
                "total_cases": cases.get("total_cases"),
                "serious_cases": cases.get("serious_cases"),
                "non_serious_cases": cases.get("non_serious_cases"),
                "serious_percentage": cases.get("serious_percentage"),
                "15_day_alerts": {
                    "alert_cases": alerts.get("alert_cases"),
                    "serious_alert_cases": alerts.get("serious_alert_cases"),
                },
                "seriousness_breakdown": cases.get("seriousness_breakdown", {}),
                "demographics": demographics,
                "top_reactions": reactions.get("most_common_reactions", {}),
                "top_serious_reactions": reactions.get("most_common_serious_reactions", {}),
                "outcome_distribution": reactions.get("outcome_distribution", {}),
                "trend_observation": trends,
            },
            "evidence_ids": ["E001", "E002", "E003", "E004", "E005", "E006", "E007", "E009", "E010", "E011"],
            "instructions": [
                "Summarize only the supplied evidence.",
                "Report 15-day Alert counts when alert evidence is present.",
                "Report major reactions and serious reactions descriptively.",
                "Demographics are descriptive only; do not infer risk or clinical significance.",
                "Seriousness categories are independent and may overlap.",
                "Reaction counts refer to reaction records unless explicitly identified otherwise.",
                "Do not infer causality or safety signals.",
                "Do not perform new arithmetic.",
            ],
        }

    # ========================================================
    # CASE SUMMARY
    # ========================================================

    def build_case_summary(self) -> dict:
        cases = self._get_analysis("case_summary", {})
        demographics = self._get_analysis("demographics", {})
        reactions = self._get_analysis("reactions", {})

        return {
            "section": "Summary Analysis of Cases",
            "approved_evidence": {
                "total_cases": cases.get("total_cases"),
                "serious_cases": cases.get("serious_cases"),
                "non_serious_cases": cases.get("non_serious_cases"),
                "serious_percentage": cases.get("serious_percentage"),
                "seriousness_breakdown": cases.get("seriousness_breakdown", {}),
                "age_groups": demographics.get("age_groups", {}),
                "sex": demographics.get("sex", {}),
                "occurrence_country": demographics.get("occurrence_country", {}),
                "primary_source_country": demographics.get("primary_source_country", {}),
                "reporter_country": demographics.get("reporter_country", {}),
                "reporter_qualification": demographics.get("reporter_qualification", {}),
                "outcome_distribution": reactions.get("outcome_distribution", {}),
            },
            "evidence_ids": ["E001", "E002", "E003", "E004", "E005", "E007"],
            "instructions": [
                "Report supplied counts exactly.",
                "Describe demographic distributions without clinical interpretation.",
                "Seriousness categories may overlap; never add them to derive a total.",
                "Use occurrence country as the primary geographic distribution and label it clearly.",
                "Do not infer causality, risk factors, or clinical significance.",
            ],
        }

    # ========================================================
    # REACTION ANALYSIS
    # ========================================================

    def build_reaction_analysis(self) -> dict:
        reactions = self._get_analysis("reactions", {})

        return {
            "section": "Reaction / Adverse Event Analysis",
            "approved_evidence": {
                "total_reaction_records": reactions.get("total_reaction_records"),
                "unique_reactions": reactions.get("unique_reactions"),
                "most_common_reactions": reactions.get("most_common_reactions", {}),
                "most_common_serious_reactions": reactions.get("most_common_serious_reactions", {}),
                "outcome_distribution": reactions.get("outcome_distribution", {}),
            },
            "evidence_ids": ["E006", "E007"],
            "instructions": [
                "Report MedDRA Preferred Terms at the PT level.",
                "Report both overall and serious-case reaction frequencies when present.",
                "State that reaction counts represent reaction records, not unique cases.",
                "Outcome counts also refer to reaction records.",
                "Do not invent System Organ Class groupings.",
                "Do not infer causality.",
            ],
        }

    # ========================================================
    # SERIOUS CASES / 15-DAY ALERTS
    # ========================================================

    def build_serious_cases(self) -> dict:
        cases = self._get_analysis("case_summary", {})
        alerts = self._get_analysis("alert_summary", {})
        reactions = self._get_analysis("reactions", {})

        return {
            "section": "Serious Cases / 15-Day Alerts",
            "approved_evidence": {
                "total_cases": cases.get("total_cases"),
                "serious_cases": cases.get("serious_cases"),
                "non_serious_cases": cases.get("non_serious_cases"),
                "serious_percentage": cases.get("serious_percentage"),
                "seriousness_breakdown": cases.get("seriousness_breakdown", {}),
                "15_day_alerts": alerts,
                "top_serious_reactions": reactions.get("most_common_serious_reactions", {}),
            },
            "evidence_ids": ["E002", "E003", "E004", "E006", "E011"],
            "instructions": [
                "Use fulfillexpeditecriteria as the explicit dataset field for Alert-case identification.",
                "Report alert counts only from the supplied alert evidence.",
                "Seriousness categories are independent and may overlap.",
                "Do not add seriousness categories together.",
                "Do not invent expectedness, labeling status, submission dates, or case narratives.",
                "Do not infer causality or clinical significance.",
            ],
        }

    # ========================================================
    # TRENDS
    # ========================================================

    def build_trends(self) -> dict:
        monthly = self._get_analysis("monthly_trend", {})
        trends = self._get_analysis("trend_observations", {})
        period = self._get_analysis("reporting_period", {})

        return {
            "section": "Trends and Important Observations",
            "approved_evidence": {
                "reporting_period": period,
                "monthly_case_counts": monthly,
                "trend_observation": trends,
            },
            "evidence_ids": ["E008", "E009", "E010"],
            "instructions": [
                "Describe temporal observations only.",
                "Use supplied dates and counts exactly.",
                "Do not perform new calculations.",
                "Do not infer causality or a safety signal.",
            ],
        }

    # ========================================================
    # HISTORY OF ACTIONS
    # ========================================================

    def build_history_of_actions(self) -> dict:
        return {
            "section": "History of Actions",
            "approved_evidence": {
                "actions_provided": False,
                "statement": "No history-of-actions information was supplied with the dataset.",
            },
            "evidence_ids": [],
            "instructions": [
                "Explicitly state that no history-of-actions information was supplied.",
                "Do not invent labeling changes, regulatory communications, studies, or risk-minimization actions.",
            ],
        }

    # ========================================================
    # CASE INDEX
    # ========================================================

    def build_case_index(self) -> dict:
        case_index = self._get_analysis("case_index", {})

        return {
            "section": "Case Index / Listing",
            "approved_evidence": case_index,
            "evidence_ids": ["E001", "E012"],
            "instructions": [
                "State that a structured CSV case listing accompanies the report.",
                "Use the supplied listing filename and fields exactly.",
                "Do not enumerate individual case records in prose.",
                "Do not invent case information.",
            ],
        }

    # ========================================================
    # BUILD + SAVE ALL
    # ========================================================

    def build_all(self) -> dict[str, dict]:
        return {
            "reporting_period": self.build_reporting_period(),
            "narrative_summary": self.build_narrative_summary(),
            "case_summary": self.build_case_summary(),
            "reaction_analysis": self.build_reaction_analysis(),
            "serious_cases": self.build_serious_cases(),
            "trends": self.build_trends(),
            "history_of_actions": self.build_history_of_actions(),
            "case_index": self.build_case_index(),
        }

    def save_all(self) -> dict[str, Path]:
        saved = {}
        for section_name, context in self.build_all().items():
            saved[section_name] = self._save_context(section_name, context)
        return saved
