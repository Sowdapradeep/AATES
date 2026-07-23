from providers.voice.interface import VoiceProvider
from providers.voice.bedrock import BedrockVoiceProvider
from providers.voice.mock import MockVoiceProvider
from providers.voice.elevenlabs_provider import ElevenLabsVoiceProvider

class VoiceRegistry:
    """Registry managing active Voice Generation engines."""

    def __init__(self) -> None:
        self._providers = {
            "bedrock": BedrockVoiceProvider(),
            "mock": MockVoiceProvider(),
            "elevenlabs": ElevenLabsVoiceProvider()
        }

    def get_provider(self, name: str) -> VoiceProvider | None:
        return self._providers.get(name)

    def get_all_providers(self) -> list[VoiceProvider]:
        return list(self._providers.values())

    def register_provider(self, name: str, provider: VoiceProvider) -> None:
        self._providers[name] = provider

voice_registry = VoiceRegistry()
