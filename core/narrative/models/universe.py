import uuid
from typing import Any, List
from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.narrative.models.base import NarrativeBaseModel

class Universe(NarrativeBaseModel):
    """
    Universe ORM Model.
    Represents a master living narrative universe containing worlds, characters, locations,
    organizations, story arcs, timeline events, and seasons.
    """
    __tablename__ = "narrative_universes"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    genre: Mapped[str] = mapped_column(String(100), default="Drama", nullable=False)
    core_themes: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    world_rules: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    long_term_direction: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    worlds = relationship("World", back_populates="universe", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="universe", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="universe", cascade="all, delete-orphan")
    organizations = relationship("Organization", back_populates="universe", cascade="all, delete-orphan")
    story_arcs = relationship("StoryArc", back_populates="universe", cascade="all, delete-orphan")
    timeline_events = relationship("NarrativeTimelineEvent", back_populates="universe", cascade="all, delete-orphan")
    seasons = relationship("Season", back_populates="universe", cascade="all, delete-orphan")
