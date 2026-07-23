import uuid
from typing import Any
from sqlalchemy import String, Float, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.narrative.models.base import NarrativeBaseModel

class Organization(NarrativeBaseModel):
    """
    Organization ORM Model.
    Represents factions, guilds, corporations, or political bodies in a Universe.
    """
    __tablename__ = "narrative_organizations"

    universe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("narrative_universes.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    faction_type: Mapped[str | None] = mapped_column(String(100), default="Guild", nullable=True)
    objectives: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    influence_level: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    allies: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    enemies: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)

    # Relationships
    universe = relationship("Universe", back_populates="organizations")
    timeline_events = relationship("NarrativeTimelineEvent", back_populates="organization")
