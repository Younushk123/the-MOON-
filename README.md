# NASA Microgravity Combustion & Spacecraft Fire Safety RAG

Evidence-grounded RAG module providing research-grade scientific explanations, source citations, experimental conditions, and verified evidence passages for the NASA Spacecraft Fire Safety project.

---

## 1. Quick Start & Setup Instructions

### Environment Setup
Python **3.10–3.12** is recommended (compatible with PyTorch, ChromaDB, and Sentence-Transformers).
```powershell
pip install -r requirements.txt
copy .env.example .env          # paste your GROQ_API_KEY (optional; offline extractive works without it)
```

### Ingestion & Verification
```powershell
python rag_pipeline.py ingest
pytest -q -W ignore            # 21 unit tests (all passing)
python evaluation/run_tests.py auto   # Benchmark evaluation suite (29/35 PASS)
```

---

## 2. Backend / AI Integration Handoff

The deliverable module is located at `src/api.py`. It provides both a direct Python function and a FastAPI HTTP service.

### Option A: Python Direct Call
```python
from src.api import answer_question

result = answer_question("Why is combustion different in microgravity?", top_k=5)
print("Claim:", result["claim"])
print("Sources:", result["sources"])
print("Evidence:", result["evidence"])
print("Conditions:", result["conditions"])
print("Abstained:", result["abstained"])
print("Data Status:", result["data_status"])
```

