import uuid
from typing import Any
from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.narrative.models.base import NarrativeBaseModel

class World(NarrativeBaseModel):
    """
    World ORM Model.
    Represents physical world, geography, climate, and world rules within a Universe.
    """
    __tablename__ = "narrative_worlds"

    universe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("narrative_universes.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    geography_type: Mapped[str | None] = mapped_column(String(100), default="Terrestrial", nullable=True)
    climate: Mapped[str | None] = mapped_column(String(100), default="Tropical", nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    world_rules: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)

    # Relationships
    universe = relationship("Universe", back_populates="worlds")
