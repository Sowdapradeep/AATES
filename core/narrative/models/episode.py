import uuid
from typing import Any
from sqlalchemy import String, Integer, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.narrative.models.base import NarrativeBaseModel

class Episode(NarrativeBaseModel):
    """
    Episode ORM Model.
    Represents an episode belonging to a Season with screenplay outlines and beat lists.
    """
    __tablename__ = "narrative_episodes"

    season_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("narrative_seasons.id", ondelete="CASCADE"), nullable=False, index=True)
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    episode_objectives: Mapped[str | None] = mapped_column(Text, nullable=True)
    story_beats: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    scene_objectives: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, default=list, nullable=True)

    # Relationships
    season = relationship("Season", back_populates="episodes")
    scenes = relationship("Scene", back_populates="episode", cascade="all, delete-orphan")
    timeline_events = relationship("NarrativeTimelineEvent", back_populates="episode")
