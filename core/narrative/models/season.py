import uuid
from typing import Any
from sqlalchemy import String, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.narrative.models.base import NarrativeBaseModel

class Season(NarrativeBaseModel):
    """
    Season ORM Model.
    Represents a structured season arc within a Universe, referencing multi-episode goals and conflicts.
    """
    __tablename__ = "narrative_seasons"

    universe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("narrative_universes.id", ondelete="CASCADE"), nullable=False, index=True)
    season_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    total_episodes: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    season_arc: Mapped[str | None] = mapped_column(String(500), nullable=True)
    major_conflicts: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    character_development_milestones: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    universe = relationship("Universe", back_populates="seasons")
    episodes = relationship("Episode", back_populates="season", cascade="all, delete-orphan")
