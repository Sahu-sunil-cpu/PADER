# PADER AI Engine — Version 0 Architecture

## Overview

Version 0 is designed as a **deterministic-first reporting pipeline**.

The main idea is to keep the responsibilities of Python and the LLM clearly separated:

- Python handles data loading, validation, version auditing, canonicalization, parsing, and statistical analysis.
- Deterministic analysis produces the actual numbers and observations used in the report.
- The Evidence Registry records where those facts came from and how they were calculated.
- The Context Builder creates section-specific evidence packets.
- Gemini is used only to turn approved evidence into readable report narrative.
- Automated validation checks that generated content remains grounded in the evidence.
- A human reviewer acts as the final approval gate.
- Only an approved report is converted into the final DOCX.

The overall flow is:

**Raw ICSR Data → Validation → Canonicalization → Deterministic Analysis → Evidence Registry → Section Context → LLM Generation → Grounding Validation → Human Review → Approved Report → DOCX**

The important design principle is that **the LLM never becomes the source of truth for the underlying statistics**.

---

# Architecture Diagram

```mermaid
flowchart TB

    %% =========================
    %% INGESTION
    %% =========================
    subgraph INGESTION["1. Ingestion & Validation"]
        A["Raw ICSR XLSX"]
        B["DataLoader"]
        C["Schema Validator"]
        D["Version Audit"]

        A --> B --> C --> D
    end

    %% =========================
    %% NORMALIZATION
    %% =========================
    subgraph NORMALIZATION["2. Canonicalization & Normalization"]
        E["Canonicalizer"]
        F["Reaction Parser"]

        E --> F
    end

    D --> E

    %% =========================
    %% DETERMINISTIC ANALYSIS
    %% =========================
    subgraph ANALYSIS["3. Deterministic Analysis"]
        G["Case-level Analysis"]
        H["Reaction-level Analysis"]
        I["Demographics & Seriousness"]
        J["Outcomes & Alerts"]
        K["Reporting Period & Monthly Trends"]
    end

    F --> G
    F --> H
    F --> I
    F --> J
    F --> K

    %% =========================
    %% EVIDENCE
    %% =========================
    subgraph EVIDENCE["4. Evidence & Context Layer"]
        L["Evidence Registry"]
        M["Context Builder"]
        N["Section-specific Evidence Packets"]

        L --> M --> N
    end

    G --> L
    H --> L
    I --> L
    J --> L
    K --> L

    %% =========================
    %% LLM
    %% =========================
    subgraph GENERATION["5. LLM Generation"]
        O["Section Prompt"]
        P["Evidence Packet"]
        Q["Gemini"]
        R["Generated Section"]

        O --> Q
        P --> Q
        Q --> R
    end

    N --> O
    N --> P

    %% =========================
    %% VALIDATION
    %% =========================
    subgraph VALIDATION["6. Grounding & Validation"]
        S["Section Grounding Validator"]
        T["Accepted Section"]
        U["Final Report Validator"]
        V["Validated final_report.md"]

        S --> T --> U --> V
    end

    R --> S

    %% =========================
    %% HUMAN REVIEW
    %% =========================
    subgraph REVIEW["7. Human Review Gate"]
        W["Human Review"]
        X{"Decision"}
        Y["Revision Required"]
        Z["approved_report.md"]
        AA["final_report.docx"]

        W --> X
        X -->|"Flag"| Y
        X -->|"Approve"| Z
        Z --> AA
    end

    V --> W

    %% =========================
    %% SIDE OUTPUT
    %% =========================
    AB["case_listing.csv"]

    E --> AB
    F --> AB

    %% =========================
    %% STYLING
    %% =========================
    classDef input fill:#e8f4ff,stroke:#2563eb,stroke-width:2px
    classDef process fill:#f8fafc,stroke:#475569,stroke-width:1.5px
    classDef analysis fill:#ecfdf5,stroke:#059669,stroke-width:1.5px
    classDef evidence fill:#fff7ed,stroke:#ea580c,stroke-width:1.5px
    classDef llm fill:#f5f3ff,stroke:#7c3aed,stroke-width:2px
    classDef validation fill:#fefce8,stroke:#ca8a04,stroke-width:1.5px
    classDef review fill:#fdf2f8,stroke:#db2777,stroke-width:1.5px
    classDef output fill:#f0fdf4,stroke:#16a34a,stroke-width:2px

    class A input
    class B,C,D,E,F process
    class G,H,I,J,K analysis
    class L,M,N evidence
    class O,P,Q,R llm
    class S,T,U,V validation
    class W,X,Y review
    class Z,AA,AB output