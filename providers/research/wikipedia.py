import random
import urllib.parse
from typing import Any
from providers.research.interface import KnowledgeProvider

class WikipediaKnowledgeProvider(KnowledgeProvider):
    """Mock Wikipedia Knowledge Provider simulating article searches and extractions."""

    @property
    def name(self) -> str:
        return "wikipedia"

    async def discover(self, topic: str) -> list[dict[str, Any]]:
        title_slug = topic.replace(" ", "_")
        results = [
            {
                "title": f"Wikipedia article on {topic}",
                "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title_slug)}",
                "snippet": f"{topic} on Wikipedia. It includes historical facts, academic classifications, and demographic statistics."
            }
        ]
        return results

    async def collect(self, discovery_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        collected = []
        for item in discovery_results:
            collected.append({
                **item,
                "raw_wiki": f"Wiki Content for {item['title']}. Academic overview, critical metrics, and bibliography references."
            })
        return collected

    async def extract(self, collected_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        extracted = []
        for item in collected_data:
            extracted.append({
                "title": item["title"],
                "url": item["url"],
                "summary": item["snippet"],
                "content": f"Wikipedia summary content for {item['title']}. Verified academic citations, statistical trends, and structural outlines of the topic history."
            })
        return extracted

    def rank(self, extracted_info: list[dict[str, Any]], topic: str) -> list[dict[str, Any]]:
        ranked = []
        for item in extracted_info:
            ranked.append({
                **item,
                "relevance_score": 0.95
            })
        return ranked
