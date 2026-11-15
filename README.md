# NASA Microgravity Combustion & Spacecraft Fire Safety RAG

Evidence-grounded RAG module providing research-grade scientific explanations, source citations, experimental conditions, and verified evidence passages for the NASA Spacecraft Fire Safety project (**THE MOON**).

---

## 1. Quick Start & Setup Instructions

### Environment Setup
Python **3.10–3.12** (or 3.14) is supported.
```powershell
# 1. Install dependencies (includes FastAPI, Uvicorn, PyMuPDF, ChromaDB, Sentence-Transformers)
pip install -r requirements.txt

# 2. Copy the environment template and set optional secrets
copy .env.example .env          # Windows
# cp .env.example .env          # Linux / macOS
```
> **Note on API Keys:** The system is completely operational in offline extractive mode without an external API key. Providing `GROQ_API_KEY` in `.env` enables generative synthesis via Llama-3.

---

## 2. Rebuilding the Corpus from a Fresh Clone

Raw document PDFs and processed ChromaDB vector databases are excluded from Git via `.gitignore` to prevent repository bloat and respect data licensing. Follow these steps to rebuild the knowledge base:

### Step 1: Place Source PDFs in `data/raw_documents/`
Ensure the target NASA research PDFs are located in `data/raw_documents/` matching the filenames in `data/raw_documents/manifest.json`:

| Source ID | Target Filename | Investigation / Topic |
|---|---|---|
| **S2** | `ccomustion research doocs.pdf` | ISS Researcher's Guide: Combustion Science (NP-2015-10-034-JSC) |
| **S3** | `saffire4 docs.pdf` | Saffire Objectives, Development and Status (GRC-E-DAA-TN32222) |
| **S5** | `firesafety.pdf` | Fire Safety in Low-Gravity Spacecraft (NASA/TM-1999-209285) |
| **S23** | `slice_fact_sheet.pdf` | Structure & Liftoff in Combustion Experiment (PSI-106) |
| **S24** | `spice_fact_sheet.pdf` | Smoke Point In Co-flow Experiment (PSI-107) |
| **S28** | `bass2_results_ntrs_20160000593.pdf` | BASS-II Microgravity Solid Combustion (NTRS 20160000593) |
| **S29** | `bass2_summary_report_ntrs_20210011385.pdf` | BASS-II Final Summary Report (NTRS 20210011385) |
| **S31** | `saffire6_ices2024_365.pdf` | Saffire VI Preliminary Results (ICES-2024-365 / NTRS 20240002981) |
| **S33** | `saffire_novel_approach_ntrs_20180005168.pdf` | Saffire Novel Testing Approach (NTRS 20180005168) |
| **S50** | `apollo204_review_board_ntrs_19820066930.pdf` | Apollo 204 (Apollo 1) Review Board Report (NASA-TM-84105) |
| **S51** | `apollo13_review_board_ntrs_20170000913.pdf` | Apollo 13 Review Board Investigation (NTRS 20170000913) |
| **S52** | `mir_fire_ntrs_20030068062.pdf` | Mir Space Station Fire Investigation (NTRS 20030068062) |
| **S56** | `same_final_report_nist_904707.pdf` | Smoke Aerosol Measurement Experiment Final Report (NIST Pub 904707) |
| **DOC-STD-6001B** | `NASA-STD-6001B.pdf` | Flammability, Offgassing, and Materials Testing Standards |

### Step 2: Run Ingestion
Execute the ingestion pipeline to parse documents, build text chunks with page markers, compute semantic embeddings, and populate ChromaDB:
```powershell
python rag_pipeline.py ingest
```
*Output:* Creates `data/processed/docs/chunks.json` (2,143 grounded chunks) and initialises the vector store in `data/processed/chroma/`.

### Step 3: Verify the Build
```powershell
pytest -q -W ignore            # Run unit test suite (23 passing)
python run_five_questions.py   # Run verified 5-question demo
```

---

## 3. Canonical Experiment Mapping & Integration Boundary

