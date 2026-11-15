"""Application settings, read from environment variables (prefix ``MOON_``) or a .env file."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

SCHEMA_VERSION = "1.0"

DataMode = Literal["mock", "psi"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MOON_", env_file=".env", extra="ignore")

    app_name: str = "THE MOON API"
    # Which data adapter backs the API. Also reported as meta.data_mode in every response.
    data_mode: DataMode = "mock"
    # Frontend origins allowed by CORS. Set as JSON, e.g. MOON_CORS_ORIGINS='["http://localhost:5173"]'
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
