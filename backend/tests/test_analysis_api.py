"""POST /analysis and POST /comparison against the mock data."""

import pytest

from app.integrations.analysis import ILLUSTRATIVE_NOTE, INCOMPATIBLE_WARNING
from app.models.analysis import AnalysisResult, Comparison
from tests.conftest import API, assert_error, assert_ok


def _metrics(result: dict, variable: str) -> dict:
    return {r["metric"]: (r["value"], r["unit"]) for r in result["results"] if r["variable"] == variable}


# ---- analysis ----

def test_statistical_summary(client):
    data = assert_ok(client.post(f"{API}/analysis", json={"experiment_id": "MOCK-EXP-001"}))
    AnalysisResult.model_validate(data)
    assert data["analysis_id"].startswith("ANALYSIS-")
    assert data["status"] == "success"

    spread = _metrics(data, "flame_spread_rate")
    assert spread["count"] == (3, None)
    assert spread["mean"][0] == pytest.approx(1.0) and spread["mean"][1] == "mm/s"
    assert spread["min"] == (0.8, "mm/s") and spread["max"] == (1.2, "mm/s")

    temp = _metrics(data, "flame_temperature")
    assert temp["count"] == (2, None)  # the null value is excluded, not counted as zero
    assert temp["mean"] == (pytest.approx(1250.0), "K")

    assert data["data_quality"]["missing_values"] == 1
    assert data["data_quality"]["validation_passed"] is False
    assert data["source_ids"] == ["SRC-MOCK-001"]
    assert ILLUSTRATIVE_NOTE in data["limitations"]


def test_analysis_of_selected_variable(client):
    body = {"experiment_id": "MOCK-EXP-001", "variables": ["flame_spread_rate"]}
    data = assert_ok(client.post(f"{API}/analysis", json=body))
    assert {r["variable"] for r in data["results"]} == {"flame_spread_rate"}
    assert data["data_quality"] == {"missing_values": 0, "validation_passed": True, "warnings": []}


def test_analysis_with_unknown_variable_is_partial(client):
    body = {"experiment_id": "MOCK-EXP-001", "variables": ["flame_spread_rate", "soot_volume"]}
    data = assert_ok(client.post(f"{API}/analysis", json=body))
    assert data["status"] == "partial"
    assert any("soot_volume" in w for w in data["data_quality"]["warnings"])


def test_analysis_without_measurements_fails_gracefully(client):
    data = assert_ok(client.post(f"{API}/analysis", json={"experiment_id": "MOCK-EXP-003"}))
    assert data["status"] == "failed"
    assert data["results"] == []
    assert data["data_quality"]["warnings"]


def test_analysis_unknown_experiment(client):
    assert_error(client.post(f"{API}/analysis", json={"experiment_id": "NOPE"}), 404, "EXPERIMENT_NOT_FOUND")


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"experiment_id": ""},
        {"experiment_id": "MOCK-EXP-001", "analysis_type": "regression"},
        {"experiment_id": "MOCK-EXP-001", "variables": []},
        {"experiment_id": "MOCK-EXP-001", "variables": ["a", "a"]},
    ],
)
def test_invalid_analysis_requests(client, body):
    assert_error(client.post(f"{API}/analysis", json=body), 422, "VALIDATION_ERROR")


# ---- comparison ----

def test_comparison_flags_incompatible_units(client):
    body = {"experiment_ids": ["MOCK-EXP-001", "MOCK-EXP-002"]}
    data = assert_ok(client.post(f"{API}/comparison", json=body))
    Comparison.model_validate(data)
    assert data["comparison_id"].startswith("COMP-")
    assert data["status"] == "partial"

    by_var = {v["variable"]: v for v in data["compared_variables"]}
    assert by_var["flame_spread_rate"] == {
        "variable": "flame_spread_rate", "unit": "mm/s", "comparable": True, "reason": None
    }
    assert by_var["flame_temperature"]["comparable"] is False
    assert "Units differ" in by_var["flame_temperature"]["reason"]

    # Findings only for comparable variables
    assert {f["variable"] for f in data["findings"]} == {"flame_spread_rate", "oxygen_concentration"}
    spread = next(f for f in data["findings"] if f["variable"] == "flame_spread_rate")
    means = {v["experiment_id"]: v["mean"] for v in spread["values"]}
    assert means == {"MOCK-EXP-001": pytest.approx(1.0), "MOCK-EXP-002": pytest.approx(2.0)}

    assert data["warnings"][0] == INCOMPATIBLE_WARNING
    assert ILLUSTRATIVE_NOTE in data["warnings"]
    assert data["source_ids"] == ["SRC-MOCK-001", "SRC-MOCK-002"]


def test_comparison_of_compatible_variable_succeeds(client):
    body = {"experiment_ids": ["MOCK-EXP-001", "MOCK-EXP-002"], "variables": ["flame_spread_rate"]}
    data = assert_ok(client.post(f"{API}/comparison", json=body))
    assert data["status"] == "success"
    assert INCOMPATIBLE_WARNING not in data["warnings"]


def test_comparison_with_missing_data_is_not_comparable(client):
    body = {"experiment_ids": ["MOCK-EXP-001", "MOCK-EXP-003"]}
    data = assert_ok(client.post(f"{API}/comparison", json=body))
    assert data["status"] == "not_comparable"
    assert data["findings"] == []
    assert all(not v["comparable"] and "MOCK-EXP-003" in v["reason"] for v in data["compared_variables"])


def test_comparison_unknown_experiments_are_all_reported(client):
    body = {"experiment_ids": ["MOCK-EXP-001", "NOPE-1", "NOPE-2"]}
    error = assert_error(client.post(f"{API}/comparison", json=body), 404, "EXPERIMENT_NOT_FOUND")
    assert error["details"] == [{"experiment_id": "NOPE-1"}, {"experiment_id": "NOPE-2"}]


@pytest.mark.parametrize(
    "body",
    [
        {"experiment_ids": ["MOCK-EXP-001"]},
        {"experiment_ids": ["MOCK-EXP-001", "MOCK-EXP-001"]},
        {"experiment_ids": [f"E{i}" for i in range(11)]},
        {"experiment_ids": ["MOCK-EXP-001", "MOCK-EXP-002"], "variables": []},
    ],
)
def test_invalid_comparison_requests(client, body):
    assert_error(client.post(f"{API}/comparison", json=body), 422, "VALIDATION_ERROR")
