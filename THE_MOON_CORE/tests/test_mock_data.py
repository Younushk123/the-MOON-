
from app.data.mock_experiments import load_mock_experiments


experiments = load_mock_experiments()

print("Total experiments:", len(experiments))

for experiment in experiments:
    print("\n-------------------------")
    print("ID:", experiment.experiment_id)
    print("Name:", experiment.experiment_name)
    print("Fuel:", experiment.combustion.fuel)
    print("Gravity:", experiment.environment.gravity_condition)
    print("Burning Duration:", experiment.measurements.burning_duration)
