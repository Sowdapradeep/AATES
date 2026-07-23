import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class ResearchJobCreateDTO(BaseModel):
    topic: str
    priority: Optional[int] = 0
    tenant_id: Optional[str] = None

class ResearchSourceDTO(BaseModel):
    id: uuid.UUID
    title: str
    url: str
    summary: Optional[str] = None
    relevance_score: float
    content: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class KnowledgePackageDTO(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    topic: str
    summary: str
    keywords: Optional[list[str]] = None
    audience: Optional[list[str]] = None
    pain_points: Optional[list[str]] = None
    faqs: Optional[list[dict[str, Any]]] = None
    competitors: Optional[list[dict[str, Any]]] = None
    statistics: Optional[list[str]] = None
    story_structure: Optional[dict[str, Any]] = None
    visual_ideas: Optional[dict[str, Any]] = None
    outline: Optional[list[dict[str, Any]]] = None
    hooks: Optional[list[str]] = None
    ctas: Optional[list[str]] = None
    titles: Optional[list[str]] = None
    references: Optional[list[str]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class KeywordDTO(BaseModel):
    id: uuid.UUID
    keyword: str
    volume: int
    difficulty: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CompetitorDTO(BaseModel):
    id: uuid.UUID
    name: str
    url: Optional[str] = None
    summary: Optional[str] = None
    strengths: Optional[list[str]] = None
    weaknesses: Optional[list[str]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ResearchJobResponseDTO(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[str] = None
    topic: str
    status: str
    stage: str
    priority: int
    attempts: int
    max_attempts: int
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    progress: float
    providers_used: Optional[list[str]] = None
    search_count: int
    duration_sec: float
    summary_time_sec: float
    created_at: datetime
    updated_at: datetime
    
    sources: Optional[list[ResearchSourceDTO]] = None
    packages: Optional[list[KnowledgePackageDTO]] = None
    keywords: Optional[list[KeywordDTO]] = None
    competitors: Optional[list[CompetitorDTO]] = None

    model_config = ConfigDict(from_attributes=True)

class ResearchMetricsDTO(BaseModel):
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
