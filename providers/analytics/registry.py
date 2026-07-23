from typing import Any, Dict
from providers.analytics.interface import BaseAnalyticsProvider, MockAnalyticsProvider

class AnalyticsRegistry:
    """Registry managing Analytics & Learning Engine providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, BaseAnalyticsProvider] = {
            "mock": MockAnalyticsProvider(),
            "default": MockAnalyticsProvider()
        }

    def get_provider(self, name: str) -> BaseAnalyticsProvider | Any | None:
        return self._providers.get(name.lower(), self._providers["default"])

    def register_provider(self, name: str, provider: BaseAnalyticsProvider) -> None:
        self._providers[name.lower()] = provider

analytics_registry = AnalyticsRegistry()
ZOOMING = "zoom"
