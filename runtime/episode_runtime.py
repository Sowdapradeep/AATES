"""
runtime/episode_runtime.py — Isolated episode execution environment.

Each episode owns:
  - Story (prompt, outline, dialogue)
  - Memory (character state, world state)
  - Budget (per-episode cap)
  - Assets (images, audio, video)
  - Production Queue (scene tasks)
  - Quality State (scores per scene)

Failure in one episode NEVER impacts another.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("aros.episode_runtime")


class EpisodeRuntime:
    """Isolated runtime for a single episode production."""

    DEFAULT_BUDGET_USD = 1.5
    QUALITY_THRESHOLD = 80.0

    def __init__(self, episode_id: str | None = None, budget_usd: float | None = None) -> None:
        self.episode_id = episode_id or f"ep-{uuid.uuid4().hex[:8]}"
        self.budget_usd = budget_usd or self.DEFAULT_BUDGET_USD
        self.spent_usd: float = 0.0

        # Isolated state — no cross-episode references
        self.story: dict[str, Any] = {}
        self.memory: dict[str, Any] = {}
        self.assets: list[dict[str, Any]] = []
        self.production_queue: list[dict[str, Any]] = []
        self.quality_state: dict[str, float] = {}

        self.status = "initialised"
        self.created_at = datetime.now(timezone.utc)
        self.completed_at: datetime | None = None
        self.error: str | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def run(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Execute the episode. Returns final episode report."""
        self.status = "running"
        self.story = {"title": spec.get("title", f"Episode {self.episode_id}")}

        try:
            for scene in spec.get("scenes", []):
                # Block scene if budget is zero or would be exceeded
                if self.budget_usd <= 0 or self.spent_usd >= self.budget_usd:
                    logger.warning("Ep %s budget exhausted at scene %s",
                                   self.episode_id, scene.get("scene_id"))
                    break
                await self._execute_scene(scene)
        except Exception as exc:
            self.status = "failed"
            self.error = str(exc)
            logger.error("Episode %s failed: %s", self.episode_id, exc)
            return self._report()

        self.status = "done"
        self.completed_at = datetime.now(timezone.utc)
        logger.info("Episode %s complete — assets=%d spend=%.4f",
                    self.episode_id, len(self.assets), self.spent_usd)
        return self._report()

    async def _execute_scene(self, scene: dict[str, Any]) -> None:
        if self.budget_usd <= 0 or self.spent_usd >= self.budget_usd:
            return

        scene_id = scene.get("scene_id", uuid.uuid4().hex[:6])
        scene_type = scene.get("type", "generic")
        logger.debug("  Episode %s — scene %s (%s)", self.episode_id, scene_id, scene_type)

        # Simulate asset creation
        asset = {
            "asset_id": f"ast-{uuid.uuid4().hex[:6]}",
            "scene_id": scene_id,
            "type": scene_type,
            "status": "generated",
        }
        cost = 0.05
        self.assets.append(asset)
        self.spent_usd += cost
        self.quality_state[scene_id] = 85.0  # baseline quality

        self.production_queue.append({
            "scene_id": scene_id,
            "status": "done",
            "cost_usd": cost,
        })

    # ── Quality ───────────────────────────────────────────────────────────────

    @property
    def avg_quality(self) -> float:
        if not self.quality_state:
            return 0.0
        return round(sum(self.quality_state.values()) / len(self.quality_state), 2)

    def passed_quality(self) -> bool:
        return self.avg_quality >= self.QUALITY_THRESHOLD

    # ── Report ────────────────────────────────────────────────────────────────

    def _report(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "status": self.status,
            "quality_score": self.avg_quality,
            "cost_usd": round(self.spent_usd, 4),
            "budget_usd": self.budget_usd,
            "asset_count": len(self.assets),
            "scene_count": len(self.production_queue),
            "passed_quality": self.passed_quality(),
            "error": self.error,
        }
