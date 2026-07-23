"""
LifelongMemoryStore — Persistent never-forget memory for the autonomous studio.

Stores:
  - Successful and failed prompts
  - Successful and failed universes
  - Successful and failed characters
  - Audience preferences
  - Production optimizations
  - Publishing optimizations

Memory grows continuously and is never reset.
Designed to be swappable to a database backend without changing the interface.
"""
import datetime
from typing import Any


class LifelongMemoryStore:
    """In-process persistent memory store (interface designed for DB migration)."""

    _CATEGORIES = [
        "successful_prompts",
        "failed_prompts",
        "successful_universes",
        "failed_universes",
        "successful_characters",
        "failed_characters",
        "audience_preferences",
        "production_optimizations",
        "publishing_optimizations",
    ]

    def __init__(self) -> None:
        self._memory: dict[str, list[dict[str, Any]]] = {cat: [] for cat in self._CATEGORIES}
        self._total_stored = 0

    def remember(self, category: str, entry: dict[str, Any]) -> None:
        """Store a memory in the specified category. Never overwrites."""
        if category not in self._memory:
            self._memory[category] = []
        self._memory[category].append({
            **entry,
            "stored_at": datetime.datetime.utcnow().isoformat(),
        })
        self._total_stored += 1

    def recall(self, category: str, limit: int = 10) -> list[dict[str, Any]]:
        """Recall the most recent entries in a category."""
        return self._memory.get(category, [])[-limit:]

    def recall_all(self) -> dict[str, list[dict[str, Any]]]:
        """Return full memory store."""
        return dict(self._memory)

    def search(self, keyword: str) -> list[dict[str, Any]]:
        """Search across all memory categories for a keyword."""
        results = []
        for entries in self._memory.values():
            for entry in entries:
                if keyword.lower() in str(entry).lower():
                    results.append(entry)
        return results

    def get_summary(self) -> dict[str, Any]:
        """Return counts across all memory categories."""
        return {
            "total_memories": self._total_stored,
            "categories": {cat: len(entries) for cat, entries in self._memory.items()},
        }

    def forget_category(self, category: str) -> int:
        """Clear a category (only for test isolation — never called in production)."""
        count = len(self._memory.get(category, []))
        self._memory[category] = []
        return count


# Module-level singleton — grows for lifetime of process
lifelong_memory = LifelongMemoryStore()
