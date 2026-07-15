import random
from typing import Any
from providers.voice.interface import VoiceProvider

class MockVoiceProvider(VoiceProvider):
    """Mock Voice Provider simulating TTS generation."""
    
    async def synthesize_speech(
        self,
        text: str,
        voice_id: str,
        emotional_tone: str,
        speaking_speed: float = 1.0,
        **kwargs: Any
    ) -> dict[str, Any]:
        voice_key = random.randint(1000, 9999)
        return {
            "storage_location": f"s3://aates-assets/audio/voice-{voice_key}.mp3",
            "cost": 0.05,
            "provider": "MockVoiceAI",
            "model": "TTS-Tamil-v1",
            "prompt_version": "v1.0.0",
            "checksum": f"sha256-mockvoice-{voice_key}"
        }
