from fastapi import APIRouter

from app.api.v1 import analysis, experiments, health, insights, media, vision

router = APIRouter(prefix="/api/v1")
for module in (health, experiments, media, analysis, insights, vision):
    router.include_router(module.router)
