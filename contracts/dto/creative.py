from pydantic import BaseModel
from typing import Any

class DialogueLine(BaseModel):
    character_name: str
    text_tamil: str
    text_english: str
    slang_type: str
    delivery_note: str | None = None

class CharacterProfile(BaseModel):
    id: str
    name: str
    role: str  # e.g., "protagonist", "villain", "mentor"
    archetype: str
    personality_traits: list[str]
    background_lore: str
    motivation: str
    slang_preference: str  # e.g., "chennai", "madurai"
    attire_note: str

class VillainProfile(BaseModel):
    character_id: str
    antagonistic_goal: str
    methods: list[str]
    redeeming_qualities: list[str]
    underlying_weakness: str

class RelationshipDTO(BaseModel):
    character_a_id: str
    character_b_id: str
    relationship_type: str  # e.g., "rivalry", "alliance", "mentor-disciple"
    tension_level: float    # 0.0 to 1.0
    history: str

class LocationDTO(BaseModel):
    id: str
    name: str
    description: str
    key_features: list[str]
    mood: str
    cultural_context: str

class OrganizationDTO(BaseModel):
    id: str
    name: str
    faction_type: str
    objectives: list[str]
    influence_level: float  # 0.0 to 1.0
    allies: list[str]
    enemies: list[str]

class StoryArcDTO(BaseModel):
    id: str
    universe_id: str
    title: str
    major_theme: str
    climax_prediction: str
    resolution_path: str

class ConflictDTO(BaseModel):
    id: str
    parties_involved: list[str]
    cause: str
    tension_score: float
    current_status: str

class PlotPointDTO(BaseModel):
    id: str
    arc_id: str
    beat_number: int
    event: str
    twist_introduced: str | None = None
    foreshadowing_clues: list[str] = []
    emotional_charge: str  # e.g., "tense", "triumphant"

class DialoguePlanDTO(BaseModel):
    scene_id: int
    character_id: str
    slang_injected: str
    dialogue_intent: str
    target_emotion: str

class ValidationResultDTO(BaseModel):
    is_valid: bool
    warnings: list[str]
    canon_compliance_score: float
    details: str
