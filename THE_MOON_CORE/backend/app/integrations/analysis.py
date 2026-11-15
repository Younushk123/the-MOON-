"""Data Analysis integration point.

`AnalysisEngine` is the interface the backend calls. `ReferenceAnalysisEngine` is a built-in
implementation so the endpoints work end to end now. The Data Analysis module should replace
or wrap it, keeping the same inputs and outputs.

Rules applied (PROJECT_CONTRACT section 4):
- Null values are excluded and counted, never treated as zero.
- Values in different units are never combined, because no documented conversion exists.
- Variables are compared only when every experiment has values, the units match, and
  recorded measurement conditions don't conflict.
"""

from collections.abc import Iterable
from statistics import fmean
from typing import Protocol

from app.ids import new_id
from app.models.analysis import (
    AnalysisResult,
    AnalysisResultItem,
    AnalysisType,
    ComparedVariable,
    Comparison,
    ComparisonFinding,
    DataQuality,
    ExperimentValueSummary,
)
from app.models.experiment import Experiment, Measurement, MeasurementConditions

CONDITION_FIELDS = tuple(MeasurementConditions.model_fields)
ILLUSTRATIVE_NOTE = "Computed from illustrative mock measurements. Not a scientific result."
INCOMPATIBLE_WARNING = "Do not interpret incompatible measurements as a direct comparison."


class AnalysisEngine(Protocol):
    def analyze(
        self,
        experiment: Experiment,
        measurements: list[Measurement],
        analysis_type: AnalysisType,
        variables: list[str] | None,
    ) -> AnalysisResult: ...

    def compare(
        self,
        experiments: list[Experiment],
        measurements: dict[str, list[Measurement]],
        variables: list[str] | None,
    ) -> Comparison: ...


