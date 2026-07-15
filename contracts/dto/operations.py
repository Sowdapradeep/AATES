import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Optional


class CampaignDTO(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    universe_id: str
    season: int = 1
    start_date: datetime
    end_date: datetime
    status: str = "draft"  # draft, active, paused, completed
    priority: int = 0
    platforms: dict[str, Any]  # {"instagram": True, "youtube": True}


class PublishRequestDTO(BaseModel):
    episode_id: str
    universe_id: str
    master_reel_path: str
    caption: str
    platforms: list[str]  # ["instagram_reel", "youtube_short"]
    campaign_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    priority: int = 0


class PublishResultDTO(BaseModel):
    episode_id: str
    platform: str
    status: str  # "success", "failed", "queued"
    external_post_id: Optional[str] = None
    publish_time: Optional[datetime] = None
    provider: str
    retry_count: int = 0
    error_message: Optional[str] = None


class DistributionHistoryDTO(BaseModel):
    episode_id: str
    platform: str
    status: str
    publish_time: Optional[datetime] = None
    asset_version: int = 1
    blueprint_version: int = 1
    retry_count: int = 0


class AnalyticsSnapshotDTO(BaseModel):
    episode_id: str
    platform: str
    views: int = 0
    watch_time: float = 0.0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    follower_growth: int = 0
    recorded_at: Optional[datetime] = None


class RecommendationDTO(BaseModel):
    episode_id: str
    category: str  # pacing, duration, comedy, hook, character
    recommendation_text: str
    source_metrics: dict[str, Any]
    reason: str
    expected_impact: str
    confidence: float = 0.8
    status: str = "pending"


class ProviderHealthDTO(BaseModel):
    provider_name: str
    platform: str
    is_available: bool = True
    latency_ms: float = 0.0
    error_rate: float = 0.0
    success_rate: float = 1.0
    last_success_at: Optional[datetime] = None


class OperationsTimelineEventDTO(BaseModel):
    event_type: str
    payload: dict[str, Any]
    timestamp: Optional[datetime] = None
