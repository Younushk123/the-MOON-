"""GET /health, /experiments, /experiments/{id}, /experiments/{id}/measurements."""

import pytest

from app.models.experiment import Experiment, Measurement
from tests.conftest import API, assert_error, assert_ok

URL = f"{API}/experiments"
ALL_IDS = ["MOCK-EXP-001", "MOCK-EXP-002", "MOCK-EXP-003"]


def test_health(client):
    assert assert_ok(client.get(f"{API}/health")) == {"status": "ok"}


def test_all_required_endpoints_are_documented(client):
    paths = client.get("/openapi.json").json()["paths"]
    required = {
        ("get", "/api/v1/health"),
        ("get", "/api/v1/experiments"),
        ("get", "/api/v1/experiments/{experiment_id}"),
        ("get", "/api/v1/experiments/{experiment_id}/measurements"),
        ("post", "/api/v1/analysis"),
        ("post", "/api/v1/comparison"),
        ("post", "/api/v1/insights"),
        ("post", "/api/v1/assistant/ask"),
        ("post", "/api/v1/vision/analyze"),
    }
    documented = {(method, path) for path, ops in paths.items() for method in ops}
    assert required <= documented


# ---- list ----

def test_list_shape(client):
    data = assert_ok(client.get(URL))
    assert set(data) == {"items", "count", "page", "page_size"}
    assert (data["count"], data["page"], data["page_size"]) == (3, 1, 20)
    assert [i["experiment_id"] for i in data["items"]] == ALL_IDS
    for item in data["items"]:
        Experiment.model_validate(item)


def test_mock_experiments_are_labelled_illustrative(client):
    for item in assert_ok(client.get(URL))["items"]:
        assert item["experiment_id"].startswith("MOCK-")
        assert item["data_status"] == "illustrative"
        assert "not nasa data" in item["description"].lower()


def test_pagination(client):
    data = assert_ok(client.get(URL, params={"page": 2, "page_size": 2}))
    assert data["count"] == 3
    assert [i["experiment_id"] for i in data["items"]] == ["MOCK-EXP-003"]


def test_page_past_the_end_is_empty(client):
    data = assert_ok(client.get(URL, params={"page": 99}))
    assert data["items"] == [] and data["count"] == 3


@pytest.mark.parametrize(
    "params, expected",
    [
        ({"q": "droplet"}, ["MOCK-EXP-003"]),
        ({"q": "FLAME SPREAD"}, ["MOCK-EXP-001", "MOCK-EXP-002"]),
        ({"q": "mock-exp-002"}, ["MOCK-EXP-002"]),
        ({"platform": "international space station"}, ["MOCK-EXP-001"]),
        ({"platform": "Drop tower"}, ["MOCK-EXP-003"]),
        ({"platform": "Moon"}, []),
        ({"data_status": "illustrative"}, ALL_IDS),
        ({"data_status": "content_verified"}, []),
        ({"q": "flame", "platform": "ground laboratory"}, ["MOCK-EXP-002"]),
    ],
)
def test_filters(client, params, expected):
    data = assert_ok(client.get(URL, params=params))
    assert [i["experiment_id"] for i in data["items"]] == expected
    assert data["count"] == len(expected)


@pytest.mark.parametrize(
    "params",
    [{"page": 0}, {"page": "abc"}, {"page_size": 0}, {"page_size": 101}, {"data_status": "made_up"}, {"q": "x" * 201}],
)
def test_invalid_list_params(client, params):
    assert_error(client.get(URL, params=params), 422, "VALIDATION_ERROR")


# ---- detail ----

def test_get_experiment(client):
    data = assert_ok(client.get(f"{URL}/MOCK-EXP-001"))
    assert data["experiment_id"] == "MOCK-EXP-001"
    assert data["last_updated"] == "2026-11-14"
    Experiment.model_validate(data)


def test_unknown_experiment(client):
    error = assert_error(client.get(f"{URL}/NOPE-999"), 404, "EXPERIMENT_NOT_FOUND")
    assert "NOPE-999" in error["message"]


def test_overlong_experiment_id(client):
    assert_error(client.get(f"{URL}/{'X' * 65}"), 422, "VALIDATION_ERROR")


# ---- measurements ----

def test_measurements(client):
    data = assert_ok(client.get(f"{URL}/MOCK-EXP-001/measurements"))
    assert data["count"] == 7
    for item in data["items"]:
        Measurement.model_validate(item)
        assert item["experiment_id"] == "MOCK-EXP-001"
        assert item["measurement_status"] == "illustrative"


def test_measurements_filter_by_variable_keeps_nulls(client):
    data = assert_ok(client.get(f"{URL}/MOCK-EXP-001/measurements", params={"variable": "flame_temperature"}))
    assert [i["value"] for i in data["items"]] == [1200.0, None, 1300.0]


def test_measurements_pagination(client):
    data = assert_ok(client.get(f"{URL}/MOCK-EXP-001/measurements", params={"page": 2, "page_size": 5}))
    assert data["count"] == 7
    assert [i["measurement_id"] for i in data["items"]] == ["MEAS-MOCK-006", "MEAS-MOCK-007"]


def test_experiment_without_measurements_returns_empty_list(client):
    data = assert_ok(client.get(f"{URL}/MOCK-EXP-003/measurements"))
    assert data["items"] == [] and data["count"] == 0


def test_measurements_for_unknown_experiment(client):
    assert_error(client.get(f"{URL}/NOPE/measurements"), 404, "EXPERIMENT_NOT_FOUND")


@pytest.mark.parametrize("params", [{"page_size": 501}, {"page": 0}, {"variable": "v" * 101}])
def test_invalid_measurement_params(client, params):
    assert_error(client.get(f"{URL}/MOCK-EXP-001/measurements", params=params), 422, "VALIDATION_ERROR")
