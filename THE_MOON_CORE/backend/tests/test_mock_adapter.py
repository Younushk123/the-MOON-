import json
import shutil

import pytest
from pydantic import ValidationError

from app.adapters.mock_adapter import DEFAULT_MOCK_DIR, MockDataError, MockDataRepository


@pytest.fixture
def data_dir(tmp_path):
    """A writable copy of the real mock data."""
    for name in ("experiments.json", "measurements.json", "sources.json", "media.json"):
        shutil.copy(DEFAULT_MOCK_DIR / name, tmp_path / name)
    return tmp_path


def _edit(path, fn):
    records = json.loads(path.read_text(encoding="utf-8"))
    fn(records)
    path.write_text(json.dumps(records), encoding="utf-8")


def test_default_mock_data_loads():
    repo = MockDataRepository()
    assert repo.data_mode == "mock"
    assert [e.experiment_id for e in repo.list_experiments()] == ["MOCK-EXP-001", "MOCK-EXP-002", "MOCK-EXP-003"]
    assert len(repo.list_measurements("MOCK-EXP-002")) == 6
    assert repo.list_measurements("MOCK-EXP-003") == []
    assert repo.get_source("SRC-MOCK-001").verification_status == "unverified"
    assert repo.get_experiment("missing") is None
    assert [m.media_id for m in repo.list_media("MOCK-EXP-001")] == ["MOCK-MEDIA-001", "MOCK-MEDIA-002"]
    assert repo.list_media("MOCK-EXP-003") == []
    assert repo.get_media("MOCK-MEDIA-003").experiment_id == "MOCK-EXP-002"
    assert repo.get_media("missing") is None


def test_every_mock_record_is_illustrative():
    repo = MockDataRepository()
    for exp in repo.list_experiments():
        assert exp.data_status == "illustrative"
        for m in repo.list_measurements(exp.experiment_id):
            assert m.measurement_status == "illustrative"
        for sid in exp.source_ids:
            src = repo.get_source(sid)
            assert src.verification_status == "unverified" and src.url is None
        for media in repo.list_media(exp.experiment_id):
            assert media.media_id.startswith("MOCK-")
            assert media.availability_status == "unavailable"
            assert media.file_url is None and media.storage_path is None


def test_duplicate_ids_rejected(data_dir):
    _edit(data_dir / "experiments.json", lambda r: r.append(dict(r[0])))
    with pytest.raises(MockDataError, match="Duplicate experiment_id"):
        MockDataRepository(data_dir)


def test_duplicate_media_ids_rejected(data_dir):
    _edit(data_dir / "media.json", lambda r: r.append(dict(r[0])))
    with pytest.raises(MockDataError, match="Duplicate media_id"):
        MockDataRepository(data_dir)


def test_media_for_unknown_experiment_rejected(data_dir):
    _edit(data_dir / "media.json", lambda r: r[0].update(experiment_id="GHOST"))
    with pytest.raises(MockDataError, match="MOCK-MEDIA-001: unknown experiment_id 'GHOST'"):
        MockDataRepository(data_dir)


def test_media_with_unknown_source_rejected(data_dir):
    _edit(data_dir / "media.json", lambda r: r[0].update(source_id="SRC-GHOST"))
    with pytest.raises(MockDataError, match="MOCK-MEDIA-001: unknown source_id 'SRC-GHOST'"):
        MockDataRepository(data_dir)


def test_measurement_for_unknown_experiment_rejected(data_dir):
    _edit(data_dir / "measurements.json", lambda r: r[0].update(experiment_id="GHOST"))
    with pytest.raises(MockDataError, match="unknown experiment_id 'GHOST'"):
        MockDataRepository(data_dir)


def test_unknown_source_reference_rejected(data_dir):
    _edit(data_dir / "measurements.json", lambda r: r[0].update(source_id="SRC-GHOST"))
    with pytest.raises(MockDataError, match="unknown source_id 'SRC-GHOST'"):
        MockDataRepository(data_dir)


def test_available_measurements_must_match_data(data_dir):
    _edit(data_dir / "experiments.json", lambda r: r[0]["available_measurements"].append("soot_volume"))
    with pytest.raises(MockDataError, match="available_measurements"):
        MockDataRepository(data_dir)


@pytest.mark.parametrize(
    "filename, change",
    [
        ("experiments.json", {"unexpected_field": 1}),
        ("experiments.json", {"data_status": "made_up"}),
        ("sources.json", {"source_type": "blog"}),
        ("sources.json", {"url": "not a url"}),
        ("measurements.json", {"measurement_status": "guessed"}),
        ("media.json", {"media_type": "audio"}),
        ("media.json", {"availability_status": "available"}),
    ],
)
def test_schema_violations_rejected(data_dir, filename, change):
    _edit(data_dir / filename, lambda r: r[0].update(change))
    with pytest.raises(ValidationError):
        MockDataRepository(data_dir)
