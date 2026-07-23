import uuid
from typing import Any
from sqlalchemy import String, Integer, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.narrative.models.base import NarrativeBaseModel

class Scene(NarrativeBaseModel):
    """
    Scene ORM Model.
    Represents an individual scene belonging to an Episode, carrying camera intents,
    lighting, audio moods, costumes, and dialogues.
    """
    __tablename__ = "narrative_scenes"

    episode_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("narrative_episodes.id", ondelete="CASCADE"), nullable=False, index=True)
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    time_of_day: Mapped[str | None] = mapped_column(String(50), default="DAY", nullable=True)
    weather: Mapped[str | None] = mapped_column(String(50), default="SUNNY", nullable=True)
    lighting_mood: Mapped[str | None] = mapped_column(String(100), nullable=True)
    characters_present: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    emotions: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    props: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    costumes: Mapped[dict[str, str] | None] = mapped_column(JSON, default=dict, nullable=True)
    camera_intent: Mapped[str | None] = mapped_column(Text, nullable=True)
    visual_style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dialogues: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, default=list, nullable=True)
    music_mood: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sound_effects: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    continuity_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rendering_hints: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    episode = relationship("Episode", back_populates="scenes")
