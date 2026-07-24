"""
StrategicMemory — Long-term business strategy store for the AATES autonomous studio.

Captures accumulated strategic knowledge across all productions:
  - Successful and failed experiments
  - Cost optimization strategies
  - Publishing strategies
  - Model strategies
  - Universe performance history
  - CEO objectives and outcomes

This is distinct from episodic or semantic memory: it records the studio's
accumulated business strategy rather than specific content details.
"""
import datetime
from typing import Any


class StrategicMemory:
    """Persistent long-term strategic knowledge store."""

    def __init__(self) -> None:
        self._store: dict[str, list[dict[str, Any]]] = {
            "successful_experiments": [],
            "failed_experiments": [],
            "cost_optimizations": [],
            "publishing_strategies": [],
            "model_strategies": [],
            "universe_performance": [],
            "ceo_objectives": [],
            "budget_strategies": [],
            "prompt_strategies": [],
            "multi_month_trends": [],
        }

    def record(self, category: str, entry: dict[str, Any]) -> None:
        """Record a strategic memory entry in the specified category."""
        if category not in self._store:
            self._store[category] = []
        self._store[category].append({
            **entry,
            "recorded_at": datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat(),
        })

    def retrieve(self, category: str, limit: int = 20) -> list[dict[str, Any]]:
        """Retrieve the most recent entries in a strategy category."""
        return self._store.get(category, [])[-limit:]

    def retrieve_all(self) -> dict[str, list[dict[str, Any]]]:
        """Return full strategic memory store."""
        return dict(self._store)

    def summary(self) -> dict[str, Any]:
        """Return count summary across all categories."""
        return {cat: len(entries) for cat, entries in self._store.items()}

    def search(self, keyword: str) -> list[dict[str, Any]]:
        """Search all categories for entries containing a keyword."""
        results = []
        for entries in self._store.values():
            for entry in entries:
                if keyword.lower() in str(entry).lower():
                    results.append(entry)
        return results


# Module-level singleton
strategic_memory = StrategicMemory()
