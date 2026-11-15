# THE MOON Backend: API and Integration Guide

**Audience:** frontend developers, and the AI/ML module owners (Data Analysis, AI insights, RAG, computer vision)
**Backend version:** 1.0.0 · **Data schema:** v1.0 (`Schema.txt`) · **Last updated:** 15 November 2026

This document describes everything the backend currently implements: how to run it, the response format, every data model, every endpoint with its request and response, the analysis rules, the mock data, and how AI/ML modules plug in.

> **All data is mock data for now.** Every record is illustrative and is **not NASA data**. Check `meta.data_mode` in every response: while it says `"mock"`, nothing should be presented as a real experimental result.

## Contents

1. [Running the backend](#1-running-the-backend)
2. [Implementation status](#2-implementation-status)
3. [API conventions](#3-api-conventions)
4. [Data models](#4-data-models)
5. [Endpoints](#5-endpoints)
6. [Analysis and comparison rules](#6-analysis-and-comparison-rules)
7. [Mock data](#7-mock-data)
8. [Guide for frontend developers](#8-guide-for-frontend-developers)
9. [Guide for AI/ML module owners](#9-guide-for-aiml-module-owners)
10. [Configuration](#10-configuration)
11. [Backend code structure](#11-backend-code-structure)
12. [Known limitations and open questions](#12-known-limitations-and-open-questions)

---

## 1. Running the backend

Requires Python 3.12. From `THE_MOON_CORE/backend`:

```powershell
python -m venv .venv
.venv\Scripts\activate              # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload       # server on http://127.0.0.1:8000
pytest                              # run the test suite
```

| URL | What it is |
|---|---|
| `http://127.0.0.1:8000/docs` | Interactive docs: try every endpoint in the browser |
| `http://127.0.0.1:8000/redoc` | Read-only reference view |
| `http://127.0.0.1:8000/openapi.json` | Machine-readable OpenAPI spec (usable for client generation) |

---

## 2. Implementation status

| Method | Path | Status | Backed by |
|---|---|---|---|
| GET | `/api/v1/health` | ✅ Working | Backend |
| GET | `/api/v1/experiments` | ✅ Working | Backend |
| GET | `/api/v1/experiments/{experiment_id}` | ✅ Working | Backend |
| GET | `/api/v1/experiments/{experiment_id}/measurements` | ✅ Working | Backend |
| GET | `/api/v1/experiments/{experiment_id}/media` | ✅ Working | Backend |
| GET | `/api/v1/media/{media_id}` | ✅ Working | Backend |
| POST | `/api/v1/analysis` | ✅ Working | Built-in reference engine, until the Data Analysis module plugs in |
| POST | `/api/v1/comparison` | ✅ Working | Built-in reference engine, until the Data Analysis module plugs in |
| POST | `/api/v1/insights` | ⏳ Placeholder | Returns `insufficient_evidence` until the AI module is connected |
| POST | `/api/v1/assistant/ask` | ⏳ Placeholder | Returns `insufficient_evidence` until the RAG module is connected |
| POST | `/api/v1/vision/analyze` | ⏳ Placeholder | Checks the media record, then returns `not_processed` until the CV module is connected |

"Placeholder" means the endpoint fully validates requests and returns a correct v1.0 response, but says honestly that no result is available. It never invents a claim, evidence or measurement.

There is no authentication. Results (analyses, comparisons, insights) are computed on each request and **not stored**: their IDs can't be looked up later.

---

## 3. API conventions

### 3.1 Base path and format

- All endpoints are under `/api/v1`.
- Requests and responses are JSON. POST requests need `Content-Type: application/json`.
- Field names use `snake_case`.
- Unknown values are `null`, never `0` or `""`.

### 3.2 Response envelope

**Every** response, success or error, has the same four fields:

```json
{
  "success": true,
  "data": { },
  "error": null,
  "meta": { "schema_version": "1.0", "data_mode": "mock" }
}
```

| Field | Type | Meaning |
|---|---|---|
| `success` | boolean | `true` if the request was handled, `false` on any error |
| `data` | object or `null` | The result. `null` when `success` is `false` |
| `error` | object or `null` | Error details (section 3.4). `null` when `success` is `true` |
| `meta.schema_version` | string | Data schema version, currently `"1.0"` |
| `meta.data_mode` | `"mock"` or `"psi"` | Where the data came from. `"mock"` means illustrative records only |

`success: true` means the request was processed, **not** that the scientific outcome was positive. For example, a comparison that finds nothing comparable is `success: true` with `data.status: "not_comparable"`.

### 3.3 Pagination

List endpoints return a page object in `data`:

```json
{ "items": [ ], "count": 3, "page": 1, "page_size": 20 }
```

| Field | Meaning |
|---|---|
| `items` | Records on this page |
| `count` | **Total matches across all pages**, not the number of items on this page |
| `page` | Current page, starting at 1 |
| `page_size` | Requested page size |

Total pages = `ceil(count / page_size)`. Asking for a page past the end returns an empty `items` list with HTTP 200, not an error.

### 3.4 Errors

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid parameters.",
    "details": [
      { "location": ["query", "page"], "message": "Input should be greater than or equal to 1", "type": "greater_than_equal" }
    ]
  },
  "meta": { "schema_version": "1.0", "data_mode": "mock" }
}
```

| `error.code` | HTTP | When | `details` |
|---|---|---|---|
| `VALIDATION_ERROR` | 422 | Invalid query parameter, path parameter or request body, malformed JSON, or an unknown field in a body | One entry per problem: `location` (e.g. `["body", "experiment_ids"]`), `message`, `type` |
| `EXPERIMENT_NOT_FOUND` | 404 | An experiment ID doesn't exist. When several IDs are missing, all are reported at once | `[{"experiment_id": "..."}]` |
| `MEDIA_NOT_FOUND` | 404 | A media ID doesn't exist | `[{"media_id": "..."}]` |
| `MEDIA_EXPERIMENT_MISMATCH` | 422 | `/vision/analyze` was given media that belongs to a different experiment | `[{"media_id": "...", "experiment_id": "<requested>", "media_experiment_id": "<actual>"}]` |
| `NOT_FOUND` | 404 | The URL doesn't match any endpoint | `null` |
| `METHOD_NOT_ALLOWED` | 405 | Wrong HTTP method for the URL | `null` |
| `HTTP_ERROR` | other | Any other HTTP-level error | `null` |
| `INTERNAL_ERROR` | 500 | Unexpected server error. Internal details are never exposed | `null` |

Two more codes, `INCOMPATIBLE_MEASUREMENTS` and `ANALYSIS_FAILED`, are reserved but not currently returned. Incompatible data is reported inside a normal 200 response (section 6), not as an error.

Use `error.code` in code, and `error.message` for display. Messages may change; codes won't.

### 3.5 Input rules that apply everywhere

| Input | Rule |
|---|---|
| IDs in request bodies (`experiment_id`, `media_id`, …) | Leading and trailing spaces are trimmed; must then be 1–64 characters |
| `experiment_id` or `media_id` in a URL path | 1–64 characters |
| Variable names | Trimmed, 1–100 characters. Matching is exact and case-sensitive |
| Lists of IDs or variables | No duplicates allowed |
| `question` | Trimmed, 3–1000 characters |
| URLs in records | Must start with `http://` or `https://` and contain no spaces |
| Unknown fields in a request body | Rejected with `VALIDATION_ERROR` (catches typos) |

### 3.6 Generated IDs

Computed results get a random ID with a prefix: `ANALYSIS-…`, `COMP-…`, `INSIGHT-…`, `CV-…` (for example `ANALYSIS-9426F958A357`). A new ID is generated on every call.

---

## 4. Data models

These match `Schema.txt` exactly, except **Media** (section 4.7), which was added by issue #4 and isn't in `Schema.txt` v1.0 yet. The backend rejects any record that doesn't fit them. "Required" means the field must be present in the data; every field is always present in responses.

Values marked *(provisional)* aren't defined in `Schema.txt` yet. They're the backend's current choice, pending answers in `Questions.md`.

### 4.1 Experiment

| Field | Type | Required | Description |
|---|---|---|---|
| `experiment_id` | string (1–64) | ✔ | Unique ID, e.g. `PSI-25`. Mock IDs start with `MOCK-` |
| `name` | string | ✔ | Display name |
| `investigation` | string \| null | | Investigation it belongs to |
| `program` | string \| null | | Program, e.g. NASA Physical Sciences Informatics |
| `description` | string \| null | | Description from the official record |
| `platform` | string \| null | | Where it ran, e.g. International Space Station |
| `source_ids` | string[] | | IDs of the Source records it comes from |
| `data_status` | enum | | `illustrative` · `unverified` (default) · `metadata_verified` · `content_verified` *(provisional)* |
| `available_measurements` | string[] | | Variables with at least one measurement record |
| `limitations` | string[] | | Known limitations, to show alongside the data |
| `last_updated` | date `YYYY-MM-DD` \| null | | When the record was last updated |

### 4.2 Measurement

| Field | Type | Required | Description |
|---|---|---|---|
| `measurement_id` | string (1–64) | ✔ | Unique ID |
| `experiment_id` | string (1–64) | ✔ | Experiment it belongs to |
| `variable` | string (1–100) | ✔ | What was measured, e.g. `flame_temperature` |
| `value` | number \| null | | The value. `null` = missing, **never** treat it as 0 |
| `unit` | string \| null | | Unit of `value`, e.g. `K`, `mm/s`, `percent` |
| `timestamp` | string \| null | | As recorded in the source. Format not yet agreed *(provisional)* |
| `conditions` | object | | See below |
| `source_id` | string \| null | | Source record it came from |
| `measurement_status` | enum | | `illustrative` · `unverified` (default) · `verified` *(provisional)* |
| `notes` | string[] | | Free-text notes |

`conditions`: the conditions the measurement was taken under. All fields are optional and `null` when unknown.

| Field | Type | Note |
|---|---|---|
| `fuel` | string \| null | Free text, e.g. `PMMA` |
| `pressure` | number \| null | No unit defined yet *(open question)* |
| `temperature` | number \| null | No unit defined yet *(open question)* |
| `flow_velocity` | number \| null | No unit defined yet *(open question)* |

### 4.3 Source

| Field | Type | Required | Description |
|---|---|---|---|
| `source_id` | string (1–64) | ✔ | Unique ID |
| `title` | string | ✔ | Title |
| `url` | string \| null | | `http(s)://` link. Always `null` in mock data |
| `publisher` | string \| null | | e.g. NASA |
| `source_type` | enum | ✔ | `dataset` · `research_paper` · `technical_report` · `webpage` |
| `experiment_id` | string \| null | | Related experiment |
| `access_status` | enum | | `accessible` · `restricted` · `unavailable` · `unknown` (default) |
| `verification_status` | enum | | `metadata_verified` · `content_verified` · `unverified` (default) |
| `ingestion_status` | enum | | `not_ingested` (default) · `ingested` · `partially_ingested` · `failed` |
| `publication_date` | string \| null | | As given by the publisher, e.g. `2019` or `2019-05-02` |

No endpoint returns Source records yet (see section 12). They're referenced by `source_ids` in other responses.

### 4.4 AnalysisResult

| Field | Type | Description |
|---|---|---|
| `analysis_id` | string | Generated, e.g. `ANALYSIS-9426F958A357` |
| `experiment_id` | string | Experiment analysed |
| `analysis_type` | enum | `statistical_summary` (the only type so far) |
| `status` | enum | `success` (all requested variables summarised) · `partial` (some) · `failed` (none) *(provisional)* |
| `results` | object[] | See below |
| `data_quality.missing_values` | integer ≥ 0 | Number of `null` values excluded |
| `data_quality.validation_passed` | boolean | `false` if any value was missing or any variable had mixed units |
| `data_quality.warnings` | string[] | Human-readable explanation of anything excluded or skipped |
| `source_ids` | string[] | Sources behind the results (sorted) |
| `limitations` | string[] | Limitations to show with the results |

Each `results` item:

| Field | Type | Description |
|---|---|---|
| `metric` | string | `count`, `mean`, `min` or `max` |
| `variable` | string | Variable summarised |
| `value` | integer \| number \| null | Integer for `count`, number otherwise |
| `unit` | string \| null | Unit of the variable (`null` for `count`) |

### 4.5 Comparison

| Field | Type | Description |
|---|---|---|
| `comparison_id` | string | Generated, e.g. `COMP-89F7DEA23BB5` |
| `experiment_ids` | string[] | Experiments compared, in request order |
| `status` | enum | `success` (all variables comparable) · `partial` (some) · `not_comparable` (none) |
| `compared_variables` | object[] | One per variable considered (below) |
| `findings` | object[] | One per **comparable** variable only (below) |
| `warnings` | string[] | Caveats to show with the comparison |
| `source_ids` | string[] | Sources behind the comparison (sorted) |

Each `compared_variables` item:

| Field | Type | Description |
|---|---|---|
| `variable` | string | Variable name |
| `unit` | string \| null | Shared unit; `null` when units differ or the variable couldn't be checked |
| `comparable` | boolean | Whether a direct comparison is valid |
| `reason` | string \| null | Why it isn't comparable; `null` when comparable |

Each `findings` item *(shape provisional)*:

| Field | Type | Description |
|---|---|---|
| `variable` | string | Variable name |
| `unit` | string \| null | Shared unit |
| `values` | object[] | One per experiment: `experiment_id`, `n` (number of values), `mean`, `min`, `max` |

### 4.6 Insight (AI and RAG)

| Field | Type | Description |
|---|---|---|
| `insight_id` | string | Generated, e.g. `INSIGHT-E146E4FE94D4` |
| `question` | string | The question asked (trimmed) |
| `claim` | string | The answer |
| `supporting_evidence` | object[] | Evidence items (below) |
| `fire_safety_relevance` | string \| null | Relevance to spacecraft fire safety |
| `limitations` | string[] | Limitations of the answer |
| `confidence` | enum | `not_assessed` · `low` · `medium` · `high` *(provisional)*. Never a number |
| `evidence_status` | enum | `supported` · `partially_supported` · `insufficient_evidence` |

Each `supporting_evidence` item: `source_id` (required), `experiment_id` (or `null`), `evidence_text` (required, non-empty), `url` (or `null`).

**Rule enforced by the backend:** if `evidence_status` is `supported` or `partially_supported`, `supporting_evidence` must contain at least one item. An insight claiming support without evidence is rejected.

### 4.7 Media (images and videos)

A Media record describes one image or video of an experiment. Records link up as **Experiment → Media → CVResult**: each Media record names its experiment in `experiment_id`, and a CVResult names the media it analysed in `media_id`.

| Field | Type | Required | Description |
|---|---|---|---|
| `media_id` | string | ✔ | Unique ID, 1–64 chars |
| `experiment_id` | string | ✔ | Experiment the media belongs to. Must exist |
| `media_type` | enum | ✔ | `image` · `video` |
| `format` | string | ✔ | File extension without the dot, e.g. `png`, `jpeg`, `mp4`. Letters and digits only, up to 10 characters. Stored in lowercase (`MP4` becomes `mp4`) |
| `file_name` | string | ✔ | File name only, 1–255 chars, no `/` or `\` |
| `file_url` | string \| null | | Public URL of the file (`http://` or `https://`) |
| `storage_path` | string \| null | | Location in the project's own storage, 1–1024 chars |
| `description` | string \| null | | What the media shows |
| `source_id` | string \| null | | Source the media comes from. Must exist |
| `metadata.width_pixels` | integer \| null | | Width in pixels, > 0 |
| `metadata.height_pixels` | integer \| null | | Height in pixels, > 0 |
| `metadata.duration_seconds` | number \| null | | Length in seconds, > 0. **Video only** |
| `metadata.frame_rate_fps` | number \| null | | Frames per second, > 0. **Video only** |
| `availability_status` | enum | | `available` · `restricted` · `unavailable` · `unknown` (default) *(provisional)* |

**Rules enforced by the backend:**
- An `image` can't have `duration_seconds` or `frame_rate_fps`.
- `available` media must have a `file_url` or a `storage_path` (or both), so there's always a file to analyse.
- Only `available` media is sent to the computer vision module (section 5.11).

### 4.8 CVResult (computer vision, optional module)

| Field | Type | Description |
|---|---|---|
| `cv_result_id` | string | Generated, e.g. `CV-ABCA27B09DD7` |
| `experiment_id` | string | Experiment the media belongs to |
| `media_id` | string | Media record analysed (section 4.7) |
| `processing_status` | enum | `success` · `failed` · `not_processed` *(provisional)* |
| `detected` | boolean \| null | Whether a flame was detected; `null` if not processed |
| `features.area_pixels` | integer \| null | Flame area in pixels |
| `features.width_pixels` | integer \| null | Width in pixels |
| `features.height_pixels` | integer \| null | Height in pixels |
| `features.brightness_mean` | number \| null | Mean brightness |
| `method` | string \| null | Method used, e.g. `image_processing` |
| `calibration_status` | enum | `not_calibrated` (default) · `calibrated` *(provisional)* |
| `limitations` | string[] | Limitations |
| `source_ids` | string[] | Sources of the media: the media record's `source_id`, if it has one |

Pixel features are **not physical flame dimensions** unless `calibration_status` is `calibrated`.

### 4.9 JSON Schema files

The backend's Pydantic models are the validation authority. JSON Schema versions of every model above, and of each request body, can be generated with:

```powershell
python -m app.schema_export          # writes to <repo>/shared/schemas/
```

These can be used to validate data or generate TypeScript types, for example with `json-schema-to-typescript`. **Note:** the generated `shared/schemas/` folder isn't committed yet, so run the command after cloning.

---

## 5. Endpoints

Every response below is wrapped in the envelope from section 3.2, and only `data` is shown, except where the full response is useful. All examples are real output from the current mock data. Generated IDs differ on every call.

### 5.1 `GET /api/v1/health`

Checks the API is up. No parameters.

**Response 200**
```json
{
  "success": true,
  "data": { "status": "ok" },
  "error": null,
  "meta": { "schema_version": "1.0", "data_mode": "mock" }
}
```

---

### 5.2 `GET /api/v1/experiments`

Lists experiments with search, filters and pagination. Results are sorted by `experiment_id`.

**Query parameters** (all optional; they combine with AND)

| Name | Type | Rules | Behaviour |
|---|---|---|---|
| `q` | string | ≤ 200 chars | Case-insensitive substring search over `experiment_id`, `name`, `investigation`, `program`, `description` |
| `platform` | string | ≤ 100 chars | Case-insensitive **exact** match on `platform` |
| `data_status` | enum | One of the Experiment `data_status` values | Exact match |
| `page` | integer | ≥ 1, default 1 | Page number |
| `page_size` | integer | 1–100, default 20 | Records per page |

**Example:** `GET /api/v1/experiments?page_size=1`
```json
{
  "items": [
    {
      "experiment_id": "MOCK-EXP-001",
      "name": "Illustrative Solid-Fuel Flame Spread (Orbital)",
      "investigation": "Illustrative solid-fuel flame spread study",
      "program": "THE MOON mock dataset (not NASA data)",
      "description": "Illustrative mock record for development and integration testing. Not NASA data.",
      "platform": "International Space Station",
      "source_ids": ["SRC-MOCK-001"],
      "data_status": "illustrative",
      "available_measurements": ["flame_spread_rate", "flame_temperature", "oxygen_concentration"],
      "limitations": ["Illustrative values only. Do not present as real experimental results."],
      "last_updated": "2026-11-14"
    }
  ],
  "count": 3,
  "page": 1,
  "page_size": 1
}
```

**Errors:** `422 VALIDATION_ERROR` for invalid parameters (e.g. `page=0`, `page_size=101`, unknown `data_status`).

---

### 5.3 `GET /api/v1/experiments/{experiment_id}`

Returns one experiment.

**Path parameter:** `experiment_id` (1–64 chars, exact and case-sensitive).

**Response 200:** `data` is one Experiment object (section 4.1), the same shape as the list items above.

**Errors**
- `404 EXPERIMENT_NOT_FOUND`, for example:
  ```json
  {
    "success": false,
    "data": null,
    "error": {
      "code": "EXPERIMENT_NOT_FOUND",
      "message": "The requested experiment 'NOPE' does not exist.",
      "details": [{ "experiment_id": "NOPE" }]
    },
    "meta": { "schema_version": "1.0", "data_mode": "mock" }
  }
  ```
- `422 VALIDATION_ERROR` if the ID is longer than 64 characters.

---

### 5.4 `GET /api/v1/experiments/{experiment_id}/measurements`

Lists the measurements for one experiment, sorted by `measurement_id`. Records with `value: null` are included, so the UI can show missing data.

**Path parameter:** `experiment_id`.

**Query parameters** (all optional)

| Name | Type | Rules | Behaviour |
|---|---|---|---|
| `variable` | string | ≤ 100 chars | Only this variable. Exact, case-sensitive |
| `page` | integer | ≥ 1, default 1 | Page number |
| `page_size` | integer | 1–500, default 100 | Records per page |

**Example:** `GET /api/v1/experiments/MOCK-EXP-001/measurements?variable=flame_temperature&page_size=2`
```json
{
  "items": [
    {
      "measurement_id": "MEAS-MOCK-004",
      "experiment_id": "MOCK-EXP-001",
      "variable": "flame_temperature",
      "value": 1200.0,
      "unit": "K",
      "timestamp": null,
      "conditions": { "fuel": "PMMA", "pressure": 101.3, "temperature": 298.0, "flow_velocity": 0.1 },
      "source_id": "SRC-MOCK-001",
      "measurement_status": "illustrative",
      "notes": ["Illustrative value. Not a NASA measurement."]
    },
    {
      "measurement_id": "MEAS-MOCK-005",
      "experiment_id": "MOCK-EXP-001",
      "variable": "flame_temperature",
      "value": null,
      "unit": "K",
      "timestamp": null,
      "conditions": { "fuel": "PMMA", "pressure": 101.3, "temperature": 298.0, "flow_velocity": 0.1 },
      "source_id": "SRC-MOCK-001",
      "measurement_status": "illustrative",
      "notes": ["Illustrative value. Not a NASA measurement.", "Value deliberately missing, to exercise null handling."]
    }
  ],
  "count": 3,
  "page": 1,
  "page_size": 2
}
```

An experiment with no measurements returns `items: []` and `count: 0` with HTTP 200.

**Errors:** `404 EXPERIMENT_NOT_FOUND`, `422 VALIDATION_ERROR`.

---

### 5.5 `GET /api/v1/experiments/{experiment_id}/media`

Lists the images and videos for one experiment, sorted by `media_id`. Use it to find a `media_id` for `/vision/analyze`. Only media with `availability_status: available` can actually be analysed.

**Path parameter:** `experiment_id`.

**Query parameters** (all optional)

| Name | Type | Rules | Behaviour |
|---|---|---|---|
| `media_type` | enum | `image` or `video` | Only this type |
| `page` | integer | ≥ 1, default 1 | Page number |
| `page_size` | integer | 1–100, default 20 | Records per page |

**Example:** `GET /api/v1/experiments/MOCK-EXP-001/media?page_size=1`
```json
{
  "items": [
    {
      "media_id": "MOCK-MEDIA-001",
      "experiment_id": "MOCK-EXP-001",
      "media_type": "video",
      "format": "mp4",
      "file_name": "mock_orbital_flame_spread.mp4",
      "file_url": null,
      "storage_path": null,
      "description": "Illustrative mock video record. No file exists. Not NASA data.",
      "source_id": "SRC-MOCK-001",
      "metadata": { "width_pixels": 1280, "height_pixels": 720, "duration_seconds": 30.0, "frame_rate_fps": 30.0 },
      "availability_status": "unavailable"
    }
  ],
  "count": 2,
  "page": 1,
  "page_size": 1
}
```

An experiment with no media returns an empty `items` list with `count: 0`, not an error.

**Errors:** `404 EXPERIMENT_NOT_FOUND`; `422 VALIDATION_ERROR` (e.g. `media_type=audio`, `page_size=101`).

---

### 5.6 `GET /api/v1/media/{media_id}`

Returns one media record.

**Path parameter:** `media_id` (1–64 chars, exact and case-sensitive).

**Response 200:** `data` is one Media object (section 4.7), the same shape as the list items above.

**Errors**
- `404 MEDIA_NOT_FOUND`, for example:
  ```json
  {
    "success": false,
    "data": null,
    "error": {
      "code": "MEDIA_NOT_FOUND",
      "message": "The requested media 'NOPE' does not exist.",
      "details": [{ "media_id": "NOPE" }]
    },
    "meta": { "schema_version": "1.0", "data_mode": "mock" }
  }
  ```
- `422 VALIDATION_ERROR` if the ID is longer than 64 characters.

---

### 5.7 `POST /api/v1/analysis`

Runs an analysis on one experiment. Currently supports `statistical_summary`: count, mean, min and max for each variable. The rules are in section 6.

**Request body**

| Field | Type | Required | Rules |
|---|---|---|---|
| `experiment_id` | string | ✔ | 1–64 chars |
| `analysis_type` | enum | | `statistical_summary` (default; the only value accepted) |
| `variables` | string[] | | 1–20 unique names. Default: all of the experiment's `available_measurements` |

```json
{ "experiment_id": "MOCK-EXP-001", "variables": ["flame_spread_rate", "flame_temperature"] }
```

**Response 200** (`data`)
```json
{
  "analysis_id": "ANALYSIS-9426F958A357",
  "experiment_id": "MOCK-EXP-001",
  "analysis_type": "statistical_summary",
  "status": "success",
  "results": [
    { "metric": "count", "variable": "flame_spread_rate", "value": 3, "unit": null },
    { "metric": "mean", "variable": "flame_spread_rate", "value": 1.0, "unit": "mm/s" },
    { "metric": "min", "variable": "flame_spread_rate", "value": 0.8, "unit": "mm/s" },
    { "metric": "max", "variable": "flame_spread_rate", "value": 1.2, "unit": "mm/s" },
    { "metric": "count", "variable": "flame_temperature", "value": 2, "unit": null },
    { "metric": "mean", "variable": "flame_temperature", "value": 1250.0, "unit": "K" },
    { "metric": "min", "variable": "flame_temperature", "value": 1200.0, "unit": "K" },
    { "metric": "max", "variable": "flame_temperature", "value": 1300.0, "unit": "K" }
  ],
  "data_quality": {
    "missing_values": 1,
    "validation_passed": false,
    "warnings": ["1 'flame_temperature' measurement(s) have no value and were excluded."]
  },
  "source_ids": ["SRC-MOCK-001"],
  "limitations": [
    "Illustrative values only. Do not present as real experimental results.",
    "Computed from illustrative mock measurements. Not a scientific result.",
    "Descriptive statistics only. Measurement uncertainty is not accounted for."
  ]
}
```

**Outcomes that are not errors** (HTTP 200)
- A requested variable has no measurements: it's skipped with a warning, and `status` is `partial`.
- An experiment with no measurements: `status: "failed"`, `results: []`, plus a warning.

**Errors:** `404 EXPERIMENT_NOT_FOUND`; `422 VALIDATION_ERROR` (missing `experiment_id`, unsupported `analysis_type`, empty or duplicate `variables`, unknown fields).

---

### 5.8 `POST /api/v1/comparison`

Compares two or more experiments, variable by variable. A variable gets a finding only when a direct comparison is valid (section 6).

**Request body**

| Field | Type | Required | Rules |
|---|---|---|---|
| `experiment_ids` | string[] | ✔ | 2–10 unique IDs |
| `variables` | string[] | | 1–20 unique names. Default: every variable measured in **any** of the experiments, so variables missing from one experiment are listed as not comparable |

```json
{ "experiment_ids": ["MOCK-EXP-001", "MOCK-EXP-002"] }
```

**Response 200** (`data`)
```json
{
  "comparison_id": "COMP-89F7DEA23BB5",
  "experiment_ids": ["MOCK-EXP-001", "MOCK-EXP-002"],
  "status": "partial",
  "compared_variables": [
    { "variable": "flame_spread_rate", "unit": "mm/s", "comparable": true, "reason": null },
    { "variable": "flame_temperature", "unit": null, "comparable": false, "reason": "Units differ (K, degC) and no documented conversion exists." },
    { "variable": "oxygen_concentration", "unit": "percent", "comparable": true, "reason": null }
  ],
  "findings": [
    {
      "variable": "flame_spread_rate",
      "unit": "mm/s",
      "values": [
        { "experiment_id": "MOCK-EXP-001", "n": 3, "mean": 1.0, "min": 0.8, "max": 1.2 },
        { "experiment_id": "MOCK-EXP-002", "n": 3, "mean": 2.0, "min": 1.6, "max": 2.4 }
      ]
    },
    {
      "variable": "oxygen_concentration",
      "unit": "percent",
      "values": [
        { "experiment_id": "MOCK-EXP-001", "n": 1, "mean": 21.0, "min": 21.0, "max": 21.0 },
        { "experiment_id": "MOCK-EXP-002", "n": 1, "mean": 21.0, "min": 21.0, "max": 21.0 }
      ]
    }
  ],
  "warnings": [
    "Do not interpret incompatible measurements as a direct comparison.",
    "Experiments ran on different platforms (Ground laboratory, International Space Station). Differences may reflect gravity level and other platform-specific factors, not a single cause.",
    "Computed from illustrative mock measurements. Not a scientific result."
  ],
  "source_ids": ["SRC-MOCK-001", "SRC-MOCK-002"]
}
```

**Errors**
- `404 EXPERIMENT_NOT_FOUND`: lists **every** missing ID, e.g. `"details": [{"experiment_id": "NOPE-1"}, {"experiment_id": "NOPE-2"}]`.
- `422 VALIDATION_ERROR`: fewer than 2 or more than 10 IDs, duplicate IDs, empty `variables`, or unknown fields.

---

### 5.9 `POST /api/v1/insights`

Generates an evidence-backed insight about a question, optionally about specific experiments. **Currently a placeholder** (section 2).

**Request body**

| Field | Type | Required | Rules |
|---|---|---|---|
| `question` | string | ✔ | Trimmed, 3–1000 chars |
| `experiment_ids` | string[] | | 0–10 unique IDs (default `[]`). Every ID must exist |

```json
{ "question": "What can this experiment tell us about combustion in microgravity?", "experiment_ids": ["MOCK-EXP-001"] }
```

**Response 200** (`data`, current placeholder)
```json
{
  "insight_id": "INSIGHT-E146E4FE94D4",
  "question": "What can this experiment tell us about combustion in microgravity?",
  "claim": "No evidence-backed answer is available: the AI integration module is not connected yet.",
  "supporting_evidence": [],
  "fire_safety_relevance": null,
  "limitations": ["AI integration module not connected. No analysis was performed."],
  "confidence": "not_assessed",
  "evidence_status": "insufficient_evidence"
}
```

When the AI module is connected, the response keeps this shape, filled in like the `Schema.txt` example: a real `claim`, `supporting_evidence` items and `evidence_status: "supported"`.

**Errors:** `404 EXPERIMENT_NOT_FOUND`; `422 VALIDATION_ERROR` (missing, too short or too long `question`; duplicate IDs; unknown fields).

---

### 5.10 `POST /api/v1/assistant/ask`

Asks a general research question, answered by the RAG module over approved sources. **Currently a placeholder.**

**Request body**

| Field | Type | Required | Rules |
|---|---|---|---|
| `question` | string | ✔ | Trimmed, 3–1000 chars |

No other fields are accepted (sending `experiment_ids` here gives a `VALIDATION_ERROR`).

**Response 200:** `data` is an Insight (section 4.6). The current placeholder is the same as in 5.9, except the `claim` and `limitations` name the research assistant (RAG) module.

**Errors:** `422 VALIDATION_ERROR`.

---

### 5.11 `POST /api/v1/vision/analyze`

Analyzes a flame image or video. **Optional module, currently a placeholder.**

Before anything reaches the CV module, the backend checks, in this order:
1. The experiment exists, or it returns `404 EXPERIMENT_NOT_FOUND`.
2. The media exists, or it returns `404 MEDIA_NOT_FOUND`.
3. The media belongs to that experiment, or it returns `422 MEDIA_EXPERIMENT_MISMATCH`.
4. The media is `available`. If not, the backend returns `processing_status: not_processed` with the reason in `limitations`, and the CV module is never called.

**Request body**

| Field | Type | Required | Rules |
|---|---|---|---|
| `experiment_id` | string | ✔ | 1–64 chars; must exist |
| `media_id` | string | ✔ | 1–64 chars; must exist and belong to the experiment |

```json
{ "experiment_id": "MOCK-EXP-001", "media_id": "MOCK-MEDIA-001" }
```

**Response 200** (`data`). All mock media is `unavailable`, so this is what the mock data returns:
```json
{
  "cv_result_id": "CV-37984460B29F",
  "experiment_id": "MOCK-EXP-001",
  "media_id": "MOCK-MEDIA-001",
  "processing_status": "not_processed",
  "detected": null,
  "features": { "area_pixels": null, "width_pixels": null, "height_pixels": null, "brightness_mean": null },
  "method": null,
  "calibration_status": "not_calibrated",
  "limitations": ["Media 'MOCK-MEDIA-001' is unavailable. No file was analysed."],
  "source_ids": ["SRC-MOCK-001"]
}
```

For `available` media, the request goes to the CV module. Until the module is connected, the response has the same shape, with the limitation `"Computer vision module not connected. No media was analysed."`

**Errors**
- `404 EXPERIMENT_NOT_FOUND`, `404 MEDIA_NOT_FOUND`.
- `422 MEDIA_EXPERIMENT_MISMATCH`, for example with `{"experiment_id": "MOCK-EXP-002", "media_id": "MOCK-MEDIA-001"}`:
  ```json
  {
    "code": "MEDIA_EXPERIMENT_MISMATCH",
    "message": "Media 'MOCK-MEDIA-001' belongs to experiment 'MOCK-EXP-001', not 'MOCK-EXP-002'.",
    "details": [{ "media_id": "MOCK-MEDIA-001", "experiment_id": "MOCK-EXP-002", "media_experiment_id": "MOCK-EXP-001" }]
  }
  ```
- `422 VALIDATION_ERROR` (e.g. missing `media_id`).

---

## 6. Analysis and comparison rules

These follow the project contract's data validation rules and apply to the built-in engine. A Data Analysis module that replaces it is expected to keep them.

**Statistical summary (`/analysis`)**
1. `null` values are excluded and counted in `data_quality.missing_values`. They are never treated as zero.
2. If one variable is recorded in more than one unit, it is **not summarised**: there's a warning instead, and `validation_passed` is `false`. Units are never converted, because no conversions are documented yet.
3. `status` is `success` when every requested variable was summarised, `partial` when some were, and `failed` when none were.
4. Limitations always say that uncertainty isn't accounted for, and say when the data is illustrative.

**Comparison (`/comparison`)**

A variable is **comparable** only if all of these hold:
1. Every experiment has at least one non-null value for it. Otherwise the reason is `"No usable values for …"`.
2. All values use the same unit. Otherwise the reason is `"Units differ (…) and no documented conversion exists."`
3. No recorded measurement condition (`fuel`, `pressure`, `temperature`, `flow_velocity`) has two different values. Otherwise the reason is `"Measurement conditions differ: pressure."` or similar.

If a condition is unrecorded (`null`) on some measurements, the variable is still comparable but gets a warning that matching conditions couldn't be fully confirmed.

Warnings:
- The first warning is always `"Do not interpret incompatible measurements as a direct comparison."` when any variable isn't comparable.
- When experiments ran on different platforms, a warning says differences may reflect gravity level and other factors.
- When the data is illustrative, a warning says so.

---

## 7. Mock data

Files: `app/adapters/mock_data/experiments.json`, `measurements.json`, `sources.json` and `media.json`. All IDs start with `MOCK-`, every record is marked `illustrative`, `unverified` or `unavailable`, and no URLs are given.

| Experiment | Platform | Measurements | Use it to test |
|---|---|---|---|
| `MOCK-EXP-001` | International Space Station | 7: `flame_spread_rate` 0.8 / 1.0 / 1.2 mm/s; `flame_temperature` 1200 / **null** / 1300 K; `oxygen_concentration` 21 percent | Normal data and a missing value |
| `MOCK-EXP-002` | Ground laboratory | 6: `flame_spread_rate` 1.6 / 2.0 / 2.4 mm/s; `flame_temperature` 1050 / 1100 **degC**; `oxygen_concentration` 21 percent | Comparison with 001: spread rate compares, temperature doesn't (K vs °C) |
| `MOCK-EXP-003` | Drop tower | None | Empty states, failed analysis, `not_comparable` |

All measurements in 001 and 002 share the same conditions: `fuel: PMMA`, `pressure: 101.3`, `temperature: 298.0`, `flow_velocity: 0.1`.

Sources: `SRC-MOCK-001` (for 001) and `SRC-MOCK-002` (for 002), both `dataset`, `unverified` and `not_ingested`. 003 has no sources.

Media: no files exist, so every record is `unavailable` with no `file_url` or `storage_path`.

| Media | Experiment | Type | Notes |
|---|---|---|---|
| `MOCK-MEDIA-001` | `MOCK-EXP-001` | video, `mp4` | Full metadata: 1280×720, 30 s, 30 fps |
| `MOCK-MEDIA-002` | `MOCK-EXP-001` | image, `png` | All metadata `null` (unknown) |
| `MOCK-MEDIA-003` | `MOCK-EXP-002` | image, `jpeg` | 640×480 |

003 has no media.

Handy requests:

| Request | Result |
|---|---|
| Compare `MOCK-EXP-001` + `MOCK-EXP-002` | `partial` |
| Compare 001 + 002 with `variables: ["flame_spread_rate"]` | `success` |
| Compare `MOCK-EXP-001` + `MOCK-EXP-003` | `not_comparable` |
| Analyse `MOCK-EXP-003` | `failed` |
| Experiments with `q=droplet` | Only 003 |
| Vision with `MOCK-EXP-001` + `MOCK-MEDIA-001` | `not_processed` (media unavailable) |
| Vision with `MOCK-EXP-002` + `MOCK-MEDIA-001` | `422 MEDIA_EXPERIMENT_MISMATCH` |

When the backend loads the mock data, it checks every record against the schema and checks that the files agree with each other (IDs are unique, referenced experiments and sources exist, `available_measurements` matches the actual measurements). Broken mock data stops the server at startup with a clear message, instead of failing during a demo.

---

## 8. Guide for frontend developers

1. **Always check `success` first.** On `false`, branch on `error.code`. For `VALIDATION_ERROR`, `error.details[].location` shows which field to highlight (e.g. `["body", "question"]`).
2. **Show a "mock data" banner while `meta.data_mode` is `"mock"`.** Records with `data_status` or `measurement_status` of `illustrative` should be visibly labelled as illustrative.
3. **Detect placeholders:**
   - For insights, `evidence_status: "insufficient_evidence"` with empty `supporting_evidence` means there's no answer. Show the `claim` and `limitations` as a notice, not as an answer.
   - For vision, `processing_status: "not_processed"` means nothing was analysed. `limitations` says why (media unavailable, or module not connected).
   - To pick media for vision, list it with `GET /experiments/{id}/media`. Only offer analysis for media with `availability_status: "available"`.
4. **Show `null` as missing ("—"),** never as 0.
5. **Show `warnings` and `limitations`** next to analysis and comparison results. Only chart variables that appear in `findings`; use `compared_variables` with `comparable: false` to explain why the others are missing.
6. **Pagination:** total pages = `ceil(count / page_size)`. A page past the end is empty, not an error.
7. **IDs are case-sensitive** and must be sent exactly as received.
8. **Status values for filters and badges** are listed in section 4. The experiment `data_status` filter only accepts those values.
9. **Types:** generate TypeScript types from `/openapi.json` (for example with `openapi-typescript`) or from the JSON Schema files (section 4.9), so they stay in sync with the backend.
10. **CORS:** `http://localhost:3000` and `http://localhost:5173` are allowed by default. Ask the backend owner to add any other origin (section 10).

Minimal envelope type:

```ts
type Envelope<T> = {
  success: boolean;
  data: T | null;
  error: { code: string; message: string; details: Record<string, unknown>[] | null } | null;
  meta: { schema_version: string; data_mode: "mock" | "psi" | null };
};
type Page<T> = { items: T[]; count: number; page: number; page_size: number };
```

---

## 9. Guide for AI/ML module owners

### 9.1 How modules plug in

Each module has an **interface** (a Python `Protocol`) in `app/integrations/`. Before calling a module, the backend:
1. validates the request,
2. looks up the experiments and measurements, returning a 404 itself if an ID is unknown (for vision, it also checks the media record: it exists, belongs to the experiment, and is `available`),
3. calls your method with plain model objects.

Your method returns a model object. The backend wraps it in the envelope. You don't handle HTTP, routing or errors for unknown IDs.

| Module | Interface | Method(s) | Current implementation | File |
|---|---|---|---|---|
| Data Analysis | `AnalysisEngine` | `analyze`, `compare` | `ReferenceAnalysisEngine` (working) | `app/integrations/analysis.py` |
| AI insights | `InsightEngine` | `generate` | `UnavailableInsightEngine` (placeholder) | `app/integrations/insights.py` |
| RAG assistant | `ResearchAssistant` | `ask` | `UnavailableResearchAssistant` (placeholder) | `app/integrations/insights.py` |
| Computer vision | `VisionAnalyzer` | `analyze` | `UnavailableVisionAnalyzer` (placeholder) | `app/integrations/vision.py` |

### 9.2 Method signatures

```python
# Data Analysis
class AnalysisEngine(Protocol):
    def analyze(self, experiment: Experiment, measurements: list[Measurement],
                analysis_type: AnalysisType, variables: list[str] | None) -> AnalysisResult: ...
    def compare(self, experiments: list[Experiment],
                measurements: dict[str, list[Measurement]],   # keyed by experiment_id
                variables: list[str] | None) -> Comparison: ...

# AI insights
class InsightEngine(Protocol):
    def generate(self, question: str, experiments: list[Experiment]) -> Insight: ...

# RAG
class ResearchAssistant(Protocol):
    def ask(self, question: str) -> Insight: ...

# Computer vision
class VisionAnalyzer(Protocol):
    def analyze(self, experiment: Experiment, media: Media) -> CVResult: ...
```

What you receive:
- `measurements` holds **all** of an experiment's measurements, including `null` values.
- `variables` is `None` when the user didn't choose any, so pick the default yourself.
- `question` is already trimmed and 3–1000 characters long.
- `experiments` can be an empty list for insights.
- `media` is a full Media record (section 4.7) that belongs to `experiment` and is `available`, so it always has a `file_url` or a `storage_path`. Use `media_type`, `format` and `metadata` to decide how to read the file.

Models are imported from `app.models.experiment`, `app.models.analysis`, `app.models.insight`, `app.models.media` and `app.models.vision`.

### 9.3 Rules your output must follow

- **Return the model objects** (`Insight`, `AnalysisResult`, …). The models validate themselves, so an invalid result fails immediately instead of reaching the frontend.
- **Every claim needs evidence.** An `Insight` with `evidence_status` `supported` or `partially_supported` and no `supporting_evidence` is rejected. If you can't support an answer, return `insufficient_evidence`.
- **Never invent citations.** `source_id` and `url` must refer to real, approved sources.
- **`confidence` is qualitative** (`not_assessed`, `low`, `medium`, `high`). Use `not_assessed` unless a validated method backs the rating.
- **Pixel features aren't physical sizes.** Keep `calibration_status: "not_calibrated"` and say so in `limitations`, unless a valid calibration exists.
- **Keep limitations honest.** Include the limitations of the data and of your method.
- **Generate IDs** with `app.ids.new_id("INSIGHT")`, `new_id("ANALYSIS")`, `new_id("COMP")` or `new_id("CV")`.

### 9.4 Example: an insight engine

```python
from app.ids import new_id
from app.models.experiment import Experiment
from app.models.insight import Evidence, Insight


class RagInsightEngine:
    def generate(self, question: str, experiments: list[Experiment]) -> Insight:
        passages = my_retriever.search(question, experiment_ids=[e.experiment_id for e in experiments])
        if not passages:
            return Insight(
                insight_id=new_id("INSIGHT"),
                question=question,
                claim="No approved source addresses this question.",
                evidence_status="insufficient_evidence",
                limitations=["No matching passages in the approved source set."],
            )
        return Insight(
            insight_id=new_id("INSIGHT"),
            question=question,
            claim=my_llm.answer(question, passages),
            supporting_evidence=[
                Evidence(source_id=p.source_id, experiment_id=p.experiment_id, evidence_text=p.text, url=p.url)
                for p in passages
            ],
            fire_safety_relevance=my_llm.fire_safety_note(question, passages),
            limitations=["Answer generated from retrieved passages; verify against the cited sources."],
            confidence="not_assessed",
            evidence_status="supported",
        )
```

### 9.5 Registering and testing your module

Register it in `build_integrations()` in `app/integrations/__init__.py`:

```python
return Integrations(
    analysis=ReferenceAnalysisEngine(),
    insights=RagInsightEngine(),            # was UnavailableInsightEngine()
    assistant=UnavailableResearchAssistant(),
    vision=UnavailableVisionAnalyzer(),
)
```

To test against the real API without changing the defaults, pass your module to the app factory:

```python
from fastapi.testclient import TestClient
from app.integrations import Integrations, build_integrations
from app.main import create_app
from app.config import Settings

defaults = build_integrations(Settings())
app = create_app(integrations=Integrations(
    analysis=defaults.analysis, insights=RagInsightEngine(),
    assistant=defaults.assistant, vision=defaults.vision,
))
client = TestClient(app)
resp = client.post("/api/v1/insights", json={"question": "Why are microgravity flames spherical?"})
assert resp.json()["success"] is True
```

Then run the full suite (`pytest`). The existing analysis and comparison tests also describe the behaviour a replacement Data Analysis engine should keep.

### 9.6 Current limits to be aware of

- Module methods are called **synchronously**, with **no timeout**. A slow model call blocks that request.
- If your method raises an exception, the client gets `500 INTERNAL_ERROR` and the error is logged. There's no dedicated "module unavailable" code yet.
- If your module needs extra dependencies, add them to `requirements.txt`. Read API keys from environment variables, never from code.

---

## 10. Configuration

Settings come from environment variables, or from a `.env` file in `backend/`, which is gitignored.

| Variable | Default | Meaning |
|---|---|---|
| `MOON_DATA_MODE` | `mock` | `mock` or `psi`. `psi` currently stops startup with a "not implemented" message, because the PSI adapter isn't built yet |
| `MOON_CORS_ORIGINS` | `["http://localhost:3000","http://localhost:5173"]` | JSON list of frontend origins allowed to call the API |

---

## 11. Backend code structure

```
backend/
  app/
    main.py              App factory: CORS, error handlers, routers
    config.py            Settings and schema version
    errors.py            Error codes and the handlers that build error envelopes
    ids.py               Generated result IDs
    schema_export.py     Writes JSON Schema files
    models/              Data models (section 4) and the response envelope
    api/v1/              One file per endpoint group; routes only validate input and call a service
    services/            Look up experiments, then hand off to a module
    integrations/        Module interfaces and current implementations (section 9)
    adapters/            Data sources: mock adapter + mock_data/*.json (PSI adapter to come)
  tests/                 137 tests: endpoints, errors, rules, models, mock data, schema files
  docs/API.md            This document
```

Request flow: **route** (validates) → **service** (looks up experiments, 404s) → **module** (computes) → **route** (wraps in the envelope).

---

## 12. Known limitations and open questions

**Not built yet**
- **Source endpoint.** No endpoint returns Source records (title, URL) for citations. Proposed: `GET /api/v1/sources/{source_id}` and `GET /api/v1/sources`.
- **Media files.** Media records exist, but there's no upload, and the backend doesn't serve files itself. How files are stored and served isn't decided yet.
- **PSI adapter.** Only mock data is served.
- **Stored results.** Analyses, comparisons and insights aren't saved.
- **Module protections.** No timeouts and no "module unavailable" error code.

**Open schema questions** (details and proposed answers in `Questions.md`)

| # | Subject | Effect on you now |
|---|---|---|
| Q1 | Units for `conditions` numbers, fuel names, missing conditions | Show condition numbers without units for now |
| Q2 | Final allowed values for status fields | Values marked *(provisional)* in section 4 may change, including Media `availability_status` |
| Q3 | Shape of comparison `findings` | The findings item shape may change |
| Q4 | POST request bodies | Request fields may be added |
| Q5 | Format of `timestamp` and `publication_date` | Treat both as opaque text for now |
| Q6 | Serving sources | See "Not built yet" |
| Q7 | Media for computer vision | Media record and endpoints added (issue #4). File storage and upload are still open; see "Not built yet" |
| Q8 | How gravity level is represented | A `gravity_level` field may be added to Experiment |

Changes to anything marked provisional will be announced, and this document updated, before they're merged.
