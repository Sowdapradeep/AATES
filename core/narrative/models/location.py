import uuid
from typing import Any
from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.narrative.models.base import NarrativeBaseModel

class Location(NarrativeBaseModel):
    """
    Location ORM Model.
    Represents set locations, architectural features, and visual moods in a Universe.
    """
    __tablename__ = "narrative_locations"

    universe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("narrative_universes.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_features: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    mood: Mapped[str | None] = mapped_column(String(100), default="Neutral", nullable=True)
    cultural_context: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    universe = relationship("Universe", back_populates="locations")
    timeline_events = relationship("NarrativeTimelineEvent", back_populates="location")
