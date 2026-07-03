from datetime import datetime

from pydantic import BaseModel, Field


class JobCreateRequest(BaseModel):
    bbox: list[int] = Field(
        description="Bounding box of the plate region as [x, y, width, height] in pixels.",
        examples=[[120, 340, 80, 80]],
    )
    mass_kg: float | None = Field(
        default=None,
        description="Total mass on the barbell in kilograms. Required for force and power calculations.",
        examples=[100.0],
    )


class JobResponse(BaseModel):
    id: str = Field(
        description="Unique job identifier.",
        examples=["3f1a2b4c-5d6e-7f8a-9b0c-1d2e3f4a5b6c"],
    )
    status: str = Field(
        description="Current status of the job: pending, processing, completed, or failed.",
        examples=["pending"],
    )
    created_at: datetime = Field(
        description="Timestamp when the job was created.",
        examples=["2026-06-28T00:00:00Z"],
    )


class JobResultResponse(BaseModel):
    id: str = Field(
        description="Unique job identifier.",
        examples=["3f1a2b4c-5d6e-7f8a-9b0c-1d2e3f4a5b6c"],
    )
    status: str = Field(
        description="Current status of the job.",
        examples=["completed"],
    )
    video_url: str | None = Field(
        default=None,
        description="URL to download the annotated output video.",
        examples=["/api/v1/jobs/3f1a2b4c-5d6e-7f8a-9b0c-1d2e3f4a5b6c/video"],
    )
    centroids_url: str | None = Field(
        default=None,
        description="URL to download the centroid CSV file.",
        examples=["/api/v1/jobs/3f1a2b4c-5d6e-7f8a-9b0c-1d2e3f4a5b6c/centroids"],
    )
    error_message: str | None = Field(
        default=None,
        description="Error detail if the job failed.",
        examples=[None],
    )
