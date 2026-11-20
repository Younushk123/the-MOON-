# THE MOON

THE MOON is a NASA Space Apps 2026 research platform for exploring microgravity combustion data,
evidence-linked research answers, and FLEX flame-media analysis.

## Repository structure

```text
the-moon/
├── README.md
├── PROJECT_CONTRACT.md
├── CONTRIBUTING.md
├── .env.example
├── docs/
├── frontend/
├── backend/
├── data_analysis/
├── research_rag/
├── computer_vision/
├── shared/
│   ├── schemas/
│   └── sample_data/
└── .github/workflows/tests.yml
```

## Modules

- `frontend/`: React, TypeScript, Vite dashboard.
- `backend/`: FastAPI REST API and canonical Pydantic schemas.
- `data_analysis/`: PSI-159 raw and processed combustion datasets and notebooks.
- `research_rag/`: evidence retrieval, source register, generation, and evaluation.
- `computer_vision/`: PSI-69 FLEX image/video processing and reference outputs.
- `shared/`: generated JSON Schemas and illustrative mock fixtures.

## Quick start

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Set `MOON_DATA_MODE=mock` or `MOON_DATA_MODE=psi`.

### Frontend

```powershell
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

The default frontend URL is `http://127.0.0.1:5173`.

### RAG

```powershell
cd research_rag
python rag_pipeline.py ask "Why is combustion different in microgravity?"
```

Set `GROQ_API_KEY` only if using Groq generation. Otherwise extraction-only mode is used.

### Computer Vision

```powershell
python -m unittest discover -s computer_vision/tests -v
python -m computer_vision --image /path/to/still.jpg --output computer_vision/outputs/generated
```

Source FLEX MP4/JPG media are intentionally not redistributed. The backend supports uploads and
temporary processing; supported source profiles are documented in `computer_vision/README.md`.

## Validation

```powershell
cd backend
python -m pytest -q

cd ../research_rag
python -m pytest -q

cd ..
python -m unittest discover -s computer_vision/tests -v

cd frontend
npm run build
```

## Scientific limitations

- PSI-159 data status is unverified unless independently validated.
- PSI-69 FLEX measurements are pixel-based and not calibrated physical dimensions.
- RAG answers abstain or remain evidence-linked when source support is insufficient.
- ISS microgravity observations are not direct Moon or Mars surface simulations.
