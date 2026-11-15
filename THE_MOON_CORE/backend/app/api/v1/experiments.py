from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.api.deps import Experiments
from app.api.v1.responses import INVALID, NOT_FOUND
from app.models.envelope import Envelope, Page, ok
from app.models.experiment import Experiment, ExperimentDataStatus, Measurement

router = APIRouter(prefix="/experiments", tags=["experiments"])

ExperimentId = Annotated[str, Path(min_length=1, max_length=64)]
PageNumber = Annotated[int, Query(ge=1, description="1-based page number.")]


@router.get(
    "",
    response_model=Envelope[Page[Experiment]],
    summary="List and filter experiments",
    description="`count` is the total number of matches across all pages.",
    responses=INVALID,
)
def list_experiments(
    service: Experiments,
    q: Annotated[
        str | None, Query(max_length=200, description="Free-text search over ID, name, investigation, program and description.")
    ] = None,
    platform: Annotated[str | None, Query(max_length=100, description="Exact platform name (case-insensitive).")] = None,
    data_status: Annotated[ExperimentDataStatus | None, Query()] = None,
    page: PageNumber = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Records per page (max 100).")] = 20,
) -> Envelope[Page[Experiment]]:
    result = service.list_experiments(q=q, platform=platform, data_status=data_status, page=page, page_size=page_size)
    return ok(result, data_mode=service.data_mode)


@router.get(
    "/{experiment_id}",
    response_model=Envelope[Experiment],
    summary="Experiment details",
    responses={**NOT_FOUND, **INVALID},
)
def get_experiment(service: Experiments, experiment_id: ExperimentId) -> Envelope[Experiment]:
    return ok(service.get_experiment(experiment_id), data_mode=service.data_mode)


@router.get(
    "/{experiment_id}/measurements",
    response_model=Envelope[Page[Measurement]],
    summary="Measurements for an experiment",
    description="`count` is the total number of matches across all pages.",
    responses={**NOT_FOUND, **INVALID},
)
def list_measurements(
    service: Experiments,
    experiment_id: ExperimentId,
    variable: Annotated[str | None, Query(max_length=100, description="Only this variable, e.g. flame_temperature.")] = None,
    page: PageNumber = 1,
    page_size: Annotated[int, Query(ge=1, le=500, description="Records per page (max 500).")] = 100,
) -> Envelope[Page[Measurement]]:
    result = service.list_measurements(experiment_id, variable=variable, page=page, page_size=page_size)
    return ok(result, data_mode=service.data_mode)
