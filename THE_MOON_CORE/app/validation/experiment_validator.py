
from app.schemas.experiment import Experiment


def validate_experiment(experiment: Experiment):

    errors = []
    warnings = []

    # Check experiment identity
    if not experiment.experiment_id.strip():
        errors.append("Experiment ID is missing.")

    if not experiment.experiment_name.strip():
        errors.append("Experiment name is missing.")

    # Check combustion conditions
    combustion = experiment.combustion

    if combustion.oxygen_concentration is not None:
        if not 0 <= combustion.oxygen_concentration <= 100:
            errors.append("Oxygen concentration must be between 0 and 100.")

    if combustion.oxygen_concentration is not None and not combustion.oxygen_unit:
        errors.append("Oxygen unit is missing.")

    if combustion.airflow_speed is not None:
        if combustion.airflow_speed < 0:
            errors.append("Airflow speed cannot be negative.")

    # Check environment
    environment = experiment.environment

    if environment.pressure is not None and environment.pressure <= 0:
        errors.append("Pressure must be greater than zero.")

    if environment.temperature is not None and environment.temperature <= 0:
        errors.append("Temperature must be greater than zero.")

    # Check measurements
    measurements = experiment.measurements

    numeric_measurements = {
        "Burning duration": measurements.burning_duration,
        "Flame size": measurements.flame_size,
        "Flame brightness": measurements.flame_brightness
    }

    for name, value in numeric_measurements.items():

        if value is not None and value < 0:
            errors.append(f"{name} cannot be negative.")

        if value is None:
            warnings.append(f"{name} is unavailable.")

    # Final status
    if errors:
        status = "invalid"
    elif warnings:
        status = "incomplete"
    else:
        status = "valid"

    return {
        "experiment_id": experiment.experiment_id,
        "status": status,
        "errors": errors,
        "warnings": warnings
    }
