from typing import Any
from brain.production.profiles import profile_loader

class SceneTimingEngine:
    """Core Scene Timing Engine managing scene target durations and runtime limits validation."""
    
    def calculate_scene_durations(
        self,
        scene_count: int,
        output_profile_name: str,
        production_profile_name: str
    ) -> list[float]:
        """Calculates paced target durations for every scene within maximum output bounds."""
        out_prof = profile_loader.load_output_profile(output_profile_name)
        max_dur = out_prof.get("max_duration", 90.0)
        intro_dur = out_prof.get("intro_duration", 1.5)
        outro_dur = out_prof.get("outro_duration", 2.0)

        usable_dur = max_dur - (intro_dur + outro_dur)

        prod_prof = profile_loader.load_production_profile(production_profile_name)
        frequency = prod_prof.get("shot_frequency", 4.5)

        # Approximate average scene duration (assuming 2 shots average per scene)
        avg_scene_dur = frequency * 2.0
        
        durations = []
        for _ in range(scene_count):
            durations.append(avg_scene_dur)

        total_scene_dur = sum(durations)

        if total_scene_dur > usable_dur:
            scaling = usable_dur / total_scene_dur
            durations = [round(d * scaling, 2) for d in durations]
        else:
            durations = [round(d, 2) for d in durations]

        return durations

scene_timing_engine = SceneTimingEngine()
