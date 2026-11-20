# Vercel Deployment

The repository is prepared for a separate Vercel Python backend deployment from the repository root.

## Backend

Deploy the repository root with `api/index.py` as the Python entry point. The FastAPI application is exposed
under `/api/*`, including `/api/v1/health`.

Required production environment variables:

- `MOON_DATA_MODE=psi`
- `MOON_RAG_MODE=extractive`
- `MOON_CORS_ORIGINS` containing the deployed frontend origin
- `GROQ_API_KEY` only if Groq generation is explicitly enabled

Example CORS value:

```text
["https://your-project.vercel.app"]
```

## Frontend

Deploy `frontend/` as a separate Vercel project. Set `VITE_USE_MOCK_DATA=false`. Set
`VITE_API_BASE_URL` to the deployed backend origin, or leave it empty for same-origin `/api/*` routing.

## Serverless limitations

- PSI-159 and mock data can run in serverless functions.
- RAG runs in extractive, no-semantic mode to avoid downloading large embedding models.
- Still-image Computer Vision runs in the serverless function.
- Background video polling, subprocess workers, and in-memory job state are not durable in serverless.
  Video analysis returns a clear unavailable response until deployed behind a persistent worker service.
