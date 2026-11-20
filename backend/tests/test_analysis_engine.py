"""Unit tests for comparability rules that the mock data doesn't cover."""

from app.integrations.analysis import ReferenceAnalysisEngine
from app.models.experiment import Experiment, Measurement

engine = ReferenceAnalysisEngine()


def _exp(eid: str, variables: list[str], platform: str = "Lab") -> Experiment:
    return Experiment(experiment_id=eid, name=eid, platform=platform, available_measurements=variables)


def _m(mid: str, eid: str, value: float | None, unit: str = "K", **conditions) -> Measurement:
    return Measurement(
        measurement_id=mid, experiment_id=eid, variable="flame_temperature", value=value, unit=unit,
        conditions=conditions,
    )


def test_conflicting_conditions_block_comparison():
    exps = [_exp("A", ["flame_temperature"]), _exp("B", ["flame_temperature"])]
    ms = {
        "A": [_m("1", "A", 1000, fuel="PMMA", pressure=101.3)],
        "B": [_m("2", "B", 1100, fuel="PMMA", pressure=50.0)],
    }
    result = engine.compare(exps, ms, None)
    assert result.status == "not_comparable"
    assert "pressure" in result.compared_variables[0].reason
    assert result.findings == []


def test_unrecorded_conditions_allow_comparison_with_warning():
    exps = [_exp("A", ["flame_temperature"]), _exp("B", ["flame_temperature"])]
    ms = {
        "A": [_m("1", "A", 1000, fuel="PMMA")],
        "B": [_m("2", "B", 1100, fuel="PMMA")],
    }
    result = engine.compare(exps, ms, None)
    assert result.status == "success"
    assert any("not recorded" in w and "pressure" in w for w in result.warnings)


def test_same_platform_has_no_platform_warning():
    exps = [_exp("A", ["flame_temperature"]), _exp("B", ["flame_temperature"])]
    ms = {"A": [_m("1", "A", 1000)], "B": [_m("2", "B", 1100)]}
    result = engine.compare(exps, ms, None)
    assert not any("platforms" in w for w in result.warnings)


def test_mixed_units_within_one_experiment_are_not_summarised():
    exp = _exp("A", ["flame_temperature"])
    ms = [_m("1", "A", 1000, unit="K"), _m("2", "A", 700, unit="degC")]
    result = engine.analyze(exp, ms, "statistical_summary", None)
    assert result.status == "failed"
    assert result.results == []
    assert result.data_quality.validation_passed is False
    assert any("mixed units" in w for w in result.data_quality.warnings)


def test_all_null_values_produce_no_statistics():
    exp = _exp("A", ["flame_temperature"])
    result = engine.analyze(exp, [_m("1", "A", None), _m("2", "A", None)], "statistical_summary", None)
    assert result.status == "failed"
    assert result.data_quality.missing_values == 2


def test_real_data_gets_no_illustrative_label():
    exp = _exp("A", ["flame_temperature"])
    result = engine.analyze(exp, [_m("1", "A", 1000)], "statistical_summary", None)
    assert not any("illustrative" in lim.lower() for lim in result.limitations)
