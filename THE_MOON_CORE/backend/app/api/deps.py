"""Service providers for routes. Override with app.dependency_overrides in tests if needed."""

from typing import Annotated

from fastapi import Depends, Request

from app.services.experiment_service import ExperimentService
from app.services.module_services import AnalysisService, InsightService, VisionService


def get_experiment_service(request: Request) -> ExperimentService:
    return ExperimentService(request.app.state.repository)


Experiments = Annotated[ExperimentService, Depends(get_experiment_service)]


def get_analysis_service(request: Request, experiments: Experiments) -> AnalysisService:
    return AnalysisService(experiments, request.app.state.integrations.analysis)


def get_insight_service(request: Request, experiments: Experiments) -> InsightService:
    integrations = request.app.state.integrations
    return InsightService(experiments, integrations.insights, integrations.assistant)


def get_vision_service(request: Request, experiments: Experiments) -> VisionService:
    return VisionService(experiments, request.app.state.integrations.vision)
