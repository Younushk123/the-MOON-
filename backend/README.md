# THE MOON: Backend API

FastAPI backend for THE MOON (NASA Space Apps: *Flame in Free Fall*), implementing the
canonical data schema v1.0. The Pydantic models in `app/models/` are the validation authority;
matching JSON Schema files are generated into `<repo>/shared/schemas/`.

## Run

```bash
cd THE_MOON_CORE/backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

- Interactive docs: http://127.0.0.1:8000/docs
- Tests: `pytest` (run from `backend/`)
- Regenerate JSON Schemas after changing a model: `python -m app.schema_export`
  (a test fails if they're stale)

## Configuration (environment variables or `backend/.env`)

| Variable | Default | Meaning |
|---|---|---|
| `MOON_DATA_MODE` | `mock` | `mock` or `psi` (loads local processed PSI-159 CSV data). Reported as `meta.data_mode`. |
| `MOON_CORS_ORIGINS` | `["http://localhost:3000","http://localhost:5173","http://127.0.0.1:5173"]` | JSON list of allowed frontend origins. |

Set `MOON_DATA_MODE=psi` in `backend/.env` to load the locally processed PSI-159 datasets from `data_analysis/data/processed/`.

## Endpoints

| Method | Path | Status |
|---|---|---|
| GET | `/api/v1/health` | Working |
| GET | `/api/v1/experiments` | Working. Filters: `q`, `platform`, `data_status`, `page`, `page_size` (≤100) |
| GET | `/api/v1/experiments/{experiment_id}` | Working |
| GET | `/api/v1/experiments/{experiment_id}/measurements` | Working. Filters: `variable`, `page`, `page_size` (≤500) |
| POST | `/api/v1/analysis` | Working (built-in `statistical_summary`; Data Analysis module to replace) |
| POST | `/api/v1/comparison` | Working (built-in comparability rules; Data Analysis module to replace) |
| POST | `/api/v1/insights` | Placeholder: returns `insufficient_evidence` until AI module is connected |
| POST | `/api/v1/assistant/ask` | Working: answers with evidence from the connected RAG pipeline |
| POST | `/api/v1/vision/analyze` | Placeholder: returns `not_processed` until CV module is connected |
| POST | `/api/v1/vision/analyze-image` | Accepts a temporary JPEG, PNG, or WebP still image (25 MB and 12 MP max) and returns PSI-69 CV features |
| POST | `/api/v1/vision/analyze-video` | Accepts a temporary MP4 upload and queues PSI-69 FLEX analysis (25 MB max; returns a job ID) |
| GET | `/api/v1/vision/jobs/{job_id}` | Returns queued/processing/completed/failed status and, on completion, the CV result |

Every response uses `{success, data, error, meta}`. In list responses, `count` is the total
number of matches across all pages. Error codes: `VALIDATION_ERROR` (422, with `details`),
`EXPERIMENT_NOT_FOUND` (404), `NOT_FOUND` (404, unknown route), `METHOD_NOT_ALLOWED` (405),
`INTERNAL_ERROR` (500).

### Analysis and comparison rules

- Null values are excluded and counted in `data_quality.missing_values`, never treated as zero.
- Values in different units are never combined (no documented conversions yet).
- A variable is comparable only if every experiment has values, units match, and recorded
  measurement conditions (`fuel`, `pressure`, `temperature`, `flow_velocity`) don't conflict.
  Unrecorded conditions produce a warning instead.

## Layout

```
app/
  main.py            app factory: CORS, error handlers, routers
  config.py          settings
  errors.py          error codes and envelope-rendering handlers
  schema_export.py   writes shared/schemas/*.schema.json
  models/            schema v1.0: experiment, analysis, insight, vision; envelope
  api/v1/            routes (thin: validate, call service, wrap in envelope)
  services/          resolve experiments, then hand off to a module
  integrations/      where teammates' modules plug in (see below)
  adapters/          data sources: mock JSON fixtures or processed PSI-159 CSVs
tests/
```

## Connecting a module

Each module has a Protocol in `app/integrations/`. Implement it and return your class from
`build_integrations()` in `app/integrations/__init__.py`. Routes don't change.

| Module | Protocol | Current implementation |
|---|---|---|
| Data Analysis | `AnalysisEngine` (`analyze`, `compare`) | `ReferenceAnalysisEngine` |
| AI integration | `InsightEngine` (`generate`) | `UnavailableInsightEngine` |
| RAG | `ResearchAssistant` (`ask`) | `UnavailableResearchAssistant` |
| Computer vision | `VisionAnalyzer` (`analyze`, `analyze_uploaded_image`, `submit_video`, `get_video_job`) | `FlexVisionAnalyzer` for PSI-69 still images and the supported MP4 profile |

The `Insight` model rejects `evidence_status` other than `insufficient_evidence` when
`supporting_evidence` is empty, so no module can return an unsupported claim.

## Mock data

`app/adapters/mock_data/` holds 3 experiments, 13 measurements and 2 sources. All IDs start
with `MOCK-`, every record is `illustrative`/`unverified`, and no URLs are given. These are
not NASA data. The adapter rejects the data at startup if records break the schema or
reference each other inconsistently.

## Provisional choices (to confirm with the project lead)

- Allowed values not listed in v1.0: `Experiment.data_status`, `Measurement.measurement_status`,
  `AnalysisResult.status`, `Insight.confidence`, `CVResult.processing_status`/`calibration_status`.
  See the `PROVISIONAL` comments in `app/models/`.
- `MeasurementConditions` pressure/temperature/flow_velocity have no units in v1.0.
- `Comparison.findings` item shape isn't defined in v1.0; see `ComparisonFinding`.
- `Measurement.timestamp` and `Source.publication_date` are kept as strings until a format is agreed.
- Request bodies for the POST endpoints aren't defined in v1.0; see `*Request` models.
