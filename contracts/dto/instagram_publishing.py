import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class InstagramPublishJobCreateDTO(BaseModel):
    quality_package_id: uuid.UUID
    platform_media_type: Optional[str] = "Reels"  # Reels, Feed
    provider: Optional[str] = "instagram_provider"
    priority: Optional[int] = 0

class PublishingAttemptDTO(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    attempt_number: int
    api_endpoint: str
    http_status_code: int
    latency_ms: int
    api_response: Optional[dict[str, Any]] = None
    failure_reason: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class InstagramMediaAssetDTO(BaseModel):
    id: uuid.UUID
    publication_id: uuid.UUID
    video_asset_key: str
    cover_image_key: Optional[str] = None
    aspect_ratio: str
    resolution: str
    duration_ms: int
    codec: str
    bitrate: int
    thumbnail_url: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class InstagramInsightSnapshotDTO(BaseModel):
    id: uuid.UUID
    publication_id: uuid.UUID
    captured_at: datetime
    views: int
    reach: int
    impressions: int
    likes: int
    comments: int
    shares: int
    saves: int
    profile_visits: int
    follows_attributed: int
    watch_time_ms: int
    engagement_rate: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class InstagramPublicationDTO(BaseModel):
    id: uuid.UUID
    publication_package_id: uuid.UUID
    instagram_media_id: str
    container_id: Optional[str] = None
    permalink: str
    caption: str
    hashtags: Optional[list[str]] = None
    alt_text: Optional[str] = None
    published_at: datetime
    visibility: str
    publishing_result: Optional[dict[str, Any]] = None
    created_at: datetime
    media_assets: Optional[list[InstagramMediaAssetDTO]] = None
    insights: Optional[list[InstagramInsightSnapshotDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class InstagramVersionDTO(BaseModel):
    id: uuid.UUID
    publication_package_id: uuid.UUID
    version: int
    parent_version: Optional[int] = None
    lineage_action: str
    assets_snapshot: list[dict[str, Any]]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PublicationPackageDTO(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    quality_package_id: uuid.UUID
    publishing_lifecycle_state: str
    platform_name: str
    platform_profile_id: str
    publication_result: Optional[dict[str, Any]] = None
    package_manifest: Optional[dict[str, Any]] = None
    
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
    
    publications: Optional[list[InstagramPublicationDTO]] = None
    versions: Optional[list[InstagramVersionDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class InstagramJobResponseDTO(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[str] = None
    quality_package_id: uuid.UUID
    platform_media_type: str
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
    
    packages: Optional[list[PublicationPackageDTO]] = None
    attempts_history: Optional[list[PublishingAttemptDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class InstagramMetricsDTO(BaseModel):
    jobs_queued: int
    jobs_processing: int
    jobs_succeeded: int
    jobs_failed: int
    jobs_retrying: int
    jobs_cancelled: int
    total_publications: int
    total_views: int
    total_reach: int
    average_engagement_rate: float
    average_duration_sec: float
    current_worker_count: int
    worker_uptime: str
    worker_is_running: bool
    worker_heartbeats: list[dict[str, Any]]
