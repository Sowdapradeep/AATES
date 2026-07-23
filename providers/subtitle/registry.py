from providers.subtitle.interface import SubtitleProvider
from providers.subtitle.alignment import AlignmentSubtitleProvider
from providers.subtitle.mock import MockSubtitleProvider

class SubtitleRegistry:
    """Registry managing AI Subtitle generation engines."""

    def __init__(self) -> None:
        self._providers = {
            "alignment": AlignmentSubtitleProvider(),
            "mock": MockSubtitleProvider()
        }

    def get_provider(self, name: str) -> SubtitleProvider | None:
        return self._providers.get(name)

    def get_all_providers(self) -> list[SubtitleProvider]:
        return list(self._providers.values())

    def register_provider(self, name: str, provider: SubtitleProvider) -> None:
        self._providers[name] = provider

subtitle_registry = SubtitleRegistry()
