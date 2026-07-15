from pydantic import BaseModel
from typing import Any

class StoryboardPanel(BaseModel):
    scene_id: str
    panel_number: int
    shot_purpose: str
    character_placement: list[str]
    environment_description: str
    emotional_intent: str
    visual_composition: str
    version: int

class ShotPlan(BaseModel):
    shot_id: str
    scene_id: str
    shot_duration: float  # in seconds
    transition_type: str  # e.g., "cut", "fade"
    camera_intent: str
    scene_relationship: str

class CameraInstruction(BaseModel):
    scene_id: str
    camera_type: str  # wide, medium, close-up, tracking, dolly, crane, handheld, over-the-shoulder, establishing
    movement_profile: str
    target_focus: str

class CinematographySpec(BaseModel):
    scene_id: str
    lighting_mood: str
    lens_style: str
    composition: str
    color_palette: list[str]
    atmosphere: str
    time_of_day: str
    weather: str

class EnvironmentSpec(BaseModel):
    scene_id: str
    location: str
    props: list[str]
    costumes: dict[str, str]  # character_name -> costume description
    environmental_effects: list[str]
