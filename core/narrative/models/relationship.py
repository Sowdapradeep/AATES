import uuid
from sqlalchemy import String, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.narrative.models.base import NarrativeBaseModel

class Relationship(NarrativeBaseModel):
    """
    Relationship ORM Model.
    Represents structural ties and dynamic tension levels between two Character entities.
    """
    __tablename__ = "narrative_relationships"

    character_a_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("narrative_characters.id", ondelete="CASCADE"), nullable=False, index=True)
    character_b_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("narrative_characters.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(100), default="rivalry", nullable=False)
    tension_level: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    history_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    character_a = relationship("Character", foreign_keys=[character_a_id], back_populates="relationships_as_a")
    character_b = relationship("Character", foreign_keys=[character_b_id], back_populates="relationships_as_b")
