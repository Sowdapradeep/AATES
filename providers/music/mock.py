import os
import uuid
from typing import Any, List
from providers.music.interface import MusicProvider

class MockMusicProvider(MusicProvider):
    """Mock Music Provider generating synthetic audio files and test waveforms."""

    @property
    def name(self) -> str:
        return "MockMusicEngine"

    def __init__(self) -> None:
        self.output_dir = "artifacts/music"
        os.makedirs(self.output_dir, exist_ok=True)

    async def select_music(self, script_pkg: Any, scene_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        scenes = []
        for i, sc in enumerate(scene_data):
            scene_num = sc.get("scene_number", i + 1)
            duration_ms = sc.get("duration_ms", 5000)
            start_ms = sc.get("timeline_start_ms", 0)

            scenes.append({
                "scene_number": scene_num,
                "track_name": f"Mock Track {scene_num}",
                "artist": "AATES Synthetic Synthesizer",
                "genre": "Ambient",
                "mood": "Neutral",
                "energy": "Medium",
                "tempo_bpm": 120,
                "musical_key": "C Major",
                "start_time_ms": start_ms,
                "end_time_ms": start_ms + duration_ms,
                "fade_in_ms": 500,
                "fade_out_ms": 500,
                "music_volume_db": -14.0,
                "narration_ducking_db": -12.0,
                "cue": {
                    "cue_name": f"Mock_Cue_{scene_num}",
                    "cue_purpose": "background",
                    "source_start_ms": 0,
                    "source_end_ms": duration_ms,
                    "trim_start_ms": 0,
                    "trim_end_ms": duration_ms,
                    "loop_start_ms": 0,
                    "loop_end_ms": duration_ms,
                    "fade_in_ms": 500,
                    "fade_out_ms": 500,
                    "gain_db": 0.0,
                    "emotion_score": 0.85,
                    "transition_compatibility": 0.90,
                    "loop_confidence": 0.95,
                    "crossfade_recommendation": 800,
                    "beat_alignment_offset_ms": 0
                }
            })
        return scenes

    async def generate_music(self, prompt: str, duration_ms: int, options: dict[str, Any]) -> dict[str, Any]:
        filepath = os.path.join(self.output_dir, f"mock_gen_{uuid.uuid4().hex[:6]}.mp3")
        with open(filepath, "wb") as f:
            f.write(b"MOCK_GEN_AUDIO")
        return {
            "title": "Mock Audio",
            "artist": "AATES Mock",
            "genre": "Synthetic",
            "mood": "Calm",
            "tempo_bpm": 120,
            "duration_ms": duration_ms,
            "filepath": filepath
        }

    async def analyze_music(self, audio_path: str) -> dict[str, Any]:
        return {
            "peak_db": -1.0,
            "lufs": -14.0,
            "dynamic_range_db": 8.0,
            "rms_db": -16.0,
            "tempo_bpm": 120,
            "musical_key": "C Major",
            "silence_regions": [],
            "speech_regions": [{"start_ms": 0, "end_ms": 4000}],
            "waveform_data": [0.1, 0.5, 0.2, 0.8, 0.3],
            "spectrum_data": {}
        }

    async def mix_audio(self, music_cues: list[dict[str, Any]], narration_path: str, profile: dict[str, Any]) -> dict[str, Any]:
        base_id = uuid.uuid4().hex[:6]
        master_path = os.path.join(self.output_dir, f"mock_master_{base_id}.mp3")
        music_stem_path = os.path.join(self.output_dir, f"mock_music_{base_id}.mp3")
        voice_stem_path = os.path.join(self.output_dir, f"mock_voice_{base_id}.mp3")
        ambient_stem_path = os.path.join(self.output_dir, f"mock_ambient_{base_id}.mp3")
        sfx_stem_path = os.path.join(self.output_dir, f"mock_sfx_{base_id}.mp3")

        for p in [master_path, music_stem_path, voice_stem_path, ambient_stem_path, sfx_stem_path]:
            with open(p, "wb") as f:
                f.write(b"MOCK_AUDIO_DATA")

        return {
            "master_path": master_path,
            "music_stem_path": music_stem_path,
            "voice_stem_path": voice_stem_path,
            "ambient_stem_path": ambient_stem_path,
            "sfx_stem_path": sfx_stem_path,
            "duration_ms": 5000,
            "automation_points": [{"timestamp_ms": 0, "value_db": -14.0, "interpolation": "linear"}],
            "waveform_metadata": {"peaks": [0.1, 0.5, 0.3]}
        }

    async def normalize(self, audio_path: str, target_lufs: float = -14.0, true_peak_db: float = -1.0) -> dict[str, Any]:
        return {
            "normalized_path": audio_path,
            "target_lufs": target_lufs,
            "achieved_lufs": target_lufs,
            "true_peak_db": true_peak_db,
            "achieved_true_peak_db": true_peak_db,
            "gain_applied_db": 0.0,
            "clipping_count": 0
        }
ZOOMING = "zoom"
