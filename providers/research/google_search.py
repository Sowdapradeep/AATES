import random
import urllib.parse
from typing import Any
from providers.research.interface import KnowledgeProvider

class GoogleSearchKnowledgeProvider(KnowledgeProvider):
    """Mock Google Search Knowledge Provider generating rich, topic-relevant references."""

    @property
    def name(self) -> str:
        return "google_search"

    async def discover(self, topic: str) -> list[dict[str, Any]]:
        query_encoded = urllib.parse.quote_plus(topic)
        results = [
            {
                "title": f"Understanding the details of {topic}",
                "url": f"https://example.com/search?q={query_encoded}&page=1",
                "snippet": f"A comprehensive guide exploring the fundamentals, recent developments, and best practices of {topic}."
            },
            {
                "title": f"Top 10 trends in {topic} for 2026",
                "url": f"https://example.com/trends-{query_encoded}",
                "snippet": f"Analyze current statistics, industry impact, and future projections for {topic}."
            },
            {
                "title": f"Why {topic} matters in modern workflows",
                "url": f"https://example.org/articles/{query_encoded}",
                "snippet": f"A deep dive into industry challenges, user pain points, and strategic solutions concerning {topic}."
            }
        ]
        return results

    async def collect(self, discovery_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        collected = []
        for item in discovery_results:
            collected.append({
                **item,
                "raw_html": f"<html><body><h1>{item['title']}</h1><p>Main content body discussing {item['snippet']}</p></body></html>"
            })
        return collected

    async def extract(self, collected_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        extracted = []
        for item in collected_data:
            extracted.append({
                "title": item["title"],
                "url": item["url"],
                "summary": item["snippet"],
                "content": f"Full extracted text from {item['title']}. This is raw context about the topic. It details various aspects of hooks, stories, solutions, statistics, and potential visuals."
            })
        return extracted

    def rank(self, extracted_info: list[dict[str, Any]], topic: str) -> list[dict[str, Any]]:
        ranked = []
        for i, item in enumerate(extracted_info):
            score = 1.0 - (i * 0.15) - random.uniform(0.0, 0.05)
            ranked.append({
                **item,
                "relevance_score": round(max(0.1, score), 2)
            })
        # Sort by relevance_score descending
        ranked.sort(key=lambda x: x["relevance_score"], reverse=True)
        return ranked
