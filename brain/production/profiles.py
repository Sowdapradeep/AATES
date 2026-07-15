import os
import yaml
from typing import Any

class ProfileConfigLoader:
    """Core Profile Config Loader loading yaml files for media outputs and editing presets."""
    
    def __init__(self) -> None:
        self.knowledge_dir = "knowledge"
        
    def load_output_profile(self, name: str) -> dict[str, Any]:
        """Loads aspect ratios and video presets for target platforms (e.g. Instagram Reels)."""
        path = os.path.join(self.knowledge_dir, "output_profiles.yaml")
        if not os.path.exists(path):
            # Fallback default values
            return {
                "aspect_ratio": "9:16",
                "resolution": "1080x1920",
                "frame_rate": 30,
                "max_duration": 90.0,
                "subtitle_style": "bold_yellow",
                "safe_text_area": {"top": 0.15, "bottom": 0.15, "left": 0.1, "right": 0.1},
                "intro_duration": 1.5,
                "outro_duration": 2.0,
                "thumbnail_frame_strategy": "highest_contrast_frame",
                "audio_loudness_target": -14.0,
                "video_codec": "h264",
                "export_preset": "slow"
            }
            
        with open(path, "r") as f:
            data = yaml.safe_load(f)
            return data.get(name, data.get("instagram_reel"))

    def load_production_profile(self, name: str) -> dict[str, Any]:
        """Loads cinematography style overrides (e.g. Cinematic, thriller cuts frequency)."""
        path = os.path.join(self.knowledge_dir, "production_profiles.yaml")
        if not os.path.exists(path):
            return {
                "shot_frequency": 4.5,
                "camera_movement": "slow dolly tracking",
                "music_intensity": 0.6,
                "transition_speed": 1.5,
                "subtitle_animation": "fade_in",
                "color_grading": "warm_cinematic",
                "editing_rhythm": "slow"
            }
            
        with open(path, "r") as f:
            data = yaml.safe_load(f)
            return data.get(name, data.get("cinematic"))

profile_loader = ProfileConfigLoader()
