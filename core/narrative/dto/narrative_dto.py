import uuid
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict

# ── Base DTO Mixin ────────────────────────────────────────────────────────────
class NarrativeBaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by: str = "system"
    version: int = 1
    status: str = "active"
    is_deleted: bool = False
    metadata_json: Optional[dict[str, Any]] = None


# ── Universe DTOs ─────────────────────────────────────────────────────────────
class UniverseCreateDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    genre: str = "Drama"
    core_themes: List[str] = Field(default_factory=list)
    world_rules: List[str] = Field(default_factory=list)
    long_term_direction: Optional[str] = None
    created_by: str = "system"

class UniverseUpdateDTO(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    core_themes: Optional[List[str]] = None
    world_rules: Optional[List[str]] = None
    long_term_direction: Optional[str] = None
    status: Optional[str] = None

class UniverseResponseDTO(NarrativeBaseDTO):
    name: str
    description: Optional[str] = None
    genre: str
    core_themes: List[str] = Field(default_factory=list)
    world_rules: List[str] = Field(default_factory=list)
    long_term_direction: Optional[str] = None


# ── World DTOs ────────────────────────────────────────────────────────────────
class WorldCreateDTO(BaseModel):
    universe_id: uuid.UUID
    name: str
    geography_type: Optional[str] = "Terrestrial"
    climate: Optional[str] = "Tropical"
    notes: Optional[str] = None
    world_rules: List[str] = Field(default_factory=list)

class WorldResponseDTO(NarrativeBaseDTO):
    universe_id: uuid.UUID
    name: str
    geography_type: Optional[str] = None
    climate: Optional[str] = None
    notes: Optional[str] = None
    world_rules: List[str] = Field(default_factory=list)


# ── Character DTOs ────────────────────────────────────────────────────────────
class CharacterCreateDTO(BaseModel):
    universe_id: uuid.UUID
    name: str
    role: str = "protagonist"
    archetype: Optional[str] = None
    personality_traits: List[str] = Field(default_factory=list)
    background_lore: Optional[str] = None
    motivation: Optional[str] = None
    slang_preference: Optional[str] = "chennai"
    attire_note: Optional[str] = None
    antagonistic_goal: Optional[str] = None
    methods: List[str] = Field(default_factory=list)
    redeeming_qualities: List[str] = Field(default_factory=list)
    underlying_weakness: Optional[str] = None

class CharacterResponseDTO(NarrativeBaseDTO):
    universe_id: uuid.UUID
    name: str
    role: str
    archetype: Optional[str] = None
    personality_traits: List[str] = Field(default_factory=list)
    background_lore: Optional[str] = None
    motivation: Optional[str] = None
    slang_preference: Optional[str] = None
    attire_note: Optional[str] = None
    antagonistic_goal: Optional[str] = None
    methods: List[str] = Field(default_factory=list)
    redeeming_qualities: List[str] = Field(default_factory=list)
    underlying_weakness: Optional[str] = None


# ── Relationship DTOs ─────────────────────────────────────────────────────────
class RelationshipCreateDTO(BaseModel):
    character_a_id: uuid.UUID
    character_b_id: uuid.UUID
    relationship_type: str = "rivalry"
    tension_level: float = 0.5
    history_notes: Optional[str] = None

class RelationshipResponseDTO(NarrativeBaseDTO):
    character_a_id: uuid.UUID
    character_b_id: uuid.UUID
    relationship_type: str
    tension_level: float
    history_notes: Optional[str] = None


# ── Location DTOs ─────────────────────────────────────────────────────────────
class LocationCreateDTO(BaseModel):
    universe_id: uuid.UUID
    name: str
    description: Optional[str] = None
    key_features: List[str] = Field(default_factory=list)
    mood: Optional[str] = "Neutral"
    cultural_context: Optional[str] = None

class LocationResponseDTO(NarrativeBaseDTO):
    universe_id: uuid.UUID
    name: str
    description: Optional[str] = None
    key_features: List[str] = Field(default_factory=list)
    mood: Optional[str] = None
    cultural_context: Optional[str] = None


# ── Organization DTOs ─────────────────────────────────────────────────────────
class OrganizationCreateDTO(BaseModel):
    universe_id: uuid.UUID
    name: str
    faction_type: Optional[str] = "Guild"
    objectives: List[str] = Field(default_factory=list)
    influence_level: float = 0.5
    allies: List[str] = Field(default_factory=list)
    enemies: List[str] = Field(default_factory=list)

class OrganizationResponseDTO(NarrativeBaseDTO):
    universe_id: uuid.UUID
    name: str
    faction_type: Optional[str] = None
    objectives: List[str] = Field(default_factory=list)
    influence_level: float
    allies: List[str] = Field(default_factory=list)
    enemies: List[str] = Field(default_factory=list)


# ── StoryArc DTOs ─────────────────────────────────────────────────────────────
class StoryArcCreateDTO(BaseModel):
    universe_id: uuid.UUID
    title: str
    major_theme: Optional[str] = None
    climax_prediction: Optional[str] = None
    resolution_path: Optional[str] = None

class StoryArcResponseDTO(NarrativeBaseDTO):
    universe_id: uuid.UUID
    title: str
    major_theme: Optional[str] = None
    climax_prediction: Optional[str] = None
    resolution_path: Optional[str] = None


# ── TimelineEvent DTOs ────────────────────────────────────────────────────────
class TimelineEventCreateDTO(BaseModel):
    universe_id: uuid.UUID
    beat_number: int = 1
    title: str
    event_type: str = "beat"
    description: Optional[str] = None
    emotional_charge: Optional[str] = "tense"
    twist_introduced: Optional[str] = None
    foreshadowing_clues: List[str] = Field(default_factory=list)
    character_id: Optional[uuid.UUID] = None
    location_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    episode_id: Optional[uuid.UUID] = None

class TimelineEventResponseDTO(NarrativeBaseDTO):
    universe_id: uuid.UUID
    beat_number: int
    title: str
    event_type: str
    description: Optional[str] = None
    emotional_charge: Optional[str] = None
    twist_introduced: Optional[str] = None
    foreshadowing_clues: List[str] = Field(default_factory=list)
    character_id: Optional[uuid.UUID] = None
    location_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    episode_id: Optional[uuid.UUID] = None


# ── Season DTOs ───────────────────────────────────────────────────────────────
class SeasonCreateDTO(BaseModel):
    universe_id: uuid.UUID
    season_number: int
    title: Optional[str] = None
    total_episodes: int = 10
    season_arc: Optional[str] = None
    major_conflicts: List[str] = Field(default_factory=list)
    character_development_milestones: dict[str, Any] = Field(default_factory=dict)

class SeasonResponseDTO(NarrativeBaseDTO):
    universe_id: uuid.UUID
    season_number: int
    title: Optional[str] = None
    total_episodes: int
    season_arc: Optional[str] = None
    major_conflicts: List[str] = Field(default_factory=list)
    character_development_milestones: dict[str, Any] = Field(default_factory=dict)


# ── Episode DTOs ──────────────────────────────────────────────────────────────
class EpisodeCreateDTO(BaseModel):
    season_id: uuid.UUID
    episode_number: int
    title: Optional[str] = None
    episode_objectives: Optional[str] = None
    story_beats: List[str] = Field(default_factory=list)
    scene_objectives: List[dict[str, Any]] = Field(default_factory=list)

class EpisodeResponseDTO(NarrativeBaseDTO):
    season_id: uuid.UUID
    episode_number: int
    title: Optional[str] = None
    episode_objectives: Optional[str] = None
    story_beats: List[str] = Field(default_factory=list)
    scene_objectives: List[dict[str, Any]] = Field(default_factory=list)


# ── Scene DTOs ────────────────────────────────────────────────────────────────
class SceneCreateDTO(BaseModel):
    episode_id: uuid.UUID
    scene_number: int
    location_name: Optional[str] = None
    time_of_day: Optional[str] = "DAY"
    weather: Optional[str] = "SUNNY"
    lighting_mood: Optional[str] = None
    characters_present: List[str] = Field(default_factory=list)
    emotions: List[str] = Field(default_factory=list)
    props: List[str] = Field(default_factory=list)
    costumes: dict[str, str] = Field(default_factory=dict)
    camera_intent: Optional[str] = None
    visual_style: Optional[str] = None
    dialogues: List[dict[str, Any]] = Field(default_factory=list)
    music_mood: Optional[str] = None
    sound_effects: List[str] = Field(default_factory=list)
    continuity_notes: Optional[str] = None
    rendering_hints: dict[str, Any] = Field(default_factory=dict)

class SceneResponseDTO(NarrativeBaseDTO):
    episode_id: uuid.UUID
    scene_number: int
    location_name: Optional[str] = None
    time_of_day: Optional[str] = None
    weather: Optional[str] = None
    lighting_mood: Optional[str] = None
    characters_present: List[str] = Field(default_factory=list)
    emotions: List[str] = Field(default_factory=list)
    props: List[str] = Field(default_factory=list)
    costumes: dict[str, str] = Field(default_factory=dict)
    camera_intent: Optional[str] = None
    visual_style: Optional[str] = None
    dialogues: List[dict[str, Any]] = Field(default_factory=list)
    music_mood: Optional[str] = None
    sound_effects: List[str] = Field(default_factory=list)
    continuity_notes: Optional[str] = None
    rendering_hints: dict[str, Any] = Field(default_factory=dict)
