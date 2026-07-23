from providers.quality.interface import QualityProvider
from providers.quality.engine import LocalPolicyQualityProvider
from providers.quality.mock import MockQualityProvider

class QualityRegistry:
    """Registry managing AI Quality & Governance engines."""

    def __init__(self) -> None:
        self._providers = {
            "policy_engine": LocalPolicyQualityProvider(),
            "mock": MockQualityProvider()
        }

    def get_provider(self, name: str) -> QualityProvider | None:
        return self._providers.get(name)

    def get_all_providers(self) -> list[QualityProvider]:
        return list(self._providers.values())

    def register_provider(self, name: str, provider: QualityProvider) -> None:
        self._providers[name] = provider

quality_registry = QualityRegistry()
