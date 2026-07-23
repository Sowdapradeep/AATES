from providers.video.interface import VideoProvider
from providers.video.ffmpeg import FFmpegVideoProvider
from providers.video.mock import MockVideoProvider

class VideoRegistry:
    """Registry managing active Video rendering composition engines."""

    def __init__(self) -> None:
        self._providers = {
            "ffmpeg": FFmpegVideoProvider(),
            "mock": MockVideoProvider()
        }

    def get_provider(self, name: str) -> VideoProvider | None:
        return self._providers.get(name)

    def get_all_providers(self) -> list[VideoProvider]:
        return list(self._providers.values())

    def register_provider(self, name: str, provider: VideoProvider) -> None:
        self._providers[name] = provider

video_registry = VideoRegistry()
