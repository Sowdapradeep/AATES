import logging
import random
import os
from typing import Any, List
import httpx
from providers.registry import BaseProvider
from providers.music.interface import MusicProvider
from core.config.settings import settings

logger = logging.getLogger("stability_music")

class StabilityMusicProvider(BaseProvider, MusicProvider):
    """Production Stability Audio Music Provider with local backup file saver."""

    @property
    def name(self) -> str:
        return "StabilityAudio"

    @property
    def capabilities(self) -> List[str]:
        return ["music_generation", "ambient_sound"]

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.ai.stability_api_key
        self.cost_per_generation = 0.12

    async def generate_music(self, mood: str, duration: float, **kwargs: Any) -> dict[str, Any]:
        """Generate ambient music backtracks matching current scene mood parameters."""
        music_key = random.randint(1000, 9999)
        
        if not self.api_key or self.api_key == "mock" or settings.app.env == "testing":
            logger.info("Stability Audio API Key not configured. Returning Mock Music track.")
            return {
                "storage_location": f"file:///{os.path.abspath(f'./storage/audio/theme-{music_key}.mp3')}",
                "cost": self.cost_per_generation,
                "provider": "StabilityAudio",
                "model": "StabilityAudio-v1-Mock",
                "prompt_version": "v1.0.0",
                "checksum": f"sha256-mockmusic-{music_key}"
            }

        # Live Stability Audio REST Call
        url = "https://api.stability.ai/v2beta/stable-audio/generate"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "audio/mpeg"
        }
        
        payload = {
            "prompt": f"Ambient background track, mood: {mood}, soundtrack style",
            "duration_seconds": duration
        }

        timeout = httpx.Timeout(45.0, connect=15.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            audio_bytes = response.content
            
            output_dir = "./storage/audio"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"theme-{music_key}.mp3")
            
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
                
            import hashlib
            checksum = hashlib.sha256(audio_bytes).hexdigest()
            abs_path = os.path.abspath(output_path)
            
            logger.info(f"Stability Audio generated soundtrack saved to {abs_path}")
            return {
                "storage_location": f"file:///{abs_path}",
                "cost": self.cost_per_generation,
                "provider": "StabilityAudio",
                "model": "stable-audio-v1.0",
                "prompt_version": "v1.0.0",
                "checksum": f"sha256-{checksum[:16]}"
            }
