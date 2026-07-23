from providers.image.interface import ImageProvider
from providers.image.bedrock import BedrockImageProvider
from providers.image.gemini import GeminiImageProvider
from providers.image.pollinations import PollinationsImageProvider
from providers.image.mock import MockImageProvider

class ImageRegistry:
    """Registry managing active Image Generation engines."""

    def __init__(self) -> None:
        self._providers = {
            "bedrock": BedrockImageProvider(),
            "gemini": GeminiImageProvider(),
            "pollinations": PollinationsImageProvider(),
            "mock": MockImageProvider()
        }

    def get_provider(self, name: str) -> ImageProvider | None:
        return self._providers.get(name)

    def get_all_providers(self) -> list[ImageProvider]:
        return list(self._providers.values())

    def register_provider(self, name: str, provider: ImageProvider) -> None:
        self._providers[name] = provider

image_registry = ImageRegistry()
