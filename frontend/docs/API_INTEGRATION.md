# Frontend ⇄ Backend integration (THE MOON, schema v1.0)

Source of truth: "GitHub Repository Structure & Final Integration Schemas", Sections 4–5.
TypeScript mirror of every schema: `src/types/schemas.ts`.

## Switching from mock to real API
1. Create `.env.local`:
   ```
   VITE_USE_MOCK_DATA=false
   VITE_API_BASE_URL=http://localhost:8000
   ```
2. Enable CORS for the Vite origin (`http://localhost:5173`) in FastAPI.
3. Restart `npm run dev`. No page code changes are needed: every call goes through
   `src/services/api.ts` → `src/services/apiClient.ts`.

## Envelope (all endpoints)
Success: `{ "success": true, "data": <payload>, "message": "..." }`
Failure: `{ "success": false, "data": null, "message": "...", "error_code": "..." }`
Failures may use a 4xx/5xx status; the frontend reads the envelope either way and shows `message`.

## Endpoints and the `data` the frontend expects
| Method | Path | Request | `data` | Used by |
|---|---|---|---|---|
| GET | /api/v1/health | – | any object | footer status |
| GET | /api/v1/experiments | – | `Experiment[]` | Overview, Explorer, Comparison, AI Insights, Data Quality |
| GET | /api/v1/experiments/{experiment_id} | – | `Experiment` | Experiment Details |
| GET | /api/v1/experiments/{experiment_id}/measurements | – | `Measurement[]` | Details, Comparison, derived conditions |
| POST | /api/v1/analysis | `{experiment_id, analysis_type?}` ⚠ | `AnalysisResult` | Overview, Data Quality, AI Insights |
| POST | /api/v1/comparison | `{experiment_ids[], variables?[]}` | `Comparison` | Comparison |
| POST | /api/v1/assistant/ask | `{question, experiment_ids[]}` | `Insight` ⚠ | AI Insights |
| POST | /api/v1/insights | `{experiment_id, analysis_id, question}` | `Insight` ⚠ | service layer ready (no UI control yet) |
| POST | /api/v1/vision/analyze | `{experiment_id, media_id}` | `CvResult` | ID-only requests return `not_processed` |
| POST | /api/v1/vision/analyze-image | multipart form with `media_id` and `image` | `CvResult` | PSI-69 still-image analysis; JPEG, PNG, or WebP; 25 MB and 12 MP max |
| POST | /api/v1/vision/analyze-video | multipart form with `media_id` and `video` | `CvAnalysisJob` (202) | PSI-69 FLEX MP4 only; 25 MB max |
| GET | /api/v1/vision/jobs/{job_id} | — | `CvAnalysisJob` | Poll until `completed` or `failed` |

⚠ = not specified in the document; see open questions.

### Fields read from each schema
- **Experiment**: experiment_id, name, investigation, program, description, platform, source_ids, data_status, available_measurements, limitations, last_updated
- **Measurement**: measurement_id, experiment_id, variable, value, unit, timestamp, conditions{fuel,pressure,temperature,flow_velocity}, source_id, measurement_status, notes
- **Source**: source_id, title, url, publisher, source_type, experiment_id, access_status, verification_status, ingestion_status, publication_date
- **AnalysisResult**: analysis_id, experiment_id, analysis_type, status, results[{metric,variable,value,unit}], data_quality{missing_values,validation_passed,warnings}, source_ids, limitations
- **Comparison**: comparison_id, experiment_ids, status (success|partial|not_comparable), compared_variables[{variable,unit,comparable,reason}], findings, warnings, source_ids
- **Insight**: insight_id, question, claim, supporting_evidence[{source_id,experiment_id,evidence_text,url}], fire_safety_relevance, limitations, confidence, evidence_status
- **CvResult**: cv_result_id, experiment_id, media_id, processing_status, detected, features{area_pixels,width_pixels,height_pixels,brightness_mean}, method, calibration_status, limitations, source_ids

## Open questions for the project lead / backend (not invented in the frontend)
1. **POST /analysis request body** is not documented. Frontend sends `{experiment_id, analysis_type: "statistical_summary"}`. Edit `AnalysisRequest` + `runAnalysis`.
2. **Response of /assistant/ask and /insights** is assumed to be the Insight schema (4.6).
3. **No endpoint returns Source objects.** Experiments carry only `source_ids`. In real-API mode the Data Quality page and Details show bare source_ids ("Source record not provided"). Suggest `GET /api/v1/sources` or embedding sources in the experiment response.
4. **Units of `conditions`** (temperature, pressure, flow_velocity) are not in the schema. Display uses K and atm (`CONDITION_UNITS` in `src/config/env.ts`). Please confirm or add unit fields.
5. **`timestamp` type** (ISO string vs numeric offset) is unspecified; charts accept both.
6. **Enums not defined** for Experiment.data_status, Measurement.measurement_status, AnalysisResult.status, Insight.confidence, CvResult statuses. Frontend renders unknown values humanized (e.g. `metadata_verified` → "Metadata verified"). Mock data uses `mock`, `illustrative`, and `failed`.
7. **List filtering**: "List and filter experiments" has no documented query parameters, so filtering is client-side.
8. **Request volume**: the app calls /measurements and /analysis once per experiment (4 at a time) after the list loads. For many experiments a batch/summary endpoint would be better.
9. Source `url` may be `null` for mock sources only; `Experiment.available_measurements` item type is assumed to be variable names (strings).
