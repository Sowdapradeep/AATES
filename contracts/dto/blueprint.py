from pydantic import BaseModel
from typing import Any
from contracts.dto.creative import DialogueLine

class SceneBlueprint(BaseModel):
    scene_number: int
    location: str
    time_of_day: str
    weather: str
    lighting_mood: str
    characters: list[str]
    emotions: list[str]
    props: list[str]
    costumes: dict[str, str]  # character_name -> costume description
    camera_intent: str
    visual_style: str
    dialogues: list[DialogueLine]
    music_mood: str
    sound_effects: list[str]
    continuity_notes: str
    rendering_hints: dict[str, Any]

class ProductionBlueprint(BaseModel):
    episode_id: str
    universe_id: str
    season: int
    episode: int
    scenes: list[SceneBlueprint]
    version: int
