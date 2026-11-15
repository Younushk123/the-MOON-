"""Interface every data source (mock, PSI, ...) implements.

Adapters only load records and map them to the canonical schema. Filtering, pagination,
analysis and business rules belong in the service layer.
"""

from typing import Protocol

from app.config import DataMode
from app.models.experiment import Experiment, Measurement, Source
from app.models.media import Media


class DataRepository(Protocol):
    data_mode: DataMode

    def list_experiments(self) -> list[Experiment]:
        """All experiments, sorted by experiment_id."""
        ...

    def get_experiment(self, experiment_id: str) -> Experiment | None: ...

    def list_measurements(self, experiment_id: str) -> list[Measurement]:
        """All measurements for one experiment, sorted by measurement_id. Empty if none."""
        ...

    def get_source(self, source_id: str) -> Source | None: ...

    def list_media(self, experiment_id: str) -> list[Media]:
        """All media for one experiment, sorted by media_id. Empty if none."""
        ...

    def get_media(self, media_id: str) -> Media | None: ...
