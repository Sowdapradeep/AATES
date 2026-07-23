import uuid
from typing import Any
from sqlalchemy import String, Integer, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.narrative.models.base import NarrativeBaseModel

class NarrativeTimelineEvent(NarrativeBaseModel):
    """
    NarrativeTimelineEvent ORM Model.
    Represents chronological beat events, historical milestones, twists, and foreshadowing clues.
    May reference a Universe, Character, Location, Organization, or Episode.
    """
    __tablename__ = "narrative_timeline_events"

    universe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("narrative_universes.id", ondelete="CASCADE"), nullable=False, index=True)
    beat_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), default="beat", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    emotional_charge: Mapped[str | None] = mapped_column(String(100), default="tense", nullable=True)
    twist_introduced: Mapped[str | None] = mapped_column(Text, nullable=True)
    foreshadowing_clues: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)

    # Optional Entity Reference Links
    character_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("narrative_characters.id", ondelete="SET NULL"), nullable=True)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("narrative_locations.id", ondelete="SET NULL"), nullable=True)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("narrative_organizations.id", ondelete="SET NULL"), nullable=True)
    episode_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("narrative_episodes.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    universe = relationship("Universe", back_populates="timeline_events")
    character = relationship("Character", back_populates="timeline_events")
    location = relationship("Location", back_populates="timeline_events")
    organization = relationship("Organization", back_populates="timeline_events")
    episode = relationship("Episode", back_populates="timeline_events")
