import random
from typing import Any
from providers.video.interface import VideoProvider

class MockVideoProvider(VideoProvider):
    """Mock Video Provider simulating clip generation."""
    
    async def generate_video(self, image_location: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        clip_id = random.randint(1000, 9999)
        return {
            "storage_location": f"s3://aates-assets/videos/clip-{clip_id}.mp4",
            "seed": clip_id,
            "cost": 0.25,
            "provider": "MockVideoAI",
            "model": "Clip-Motion-v2",
            "prompt_version": "v1.0.0",
            "checksum": f"sha256-mockvideo-{clip_id}"
        }