### Option B: FastAPI Service
Start the server:
```powershell
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

Available Endpoints:
- `POST /ask`: Accepts `{"query": "...", "top_k": 5}`. Returns standardized JSON response envelope with claim, sources, verbatim evidence passages with page citations, and conditions.
- `GET /health`: Reports service health, retrieval mode (`hybrid (BM25 + semantic + entity)`), total indexed chunks, and registered sources.
- `GET /sources`: Returns full enumeration of all 47 registered NASA sources with verification statuses (`unverified`, `unverified/no`).
- `POST /api/v1/assistant/ask`: Preserves team envelope with pass-through support for `experiment_ids` (PSI-xx focus) and `validated_findings` from the Data Analysis module.

---

## 3. Knowledge Base Status (Corpus)

The corpus is manifest-driven (`data/raw_documents/manifest.json`) and currently indexes **over 2,140 real chunks** from primary NASA and peer-reviewed documents:

1. **PSI Repository & Investigation Records:**
   - **BASS-II:** `bass2_summary_report_ntrs_20210011385.pdf` (S29, 144 pages, 381 chunks) & `bass2_results_ntrs_20160000593.pdf` (S28, 21 pages).
   - **SAFFIRE:** `saffire6_ices2024_365.pdf` (S31, ICES-2024-365, NTRS 20240002981), `saffire4 docs.pdf` (S3), and `saffire_novel_approach_ntrs_20180005168.pdf` (S33).
   - **SAME:** `same_final_report_nist_904707.pdf` (S56, NIST pub_id 904707, 61 pages, 205 chunks).
   - **SPICE & SLICE:** `spice_fact_sheet.pdf` (S24, PSI-107) and `slice_fact_sheet.pdf` (S23, PSI-106).
2. **NASA Combustion Science Overviews:**
   - `ccomustion research doocs.pdf` (S2, *International Space Station (ISS) Researcher's Guide to: Combustion Science*, NP-2015-10-034-JSC).
   - `firesafety.pdf` (S5, *Fire Safety in the Low-Gravity Spacecraft Environment*, NASA/TM-1999-209285, R. Friedman).
3. **Historical Fire Accidents (Spacecraft Safety Context):**
   - **Apollo 1 (Apollo 204):** `apollo204_review_board_ntrs_19820066930.pdf` (S50, NASA-TM-84105, 222 pages, 381 chunks).
   - **Apollo 13:** `apollo13_review_board_ntrs_20170000913.pdf` (S51, NTRS 20170000913, oxygen tank failure investigation, 208 pages, 376 chunks).
   - **Mir Fire:** `mir_fire_ntrs_20030068062.pdf` (S52, *Fire In Space- What Do You Do?*, February 23, 1997 solid-fuel oxygen generator fire).
4. **Standards & Testing:**
   - `NASA-STD-6001B` (DOC-STD-6001B, Flammability and offgassing test procedures, 329 chunks).

---

## 4. Current Limitations & Retrieval Test Observations

In the benchmark suite (`python evaluation/run_tests.py auto`), **29 of 35 tests PASS** under strict automated criteria with zero hardcoded question branches. The remaining 6 tests highlight specific architectural characteristics and corpus priorities noted below:

### Known Retrieval Issues & Analysis:
1. **Primary Literature vs Legacy Placeholders (T4, TEST_A):**
   - In `T4` (*why does the ISS fire alarm protocol turn off forced air flow*), Robert Friedman's technical report (`S5`) directly covers module ventilation isolation and alarm actuation, outranking the general guide (`S2`).
   - In `TEST_A` (*What does Friedman say about smoke particle agglomeration in microgravity?*), the 61-page SAME Final Report (`S56`) extensively details smoke agglomeration and cites Friedman, giving `S56` a higher BM25 keyword density than `S5`.
2. **Unindexed Conference Posters (T5):**
   - In `T5` (*flamelet that survives with very little oxygen*), the expected source `S7` is a 2014 conference poster abstract that was never published as a full technical paper. The retriever authentically returns available microgravity combustion results (`S28`, `S52`, `DOC-SOFIE-WKSHP`).
3. **Multi-Source Cross-Comparison Density (T23):**
   - In `T23` (*Compare Saffire, BASS-II and SAME*), the test strictly requires all three source groups in the top-3 slots. The system retrieved Saffire (`S31`, `S3`) and BASS-II (`S29`), while SAME (`S56`) was ranked 4th.
4. **Catalogue Metadata vs Full Documents (T18):**
   - In `T18` (*official NASA microgravity combustion experiment codes and PSI identifiers*), metadata catalogue stubs (`S35/S36/S37`) have lower lexical length compared to 200-page ingested reports, causing full reports to rank higher unless metadata intent filtering is explicitly forced.
5. **Relative Flammability Limits (T7):**
   - In `T7` (*limits of flammability testing on small samples and drop towers*), full experimental reports (`S3`, `S28`, `S29`) discussing large-scale Cygnus sample limitations outranked the secondary review (`S5`).

### Operational Safeguards:
- **Zero Hallucination / Numeric Gate:** For exact quantitative thresholds (e.g., flammability percentages), if no verified experimental table is indexed, the system strictly abstains with Data Status `Insufficient Evidence` or `Raw Data Not Indexed`.
- **Catalogue Record Policy:** PSI catalogue pages are categorized as `catalogue_record` and never treated as proof of downloadable or indexed raw data.

---

## 5. Verified Demo Questions

Run `python run_five_questions.py` to execute the 5 integration questions:
1. **Why is combustion different in microgravity?** $\rightarrow$ Cites S2 (p. 10) and S28 (p. 5) [Removal of buoyancy flow & simpler modeling].
2. **What was the objective of BASS-II?** $\rightarrow$ Cites S29 (p. 54) and PSI-25 [Burning and extinction of PMMA/fabrics in diluted O2].
3. **What did Saffire VI investigate?** $\rightarrow$ Cites S31 (p. 3) [4 sample card concurrent spread, heat release & gas emissions].
4. **How are smoke particles studied in microgravity?** $\rightarrow$ Cites S56 (p. 10) [Comparative Soot Diagnostics & particle sizing for detectors].
5. **What can microgravity combustion research teach us about spacecraft fire safety?** $\rightarrow$ Cites S5 (p. 3) and S2 (p. 10) [Fire prevention, detector design, and realistic simulation of spacecraft fire risk].

---

## 6. Project Layout

```text
research_rag/
├── data/
│   ├── raw_documents/        # manifest.json (PDFs excluded via .gitignore)
│   └── processed/            # Ingested chunks and ChromaDB vector store
├── src/
│   ├── api.py                # Backend handoff API & answer_question()
│   ├── api_adapter.py        # Team router (POST /api/v1/assistant/ask)
│   ├── config.py             # Settings and paths
│   ├── ingestion.py          # PDF/DOCX ingestion and chunking
│   ├── retrieval.py          # Hybrid retrieval (BM25 + ChromaDB + entity)
│   ├── generator.py          # Grounded generator (Extractive + Groq)
│   ├── evidence_validator.py # Verbatim quote and sufficiency validator
│   └── source_register.py    # 6-level verification ladder & corpus builder
├── tests/                    # 21 unit tests (pytest)
├── evaluation/               # T1-T30 benchmark runner and export scripts
├── rag_pipeline.py           # CLI entry point (ingest, ask, chat)
├── Source_Register_Updated.xlsx # 47 records with 6-level verification ladder
└── requirements.txt
```
