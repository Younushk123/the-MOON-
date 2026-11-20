"""Application settings, read from environment variables (prefix ``MOON_``) or a .env file."""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SCHEMA_VERSION = "1.0"

DataMode = Literal["mock", "psi"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MOON_", env_file=".env", extra="ignore")

    app_name: str = "THE MOON API"
    # "mock" serves illustrative fixtures; "psi" loads local processed PSI-159 CSVs.
    data_mode: DataMode = "mock"
    # Frontend origins allowed by CORS. Set as JSON, e.g. MOON_CORS_ORIGINS='["http://localhost:5173"]'
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("data_mode", mode="before")
    @classmethod
    def normalize_data_mode(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


@lru_cache
def get_settings() -> Settings:
    return Settings()
