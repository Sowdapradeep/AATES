import random
from typing import Any
from providers.registry import BaseProvider
from providers.rendering.interface import RenderingProvider
from core.config import settings

class MockRenderingProvider(BaseProvider, RenderingProvider):
    """Mock Rendering Provider simulating FFmpeg mixes and concatenations."""

    @property
    def name(self) -> str:
        return "MockFFmpeg"

    @property
    def capabilities(self) -> list[str]:
        return ["ffmpeg_rendering", "scene_mixing"]
    
    async def mix_scene_assets(
        self,
        video_location: str,
        audio_locations: list[str],
        subtitle_location: str | None = None,
        **kwargs: Any
    ) -> dict[str, Any]:
        mix_key = random.randint(1000, 9999)
        return {
            "storage_location": f"s3://{settings.aws.s3_bucket}/renders/scene-mix-{mix_key}.mp4",
            "cost": 0.08,
            "provider": "MockFFmpeg",
            "model": "FFmpeg-CLI-Wrapper",
            "prompt_version": "v1.0.0",
            "checksum": f"sha256-mockmix-{mix_key}"
        }

    async def concatenate_scenes(self, scene_video_locations: list[str], **kwargs: Any) -> dict[str, Any]:
        reel_key = random.randint(1000, 9999)
        return {
            "storage_location": f"s3://{settings.aws.s3_bucket}/reels/master-reel-{reel_key}.mp4",
            "cost": 0.15,
            "provider": "MockFFmpeg",
            "model": "FFmpeg-CLI-Wrapper",
            "prompt_version": "v1.0.0",
            "checksum": f"sha256-mockreel-{reel_key}"
        }
