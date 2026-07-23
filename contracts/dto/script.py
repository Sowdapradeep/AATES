import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class ScriptJobCreateDTO(BaseModel):
    knowledge_package_id: uuid.UUID
    platform: str
    language: Optional[str] = "ta"
    priority: Optional[int] = 0

class ScriptVersionDTO(BaseModel):
    id: uuid.UUID
    script_package_id: uuid.UUID
    version: int
    parent_version: Optional[int] = None
    lineage_action: str
    title: str
    hook: str
    opening: Optional[str] = None
    problem: str
    story: str
    solution: str
    cta: str
    narration: str
    scene_breakdown: list[dict[str, Any]]
    thumbnail_prompt: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    hashtags: Optional[list[str]] = None
    quality_score: float
    review_report: Optional[dict[str, Any]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ScriptPackageDTO(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    knowledge_package_id: uuid.UUID
    title: str
    platform: str
    language: str
    target_audience: Optional[list[str]] = None
    tone: Optional[str] = None
    style: Optional[str] = None
    estimated_duration_sec: float
    word_count: int
    reading_time_sec: float
    hook: str
    opening: Optional[str] = None
    problem: str
    story: str
    solution: str
    cta: str
    narration: str
    scene_breakdown: list[dict[str, Any]]
    on_screen_text: Optional[list[str]] = None
    visual_prompts: Optional[list[str]] = None
    thumbnail_prompt: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    hashtags: Optional[list[str]] = None
    references: Optional[list[str]] = None
    telemetry_metadata: Optional[dict[str, Any]] = None
    version: int
    parent_package_id: Optional[uuid.UUID] = None
    source_agent: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    prompt_version: Optional[str] = None
    quality_score: float
    review_report: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    versions: Optional[list[ScriptVersionDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class ScriptJobResponseDTO(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[str] = None
    knowledge_package_id: uuid.UUID
    provider: str
    platform: str
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
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    packages: Optional[list[ScriptPackageDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class ScriptMetricsDTO(BaseModel):
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
