import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class ImageJobCreateDTO(BaseModel):
    script_package_id: uuid.UUID
    priority: Optional[int] = 0

class SceneAssetDTO(BaseModel):
    id: uuid.UUID
    image_package_id: uuid.UUID
    scene_number: int
    duration: float
    prompt: str
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    provider: str
    model: str
    model_version: Optional[str] = None
    prompt_version: Optional[str] = None
    aspect_ratio: str
    resolution: str
    style: Optional[str] = None
    camera_angle: Optional[str] = None
    character_reference: Optional[str] = None
    background: Optional[str] = None
    emotion: Optional[str] = None
    lighting: Optional[str] = None
    color_palette: Optional[list[str]] = None
    local_path: str
    storage_key: str
    public_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    preview_url: Optional[str] = None
    previous_scene_id: Optional[uuid.UUID] = None
    next_scene_id: Optional[uuid.UUID] = None
    transition_suggestion: Optional[str] = None
    generation_duration_sec: float
    quality_score: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ImageVersionDTO(BaseModel):
    id: uuid.UUID
    image_package_id: uuid.UUID
    version: int
    parent_version: Optional[int] = None
    lineage_action: str
    scene_number: Optional[int] = None
    assets_snapshot: list[dict[str, Any]]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ImagePackageDTO(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    script_package_id: uuid.UUID
    platform: str
    aspect_ratio: str
    resolution: str
    style_preset: str
    overall_theme: Optional[str] = None
    image_count: int
    generation_settings: Optional[dict[str, Any]] = None
    character_profile: Optional[Any] = None
    character_reference_images: Optional[list[str]] = None
    character_id: Optional[str] = None
    
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
    
    assets: Optional[list[SceneAssetDTO]] = None
    versions: Optional[list[ImageVersionDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class ImageJobResponseDTO(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[str] = None
    script_package_id: uuid.UUID
    provider: str
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
    
    packages: Optional[list[ImagePackageDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class ImageMetricsDTO(BaseModel):
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
