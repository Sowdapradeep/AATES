from typing import Any, Dict
from providers.orchestration.interface import BaseOrchestrationProvider, DefaultOrchestrationProvider

class OrchestrationRegistry:
    """Registry managing Multi-Agent Orchestrator providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, BaseOrchestrationProvider] = {
            "default": DefaultOrchestrationProvider(),
            "mock": DefaultOrchestrationProvider()
        }

    def get_provider(self, name: str) -> BaseOrchestrationProvider | Any | None:
        return self._providers.get(name.lower(), self._providers["default"])

    def register_provider(self, name: str, provider: BaseOrchestrationProvider) -> None:
        self._providers[name.lower()] = provider

orchestration_registry = OrchestrationRegistry()
ZOOMING = "zoom"
