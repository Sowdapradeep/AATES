from typing import Any, List

class VoiceProvider:
    """Abstract interface contract for all downstream Text-to-Speech (Voice) providers."""

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def capabilities(self) -> List[str]:
        return ["voice_generation"]

    async def generate(self, text: str, voice_id: str, options: dict[str, Any]) -> dict[str, Any]:
        """Synthesize text speech narration, returning duration_ms, audio file path, alignments, etc."""
        raise NotImplementedError

    async def regenerate(self, text: str, voice_id: str, options: dict[str, Any]) -> dict[str, Any]:
        """Regenerate narration scene with adjusted SSML speed/pitch or settings."""
        raise NotImplementedError

    async def clone_voice(self, audio_file_path: str, name: str) -> str:
        """Create a custom cloned speaker profile from sample file, returning cloned voice_id."""
        raise NotImplementedError

    async def align(self, audio_file_path: str, text: str) -> dict[str, Any]:
        """Align narration text to synthesized audio file, returning millisecond alignments."""
        raise NotImplementedError

    # ── Legacy Compatibility ─────────────────────────────────────────────────
    async def synthesize_speech(
        self,
        text: str,
        voice_id: str,
        emotional_tone: str,
        speaking_speed: float = 1.0,
        **kwargs: Any
    ) -> dict[str, Any]:
        """Legacy synthesis function mapping to generate."""
        options = {
            "emotion": emotional_tone,
            "speed": f"{speaking_speed}x"
        }
        res = await self.generate(text, voice_id, options)
        return {
            "storage_location": f"file:///{res['local_path']}",
            "cost": res.get("cost", 0.05),
            "provider": self.name,
            "model": res.get("model", "TTS-Model"),
            "prompt_version": "v1.0.0",
            "checksum": f"sha255-{res['storage_key'][-12:]}"
        }
