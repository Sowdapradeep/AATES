import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Optional

class PublishingJobCreateDTO(BaseModel):
    tenant_id: Optional[str] = None
    content_id: str
    provider: str  # youtube_short, instagram_reel
    priority: int = 0
    scheduled_at: Optional[datetime] = None
    payload: dict[str, Any] = Field(default_factory=dict)

class PublishingJobResponseDTO(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[str] = None
    content_id: str
    provider: str
    status: str
    priority: int
    attempts: int
    max_attempts: int
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    video_id: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    provider_response: Optional[dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
