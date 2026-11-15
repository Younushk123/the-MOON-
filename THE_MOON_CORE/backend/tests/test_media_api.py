"""GET /experiments/{id}/media and GET /media/{media_id} (issue #4)."""

import pytest

from app.models.media import Media
from tests.conftest import API, assert_error, assert_ok


def test_list_media_for_experiment(client):
    data = assert_ok(client.get(f"{API}/experiments/MOCK-EXP-001/media"))
    assert data["count"] == 2
    assert (data["page"], data["page_size"]) == (1, 20)
    assert [m["media_id"] for m in data["items"]] == ["MOCK-MEDIA-001", "MOCK-MEDIA-002"]
    for item in data["items"]:
        Media.model_validate(item)
        assert item["experiment_id"] == "MOCK-EXP-001"


def test_list_media_empty(client):
    data = assert_ok(client.get(f"{API}/experiments/MOCK-EXP-003/media"))
    assert data == {"items": [], "count": 0, "page": 1, "page_size": 20}


@pytest.mark.parametrize("media_type, expected", [("video", ["MOCK-MEDIA-001"]), ("image", ["MOCK-MEDIA-002"])])
def test_list_media_filter_by_type(client, media_type, expected):
    data = assert_ok(client.get(f"{API}/experiments/MOCK-EXP-001/media", params={"media_type": media_type}))
    assert [m["media_id"] for m in data["items"]] == expected
    assert data["count"] == 1


def test_list_media_pagination(client):
    data = assert_ok(client.get(f"{API}/experiments/MOCK-EXP-001/media", params={"page": 2, "page_size": 1}))
    assert [m["media_id"] for m in data["items"]] == ["MOCK-MEDIA-002"]
    assert data["count"] == 2


def test_list_media_unknown_experiment(client):
    assert_error(client.get(f"{API}/experiments/NOPE/media"), 404, "EXPERIMENT_NOT_FOUND")


@pytest.mark.parametrize(
    "params", [{"media_type": "audio"}, {"page": 0}, {"page_size": 0}, {"page_size": 101}]
)
def test_list_media_invalid_params(client, params):
    assert_error(client.get(f"{API}/experiments/MOCK-EXP-001/media", params=params), 422, "VALIDATION_ERROR")


def test_get_media(client):
    data = assert_ok(client.get(f"{API}/media/MOCK-MEDIA-003"))
    media = Media.model_validate(data)
    assert media.experiment_id == "MOCK-EXP-002"
    assert media.media_type == "image" and media.format == "jpeg"
    assert media.availability_status == "unavailable"


def test_get_media_unknown(client):
    error = assert_error(client.get(f"{API}/media/NOPE"), 404, "MEDIA_NOT_FOUND")
    assert error["details"] == [{"media_id": "NOPE"}]


def test_get_media_id_too_long(client):
    assert_error(client.get(f"{API}/media/{'X' * 65}"), 422, "VALIDATION_ERROR")
