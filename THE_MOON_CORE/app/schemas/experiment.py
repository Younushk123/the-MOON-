from typing import Optional, Any

from pydantic import BaseModel, ConfigDict, Field


class FlexibleModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class Investigation(FlexibleModel):
    name: Optional[str] = None
    objective: Optional[str] = None


class Combustion(FlexibleModel):
    fuel: Optional[str] = None
    sample_shape: Optional[str] = None
    sample_size: Optional[str] = None

    oxygen_concentration: Optional[float] = None
    oxygen_unit: Optional[str] = "%"

    airflow_speed: Optional[float] = None
    airflow_unit: Optional[str] = "m/s"


class Environment(FlexibleModel):
    gravity_condition: Optional[str] = None

    pressure: Optional[float] = None
    pressure_unit: Optional[str] = "kPa"

    temperature: Optional[float] = None
    temperature_unit: Optional[str] = "K"


class Measurements(FlexibleModel):
    burning_duration: Optional[float] = None
    flame_size: Optional[float] = None
    flame_brightness: Optional[float] = None
    flame_shape: Optional[str] = None


class Media(FlexibleModel):
    image: list[str] = Field(default_factory=list)
    video: list[str] = Field(default_factory=list)


class Analysis(FlexibleModel):
    summary: Optional[str] = None
    comparison: Optional[Any] = None
    insights: Optional[Any] = None


class Source(FlexibleModel):
    title: Optional[str] = None
    url: Optional[str] = None
    source_type: Optional[str] = None


class Experiment(FlexibleModel):
    schema_version: str = "0.1"
    data_status: str = "mock"

    experiment_id: str
    experiment_name: str

    investigation: Investigation = Field(default_factory=Investigation)
    combustion: Combustion = Field(default_factory=Combustion)
    environment: Environment = Field(default_factory=Environment)
    measurements: Measurements = Field(default_factory=Measurements)
    media: Media = Field(default_factory=Media)
    analysis: Analysis = Field(default_factory=Analysis)
    source: Source = Field(default_factory=Source)

    uncertainty: Optional[Any] = None
    notes: list[str] = Field(default_factory=list)