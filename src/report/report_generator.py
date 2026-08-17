import hashlib
import json
from pathlib import Path
from typing import Dict


from src.config import (
    DRAFT_REPORT,
    GENERATED_REPORT_DIR,
    GENERATED_SECTIONS_OUTPUT,
    PRODUCT_NAME,
    REPORT_TYPE,
    REVIEW_STATUS_OUTPUT,
)


# ============================================================
# REPORT SECTION ORDER
# ============================================================

REPORT_SECTIONS = [
    "reporting_period",
    "narrative_summary",
    "case_summary",
    "reaction_analysis",
    "serious_cases",
    "trends",
    "history_of_actions",
    "case_index",
]


# ============================================================
# HUMAN-READABLE SECTION TITLES
# ============================================================

SECTION_TITLES = {
    "reporting_period": "Reporting Period",
    "narrative_summary": "Narrative Summary and Analysis",
    "case_summary": "Case Summary",
    "reaction_analysis": "Reaction Analysis",
    "serious_cases": "Serious Cases",
    "trends": "Trends",
    "history_of_actions": "History of Actions",
    "case_index": "Case Index",
}


# ============================================================
# REPORT GENERATOR
# ============================================================

class ReportGenerator:
    """
    Generates individual report sections using the existing
    LLM generator and grounding validator.

    The generator is resumable:
    already-generated sections are reused.

    It also assembles all generated sections into a final
    Markdown report.
    """

    def __init__(
        self,
        context_dir: Path,
        output_dir: Path,
    ):

        self.context_dir = Path(
            context_dir
        )

        self.output_dir = Path(
            output_dir
        )

        self.sections_dir = (
            self.output_dir
            / "sections"
        )

        # ----------------------------------------------------
        # Create directories
        # ----------------------------------------------------

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.sections_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ========================================================
    # FIND CONTEXT FILE
    # ========================================================

    def _get_context_path(
        self,
        section_name: str,
    ) -> Path:
        """
        Find the context JSON file for a section.
        """

        possible_paths = [
            self.context_dir
            / f"{section_name}.json",

            self.context_dir
            / f"{section_name}_context.json",
        ]

        for path in possible_paths:

            if path.exists():
                return path

        searched_paths = "\n".join(
            str(path)
            for path in possible_paths
        )

        raise FileNotFoundError(
            f"""
Context file not found for section:

{section_name}

Searched:

{searched_paths}
"""
        )

    # ========================================================
    # SECTION OUTPUT PATH
    # ========================================================

    def _get_section_output_path(
        self,
        section_name: str,
    ) -> Path:
        """
        Return the Markdown output path for a section.
        """

        return (
            self.sections_dir
            / f"{section_name}.md"
        )

    def _get_section_meta_path(self, section_name: str) -> Path:
        return self.sections_dir / f"{section_name}.meta.json"

    def _context_fingerprint(self, context_path: Path) -> str:
        return hashlib.sha256(
            context_path.read_bytes()
        ).hexdigest()

    def _section_is_current(self, section_name: str, context_path: Path) -> bool:
        meta_path = self._get_section_meta_path(section_name)
        if not meta_path.exists():
            # Backward compatibility for sections generated before
            # fingerprint metadata was introduced. Reuse them rather
            # than triggering unnecessary LLM calls after a transient
            # API outage. Remove the section file to force regeneration.
            return True
        try:
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return False
        if metadata.get("status") == "stale":
            return False
        return metadata.get("context_sha256") == self._context_fingerprint(context_path)

    def _save_section_meta(self, section_name: str, context_path: Path) -> None:
        meta_path = self._get_section_meta_path(section_name)
        metadata = {
            "section": section_name,
            "context_sha256": self._context_fingerprint(context_path),
        }
        meta_path.write_text(
            json.dumps(metadata, indent=2) + "\n",
            encoding="utf-8",
        )

    # ========================================================
    # FINAL REPORT PATH
    # ========================================================

    def _get_final_report_path(
        self,
    ) -> Path:
        """
        Return the path of the assembled DRAFT report.
        This is unreviewed output -- see src/config.py for why
        this generator never writes to FINAL_REPORT directly.
        """

        return DRAFT_REPORT

    # ========================================================
    # CHECK EXISTING SECTION
    # ========================================================

    def _load_existing_section(
        self,
        section_name: str,
    ) -> str | None:
        """
        Load an already-generated section.

        Returns None when the section does not exist
        or is empty.
        """

        output_path = (
            self._get_section_output_path(
                section_name
            )
        )

        if not output_path.exists():
            return None

        content = output_path.read_text(
            encoding="utf-8"
        ).strip()

        if not content:
            return None

        return content

    # ========================================================
    # GENERATE ONE SECTION
    # ========================================================

    def generate_one_section(
        self,
        section_name: str,
    ) -> str:
        """
        Generate one report section.

        Existing sections are reused so that temporary
        Gemini failures do not force regeneration.
        """

        # ----------------------------------------------------
        # Validate section name
        # ----------------------------------------------------

        if section_name not in REPORT_SECTIONS:

            raise ValueError(
                f"Unknown report section: "
                f"{section_name}"
            )

        # ----------------------------------------------------
        # Find context before deciding whether a saved section
        # can be safely reused.
        # ----------------------------------------------------

        context_path = self._get_context_path(section_name)

        existing = self._load_existing_section(section_name)

        if existing and self._section_is_current(section_name, context_path):
            print("\n" + "-" * 70)
            print(f"SKIPPING EXISTING SECTION: {section_name}")
            print("-" * 70)
            return existing

        if existing:
            print("\n" + "-" * 70)
            print(f"REGENERATING STALE SECTION: {section_name}")
            print("-" * 70)

        # ----------------------------------------------------
        # Generate
        # ----------------------------------------------------

        print(
            "\n"
            + "=" * 70
        )

        print(
            f"GENERATING: {section_name}"
        )

        print(
            f"Context: {context_path}"
        )

        print(
            "=" * 70
        )

        # Import lazily so deterministic report assembly and validation
        # remain usable even when the LLM dependency is unavailable.
        from src.llm.generator import generate_section

        generated_text = generate_section(
            section_name=section_name,
            context_path=context_path,
        )

        if not generated_text:

            raise ValueError(
                f"LLM returned empty output for "
                f"{section_name}"
            )

        generated_text = (
            generated_text
            .strip()
        )

        if not generated_text:

            raise ValueError(
                f"Generated output is empty for "
                f"{section_name}"
            )

        # ----------------------------------------------------
        # Save immediately
        # ----------------------------------------------------

        output_path = (
            self._get_section_output_path(
                section_name
            )
        )

        output_path.write_text(
            generated_text
            + "\n",
            encoding="utf-8",
        )

        self._save_section_meta(section_name, context_path)

        print(
            f"Saved: {output_path}"
        )

        return generated_text

    # ========================================================
    # GENERATE ALL SECTIONS
    # ========================================================

    def generate_all_sections(
        self,
    ) -> Dict[str, str]:
        """
        Generate all report sections in the predefined
        order.
        """

        sections: Dict[str, str] = {}

        total = len(
            REPORT_SECTIONS
        )

        for index, section_name in enumerate(
            REPORT_SECTIONS,
            start=1,
        ):

            print(
                "\n"
                + "=" * 70
            )

            print(
                f"SECTION {index}/{total}: "
                f"{section_name}"
            )

            print(
                "=" * 70
            )

            sections[
                section_name
            ] = self.generate_one_section(
                section_name
            )

        return sections

    # ========================================================
    # LOAD ALL SAVED SECTIONS
    # ========================================================

    def load_all_sections(
        self,
    ) -> Dict[str, str]:
        """
        Load all existing section files.

        Only sections that actually exist are returned.
        """

        sections: Dict[str, str] = {}

        for section_name in REPORT_SECTIONS:

            content = (
                self._load_existing_section(
                    section_name
                )
            )

            if content:

                sections[
                    section_name
                ] = content

        return sections

    # ========================================================
    # SAVE COMBINED JSON
    # ========================================================

    def save_sections(
        self,
        sections: Dict[str, str],
    ) -> Path:
        """
        Save all generated sections as JSON.
        """

        output_path = (
            self.output_dir
            / "generated_sections.json"
        )

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                sections,
                file,
                indent=2,
                ensure_ascii=False,
            )

        print(
            f"Saved: {output_path}"
        )

        return output_path

    # ========================================================
    # BUILD REPORT HEADER
    # ========================================================

    def _get_reporting_period(self) -> tuple[str | None, str | None]:
        path = self._get_context_path("reporting_period")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            evidence = data.get("approved_evidence", {})
            return evidence.get("start_date"), evidence.get("end_date")
        except (OSError, json.JSONDecodeError):
            return None, None

    def _build_report_header(self) -> str:
        start_date, end_date = self._get_reporting_period()
        period = (
            f"{start_date} to {end_date}"
            if start_date and end_date
            else "As supported by the supplied receivedate evidence"
        )

        return (
            "# Periodic Adverse Event Data Report\n\n"
            f"**Product:** {PRODUCT_NAME}  \n"
            f"**Report Type:** {REPORT_TYPE}  \n"
            f"**Reporting Period:** {period}\n\n"
            "This report was generated from deterministic analyses, "
            "registered evidence, and section-specific LLM outputs. "
            "The raw dataset is not provided directly to the LLM.\n\n"
            "---\n\n"
        )

    # ========================================================
    # BUILD SECTION
    # ========================================================

    @staticmethod
    def _strip_redundant_heading(content: str, title: str) -> str:
        """Remove an LLM-generated heading that duplicates the wrapper title."""
        cleaned = content.strip()
        if not cleaned:
            return cleaned

        match = __import__("re").match(r"^\s*#{1,6}\s+(.+?)\s*(?:\n|$)", cleaned)
        if not match:
            return cleaned

        heading = match.group(1).strip().lower().rstrip(":")
        normalized_title = title.strip().lower().rstrip(":")

        aliases = {
            normalized_title,
            normalized_title.replace(" and ", " / "),
            "serious cases / 15-day alerts" if title.lower() == "serious cases" else "",
            "reaction / adverse event analysis" if title.lower() == "reaction analysis" else "",
        }

        if heading in {value for value in aliases if value}:
            return cleaned[match.end():].lstrip()

        return cleaned

    def _build_report_section(self, section_name: str, content: str) -> str:
        title = SECTION_TITLES.get(
            section_name,
            section_name.replace("_", " ").title(),
        )
        cleaned_content = self._strip_redundant_heading(content, title)

        return (
            f"## {title}\n\n"
            f"{cleaned_content}\n\n"
            "---\n\n"
        )

    # ========================================================
    # BUILD FINAL MARKDOWN REPORT
    # ========================================================

    def build_final_report(
        self,
        sections: Dict[str, str],
    ) -> str:
        """
        Assemble all generated sections into one Markdown
        report.

        Sections are always written in REPORT_SECTIONS order.
        """

        report_parts = []

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        report_parts.append(
            self._build_report_header()
        )

        # ----------------------------------------------------
        # Sections
        # ----------------------------------------------------

        for section_name in REPORT_SECTIONS:

            content = sections.get(
                section_name
            )

            if not content:

                print(
                    f"WARNING: Section missing: "
                    f"{section_name}"
                )

                continue

            report_parts.append(
                self._build_report_section(
                    section_name,
                    content,
                )
            )

        return "".join(
            report_parts
        ).rstrip() + "\n"

    # ========================================================
    # SAVE FINAL REPORT
    # ========================================================

    def save_final_report(
        self,
        report_text: str,
    ) -> Path:
        """
        Save the assembled Markdown report.
        """

        output_path = (
            self._get_final_report_path()
        )

        output_path.write_text(
            report_text,
            encoding="utf-8",
        )

        print(
            f"Final report saved: "
            f"{output_path}"
        )

        return output_path

    # ========================================================
    # GENERATE REPORT
    # ========================================================

    def generate_report(
        self,
    ) -> Dict[str, str]:
        """
        Complete report-generation workflow.

        Steps:

        1. Generate all sections.
        2. Save generated_sections.json.
        3. Assemble final Markdown report.
        4. Save final_report.md.
        """

        print(
            "\n"
            + "=" * 70
        )

        print(
            "PADER REPORT GENERATION"
        )

        print(
            "=" * 70
        )

        # ----------------------------------------------------
        # Generate sections
        # ----------------------------------------------------

        sections = (
            self.generate_all_sections()
        )

        # ----------------------------------------------------
        # Save JSON
        # ----------------------------------------------------

        json_path = (
            self.save_sections(
                sections
            )
        )

        # ----------------------------------------------------
        # Build final report
        # ----------------------------------------------------

        report_text = (
            self.build_final_report(
                sections
            )
        )

        # ----------------------------------------------------
        # Save Markdown
        # ----------------------------------------------------

        markdown_path = (
            self.save_final_report(
                report_text
            )
        )

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

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

        print(
            f"Sections       : {len(sections)}"
        )

        print(
            f"Sections JSON   : {json_path}"
        )

        review_status = {
            "status": "pending_review",
            "report_path": str(markdown_path),
            "sections_path": str(json_path),
            "validation_path": None,
            "reviewer": None,
            "reason": None,
        }
        REVIEW_STATUS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        REVIEW_STATUS_OUTPUT.write_text(
            json.dumps(review_status, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        print(f"Final Markdown  : {markdown_path}")
        print(f"Review status   : {REVIEW_STATUS_OUTPUT}")
        print("=" * 70)

        return sections