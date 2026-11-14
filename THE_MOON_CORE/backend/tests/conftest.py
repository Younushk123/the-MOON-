import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

API = "/api/v1"


@pytest.fixture
def app():
    return create_app(Settings(data_mode="mock"))


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


def assert_ok(resp, status: int = 200) -> dict:
    """Assert a success envelope and return its data."""
    assert resp.status_code == status, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["error"] is None
    assert body["meta"] == {"schema_version": "1.0", "data_mode": "mock"}
    return body["data"]


def assert_error(resp, status: int, code: str) -> dict:
    """Assert an error envelope and return its error object."""
    assert resp.status_code == status, resp.text
    body = resp.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == code
    assert body["error"]["message"]
    assert body["meta"]["schema_version"] == "1.0"
    return body["error"]
