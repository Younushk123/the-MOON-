"""Media records: images and videos of an experiment, analysed by the CV module (issue #4).

Relationship: Experiment --(experiment_id)--> Media --(media_id)--> CVResult.
"""

from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from app.models.base import Identifier, StrictModel, Url

MediaType = Literal["image", "video"]
# PROVISIONAL: issue #4 names the field but not its values. These mirror Source.access_status.
AvailabilityStatus = Literal["available", "restricted", "unavailable", "unknown"]

MediaFormat = Annotated[
    str, StringConstraints(strip_whitespace=True, to_lower=True, pattern=r"^[A-Za-z0-9]{1,10}$")
]
FileName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255, pattern=r"^[^/\\]+$")]
StoragePath = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1024)]


class MediaMetadata(StrictModel):
    """Technical properties of the file. Unknown values are null. Duration and frame rate apply to video only."""

    width_pixels: int | None = Field(default=None, gt=0)
    height_pixels: int | None = Field(default=None, gt=0)
    duration_seconds: float | None = Field(default=None, gt=0)
    frame_rate_fps: float | None = Field(default=None, gt=0)


class Media(StrictModel):
    media_id: Identifier
    experiment_id: Identifier
    media_type: MediaType
    format: MediaFormat = Field(description="File extension in lowercase, without the dot, e.g. png, jpeg, mp4.")
    file_name: FileName = Field(description="File name only, without directories.")
    file_url: Url | None = None
    storage_path: StoragePath | None = Field(default=None, description="Location in the project's own storage.")
    description: str | None = None
    source_id: Identifier | None = None
    metadata: MediaMetadata = Field(default_factory=MediaMetadata)
    availability_status: AvailabilityStatus = "unknown"

    @model_validator(mode="after")
    def _check_consistency(self) -> "Media":
        if self.media_type == "image" and (
            self.metadata.duration_seconds is not None or self.metadata.frame_rate_fps is not None
        ):
            raise ValueError("duration_seconds and frame_rate_fps apply to video only")
        if self.availability_status == "available" and self.file_url is None and self.storage_path is None:
            raise ValueError("available media needs a file_url or a storage_path")
        return self
