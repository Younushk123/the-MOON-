# THE MOON — Frontend

React + Vite + TypeScript-friendly frontend for **THE MOON – Flame in Freefall** (NASA Space Apps Challenge 2026).
Implements the canonical schemas (Section 4) and API contract (Section 5) of the integration document, v1.0.

## Requirements
- Node.js 20.19+ or 22.12+
- npm

## Install and run
```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # production build in dist/
```

## Mock data now, real API later
- Default is **mock mode** (`VITE_USE_MOCK_DATA=true`): an in-browser mock backend answers every endpoint with the standard envelope.
- Mock records are fictional (`MOCK-*` ids, `data_status: "mock"`, `measurement_status: "illustrative"`) and are labelled in the UI. They are **not NASA findings**.
- To use the backend, copy `.env.example` to `.env.local`, set `VITE_USE_MOCK_DATA=false` and `VITE_API_BASE_URL=http://localhost:8000`, restart Vite.
- Full endpoint/field list and open questions: [`docs/API_INTEGRATION.md`](docs/API_INTEGRATION.md).

## Structure
```
src/
  types/schemas.ts      TypeScript mirror of Section 4 schemas + envelope + requests
  types/view.ts         ExperimentView used by the existing pages
  config/env.ts         mock/real switch, base URL, units for conditions
  services/apiClient.ts transport + envelope validation (mock or fetch)
  services/api.ts       one function per endpoint (only module pages use for data)
  services/adapters.ts  schema -> ExperimentView
  data/mock/            mock backend + mock Experiment/Measurement/Source records
  hooks/                useDashboardData (app-level), useAsyncData (generic)
  components/ui/        StatusBadge, StateNotice, Tag, MockNotice, CvResultCard
  pages/                Overview, Explorer, Details, Comparison, AIInsights, DataQuality, Settings
```

## Page ⇄ schema mapping
| Page | Schemas / endpoints |
|---|---|
| Overview | Experiment, AnalysisResult |
| Experiment Explorer | Experiment (+ Measurement.conditions for filters) |
| Experiment Details | Experiment, Measurement, Source |
| Comparison | Comparison (POST /comparison), Measurement |
| AI Insights | Insight (POST /assistant/ask) |
| Data Quality | AnalysisResult.data_quality, Source |
