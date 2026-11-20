
from app.adapters.base import DataRepository
from app.config import Settings


def build_repository(settings: Settings) -> DataRepository:
    """Build the repository according to the configured data mode."""

    if settings.data_mode == "mock":
        from app.adapters.mock_adapter import MockDataRepository
        return MockDataRepository()

    if settings.data_mode == "psi":
        from app.adapters.psi_adapter import PSIDataRepository
        return PSIDataRepository()

    raise ValueError(f"Unknown data mode: {settings.data_mode}")
