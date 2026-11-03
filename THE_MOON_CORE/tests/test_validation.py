
from app.data.mock_experiments import load_mock_experiments
from app.validation.experiment_validator import validate_experiment


experiments = load_mock_experiments()

for experiment in experiments:

    result = validate_experiment(experiment)

    print("\n-------------------------")
    print("Experiment:", result["experiment_id"])
    print("Status:", result["status"])

    print("Errors:", result["errors"])
    print("Warnings:", result["warnings"])
