# Testing Report

Run module tests before submitting changes.

```powershell
cd backend
python -m pytest -q
python -m app.schema_export

cd ../research_rag
python -m pytest -q

cd ..
python -m unittest discover -s computer_vision/tests -v

cd frontend
npm run build
```

The schema exporter should not leave stale or unexpected schema files. UI analysis limits, RAG abstention,
and no-fabrication behavior are security and scientific-integrity requirements.
