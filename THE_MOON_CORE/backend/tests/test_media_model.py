"""Validation rules of the Media model (issue #4)."""

import pytest
from pydantic import ValidationError

from app.models.media import Media

BASE = {
    "media_id": "MEDIA-001",
    "experiment_id": "EXP-001",
    "media_type": "video",
    "format": "mp4",
    "file_name": "flame_001.mp4",
}


def _media(**changes) -> Media:
    return Media.model_validate({**BASE, **changes})


def test_minimal_media_defaults():
    m = _media()
    assert m.availability_status == "unknown"
    assert m.file_url is None and m.storage_path is None
    assert m.metadata.model_dump() == {
        "width_pixels": None,
        "height_pixels": None,
        "duration_seconds": None,
        "frame_rate_fps": None,
    }


def test_full_video_record():
    m = _media(
        file_url="https://example.org/flame_001.mp4",
        storage_path="media/EXP-001/flame_001.mp4",
        description="Side view",
        source_id="SRC-001",
        metadata={"width_pixels": 1920, "height_pixels": 1080, "duration_seconds": 12.5, "frame_rate_fps": 30},
        availability_status="available",
    )
    assert m.metadata.frame_rate_fps == 30


def test_format_is_normalised():
    assert _media(format=" MP4 ").format == "mp4"


@pytest.mark.parametrize("location", [{"file_url": "https://example.org/a.png"}, {"storage_path": "media/a.png"}])
def test_available_media_with_a_location(location):
    m = _media(media_type="image", format="png", file_name="a.png", availability_status="available", **location)
    assert m.availability_status == "available"


def test_available_media_needs_a_location():
    with pytest.raises(ValidationError, match="file_url or a storage_path"):
        _media(availability_status="available")


@pytest.mark.parametrize("field", ["duration_seconds", "frame_rate_fps"])
def test_image_rejects_video_metadata(field):
    with pytest.raises(ValidationError, match="video only"):
        _media(media_type="image", format="png", metadata={field: 1.0})


@pytest.mark.parametrize(
    "change",
    [
        {"media_type": "audio"},
        {"availability_status": "lost"},
        {"format": ".mp4"},
        {"format": "toolongformat"},
        {"file_name": "dir/flame.mp4"},
        {"file_name": "dir\\flame.mp4"},
        {"file_name": "  "},
        {"file_url": "ftp://example.org/a.mp4"},
        {"storage_path": ""},
        {"media_id": ""},
        {"metadata": {"width_pixels": 0}},
        {"metadata": {"frame_rate_fps": -1}},
        {"metadata": {"bitrate": 1}},
        {"unexpected": 1},
    ],
)
def test_invalid_values_rejected(change):
    with pytest.raises(ValidationError):
        _media(**change)


@pytest.mark.parametrize("field", ["media_id", "experiment_id", "media_type", "format", "file_name"])
def test_required_fields(field):
    data = dict(BASE)
    del data[field]
    with pytest.raises(ValidationError):
        Media.model_validate(data)
