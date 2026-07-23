import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class SubtitleJobCreateDTO(BaseModel):
    voice_package_id: uuid.UUID
    video_package_id: uuid.UUID
    language: Optional[str] = "en"
    provider: Optional[str] = "alignment"
    priority: Optional[int] = 0

class CaptionStyleProfileDTO(BaseModel):
    id: uuid.UUID
    name: str
    platform: str
    font_family: str
    font_size: int
    font_weight: str
    text_color: str
    outline_color: str
    outline_width: int
    shadow: Optional[str] = None
    background_box: bool
    background_color: Optional[str] = None
    alignment: str
    vertical_position: str
    margins: Optional[dict[str, Any]] = None
    animation: Optional[str] = None
    safe_region: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CaptionSegmentDTO(BaseModel):
    id: uuid.UUID
    scene_subtitle_id: uuid.UUID
    segment_number: int
    start_ms: int
    end_ms: int
    text: str
    words: list[dict[str, Any]]
    reading_speed_wpm: float
    reading_speed_cps: float
    reading_speed_cpl: float
    confidence: float
    model_config = ConfigDict(from_attributes=True)

class SceneSubtitleDTO(BaseModel):
    id: uuid.UUID
    subtitle_package_id: uuid.UUID
    scene_number: int
    caption_text: str
    word_timings: list[dict[str, Any]]
    sentence_timings: list[dict[str, Any]]
    caption_position: str
    safe_region: Optional[str] = None
    reading_speed_wpm: float
    reading_speed_cps: float
    reading_speed_cpl: float
    confidence: float
    language: str
    key_phrases: Optional[list[str]] = None
    importance_score: float
    quality_score: float
    created_at: datetime
    segments: Optional[list[CaptionSegmentDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class SubtitleTrackDTO(BaseModel):
    id: uuid.UUID
    subtitle_package_id: uuid.UUID
    style_profile_id: Optional[uuid.UUID] = None
    track_name: str
    language: str
    is_default: bool
    is_original: bool
    is_translated: bool
    is_auto_generated: bool
    is_human_edited: bool
    srt_path: str
    webvtt_path: str
    ass_path: str
    json_timeline_path: str
    burned_caption_metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    style_profile: Optional[CaptionStyleProfileDTO] = None
    model_config = ConfigDict(from_attributes=True)

class SubtitleVersionDTO(BaseModel):
    id: uuid.UUID
    subtitle_package_id: uuid.UUID
    version: int
    parent_version: Optional[int] = None
    lineage_action: str
    assets_snapshot: list[dict[str, Any]]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SubtitlePackageDTO(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    voice_package_id: uuid.UUID
    video_package_id: uuid.UUID
    language: str
    caption_style: str
    subtitle_formats: list[str]
    scene_count: int
    total_captions: int
    total_words: int
    metadata_artifacts: Optional[dict[str, Any]] = None
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
    
    scene_subtitles: Optional[list[SceneSubtitleDTO]] = None
    tracks: Optional[list[SubtitleTrackDTO]] = None
    versions: Optional[list[SubtitleVersionDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class SubtitleJobResponseDTO(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[str] = None
    voice_package_id: uuid.UUID
    video_package_id: uuid.UUID
    language: str
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
    
    packages: Optional[list[SubtitlePackageDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class SubtitleMetricsDTO(BaseModel):
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
