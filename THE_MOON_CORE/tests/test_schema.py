from app.schemas.experiment import Experiment


sample_experiment = {
    "experiment_id": "MOCK-EXP-001",
    "experiment_name": "Example Microgravity Combustion",

    "investigation": {
        "name": "Flame Behaviour Study",
        "objective": "Study flame behaviour in microgravity"
    },

    "combustion": {
        "fuel": "Methane",
        "sample_shape": "sphere",
        "sample_size": "10 mm",
        "oxygen_concentration": 21,
        "oxygen_unit": "%",
        "airflow_speed": 0,
        "airflow_unit": "m/s"
    },

    "environment": {
        "gravity_condition": "microgravity",
        "pressure": 101.3,
        "pressure_unit": "kPa",
        "temperature": 300,
        "temperature_unit": "K"
    },

    "measurements": {
        "burning_duration": 12.5,
        "flame_size": None,
        "flame_brightness": None,
        "flame_shape": "spherical"
    },

    "media": {
        "image": [],
        "video": []
    },

    "analysis": {
        "summary": None,
        "comparison": None,
        "insights": None
    },

    "source": {
        "title": "Example Source",
        "url": None,
        "source_type": "Mock"
    }
}


experiment = Experiment.model_validate(sample_experiment)

print("Schema validation successful!\n")

print(experiment.model_dump_json(indent=4))