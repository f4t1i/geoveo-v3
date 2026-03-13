from typing import Any, Literal
from pydantic import BaseModel, Field

class RoutePoint(BaseModel):
    lat: float
    lng: float
    heading_deg: float = 0

class GeoVeoJob(BaseModel):
    prompt: str
    location: str
    mode: Literal["drive", "walk", "bike"] = "drive"
    sampling_meters: int = Field(default=15, ge=1, le=200)
    imagery_source: Literal["mapillary", "streetview", "stub"] = "stub"
    video_backend: Literal["cogvideox", "animatediff", "veo", "stub"] = "stub"

class PlannedJob(BaseModel):
    route_id: str
    route: list[RoutePoint]
    keyframe_paths: list[str]
    conditioning_bundle_path: str

class RunResult(BaseModel):
    job_id: str
    status: Literal["done", "failed"]
    output_video: str
    metadata: dict[str, Any] = Field(default_factory=dict)
