import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class VoiceJobCreateDTO(BaseModel):
    script_package_id: uuid.UUID
    language: Optional[str] = "en"
    priority: Optional[int] = 0

class SceneVoiceDTO(BaseModel):
    id: uuid.UUID
    voice_package_id: uuid.UUID
    scene_number: int
    duration_ms: int
    narration: str
    local_path: str
    storage_key: str
    public_url: Optional[str] = None
    preview_url: Optional[str] = None
    voice_id: str
    provider: str
    model: str
    language: str
    emotion: Optional[str] = None
    speaking_style: Optional[str] = None
    pitch: Optional[str] = None
    speed: Optional[str] = None
    volume: Optional[str] = None
    ssml: Optional[str] = None
    pause_map: Optional[dict[str, Any]] = None
    word_alignment: Optional[list[dict[str, Any]]] = None
    sentence_alignment: Optional[list[dict[str, Any]]] = None
    phoneme_alignment: Optional[list[dict[str, Any]]] = None
    generation_duration_sec: float
    quality_score: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class VoiceVersionDTO(BaseModel):
    id: uuid.UUID
    voice_package_id: uuid.UUID
    version: int
    parent_version: Optional[int] = None
    lineage_action: str
    scene_number: Optional[int] = None
    assets_snapshot: list[dict[str, Any]]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class VoicePackageDTO(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    script_package_id: uuid.UUID
    platform: str
    language: str
    voice_profile: Optional[dict[str, Any]] = None
    speaking_style: Optional[str] = None
    overall_duration_ms: int
    total_words: int
    total_scenes: int
    audio_format: str
    sample_rate: int
    bitrate: int
    pronunciation_dictionary: Optional[dict[str, str]] = None
    
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
    
    assets: Optional[list[SceneVoiceDTO]] = None
    versions: Optional[list[VoiceVersionDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class VoiceJobResponseDTO(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[str] = None
    script_package_id: uuid.UUID
    provider: str
    voice_model: str
    language: str
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
    
    packages: Optional[list[VoicePackageDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class VoiceMetricsDTO(BaseModel):
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
