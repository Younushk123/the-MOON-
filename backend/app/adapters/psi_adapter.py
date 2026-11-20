
"""Repository adapter for NASA PSI-159 processed combustion datasets."""

import csv
import math
import re
from pathlib import Path

from app.config import DataMode
from app.models.experiment import Experiment, Measurement, MeasurementConditions, Source


# THE_MOON_CORE/data-anlysis/data/processed/
PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = PROJECT_ROOT / "data_analysis" / "data" / "processed"


DATASETS = {
    "normal": {
        "experiment_id": "PSI159-CFIG-NORMAL",
        "source_id": "PSI159-NORMAL-CSV",
        "name": "PSI-159 Normal Flame Experiments",
        "filename": "normal_analysis.csv",
        "description": (
            "Processed normal-flame observations from NASA's PSI-159 "
            "Cool Flames Investigation with Gases (CFI-G)."
        ),
        "fields": {
            "approx p (bar)": ("pressure", "bar"),
            "Xf": ("fuel_fraction", None),
            "mHC (mg/s)": ("hydrocarbon_mass_flow", "mg/s"),
            "Tad (K)": ("adiabatic_flame_temperature", "K"),
            "Zst": ("stoichiometric_mixture_fraction", None),
            "burn time (sec)": ("burn_time", "sec"),
            "Peak burner T (C )": ("peak_burner_temperature", "C"),
            "XO2 before test": ("oxygen_fraction_before", None),
            "XO2 after test": ("oxygen_fraction_after", None),
        },
    },
    "inverse": {
        "experiment_id": "PSI159-CFIG-INVERSE",
        "source_id": "PSI159-INVERSE-CSV",
        "name": "PSI-159 Inverse Flame Experiments",
        "filename": "inverse_analysis.csv",
        "description": (
            "Processed inverse-flame observations from NASA's PSI-159 "
            "Cool Flames Investigation with Gases (CFI-G)."
        ),
        "fields": {
            "approx p (bar)": ("pressure", "bar"),
            "Xf before test": ("fuel_fraction_before", None),
            "Xf after test": ("fuel_fraction_after", None),
            "XO2": ("oxygen_fraction", None),
            "HC burnrate (mg/s)": ("hydrocarbon_burn_rate", "mg/s"),
            "O2 flow rate (mg/s)": ("oxygen_flow_rate", "mg/s"),
            "Tad (K)": ("adiabatic_flame_temperature", "K"),
            "Zst": ("stoichiometric_mixture_fraction", None),
            "burn time (sec)": ("burn_time", "sec"),
            "Peak burner Temp (C)": ("peak_burner_temperature", "C"),
            "Peak burner temp (K)": ("peak_burner_temperature", "K"),
        },
    },
}


def _normalize_header(value: str | None) -> str:
    return (value or "").strip().lower()


def _parse_number(value: str | None) -> float | None:
    if value is None:
        return None

    value = value.strip()
    if not value or value.lower() in {"nan", "none", "null", "-"}:
        return None

    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except ValueError:
        return None


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


class PSIDataRepository:
    """Loads processed PSI-159 CSV files into the application's schemas."""

    data_mode: DataMode = "psi"

    def __init__(self):
        self._experiments: dict[str, Experiment] = {}
        self._measurements: dict[str, list[Measurement]] = {}
        self._sources: dict[str, Source] = {}

        for dataset_name, config in DATASETS.items():
            self._load_dataset(dataset_name, config)

    def _load_dataset(self, dataset_name: str, config: dict) -> None:
        csv_path = PROCESSED_DIR / config["filename"]

        if not csv_path.exists():
            raise FileNotFoundError(
                f"PSI-159 dataset not found: {csv_path}"
            )

        source_id = config["source_id"]
        experiment_id = config["experiment_id"]
        measurements: list[Measurement] = []
        available_variables: set[str] = set()

        with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            for row_number, raw_row in enumerate(reader, start=1):
                # Normalize column names to avoid whitespace/case issues.
                row = {
                    _normalize_header(key): value
                    for key, value in raw_row.items()
                    if key is not None
                }

                fuel = row.get("fuel", "").strip() or None
                pressure = _parse_number(row.get("approx p (bar)"))

                if dataset_name == "normal":
                    temperature = _parse_number(row.get("peak burner t (c )"))
                else:
                    temperature = _parse_number(
                        row.get("peak burner temp (c)")
                    )

                conditions = MeasurementConditions(
                    fuel=fuel,
                    pressure=pressure,
                    temperature=temperature,
                )

                for column, (variable, unit) in config["fields"].items():
                    value = _parse_number(row.get(_normalize_header(column)))

                    if value is None:
                        continue

                    measurement_id = (
                        f"PSI159-{dataset_name[0].upper()}-"
                        f"{row_number:05d}-{_slug(variable)}"
                    )

                    # Preserve categorical observations as notes.
                    categorical_notes = []
                    for field in (
                        "hot ignition",
                        "tfp",
                        "self-ext or flow term",
                        "self -ext or flow term",
                        "comments",
                        "color",
                    ):
                        field_value = row.get(field)
                        if field_value and field_value.strip().lower() not in {
                            "nan", "-", "none"
                        }:
                            categorical_notes.append(
                                f"{field}: {field_value.strip()}"
                            )

                    measurements.append(
                        Measurement(
                            measurement_id=measurement_id,
                            experiment_id=experiment_id,
                            variable=variable,
                            value=value,
                            unit=unit,
                            conditions=conditions,
                            source_id=source_id,
                            measurement_status="unverified",
                            notes=categorical_notes,
                        )
                    )
                    available_variables.add(variable)

        self._experiments[experiment_id] = Experiment(
            experiment_id=experiment_id,
            name=config["name"],
            investigation="Cool Flames Investigation with Gases (CFI-G)",
            program="Advanced Combustion via Microgravity Experiments (ACME)",
            description=config["description"],
            platform="International Space Station (ISS)",
            source_ids=[source_id],
            data_status="unverified",
            available_measurements=sorted(available_variables),
            limitations=[
                "Imported from locally processed PSI-159 CSV data.",
                "Dataset values have not been independently re-verified by this adapter.",
                "ISS microgravity observations are not direct Moon or Mars simulations.",
                "Categorical outcomes are preserved in measurement notes.",
            ],
        )

        self._measurements[experiment_id] = measurements

        self._sources[source_id] = Source(
            source_id=source_id,
            title=f"NASA PSI-159 {dataset_name.title()} Flame Dataset",
            publisher="NASA",
            source_type="dataset",
            experiment_id=experiment_id,
            access_status="unknown",
            verification_status="unverified",
            ingestion_status="ingested",
        )

    def list_experiments(self) -> list[Experiment]:
        return list(self._experiments.values())

    def get_experiment(self, experiment_id: str) -> Experiment | None:
        return self._experiments.get(experiment_id)

    def list_measurements(self, experiment_id: str) -> list[Measurement]:
        return self._measurements.get(experiment_id, [])

    def get_source(self, source_id: str) -> Source | None:
        return self._sources.get(source_id)
