import uuid
from typing import Any, List
from sqlalchemy import String, Float, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.marketing.models.base import MarketingBaseModel

class AudienceSegment(MarketingBaseModel):
    """
    AudienceSegment ORM Model.
    Tracks demographics, regional interests, preferred genres, and engagement profiles.
    """
    __tablename__ = "marketing_audience_segments"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(100), default="Tamil Nadu", nullable=False)
    demographics: Mapped[str] = mapped_column(String(100), default="18-35 Youth", nullable=False)
    preferred_genre: Mapped[str] = mapped_column(String(100), default="Drama", nullable=False)
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.05, nullable=False)
    keywords: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)

    # Relationships
    campaigns = relationship("MarketingCampaign", back_populates="audience_segment", cascade="all, delete-orphan")
