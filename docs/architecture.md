# Architecture

THE MOON is a monorepo containing an interactive frontend, FastAPI backend, scientific data analysis,
RAG research module, and FLEX computer-vision module.

```text
Frontend (React + TypeScript)
        |
        | REST /api/v1
        v
FastAPI backend
        |
        +--> PSI-159 data adapters
        +--> Statistical analysis module
        +--> RAG research assistant
        +--> Computer-vision integration
```

- `frontend/` provides the dashboard and uploads.
- `backend/` validates requests and owns canonical Pydantic response models.
- `data_analysis/` processes and stores PSI-159 combustion records.
- `research_rag/` retrieves evidence and generates abstaining, evidence-linked responses.
- `computer_vision/` runs the PSI-69 FLEX image and video pipelines.
- `shared/` contains canonical JSON Schemas and illustrative sample data.
