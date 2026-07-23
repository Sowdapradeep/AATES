from providers.script.interface import ScriptProvider
from providers.script.bedrock import BedrockScriptProvider
from providers.script.mock import MockScriptProvider

class ScriptRegistry:
    """Registry managing active Script Generation LLM engine providers."""

    def __init__(self) -> None:
        self._providers = {
            "bedrock": BedrockScriptProvider(),
            "mock": MockScriptProvider()
        }

    def get_provider(self, name: str) -> ScriptProvider | None:
        return self._providers.get(name)

    def get_all_providers(self) -> list[ScriptProvider]:
        return list(self._providers.values())

    def register_provider(self, name: str, provider: ScriptProvider) -> None:
        self._providers[name] = provider

script_registry = ScriptRegistry()
