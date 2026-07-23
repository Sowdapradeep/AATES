from providers.music.interface import MusicProvider
from providers.music.library import LocalLibraryMusicProvider
from providers.music.mock import MockMusicProvider

class MusicRegistry:
    """Registry managing AI Music engines."""

    def __init__(self) -> None:
        self._providers = {
            "library": LocalLibraryMusicProvider(),
            "mock": MockMusicProvider()
        }

    def get_provider(self, name: str) -> MusicProvider | None:
        return self._providers.get(name)

    def get_all_providers(self) -> list[MusicProvider]:
        return list(self._providers.values())

    def register_provider(self, name: str, provider: MusicProvider) -> None:
        self._providers[name] = provider

music_registry = MusicRegistry()
