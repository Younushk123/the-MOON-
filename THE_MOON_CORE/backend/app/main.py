"""FastAPI app factory. Run with:  uvicorn app.main:app --reload  (from backend/)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters import build_repository
from app.adapters.base import DataRepository
from app.api.v1 import router as v1_router
from app.config import SCHEMA_VERSION, Settings, get_settings
from app.errors import register_exception_handlers
from app.integrations import Integrations, build_integrations


def create_app(
    settings: Settings | None = None,
    repository: DataRepository | None = None,
    integrations: Integrations | None = None,
) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "Backend for THE MOON (NASA Space Apps: Flame in Free Fall). "
            f"Canonical data schema v{SCHEMA_VERSION}. "
            "Check `meta.data_mode`: `mock` records are illustrative, not NASA data."
        ),
    )
    app.state.settings = settings
    app.state.repository = repository or build_repository(settings)
    app.state.integrations = integrations or build_integrations(settings)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(v1_router)
    return app


app = create_app()