### Integration Principle: Separation of Concerns
To ensure strict scientific integrity across THE MOON system:
- **Research RAG Module:** Handles scientific research literature, combustion physics explanations, experimental background, and verified evidence passages with citations.
- **Scientific Data Module:** Handles raw sensor telemetry, numerical tables, units, calibrations, and quantitative calculations.
- Passages retrieved by RAG serve as supporting qualitative evidence; numeric charts and measurements originate directly from the Scientific Data module.

### Dashboard Canonical IDs to PSI Investigation Mapping
The backend can resolve dashboard experiment IDs (`EXP-001` .. `EXP-010`) to official NASA PSI investigation codes and target research sources:

| Dashboard Canonical ID | Experiment / Investigation Name | NASA PSI ID | Target Research Sources | Scientific Scope |
|---|---|---|---|---|
| **EXP-001** | Burning and Suppression of Solids - II (BASS-II) | `PSI-25` | `S28`, `S29` | Extinction limits, airflow quenching, and PMMA burning in microgravity |
| **EXP-002** | Spacecraft Fire Experiment VI (Saffire-VI) | `Saffire-VI` | `S31`, `S3`, `S33` | Large-scale sample card spread, heat flux, and toxic combustion gases |
| **EXP-003** | Smoke Aerosol Measurement Experiment (SAME) | `SAME` | `S56` | Smoke particle size distribution and agglomeration in low gravity |
| **EXP-004** | Smoke Point In Co-flow Experiment (SPICE) | `PSI-107` | `S24` | Soot inception, smoke points, and laminar coflow diffusion flames |
| **EXP-005** | Structure and Liftoff in Combustion Experiment (SLICE) | `PSI-106` | `S23` | Non-buoyant flame liftoff, stabilization, and blow-off limits |
| **EXP-006** | Advanced Combustion via Microgravity Experiments (ACME) | `PSI-98` | `S35`, `S36`, `DOC-ACME-PUBS` | Spherical diffusion flame extinction and soot suppression |
| **EXP-007** | Flame Extinguishment Experiment (FLEX / FLEX-2) | `PSI-10` | `S38`, `S39` | Droplet combustion, d-squared law, and radiative extinction |
| **EXP-008** | Apollo 1 (Apollo 204) Fire Investigation | `APOLLO-204` | `S50` | Pure oxygen high-pressure flammability and rapid fire growth |
| **EXP-009** | Apollo 13 Oxygen Tank Incident Investigation | `APOLLO-13` | `S51` | Cryogenic oxygen combustion, wire insulation arcing, and tank rupture |
| **EXP-010** | Mir Space Station Fire Incident Investigation | `MIR-1997` | `S52` | Solid fuel oxygen generator (SFOG) candle failure and toxic smoke response |
| *MOCK-EXP-001..003* | Synthetic Test Records (Core Foundation) | *MOCK* | `S2`, `S28`, `S24` | Methane combustion normal vs reduced gravity baselines |

---

## 4. Backend / API Integration Handoff

The deliverable API is located at `src/api.py`. It provides both a callable Python function and standalone FastAPI endpoints.

### Option A: Python Direct Call
```python
from src.api import answer_question

# Call with optional experiment ID focus (e.g. EXP-001, Saffire-VI, or PSI-25)
result = answer_question("What fuel materials were tested?", experiment_ids=["EXP-001"], top_k=5)

print("Claim:", result["claim"])
print("Sources:", result["sources"])
print("Evidence:", result["evidence"])
print("Conditions:", result["conditions"])
print("Resolved Experiments:", result["resolved_experiments"])
print("Integration Note:", result["integration_note"])
```

