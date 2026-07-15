from abc import ABC, abstractmethod
from typing import Any

class RenderingProvider(ABC):
    """Abstract interface contract for rendering video-audio mixes and concatenations (FFmpeg)."""
    
    @abstractmethod
    async def mix_scene_assets(
        self,
        video_location: str,
        audio_locations: list[str],
        subtitle_location: str | None = None,
        **kwargs: Any
    ) -> dict[str, Any]:
        """Mixes video segment with multiple synchronized voice/music audio tracks and overlays subtitles."""
        pass

    @abstractmethod
    async def concatenate_scenes(self, scene_video_locations: list[str], **kwargs: Any) -> dict[str, Any]:
        """Concatenates completed scene packages video clips into a single Master Reel video file."""
        pass
