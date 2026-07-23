import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class VideoJobCreateDTO(BaseModel):
    script_package_id: uuid.UUID
    image_package_id: uuid.UUID
    voice_package_id: uuid.UUID
    renderer: Optional[str] = "ffmpeg"
    priority: Optional[int] = 0

class RenderProfileDTO(BaseModel):
    id: uuid.UUID
    name: str
    platform: str
    resolution: str
    aspect_ratio: str
    fps: int
    codec: str
    bitrate: int
    container: str
    audio_codec: str
    audio_sample_rate: int
    audio_bitrate: int
    color_space: Optional[str] = None
    hardware_acceleration: bool
    preset: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SceneVideoDTO(BaseModel):
    id: uuid.UUID
    video_package_id: uuid.UUID
    scene_number: int
    timeline_start_ms: int
    timeline_end_ms: int
    duration_ms: int
    image_asset_id: Optional[uuid.UUID] = None
    voice_asset_id: Optional[uuid.UUID] = None
    motion_preset: Optional[str] = None
    transition_preset: Optional[str] = None
    rendered_clip: Optional[str] = None
    storage_key: str
    preview_url: Optional[str] = None
    render_metadata: Optional[dict[str, Any]] = None
    quality_score: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TimelineEventDTO(BaseModel):
    id: uuid.UUID
    video_package_id: uuid.UUID
    scene_number: int
    start_time_ms: int
    end_time_ms: int
    voice_offset_ms: int
    transition_start_ms: int
    transition_end_ms: int
    motion_start_ms: int
    motion_end_ms: int
    caption_region: Optional[str] = None
    audio_fade_in_ms: int
    audio_fade_out_ms: int
    video_fade_in_ms: int
    video_fade_out_ms: int
    model_config = ConfigDict(from_attributes=True)

class VideoVersionDTO(BaseModel):
    id: uuid.UUID
    video_package_id: uuid.UUID
    version: int
    parent_version: Optional[int] = None
    lineage_action: str
    assets_snapshot: list[dict[str, Any]]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class VideoPackageDTO(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    script_package_id: uuid.UUID
    image_package_id: uuid.UUID
    voice_package_id: uuid.UUID
    platform: str
    resolution: str
    aspect_ratio: str
    fps: int
    codec: str
    bitrate: int
    container: str
    duration_ms: int
    storage_key: str
    preview_video: Optional[str] = None
    thumbnail_frame: Optional[str] = None
    scene_count: int
    timeline_version: int
    metadata_artifacts: Optional[dict[str, Any]] = None
    
    # Mixin fields
    version: int
    parent_package_id: Optional[uuid.UUID] = None
    source_agent: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    prompt_version: Optional[str] = None
    quality_score: float
    telemetry_metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    
    assets: Optional[list[SceneVideoDTO]] = None
    events: Optional[list[TimelineEventDTO]] = None
    versions: Optional[list[VideoVersionDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class VideoJobResponseDTO(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[str] = None
    script_package_id: uuid.UUID
    image_package_id: uuid.UUID
    voice_package_id: uuid.UUID
    render_profile_id: Optional[uuid.UUID] = None
    renderer: str
    status: str
    stage: str
    progress: float
    attempts: int
    max_attempts: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    duration_sec: float
    worker_id: Optional[str] = None
    priority: int
    scheduled_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    profile: Optional[RenderProfileDTO] = None
    packages: Optional[list[VideoPackageDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class VideoMetricsDTO(BaseModel):
    jobs_queued: int
    jobs_processing: int
    jobs_succeeded: int
    jobs_failed: int
    jobs_retrying: int
    jobs_cancelled: int
    average_duration_sec: float
    current_worker_count: int
    worker_uptime: str
    worker_is_running: bool
    worker_heartbeats: list[dict[str, Any]]
