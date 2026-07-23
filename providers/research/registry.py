from providers.research.interface import KnowledgeProvider
from providers.research.google_search import GoogleSearchKnowledgeProvider
from providers.research.wikipedia import WikipediaKnowledgeProvider

class KnowledgeRegistry:
    """Registry managing list of active knowledge acquisition providers."""

    def __init__(self) -> None:
        self._providers = {
            "google_search": GoogleSearchKnowledgeProvider(),
            "wikipedia": WikipediaKnowledgeProvider()
        }

    def get_provider(self, name: str) -> KnowledgeProvider | None:
        return self._providers.get(name)

    def get_all_providers(self) -> list[KnowledgeProvider]:
        return list(self._providers.values())

    def register_provider(self, name: str, provider: KnowledgeProvider) -> None:
        self._providers[name] = provider

knowledge_registry = KnowledgeRegistry()