### Option B: FastAPI Endpoints
Start the server:
```powershell
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

Available Endpoints:
- `POST /ask`: Accepts `{"query": "...", "experiment_ids": ["EXP-001"], "top_k": 5}`. Returns standardized JSON envelope with claim, sources, verbatim evidence passages with page citations, and conditions.
- `GET /experiments/mapping`: Returns the canonical mapping table between Dashboard IDs (`EXP-001` .. `EXP-010`) and NASA PSI IDs.
- `GET /health`: Reports service health, retrieval mode (`hybrid (BM25 + semantic + entity)`), total indexed chunks, and registered sources.
- `GET /sources`: Returns enumeration of all 47 registered NASA sources with their 6-level verification ladder statuses.
- `POST /api/v1/assistant/ask`: Preserves team router contract with pass-through support for `experiment_ids` and `validated_findings` from the Data Analysis module.

---

## 5. Verification Status Consistency

In compliance with NASA PSI scientific evaluation standards, our Source Register (`Source_Register_Updated.xlsx`) tracks a 6-level verification ladder:

1. **Document Ingestion Status:**
   - **Indexed Documents (18 Sources / 2,143 Chunks):** Primary NASA PDFs (S2, S3, S5, S23, S24, S28, S29, S31, S33, S50, S51, S52, S56, DOC-STD-6001B, etc.) have their actual full-text downloaded, SHA-256 validated, and indexed into ChromaDB.
   - **Catalogue Only (29 Sources):** Sources where only portal metadata/summary cards were recorded. These are explicitly tagged as `catalogue_record` and never treated as primary experimental findings.
2. **Scientific Claim & Raw Data Status:**
   - In `Source_Register_Updated.xlsx`, columns `5_raw_data_available` and `6_claim_verified` are marked `not verified` or `no` across the literature corpus.
   - **Reason:** Raw numerical telemetry (e.g. sensor millivolt traces, pressure readings, gas chromatograph outputs) has not been ingested as raw datasets in this RAG module; it is provided by the **Scientific Data Module**.
   - The RAG module guarantees that every claim is grounded in official peer-reviewed NASA text, but refrains from asserting that raw sensor datasets have been independently re-measured.

---

## 6. Tested Demo Questions

Run `python run_five_questions.py` to execute the 5 integration questions:
1. **Why is combustion different in microgravity?** $\rightarrow$ Cites S2 (p. 10) and S28 (p. 5) [Removal of buoyancy flow & simpler modeling].
2. **What was the objective of BASS-II?** $\rightarrow$ Cites S29 (p. 54) and PSI-25 [Burning and extinction of PMMA/fabrics in diluted O2].
3. **What did Saffire VI investigate?** $\rightarrow$ Cites S31 (p. 3) [4 sample card concurrent spread, heat release & gas emissions].
4. **How are smoke particles studied in microgravity?** $\rightarrow$ Cites S56 (p. 10) [Comparative Soot Diagnostics & particle sizing for detectors].
5. **What can microgravity combustion research teach us about spacecraft fire safety?** $\rightarrow$ Cites S5 (p. 3) and S2 (p. 10) [Fire prevention, detector design, and realistic simulation of spacecraft fire risk].

---

## 7. Project Layout

```text
research_rag/
├── .env.example              # Template configuration with placeholder values
├── requirements.txt          # Module dependencies (FastAPI, Uvicorn, ChromaDB, etc.)
├── data/
│   ├── experiment_mapping.json # Canonical mapping (EXP-001..010 <-> PSI IDs)
│   ├── raw_documents/        # manifest.json (PDFs excluded via .gitignore)
│   └── processed/            # Ingested chunks and ChromaDB vector store
├── src/
│   ├── api.py                # Backend handoff API & answer_question()
│   ├── api_adapter.py        # Team router (POST /api/v1/assistant/ask)
│   ├── experiment_mapping.py # Canonical ID resolution and source lookup
│   ├── config.py             # Settings and paths
│   ├── ingestion.py          # PDF/DOCX ingestion and chunking
│   ├── retrieval.py          # Hybrid retrieval (BM25 + ChromaDB + entity)
│   ├── generator.py          # Grounded generator (Extractive + Groq)
│   ├── evidence_validator.py # Verbatim quote and sufficiency validator
│   └── source_register.py    # 6-level verification ladder & corpus builder
├── tests/                    # 23 unit tests (pytest)
├── evaluation/               # T1-T30 benchmark runner and export scripts
├── rag_pipeline.py           # CLI entry point (ingest, ask, chat)
└── Source_Register_Updated.xlsx # 47 records with 6-level verification ladder
```
