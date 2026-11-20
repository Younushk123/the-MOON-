"""Every failure must come back in the error envelope."""

from fastapi.testclient import TestClient

from app.config import Settings
from tests.conftest import API, assert_error


def test_settings_trim_trailing_environment_whitespace():
    assert Settings(data_mode="mock\r\n").data_mode == "mock"


def test_unknown_route(client):
    assert_error(client.get(f"{API}/does-not-exist"), 404, "NOT_FOUND")


def test_wrong_method(client):
    assert_error(client.delete(f"{API}/experiments"), 405, "METHOD_NOT_ALLOWED")


def test_invalid_query_param_lists_location(client):
    error = assert_error(client.get(f"{API}/experiments", params={"page": 0}), 422, "VALIDATION_ERROR")
    assert any(d["location"] == ["query", "page"] for d in error["details"])


def test_malformed_json_body(client):
    resp = client.post(f"{API}/analysis", content=b"{not json", headers={"content-type": "application/json"})
    assert_error(resp, 422, "VALIDATION_ERROR")


def test_unknown_body_field_is_rejected(client):
    resp = client.post(f"{API}/analysis", json={"experiment_id": "MOCK-EXP-001", "typo_field": 1})
    error = assert_error(resp, 422, "VALIDATION_ERROR")
    assert any(d["location"] == ["body", "typo_field"] for d in error["details"])


def test_unexpected_exception_does_not_leak(app):
    @app.get(f"{API}/_boom")
    def boom():
        raise RuntimeError("secret internal detail")

    with TestClient(app, raise_server_exceptions=False) as c:
        resp = c.get(f"{API}/_boom")
    assert_error(resp, 500, "INTERNAL_ERROR")
    assert "secret" not in resp.text
