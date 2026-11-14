from fastapi import APIRouter

from app.api.v1 import analysis, experiments, health, insights, vision

router = APIRouter(prefix="/api/v1")
for module in (health, experiments, analysis, insights, vision):
    router.include_router(module.router)
