import json
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    ANALYSIS_OUTPUT,
    CASE_LISTING_OUTPUT,
    DATA_FILE,
    EVIDENCE_OUTPUT,
    OUTPUT_DIR,
    REPORT_CONTEXT_DIR,
)
from src.ingestion.loader import DataLoader
from src.preprocessing.validator import DataValidator
from src.preprocessing.canonicalizer import canonicalize_cases, version_audit
from src.preprocessing.reaction_parser import parse_reactions
from src.analysis.case_analysis import (
    alert_case_summary,
    case_summary,
    export_case_listing,
)
from src.analysis.demographics import demographic_summary
from src.analysis.reactions import reaction_summary
from src.analysis.trends import identify_trends, monthly_trend, reporting_period
from src.evidence.registry import EvidenceRegistry
from src.context.builder import ReportContextBuilder


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(value, file, indent=2, ensure_ascii=False)


def main() -> None:
    load_dotenv()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("PADER AI ENGINE - VERSION 0")
    print("=" * 70)

    # ========================================================
    # 1. LOAD
    # ========================================================
    print("\n[1] LOADING DATA")
    raw_df = DataLoader().load(DATA_FILE)
    print(f"Rows    : {len(raw_df):,}")
    print(f"Columns : {len(raw_df.columns):,}")

    # ========================================================
    # 2. VALIDATE
    # ========================================================
    print("\n[2] VALIDATING DATA")
    validator = DataValidator()
    validator.validate(raw_df)
    quality = validator.quality_summary(raw_df)
    print(f"Unique cases  : {quality['unique_cases']:,}")
    print(f"Missing values: {quality['missing_values']:,}")

    # ========================================================
    # 3. VERSION AUDIT + CANONICALIZATION
    # ========================================================
    print("\n[3] CASE VERSION AUDIT")
    audit = version_audit(raw_df)
    multiple_version_cases = int(audit["multiple_versions"].sum())
    print(f"Cases with multiple versions: {multiple_version_cases:,}")

    print("\n[4] CASE CANONICALIZATION")
    canonical_df = canonicalize_cases(raw_df)
    print(f"Raw rows       : {len(raw_df):,}")
    print(f"Canonical cases: {len(canonical_df):,}")

    # ========================================================
    # 5. REACTION PARSING
    # ========================================================
    print("\n[5] PARSING REACTIONS AND OUTCOMES")
    reaction_df = parse_reactions(raw_df)
    print(f"Parsed reaction records: {len(reaction_df):,}")

    # ========================================================
    # 6. DETERMINISTIC ANALYSIS
    # ========================================================
    print("\n[6] RUNNING DETERMINISTIC ANALYSIS")

    cases = case_summary(canonical_df)
    demographics = demographic_summary(canonical_df)
    reactions = reaction_summary(reaction_df, canonical_df)
    monthly = monthly_trend(canonical_df)
    trends = identify_trends(monthly)
    period = reporting_period(canonical_df)
    alerts = alert_case_summary(canonical_df, reaction_df)
    case_index = export_case_listing(canonical_df, reaction_df)

    analysis_results = {
        "data_quality": {
            "raw_rows": int(len(raw_df)),
            "columns": int(len(raw_df.columns)),
            "unique_cases": int(raw_df["safetyreportid"].nunique()),
            "canonical_cases": int(len(canonical_df)),
            "multiple_version_cases": multiple_version_cases,
            "parsed_reaction_records": int(len(reaction_df)),
            "missing_values": int(quality["missing_values"]),
        },
        "reporting_period": period,
        "case_summary": cases,
        "alert_summary": alerts,
        "demographics": demographics,
        "reactions": reactions,
        "monthly_trend": monthly,
        "trend_observations": trends,
        "case_index": case_index,
    }

    # ========================================================
    # 7. SAVE ANALYSIS
    # ========================================================
    print("\n[7] SAVING ANALYSIS RESULTS")
    save_json(ANALYSIS_OUTPUT, analysis_results)
    print(f"Saved: {ANALYSIS_OUTPUT}")
    print(f"Case listing: {CASE_LISTING_OUTPUT}")

    # ========================================================
    # 8. EVIDENCE REGISTRY
    # ========================================================
    print("\n[8] BUILDING EVIDENCE REGISTRY")
    registry = EvidenceRegistry()

    registry.add(
        "E001",
        "total_cases",
        cases["total_cases"],
        ["safetyreportid"],
        "Count unique safetyreportid after case canonicalization.",
    )
    registry.add(
        "E002",
        "serious_cases",
        cases["serious_cases"],
        ["safetyreportid", "serious"],
        "Count canonical cases where serious = serious.",
    )
    registry.add(
        "E003",
        "non_serious_cases",
        cases["non_serious_cases"],
        ["safetyreportid", "serious"],
        "Canonical case count minus serious case count.",
    )
    registry.add(
        "E004",
        "seriousness_breakdown",
        cases["seriousness_breakdown"],
        [
            "seriousnessdeath",
            "seriousnesslifethreatening",
            "seriousnesshospitalization",
            "seriousnessdisabling",
            "seriousnesscongenitalanomali",
            "seriousnessother",
        ],
        "Count independent affirmative seriousness flags.",
    )
    registry.add(
        "E005",
        "demographics",
        demographics,
        [
            "patient_patientsex",
            "patient_patientonsetage",
            "patient_patientonsetageunit",
            "occurcountry",
            "primarysourcecountry",
            "primarysource_reportercountry",
            "primarysource_qualification",
        ],
        "Frequency distributions using canonical case records.",
    )
    registry.add(
        "E006",
        "reaction_analysis",
        {
            "total_reaction_records": reactions["total_reaction_records"],
            "unique_reactions": reactions["unique_reactions"],
            "most_common_reactions": reactions["most_common_reactions"],
            "most_common_serious_reactions": reactions["most_common_serious_reactions"],
        },
        ["patient_reaction_reactionmeddrapt", "serious"],
        "Split reaction terms into reaction records and count overall and serious-case records.",
    )
    registry.add(
        "E007",
        "outcome_distribution",
        reactions["outcome_distribution"],
        ["patient_reaction_reactionoutcome"],
        "Count individual reaction outcome records with case-version rows retained at reaction level.",
    )
    registry.add(
        "E008",
        "monthly_case_trend",
        monthly,
        ["receivedate", "safetyreportid"],
        "Count canonical cases by month of receivedate.",
    )
    registry.add(
        "E009",
        "trend_observations",
        trends,
        ["receivedate", "safetyreportid"],
        "Identify peak month, lowest month, and supplied descriptive average.",
    )
    registry.add(
        "E010",
        "reporting_period",
        period,
        ["receivedate"],
        "Minimum and maximum valid receivedate values from canonical cases.",
    )
    registry.add(
        "E011",
        "15_day_alerts",
        alerts,
        ["safetyreportid", "serious", "fulfillexpeditecriteria"],
        "Count canonical cases explicitly flagged by fulfillexpeditecriteria and summarize their linked reaction records.",
    )
    registry.add(
        "E012",
        "case_listing",
        case_index,
        [
            "safetyreportid",
            "patient_reaction_reactionmeddrapt",
            "serious",
            "receivedate",
            "occurcountry",
            "patient_reaction_reactionoutcome",
        ],
        "Join parsed reaction records to canonical case attributes to create a traceable CSV listing.",
    )

    registry.save(EVIDENCE_OUTPUT)
    print(f"Saved: {EVIDENCE_OUTPUT}")

    # ========================================================
    # 9. BUILD SECTION-SPECIFIC CONTEXT
    # ========================================================
    print("\n[9] BUILDING REPORT CONTEXT")
    context_builder = ReportContextBuilder(
        analysis_results_path=ANALYSIS_OUTPUT,
        evidence_registry_path=EVIDENCE_OUTPUT,
        output_dir=REPORT_CONTEXT_DIR,
    )
    generated_context = context_builder.save_all()

    print(f"Generated {len(generated_context)} section context packets.")
    for name, path in generated_context.items():
        print(f"  {name}: {path}")

    # ========================================================
    # 10. SUMMARY
    # ========================================================
    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    print(f"Reporting period      : {period.get('start_date')} to {period.get('end_date')}")
    print(f"Raw rows              : {len(raw_df):,}")
    print(f"Canonical cases       : {len(canonical_df):,}")
    print(f"Multiple-version cases: {multiple_version_cases:,}")
    print(f"Reaction records      : {len(reaction_df):,}")
    print(f"Serious cases         : {cases['serious_cases']:,}")
    print(f"Non-serious cases     : {cases['non_serious_cases']:,}")
    print(f"15-day alert cases    : {alerts['alert_cases']:,}")
    print(f"Serious alert cases   : {alerts['serious_alert_cases']:,}")
    print(f"Listing rows          : {case_index['listing_rows']:,}")
    print(f"Peak month            : {trends['peak_month']} ({trends['peak_cases']:,})")
    print(f"Lowest month          : {trends['lowest_month']} ({trends['lowest_cases']:,})")
    print("\nVERSION 0 DETERMINISTIC PIPELINE COMPLETED")


if __name__ == "__main__":
    main()
