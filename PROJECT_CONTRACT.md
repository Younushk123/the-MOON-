# THE MOON — Project Contract

**Version:** Draft v0.1  
**Owner:** Project Lead / AI-ML Integration  
**Status:** Proposed for team review  
**Last updated:** 24 October 2026

## 1. Purpose

This document defines the shared data schema, API response formats, module interfaces, and integration rules for THE MOON.

All frontend, backend, scientific analysis, research/RAG, and computer vision components should follow this contract.

This is a preliminary contract. Fields may be updated after the official NASA challenge resources become available on 28 October 2026.

## 2. System Architecture

User → Web Dashboard → FastAPI Backend → Scientific Analysis / Research & RAG / Image Analysis → Structured Results → Dashboard

The backend coordinates requests and returns consistent JSON. Each module has a defined responsibility and must not silently substitute unsupported results.

## 3. Common Data Schema v0.1

### 3.1 Experiment record

```json
{
  "schema_version": "0.1",
  "experiment_id": "MOCK-001",
  "experiment_name": "Illustrative Combustion Experiment",
  "fuel": null,
  "oxygen_concentration": {
    "value": null,
    "unit": "percent",
    "basis": null
  },
  "pressure": {
    "value": null,
    "unit": null
  },
  "gravity_condition": {
    "value": "unknown",
    "source_value": null
  },
  "temperature": {
    "value": null,
    "unit": null
  },
  "flame_media": [],
  "measurements": [],
  "source_references": [],
  "validation_status": "unverified",
  "data_notes": []
}
```

**Rules:**
- `experiment_id` is required and must be unique within the dataset.
- Unknown measurements must be represented as `null`, not zero.
- Values must include units where applicable.
- `source_value` preserves the original wording when a value is mapped to a standardized category.
- `MOCK-001` is an illustrative identifier, not an official NASA experiment ID.
- Do not assume that every field exists in the official dataset.

### 3.2 Flame media object

```json
{
  "media_id": "MEDIA-MOCK-001",
  "media_type": "image",
  "uri": null,
  "source_reference_id": null,
  "analysis_status": "not_processed"
}
```

Allowed `media_type` values: `image`, `video`, `unknown`.

The media URI and source must be verified before the media is presented as official NASA material.

### 3.3 Measurement object

```json
{
  "measurement_id": "MEAS-MOCK-001",
  "metric_name": "flame_area",
  "value": null,
  "unit": "pixel_squared",
  "method": null,
  "source_media_id": null,
  "confidence": null,
  "limitations": []
}
```

Measurements may include temperature, burning duration, flame-region area, brightness, or other supported variables. The actual available variables and units must be confirmed from the source.

A pixel-based image measurement must not be described as a physical flame area unless a valid calibration method supports that conversion.

### 3.4 Source reference object

```json
{
  "source_reference_id": "SRC-MOCK-001",
  "title": "Illustrative Source Record",
  "source_type": "unknown",
  "publisher": null,
  "uri": null,
  "publication_date": null,
  "accessed_date": null,
  "locator": null
}
```

`locator` may identify a page, section, figure, table, dataset record, or relevant passage.

Never invent a source URL, publication date, or citation.

## 4. Data Validation Rules

1. Validate required fields and data types before processing.
2. Preserve original source values and units.
3. Normalize units only when the conversion is documented.
4. Flag missing, invalid, or incompatible measurements.
5. Compare experiments only when the selected variables are meaningfully compatible.
6. Distinguish observed data, calculated results, image-derived measurements, and AI-generated explanations.
7. Record the method and source references for derived scientific results.
8. Label all illustrative records and outputs as mock data until replaced with verified data.

### Validation status values

- `unverified`: source or record has not yet been verified.
- `pending`: validation has started but is incomplete.
- `valid`: required checks passed for the intended use.
- `invalid`: a blocking validation failure was found.

A valid record does not automatically mean every measurement in it is suitable for every comparison.

## 5. API Conventions

**Base path:** `/api/v1`

**Format:** JSON

**Common rules:**
- Successful responses use a consistent response envelope.
- Errors include a machine-readable code and a human-readable message.
- Lists return an `items` array and a `count`.
- Query parameters must be validated.
- Responses must not claim that mock records are official NASA data.

