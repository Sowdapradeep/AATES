import uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.narrative.models.base import NarrativeBaseModel

class StoryArc(NarrativeBaseModel):
    """
    StoryArc ORM Model.
    Represents macro narrative themes, climax predictions, and resolution paths for a Universe.
    """
    __tablename__ = "narrative_story_arcs"

    universe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("narrative_universes.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    major_theme: Mapped[str | None] = mapped_column(String(255), nullable=True)
    climax_prediction: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    universe = relationship("Universe", back_populates="story_arcs")
