import uuid
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict

class MarketingBaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by: str = "system"
    version: int = 1
    status: str = "active"
    metadata_json: Optional[dict[str, Any]] = None

class SegmentCreateDTO(BaseModel):
    name: str
    region: str = "Tamil Nadu"
    demographics: str = "18-35 Youth"
    preferred_genre: str = "Drama"
    engagement_rate: float = 0.05
    keywords: Optional[List[str]] = Field(default_factory=list)

class SegmentResponseDTO(MarketingBaseDTO):
    name: str
    region: str
    demographics: str
    preferred_genre: str
    engagement_rate: float
    keywords: Optional[List[str]] = Field(default_factory=list)

class CampaignCreateDTO(BaseModel):
    title: str
    segment_id: Optional[uuid.UUID] = None
    target_platform: str = "youtube_reels"
    viral_hook: Optional[str] = None
    hashtags: Optional[List[str]] = Field(default_factory=list)
    budget_allocation_usd: float = 0.0

class CampaignResponseDTO(MarketingBaseDTO):
    title: str
    segment_id: Optional[uuid.UUID] = None
    target_platform: str
    viral_hook: Optional[str] = None
    hashtags: Optional[List[str]] = Field(default_factory=list)
    budget_allocation_usd: float
    performance_score: float
