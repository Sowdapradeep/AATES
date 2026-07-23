from typing import Any, Dict
from providers.automation.interface import BaseAutomationProvider, DefaultAutomationProvider

class AutomationRegistry:
    """Registry managing Automation Engine providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, BaseAutomationProvider] = {
            "default": DefaultAutomationProvider(),
            "mock": DefaultAutomationProvider()
        }

    def get_provider(self, name: str) -> BaseAutomationProvider | Any | None:
        return self._providers.get(name.lower(), self._providers["default"])

    def register_provider(self, name: str, provider: BaseAutomationProvider) -> None:
        self._providers[name.lower()] = provider

automation_registry = AutomationRegistry()
ZOOMING = "zoom"
