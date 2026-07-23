import uuid
from typing import Any
from sqlalchemy import String, Float, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.marketing.models.base import MarketingBaseModel

class MarketingCampaign(MarketingBaseModel):
    """
    MarketingCampaign ORM Model.
    Tracks promotional campaigns, targeted hashtags, viral hooks, and ad channel strategies.
    """
    __tablename__ = "marketing_campaigns"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    segment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("marketing_audience_segments.id", ondelete="SET NULL"), nullable=True, index=True)
    target_platform: Mapped[str] = mapped_column(String(100), default="youtube_reels", nullable=False) # youtube_reels, instagram_reels
    viral_hook: Mapped[str | None] = mapped_column(Text, nullable=True)
    hashtags: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    budget_allocation_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    performance_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Relationships
    audience_segment = relationship("AudienceSegment", back_populates="campaigns")
