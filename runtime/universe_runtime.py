"""
runtime/universe_runtime.py — Independently evolving universe runtime.

Each universe owns:
  - Story Bible
  - Characters
  - Memories (episodic + semantic)
  - Goals
  - Budget
  - Assets
  - Analytics

Universes evolve independently. No universe shares mutable state with another.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("aros.universe_runtime")


class UniverseRuntime:
    """Isolated runtime for a single story universe."""

    def __init__(self, universe_id: str, name: str, seed_budget_usd: float = 10.0) -> None:
        self.universe_id = universe_id
        self.name = name
        self.budget_usd = seed_budget_usd
        self.spent_usd: float = 0.0

        # Isolated universe state
        self.story_bible: dict[str, Any] = {
            "universe_id": universe_id,
            "name": name,
            "lore": [],
            "themes": [],
            "setting": {},
        }
        self.characters: dict[str, dict[str, Any]] = {}
        self.memories: list[dict[str, Any]] = []
        self.goals: list[dict[str, Any]] = []
        self.assets: list[dict[str, Any]] = []
        self.analytics: dict[str, Any] = {
            "episodes_produced": 0,
            "avg_quality": 0.0,
            "avg_retention_pct": 0.0,
            "engagement_score": 0.0,
        }

        self.created_at = datetime.now(timezone.utc).isoformat()
        self.last_evolved_at: str | None = None

    # ── Characters ────────────────────────────────────────────────────────────

    def add_character(self, name: str, role: str, traits: list[str]) -> str:
        char_id = f"chr-{uuid.uuid4().hex[:6]}"
        self.characters[char_id] = {
            "char_id": char_id,
            "name": name,
            "role": role,
            "traits": traits,
            "episodes_featured": 0,
            "status": "active",
        }
        logger.info("Universe %s — character added: %s (%s)", self.universe_id, name, role)
        return char_id

    def retire_character(self, char_id: str) -> bool:
        if char_id in self.characters:
            self.characters[char_id]["status"] = "retired"
            logger.info("Universe %s — character retired: %s", self.universe_id, char_id)
            return True
        return False

    # ── Goals ─────────────────────────────────────────────────────────────────

    def add_goal(self, goal: dict[str, Any]) -> None:
        self.goals.append({**goal, "universe_id": self.universe_id})

    def get_active_goals(self) -> list[dict[str, Any]]:
        return [g for g in self.goals if g.get("status") == "active"]

    # ── Analytics ─────────────────────────────────────────────────────────────

    def record_episode(self, quality: float, retention_pct: float, cost_usd: float) -> None:
        n = self.analytics["episodes_produced"]
        self.analytics["avg_quality"] = round(
            (self.analytics["avg_quality"] * n + quality) / (n + 1), 2)
        self.analytics["avg_retention_pct"] = round(
            (self.analytics["avg_retention_pct"] * n + retention_pct) / (n + 1), 2)
        self.analytics["episodes_produced"] = n + 1
        self.spent_usd += cost_usd
        self.memories.append({
            "type": "episode_completed",
            "quality": quality,
            "retention_pct": retention_pct,
            "cost_usd": cost_usd,
            "at": datetime.now(timezone.utc).isoformat(),
        })

    # ── Evolution ─────────────────────────────────────────────────────────────

    def evolve(self, directive: dict[str, Any]) -> str:
        """Apply an evolution directive from the UniverseEvolutionEngine."""
        action = directive.get("action", "expand_lore")
        self.story_bible["lore"].append({
            "action": action,
            "payload": directive.get("payload", {}),
            "at": datetime.now(timezone.utc).isoformat(),
        })
        self.last_evolved_at = datetime.now(timezone.utc).isoformat()
        logger.info("Universe %s evolved: %s", self.universe_id, action)
        return action

    # ── Snapshot ──────────────────────────────────────────────────────────────

    def snapshot(self) -> dict[str, Any]:
        return {
            "universe_id": self.universe_id,
            "name": self.name,
            "budget_usd": self.budget_usd,
            "spent_usd": round(self.spent_usd, 4),
            "character_count": len(self.characters),
            "active_characters": sum(1 for c in self.characters.values() if c["status"] == "active"),
            "active_goals": len(self.get_active_goals()),
            "analytics": self.analytics,
            "lore_events": len(self.story_bible["lore"]),
            "last_evolved_at": self.last_evolved_at,
        }


class UniverseRegistry:
    """Registry of all active universe runtimes."""

    def __init__(self) -> None:
        self._universes: dict[str, UniverseRuntime] = {}

    def create(self, name: str, budget_usd: float = 10.0) -> UniverseRuntime:
        u_id = f"u-{uuid.uuid4().hex[:8]}"
        universe = UniverseRuntime(u_id, name, budget_usd)
        self._universes[u_id] = universe
        logger.info("Universe created: %s (%s)", u_id, name)
        return universe

    def get(self, universe_id: str) -> UniverseRuntime | None:
        return self._universes.get(universe_id)

    def get_all(self) -> list[dict[str, Any]]:
        return [u.snapshot() for u in self._universes.values()]

    def count(self) -> int:
        return len(self._universes)


universe_registry = UniverseRegistry()
