import random
from typing import Any
from providers.music.interface import MusicProvider

class MockMusicProvider(MusicProvider):
    """Mock Music Provider simulating soundtrack generation."""
    
    async def generate_music(self, mood: str, duration: float, **kwargs: Any) -> dict[str, Any]:
        music_key = random.randint(1000, 9999)
        return {
            "storage_location": f"s3://aates-assets/audio/theme-{music_key}.mp3",
            "cost": 0.12,
            "provider": "MockMusicAI",
            "model": "Soundtrack-Gen-v2",
            "prompt_version": "v1.0.0",
            "checksum": f"sha256-mockmusic-{music_key}"
        }
