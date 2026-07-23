from typing import Any
from providers.publishing.interface import PublishProvider
from providers.publishing.youtube import YouTubePublisher
from providers.publishing.instagram import InstagramPublishingProvider
from providers.publishing.mock import MockInstagramPublisher

class PublishingRegistry:
    """Registry managing multi-platform publishing providers."""

    def __init__(self) -> None:
        self._providers = {
            "youtube": YouTubePublisher(),
            "instagram": InstagramPublishingProvider(),
            "mock": MockInstagramPublisher()
        }

    def get_provider(self, name: str) -> PublishProvider | Any | None:
        return self._providers.get(name.lower())

    def get_all_providers(self) -> list[Any]:
        return list(self._providers.values())

    def register_provider(self, name: str, provider: Any) -> None:
        self._providers[name.lower()] = provider

publishing_registry = PublishingRegistry()
