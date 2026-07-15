from typing import Any
from contracts.dto.blueprint import SceneBlueprint
from contracts.dto.production import StoryboardPanel, ShotPlan, CameraInstruction, CinematographySpec, EnvironmentSpec
from brain.production.profiles import profile_loader

class StoryboardEngine:
    """Core Storyboard Engine converting Scene Blueprints into visual panels specs using Production Profiles pacing."""
    
    async def generate_panels(self, scene: SceneBlueprint, production_profile: str = "cinematic") -> list[StoryboardPanel]:
        """Assembles character placements and visual framing guidelines into storyboard panels."""
        prof = profile_loader.load_production_profile(production_profile)
        frequency = prof.get("shot_frequency", 4.5)
        
        # Build panels frequency (cinematic = 1 panel, fast-paced = 2 panels)
        panel_count = 2 if frequency <= 2.5 else 1
        panels = []
        for i in range(1, panel_count + 1):
            panels.append(
                StoryboardPanel(
                    scene_id=f"scene_{scene.scene_number}",
                    panel_number=i,
                    shot_purpose=f"Establishing panel {i} focus",
                    character_placement=scene.characters,
                    environment_description=f"Location: {scene.location}. Weather: {scene.weather}.",
                    emotional_intent=scene.emotions[0] if scene.emotions else "neutral",
                    visual_composition=f"Framing composition matching {prof.get('camera_movement')}",
                    version=1
                )
            )
        return panels

class ShotPlanner:
    """Core Shot Planner defining duration and transitions between clips based on editing rhythm."""
    
    async def plan_shots(self, scene: SceneBlueprint, production_profile: str = "cinematic") -> list[ShotPlan]:
        """Maps out durations and transitions between individual shots of a scene."""
        prof = profile_loader.load_production_profile(production_profile)
        freq = prof.get("shot_frequency", 4.5)
        
        shot = ShotPlan(
            shot_id=f"shot_{scene.scene_number}_1",
            scene_id=f"scene_{scene.scene_number}",
            shot_duration=freq,
            transition_type="cut" if freq <= 2.5 else "fade",
            camera_intent=scene.camera_intent,
            scene_relationship=f"Shot pace aligns with editing rhythm: {prof.get('editing_rhythm')}"
        )
        return [shot]

class CameraDirector:
    """Core Camera Director generating provider-independent camera movements specs matching profiles."""
    
    async def create_camera_instructions(self, scene: SceneBlueprint, production_profile: str = "cinematic") -> CameraInstruction:
        """Determines framing angles and active focus targets specs."""
        prof = profile_loader.load_production_profile(production_profile)
        return CameraInstruction(
            scene_id=f"scene_{scene.scene_number}",
            camera_type="establishing",
            movement_profile=prof.get("camera_movement", "slow dolly tracking"),
            target_focus="Traditional forest boundary stones marker"
        )

class CinematographyEngine:
    """Core Cinematography Engine configuring lighting mood, lenses, and color grading palettes."""
    
    async def generate_specs(self, scene: SceneBlueprint, production_profile: str = "cinematic") -> CinematographySpec:
        """Formulates lighting layouts and anamorphic frame styling presets with color grading overrides."""
        prof = profile_loader.load_production_profile(production_profile)
        return CinematographySpec(
            scene_id=f"scene_{scene.scene_number}",
            lighting_mood=scene.lighting_mood,
            lens_style="Anamorphic 35mm wide lens",
            composition="Framing characters on opposite margins to indicate high emotional distance tension",
            color_palette=["#5c3d2e", "#865439", "#c68b59"],
            atmosphere=f"Cinematic color grading: {prof.get('color_grading')}",
            time_of_day=scene.time_of_day,
            weather=scene.weather
        )

class EnvironmentPlanner:
    """Core Environment Planner coordinating costumes, prop placements and VFX specifications."""
    
    async def plan_environment(self, scene: SceneBlueprint) -> EnvironmentSpec:
        """Maps props, attire details, and weather overlays specifications."""
        return EnvironmentSpec(
            scene_id=f"scene_{scene.scene_number}",
            location=scene.location,
            props=scene.props,
            costumes=scene.costumes,
            environmental_effects=["gentle falling leaves", "drifting dust motes in golden light rays"]
        )

storyboard_engine = StoryboardEngine()
shot_planner = ShotPlanner()
camera_director = CameraDirector()
cinematography_engine = CinematographyEngine()
environment_planner = EnvironmentPlanner()
