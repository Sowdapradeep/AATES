from providers.thumbnail.interface import ThumbnailProvider
from providers.thumbnail.template import LocalTemplateThumbnailProvider
from providers.thumbnail.mock import MockThumbnailProvider

class ThumbnailRegistry:
    """Registry managing AI Thumbnail engines."""

    def __init__(self) -> None:
        self._providers = {
            "template": LocalTemplateThumbnailProvider(),
            "mock": MockThumbnailProvider()
        }

    def get_provider(self, name: str) -> ThumbnailProvider | None:
        return self._providers.get(name)

    def get_all_providers(self) -> list[ThumbnailProvider]:
        return list(self._providers.values())

    def register_provider(self, name: str, provider: ThumbnailProvider) -> None:
        self._providers[name] = provider

thumbnail_registry = ThumbnailRegistry()
