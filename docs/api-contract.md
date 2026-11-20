# API Contract

All versioned endpoints use the FastAPI `/api/v1` namespace and a success/error envelope.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Backend status |
| GET | `/experiments` | Experiment list |
| GET | `/experiments/{experiment_id}` | Experiment details |
| GET | `/experiments/{experiment_id}/measurements` | Measurements |
| POST | `/analysis` | Statistical analysis |
| POST | `/comparison` | Experiment comparison |
| POST | `/insights` | Evidence-aware insight request |
| POST | `/assistant/ask` | RAG question |
| POST | `/vision/analyze-image` | PSI-69 still-image analysis |
| POST | `/vision/analyze-video` | Queue PSI-69 FLEX video analysis |
| GET | `/vision/jobs/{job_id}` | Poll video job status |

Run the interactive contract at `http://127.0.0.1:8000/docs`.
