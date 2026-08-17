from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

DATA_FILE = DATA_DIR / "Bisoprolol_icsr_sample_1068rows.xlsx"


# ============================================================
# REPORT
# ============================================================

REPORT_NAME = "Bisoprolol PADER"
PRODUCT_NAME = "Bisoprolol"
REPORT_TYPE = "PADER-style Periodic Adverse Event Data Report"


# ============================================================
# CORE DATA COLUMNS
# ============================================================

CASE_ID = "safetyreportid"
VERSION = "safetyreportversion"

RECEIVED_DATE = "receivedate"

SERIOUS = "serious"
EXPEDITED = "fulfillexpeditecriteria"

SEX = "patient_patientsex"
AGE = "patient_patientonsetage"
AGE_UNIT = "patient_patientonsetageunit"

REACTION = "patient_reaction_reactionmeddrapt"
OUTCOME = "patient_reaction_reactionoutcome"

COUNTRY = "occurcountry"
PRIMARY_SOURCE_COUNTRY = "primarysourcecountry"
REPORTER_COUNTRY = "primarysource_reportercountry"
REPORTER_QUALIFICATION = "primarysource_qualification"


# ============================================================
# ANALYSIS CONFIGURATION
# ============================================================

TOP_N_REACTIONS = 10
TOP_N_COUNTRIES = 10


# ============================================================
# OUTPUT FILES
# ============================================================

ANALYSIS_OUTPUT = OUTPUT_DIR / "analysis_results.json"
EVIDENCE_OUTPUT = OUTPUT_DIR / "evidence_registry.json"
CASE_LISTING_OUTPUT = OUTPUT_DIR / "case_listing.csv"

GENERATED_REPORT_DIR = OUTPUT_DIR / "generated_report"

# DRAFT_REPORT is what the generation pipeline writes automatically,
# unreviewed. FINAL_REPORT is only ever created by review_report.py's
# `approve` command, as a copy of DRAFT_REPORT taken at approval time.
# Nothing downstream (validate_report.py aside, which validates the
# draft) should read FINAL_REPORT before it exists -- its mere
# existence is itself the signal that a human has approved this report.
DRAFT_REPORT = GENERATED_REPORT_DIR / "draft_report.md"
GENERATED_SECTIONS_OUTPUT = GENERATED_REPORT_DIR / "generated_sections.json"
FINAL_REPORT = GENERATED_REPORT_DIR / "final_report.md"
VALIDATION_OUTPUT = GENERATED_REPORT_DIR / "validation_result.json"
REVIEW_STATUS_OUTPUT = GENERATED_REPORT_DIR / "review_status.json"


# ============================================================
# REPORT CONTEXT
# ============================================================

REPORT_CONTEXT_DIR = OUTPUT_DIR / "report_context"