class ReferenceAnalysisEngine:
    def analyze(
        self,
        experiment: Experiment,
        measurements: list[Measurement],
        analysis_type: AnalysisType,
        variables: list[str] | None,
    ) -> AnalysisResult:
        variables = variables or list(experiment.available_measurements)
        results: list[AnalysisResultItem] = []
        warnings: list[str] = []
        used: list[Measurement] = []
        missing = 0
        mixed_units = False
        summarised = 0

        if not variables:
            warnings.append("This experiment has no measurements to analyse.")

        for var in variables:
            records = [m for m in measurements if m.variable == var]
            if not records:
                warnings.append(f"No '{var}' measurements for this experiment.")
                continue

            with_values = [m for m in records if m.value is not None]
            n_missing = len(records) - len(with_values)
            if n_missing:
                missing += n_missing
                warnings.append(f"{n_missing} '{var}' measurement(s) have no value and were excluded.")
            if not with_values:
                continue

            units = {m.unit for m in with_values}
            if len(units) > 1:
                mixed_units = True
                warnings.append(
                    f"'{var}' is recorded in mixed units ({_fmt_units(units)}). "
                    "It was not summarised because no documented conversion exists."
                )
                continue

            unit = units.pop()
            stats = _stats(with_values)
            results += [
                AnalysisResultItem(metric="count", variable=var, value=stats["n"], unit=None),
                AnalysisResultItem(metric="mean", variable=var, value=stats["mean"], unit=unit),
                AnalysisResultItem(metric="min", variable=var, value=stats["min"], unit=unit),
                AnalysisResultItem(metric="max", variable=var, value=stats["max"], unit=unit),
            ]
            used += with_values
            summarised += 1

        if variables and summarised == len(variables):
            status = "success"
        elif summarised:
            status = "partial"
        else:
            status = "failed"

        return AnalysisResult(
            analysis_id=new_id("ANALYSIS"),
            experiment_id=experiment.experiment_id,
            analysis_type=analysis_type,
            status=status,
            results=results,
            data_quality=DataQuality(
                missing_values=missing,
                validation_passed=missing == 0 and not mixed_units,
                warnings=warnings,
            ),
            source_ids=_source_ids([experiment], used),
            limitations=_limitations([experiment], used),
        )

    def compare(
        self,
        experiments: list[Experiment],
        measurements: dict[str, list[Measurement]],
        variables: list[str] | None,
    ) -> Comparison:
        variables = variables or _dedupe(v for e in experiments for v in e.available_measurements)
        compared: list[ComparedVariable] = []
        findings: list[ComparisonFinding] = []
        warnings: list[str] = []
        used: list[Measurement] = []

        for var in variables:
            per_exp = {
                e.experiment_id: [
                    m for m in measurements.get(e.experiment_id, []) if m.variable == var and m.value is not None
                ]
                for e in experiments
            }

            lacking = [eid for eid, ms in per_exp.items() if not ms]
            if lacking:
                compared.append(_not_comparable(var, None, f"No usable values for {', '.join(lacking)}."))
                continue

            all_ms = [m for ms in per_exp.values() for m in ms]
            units = {m.unit for m in all_ms}
            if len(units) > 1:
                compared.append(
                    _not_comparable(var, None, f"Units differ ({_fmt_units(units)}) and no documented conversion exists.")
                )
                continue
            unit = units.pop()

            conflicting, unrecorded = _check_conditions(all_ms)
            if conflicting:
                compared.append(_not_comparable(var, unit, f"Measurement conditions differ: {', '.join(conflicting)}."))
                continue

            compared.append(ComparedVariable(variable=var, unit=unit, comparable=True, reason=None))
            findings.append(
                ComparisonFinding(
                    variable=var,
                    unit=unit,
                    values=[ExperimentValueSummary(experiment_id=eid, **_stats(ms)) for eid, ms in per_exp.items()],
                )
            )
            used += all_ms
            if unrecorded:
                warnings.append(
                    f"'{var}': {', '.join(unrecorded)} not recorded for every measurement, "
                    "so matching conditions could not be fully confirmed."
                )

        n_comparable = sum(c.comparable for c in compared)
        if compared and n_comparable == len(compared):
            status = "success"
        elif n_comparable:
            status = "partial"
        else:
            status = "not_comparable"

        if not compared:
            warnings.append("None of the selected experiments have measured variables to compare.")
        if n_comparable < len(compared):
            warnings.insert(0, INCOMPATIBLE_WARNING)

        platforms = {e.platform for e in experiments}
        if len(platforms) > 1 and n_comparable:
            warnings.append(
                f"Experiments ran on different platforms ({_fmt_units(platforms)}). Differences may reflect "
                "gravity level and other platform-specific factors, not a single cause."
            )
        if any(e.data_status == "illustrative" for e in experiments):
            warnings.append(ILLUSTRATIVE_NOTE)

        return Comparison(
            comparison_id=new_id("COMP"),
            experiment_ids=[e.experiment_id for e in experiments],
            status=status,
            compared_variables=compared,
            findings=findings,
            warnings=warnings,
            source_ids=_source_ids(experiments, used),
        )


def _stats(ms: list[Measurement]) -> dict:
    xs = [m.value for m in ms]
    return {"n": len(xs), "mean": fmean(xs), "min": min(xs), "max": max(xs)}


def _check_conditions(ms: list[Measurement]) -> tuple[list[str], list[str]]:
    """Return (fields with conflicting recorded values, fields missing on some measurements)."""
    conflicting, unrecorded = [], []
    for field in CONDITION_FIELDS:
        values = {getattr(m.conditions, field) for m in ms}
        if len(values - {None}) > 1:
            conflicting.append(field)
        elif None in values:
            unrecorded.append(field)
    return conflicting, unrecorded


def _not_comparable(variable: str, unit: str | None, reason: str) -> ComparedVariable:
    return ComparedVariable(variable=variable, unit=unit, comparable=False, reason=reason)


def _source_ids(experiments: list[Experiment], used: list[Measurement]) -> list[str]:
    ids = {sid for e in experiments for sid in e.source_ids} | {m.source_id for m in used if m.source_id}
    return sorted(ids)


def _limitations(experiments: list[Experiment], used: list[Measurement]) -> list[str]:
    limitations = _dedupe(lim for e in experiments for lim in e.limitations)
    if any(m.measurement_status == "illustrative" for m in used) or any(
        e.data_status == "illustrative" for e in experiments
    ):
        limitations.append(ILLUSTRATIVE_NOTE)
    limitations.append("Descriptive statistics only. Measurement uncertainty is not accounted for.")
    return limitations


def _fmt_units(units: Iterable[str | None]) -> str:
    return ", ".join(sorted(u if u else "none" for u in units))


def _dedupe(items: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(items))
