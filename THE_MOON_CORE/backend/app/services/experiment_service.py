"""Experiment exploration: search, filter, paginate, look up."""

from typing import TypeVar

from app.adapters.base import DataRepository
from app.config import DataMode
from app.errors import ExperimentNotFoundError
from app.models.envelope import Page
from app.models.experiment import Experiment, ExperimentDataStatus, Measurement

T = TypeVar("T")


class ExperimentService:
    def __init__(self, repository: DataRepository) -> None:
        self.repository = repository

    @property
    def data_mode(self) -> DataMode:
        return self.repository.data_mode

    def list_experiments(
        self,
        q: str | None = None,
        platform: str | None = None,
        data_status: ExperimentDataStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Page[Experiment]:
        records = self.repository.list_experiments()
        if q:
            needle = q.strip().lower()
            records = [r for r in records if needle in _search_text(r)]
        if platform:
            wanted = platform.strip().lower()
            records = [r for r in records if r.platform is not None and r.platform.lower() == wanted]
        if data_status is not None:
            records = [r for r in records if r.data_status == data_status]
        return _paginate(records, page, page_size)

    def get_experiment(self, experiment_id: str) -> Experiment:
        record = self.repository.get_experiment(experiment_id)
        if record is None:
            raise ExperimentNotFoundError(experiment_id)
        return record

    def get_experiments(self, experiment_ids: list[str]) -> list[Experiment]:
        """Look up several experiments, reporting every missing ID at once."""
        found = {i: self.repository.get_experiment(i) for i in experiment_ids}
        missing = [i for i, exp in found.items() if exp is None]
        if missing:
            raise ExperimentNotFoundError(missing)
        return [found[i] for i in experiment_ids]

    def all_measurements(self, experiment_id: str) -> list[Measurement]:
        return self.repository.list_measurements(experiment_id)

    def list_measurements(
        self, experiment_id: str, variable: str | None = None, page: int = 1, page_size: int = 100
    ) -> Page[Measurement]:
        self.get_experiment(experiment_id)  # 404 if unknown
        records = self.repository.list_measurements(experiment_id)
        if variable:
            records = [m for m in records if m.variable == variable.strip()]
        return _paginate(records, page, page_size)


def _search_text(record: Experiment) -> str:
    fields = [record.experiment_id, record.name, record.investigation, record.program, record.description]
    return " ".join(f for f in fields if f).lower()


def _paginate(records: list[T], page: int, page_size: int) -> Page[T]:
    start = (page - 1) * page_size
    return Page(items=records[start : start + page_size], count=len(records), page=page, page_size=page_size)
