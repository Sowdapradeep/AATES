import uuid
from typing import Any
from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.narrative.models.base import NarrativeBaseModel

class Character(NarrativeBaseModel):
    """
    Character ORM Model.
    Represents a character entity in a Universe with rich traits, backstory, and dialect preferences.
    """
    __tablename__ = "narrative_characters"

    universe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("narrative_universes.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(100), default="protagonist", nullable=False)
    archetype: Mapped[str | None] = mapped_column(String(100), nullable=True)
    personality_traits: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    background_lore: Mapped[str | None] = mapped_column(Text, nullable=True)
    motivation: Mapped[str | None] = mapped_column(Text, nullable=True)
    slang_preference: Mapped[str | None] = mapped_column(String(100), default="chennai", nullable=True)
    attire_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Antagonistic parameters (for villains)
    antagonistic_goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    methods: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    redeeming_qualities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    underlying_weakness: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    universe = relationship("Universe", back_populates="characters")
    relationships_as_a = relationship("Relationship", foreign_keys="Relationship.character_a_id", back_populates="character_a", cascade="all, delete-orphan")
    relationships_as_b = relationship("Relationship", foreign_keys="Relationship.character_b_id", back_populates="character_b", cascade="all, delete-orphan")
    timeline_events = relationship("NarrativeTimelineEvent", back_populates="character")
