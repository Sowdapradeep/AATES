from typing import Any, List

class MusicProvider:
    """Abstract interface contract for all AI Music engines."""

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def capabilities(self) -> List[str]:
        return ["music_selection", "audio_mixing", "ducking", "loudness_normalization"]

    def supports_ducking(self) -> bool:
        return True

    def supports_generation(self) -> bool:
        return False

    def supports_normalization(self) -> bool:
        return True

    async def select_music(self, script_pkg: Any, scene_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Select or map appropriate music tracks and cues for scenes based on mood/genre/energy/tempo."""
        raise NotImplementedError

    async def generate_music(self, prompt: str, duration_ms: int, options: dict[str, Any]) -> dict[str, Any]:
        """Synthesize new background music track using generative models."""
        raise NotImplementedError

    async def analyze_music(self, audio_path: str) -> dict[str, Any]:
        """Analyze peak, LUFS, RMS, tempo, key, silence regions, and waveform points."""
        raise NotImplementedError

    async def mix_audio(self, music_cues: list[dict[str, Any]], narration_path: str, profile: dict[str, Any]) -> dict[str, Any]:
        """Combine music cues with narration track applying ducking envelopes and volume automation."""
        raise NotImplementedError

    async def normalize(self, audio_path: str, target_lufs: float = -14.0, true_peak_db: float = -1.0) -> dict[str, Any]:
        """Normalize audio file to target platform LUFS and True Peak limits."""
        raise NotImplementedError
ZOOMING = "zoom"
