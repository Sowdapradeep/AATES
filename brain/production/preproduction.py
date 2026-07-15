from contracts.dto.blueprint import SceneBlueprint
from contracts.dto.production import StoryboardPanel, ShotPlan, CameraInstruction, CinematographySpec, EnvironmentSpec

class StoryboardEngine:
    """Core Storyboard Engine converting Scene Blueprints into visual panels specs."""
    
    async def generate_panels(self, scene: SceneBlueprint) -> list[StoryboardPanel]:
        """Assembles character placements and visual framing guidelines into storyboard panels."""
        panel = StoryboardPanel(
            scene_id=f"scene_{scene.scene_number}",
            panel_number=1,
            shot_purpose="Establishing scene location atmosphere",
            character_placement=scene.characters,
            environment_description=f"Location: {scene.location}. Weather: {scene.weather}.",
            emotional_intent=scene.emotions[0] if scene.emotions else "neutral",
            visual_composition="Wide screen framing, rule of thirds matching local trees outline.",
            version=1
        )
        return [panel]

class ShotPlanner:
    """Core Shot Planner defining duration and transitions between clips."""
    
    async def plan_shots(self, scene: SceneBlueprint) -> list[ShotPlan]:
        """Maps out durations and transitions between individual shots of a scene."""
        shot = ShotPlan(
            shot_id=f"shot_{scene.scene_number}_1",
            scene_id=f"scene_{scene.scene_number}",
            shot_duration=5.5,
            transition_type="fade",
            camera_intent=scene.camera_intent,
            scene_relationship="Initial establishing scene visual context."
        )
        return [shot]

class CameraDirector:
    """Core Camera Director generating provider-independent camera movements specs."""
    
    async def create_camera_instructions(self, scene: SceneBlueprint) -> CameraInstruction:
        """Determines framing angles and active focus targets specs."""
        return CameraInstruction(
            scene_id=f"scene_{scene.scene_number}",
            camera_type="establishing",
            movement_profile="slow pan-right tracking shot",
            target_focus="Traditional forest boundary stones marker"
        )

class CinematographyEngine:
    """Core Cinematography Engine configuring lighting mood, lenses, and color grading palettes."""
    
    async def generate_specs(self, scene: SceneBlueprint) -> CinematographySpec:
        """Formulates lighting layouts and anamorphic frame styling presets."""
        return CinematographySpec(
            scene_id=f"scene_{scene.scene_number}",
            lighting_mood=scene.lighting_mood,
            lens_style="Anamorphic 35mm wide lens",
            composition="Framing characters on opposite margins to indicate high emotional distance tension",
            color_palette=["#5c3d2e", "#865439", "#c68b59"],
            atmosphere="Tense rustic silence",
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
