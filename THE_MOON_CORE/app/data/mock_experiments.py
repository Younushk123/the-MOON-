
from app.schemas.experiment import Experiment


def load_mock_experiments():

    mock_data = [

        {
            "experiment_id": "MOCK-EXP-001",
            "experiment_name": "Methane Combustion - Microgravity",

            "investigation": {
                "name": "Microgravity Flame Study",
                "objective": "Observe flame behaviour under microgravity"
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
                "flame_size": 8.2,
                "flame_brightness": 75.0,
                "flame_shape": "spherical"
            },

            "source": {
                "title": "Synthetic Test Record 001",
                "url": None,
                "source_type": "Mock"
            }
        },

        {
            "experiment_id": "MOCK-EXP-002",
            "experiment_name": "Methane Combustion - Normal Gravity",

            "investigation": {
                "name": "Normal Gravity Flame Study",
                "objective": "Observe flame behaviour under normal gravity"
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
                "gravity_condition": "normal_gravity",
                "pressure": 101.3,
                "pressure_unit": "kPa",
                "temperature": 300,
                "temperature_unit": "K"
            },

            "measurements": {
                "burning_duration": 9.0,
                "flame_size": 11.5,
                "flame_brightness": 82.0,
                "flame_shape": "elongated"
            },

            "source": {
                "title": "Synthetic Test Record 002",
                "url": None,
                "source_type": "Mock"
            }
        },

        {
            "experiment_id": "MOCK-EXP-003",
            "experiment_name": "Methane Combustion - Reduced Oxygen",

            "investigation": {
                "name": "Oxygen Concentration Study",
                "objective": "Test combustion under reduced oxygen concentration"
            },

            "combustion": {
                "fuel": "Methane",
                "sample_shape": "sphere",
                "sample_size": "10 mm",
                "oxygen_concentration": 18,
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
                "burning_duration": 7.5,
                "flame_size": 6.0,
                "flame_brightness": 60.0,
                "flame_shape": "spherical"
            },

            "source": {
                "title": "Synthetic Test Record 003",
                "url": None,
                "source_type": "Mock"
            }
        }
    ]

    return [
        Experiment.model_validate(record)
        for record in mock_data
    ]