### 5.1 List experiments

`GET /api/v1/experiments`

Optional query parameters: `q`, `fuel`, `gravity_condition`, `page`, `page_size`.

Example response:

```json
{
  "success": true,
  "data": {
    "items": [],
    "count": 0,
    "page": 1,
    "page_size": 20
  },
  "error": null,
  "meta": {
    "schema_version": "0.1",
    "data_mode": "mock"
  }
}
```

### 5.2 Get experiment details

`GET /api/v1/experiments/{experiment_id}`

The `data` field contains one experiment object matching Section 3.1.

If the ID does not exist, return HTTP `404` with a structured error response.

### 5.3 Compare experiments

`POST /api/v1/comparisons`

Example request:

```json
{
  "experiment_ids": ["MOCK-001", "MOCK-002"],
  "metrics": ["temperature", "burning_duration"]
}
```

Example response:

```json
{
  "success": true,
  "data": {
    "comparison_id": "CMP-MOCK-001",
    "experiment_ids": ["MOCK-001", "MOCK-002"],
    "metrics": [],
    "warnings": [],
    "source_references": []
  },
  "error": null,
  "meta": {
    "data_mode": "mock"
  }
}
```

Each comparison metric must identify the variable, values, units, compatibility status, and any relevant warnings. Do not produce a numerical comparison when the underlying values or units are incompatible.

### 5.4 Request AI insights

`POST /api/v1/insights`

Example request:

```json
{
  "experiment_ids": ["MOCK-001"],
  "question": "What does the available evidence indicate about flame behavior?",
  "include_research": true
}
```

Example response:

```json
{
  "success": true,
  "data": {
    "insight_id": "INS-MOCK-001",
    "summary": "Illustrative response. No scientific conclusion has been established.",
    "claims": [],
    "evidence": [],
    "limitations": [],
    "confidence": null,
    "status": "mock"
  },
  "error": null,
  "meta": {
    "data_mode": "mock"
  }
}
```

Every scientific claim should link to supporting evidence or explicitly state that evidence is unavailable.

### 5.5 Error response

Example:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "EXPERIMENT_NOT_FOUND",
    "message": "The requested experiment does not exist."
  },
  "meta": {
    "schema_version": "0.1"
  }
}
```

Suggested error codes include `VALIDATION_ERROR`, `EXPERIMENT_NOT_FOUND`, `INCOMPATIBLE_MEASUREMENTS`, and `ANALYSIS_FAILED`.

## 6. Evidence and AI Traceability

Each evidence item should identify:

- The claim it supports.
- The source reference or experiment record.
- A relevant passage, measurement, or data locator.
- The relationship between the evidence and the claim.
- Any uncertainty or limitation.

AI-generated explanations must distinguish between:
- Directly observed source data.
- Calculated or image-derived results.
- Background research.
- Interpretations and recommendations.

If no suitable evidence supports a claim, the system must say so rather than inventing a citation or presenting speculation as fact.

## 7. Module Interfaces

| Module | Expected input | Expected output |
|---|---|---|
| Frontend | API JSON | Dashboard views and visualizations |
| Backend | Validated requests and records | Consistent API responses |
| Scientific analysis | Experiment records and selected metrics | Calculations, comparisons, warnings |
| Research/RAG | Approved documents and user question | Claims with evidence references |
| Computer vision | Verified image/video reference | Image-derived measurements with method and limitations |
| Integration owner | Module outputs and tests | Verified end-to-end workflow |

## 8. Versioning and Change Control

- This is Draft v0.1, not a finalized NASA data specification.
- The project lead approves shared schema and API changes.
- Changes must be communicated to all affected members.
- Record changes in a short change log.
- After the official resources are released, map actual source fields to this schema and document any necessary changes.

## 9. Acceptance Criteria

The contract is ready for integration when:
- All members can identify the required input and output of their module.
- The backend validates records against the agreed models.
- Frontend and backend can exchange example JSON successfully.
- The comparison module flags incompatible or missing values.
- AI insights can represent evidence, limitations, and unsupported claims.
- Mock data is clearly separated from verified source data.

**End of Draft v0.1**
