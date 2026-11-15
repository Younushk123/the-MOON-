from app.adapters.base import DataRepository
from app.config import Settings


def build_repository(settings: Settings) -> DataRepository:
    """Pick the data adapter for the configured data mode."""
    if settings.data_mode == "mock":
        from app.adapters.mock_adapter import MockDataRepository

        return MockDataRepository()
    if settings.data_mode == "psi":
        raise NotImplementedError(
            "The PSI adapter isn't implemented yet. Run with MOON_DATA_MODE=mock until the field mapping is agreed."
        )
    raise ValueError(f"Unknown data mode: {settings.data_mode}")
