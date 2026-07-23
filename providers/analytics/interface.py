from abc import ABC, abstractmethod
from typing import Any, Dict, List
from providers.analytics.feature_store import FeatureVector

class BaseAnalyticsProvider(ABC):
    """Abstract Base Class for Analytics & Learning Providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Canonical provider identifier."""

    @abstractmethod
    async def evaluate_learning(
        self, 
        feature_vectors: List[FeatureVector], 
        target_platform: str = "all"
    ) -> Dict[str, Any]:
        """Execute learning evaluation and return structured metrics, signals, and recommendations."""

class MockAnalyticsProvider(BaseAnalyticsProvider):
    """Mock Analytics Provider simulating statistical correlation and pattern discovery."""

    @property
    def name(self) -> str:
        return "mock_analytics_provider"

    async def evaluate_learning(
        self, 
        feature_vectors: List[FeatureVector], 
        target_platform: str = "all"
    ) -> Dict[str, Any]:
        from providers.analytics.engine import analytics_engine
        return await analytics_engine.execute_learning_analysis(feature_vectors, target_platform)
ZOOMING = "zoom"
