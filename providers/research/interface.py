from typing import Any

class KnowledgeProvider:
    """Base class for all knowledge retrieval sources."""

    @property
    def name(self) -> str:
        raise NotImplementedError

    async def discover(self, topic: str) -> list[dict[str, Any]]:
        """Identify candidate reference targets or URLs for a topic."""
        raise NotImplementedError

    async def collect(self, discovery_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Retrieve raw data or document bodies from discovered targets."""
        raise NotImplementedError

    async def extract(self, collected_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Parse clean text snippets and structure information."""
        raise NotImplementedError

    def rank(self, extracted_info: list[dict[str, Any]], topic: str) -> list[dict[str, Any]]:
        """Remove duplicates and evaluate relevance scores relative to target topic."""
        raise NotImplementedError
