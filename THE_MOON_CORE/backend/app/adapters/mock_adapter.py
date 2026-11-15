"""Serves illustrative records from mock_data/*.json. These are NOT NASA data.

On load, every record is validated against the canonical schema and the four files are
checked against each other, so broken mock data fails at startup rather than mid-demo.
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from app.config import DataMode
from app.models.experiment import Experiment, Measurement, Source
from app.models.media import Media

DEFAULT_MOCK_DIR = Path(__file__).parent / "mock_data"

M = TypeVar("M", bound=BaseModel)


class MockDataError(ValueError):
    """The mock data files are inconsistent."""


class MockDataRepository:
    data_mode: DataMode = "mock"

    def __init__(self, data_dir: Path = DEFAULT_MOCK_DIR) -> None:
        experiments = _load(data_dir / "experiments.json", Experiment)
        measurements = _load(data_dir / "measurements.json", Measurement)
        sources = _load(data_dir / "sources.json", Source)
        media = _load(data_dir / "media.json", Media)

        self._experiments = _index(experiments, "experiment_id", "experiments.json")
        self._sources = _index(sources, "source_id", "sources.json")
        measurements_by_id = _index(measurements, "measurement_id", "measurements.json")

        self._measurements: dict[str, list[Measurement]] = defaultdict(list)
        for m in measurements_by_id.values():
            self._measurements[m.experiment_id].append(m)

        self._media = _index(media, "media_id", "media.json")
        self._media_by_experiment: dict[str, list[Media]] = defaultdict(list)
        for item in self._media.values():
            self._media_by_experiment[item.experiment_id].append(item)

        _check_integrity(self._experiments, self._measurements, self._sources, self._media)

    def list_experiments(self) -> list[Experiment]:
        return list(self._experiments.values())

    def get_experiment(self, experiment_id: str) -> Experiment | None:
        return self._experiments.get(experiment_id)

    def list_measurements(self, experiment_id: str) -> list[Measurement]:
        return list(self._measurements.get(experiment_id, []))

    def get_source(self, source_id: str) -> Source | None:
        return self._sources.get(source_id)

    def list_media(self, experiment_id: str) -> list[Media]:
        return list(self._media_by_experiment.get(experiment_id, []))

    def get_media(self, media_id: str) -> Media | None:
        return self._media.get(media_id)


def _load(path: Path, model: type[M]) -> list[M]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [model.model_validate(item) for item in raw]


def _index(records: list[M], key: str, filename: str) -> dict[str, M]:
    """Index by ID, sorted by ID. Rejects duplicates."""
    ids = [getattr(r, key) for r in records]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise MockDataError(f"Duplicate {key} values in {filename}: {duplicates}")
    return {getattr(r, key): r for r in sorted(records, key=lambda r: getattr(r, key))}


def _check_integrity(
    experiments: dict[str, Experiment],
    measurements: dict[str, list[Measurement]],
    sources: dict[str, Source],
    media: dict[str, Media],
) -> None:
    problems: list[str] = []

    for exp in experiments.values():
        for sid in exp.source_ids:
            if sid not in sources:
                problems.append(f"{exp.experiment_id}: unknown source_id '{sid}'")
        measured = {m.variable for m in measurements.get(exp.experiment_id, [])}
        if measured != set(exp.available_measurements):
            problems.append(
                f"{exp.experiment_id}: available_measurements {sorted(exp.available_measurements)} "
                f"don't match measured variables {sorted(measured)}"
            )

    for exp_id, ms in measurements.items():
        for m in ms:
            if exp_id not in experiments:
                problems.append(f"{m.measurement_id}: unknown experiment_id '{exp_id}'")
            if m.source_id is not None and m.source_id not in sources:
                problems.append(f"{m.measurement_id}: unknown source_id '{m.source_id}'")

    for src in sources.values():
        if src.experiment_id is not None and src.experiment_id not in experiments:
            problems.append(f"{src.source_id}: unknown experiment_id '{src.experiment_id}'")

    for item in media.values():
        if item.experiment_id not in experiments:
            problems.append(f"{item.media_id}: unknown experiment_id '{item.experiment_id}'")
        if item.source_id is not None and item.source_id not in sources:
            problems.append(f"{item.media_id}: unknown source_id '{item.source_id}'")

    if problems:
        raise MockDataError("Mock data is inconsistent:\n  " + "\n  ".join(problems))
