"""
ContinuousLearningEngine — Updates all studio knowledge libraries after every episode.

Learns from:
  - Story Bible (narrative patterns)
  - Character Memory (personality consistency)
  - Universe Memory (lore continuity)
  - Prompt Library (generation quality)
  - Asset Library (reuse patterns)
  - Model Performance Statistics

Poor-performing strategies lose priority weight.
Successful strategies gain priority weight.

All updates are submitted as recommendations to the AutonomousDecisionEngine.
"""
import datetime
from typing import Any

from brain.autonomy.decision_engine import AutonomousDecisionEngine, Recommendation
from brain.autonomy.strategic_memory import strategic_memory


class ContinuousLearningEngine:
    """Learns from every episode and submits strategic updates."""

    def __init__(self, decision_engine: AutonomousDecisionEngine) -> None:
        self.decision_engine = decision_engine
        self._prompt_weights: dict[str, float] = {}
        self._model_weights: dict[str, float] = {}
        self._universe_scores: dict[str, float] = {}
        self._character_scores: dict[str, float] = {}
        self._episode_history: list[dict[str, Any]] = []

    def record_episode_outcome(self, episode_data: dict[str, Any]) -> None:
        """Ingest episode result and update all knowledge libraries."""
        self._episode_history.append({
            **episode_data,
            "recorded_at": datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat(),
        })

        quality = episode_data.get("quality_score", 80.0)
        universe_id = episode_data.get("universe_id", "default")
        model_used = episode_data.get("primary_model", "")
        prompt_id = episode_data.get("prompt_id", "")

        # ── 1. Update prompt priority weights ────────────────────────────────
        if prompt_id:
            current = self._prompt_weights.get(prompt_id, 1.0)
            if quality >= 85.0:
                self._prompt_weights[prompt_id] = min(current * 1.1, 3.0)
                strategic_memory.record("prompt_strategies", {
                    "prompt_id": prompt_id,
                    "action": "weight_increased",
                    "new_weight": self._prompt_weights[prompt_id],
                    "quality": quality,
                })
            elif quality < 70.0:
                self._prompt_weights[prompt_id] = max(current * 0.8, 0.1)
                strategic_memory.record("failed_experiments", {
                    "prompt_id": prompt_id,
                    "action": "weight_decreased",
                    "new_weight": self._prompt_weights[prompt_id],
                    "quality": quality,
                })

        # ── 2. Update model performance weights ──────────────────────────────
        if model_used:
            current = self._model_weights.get(model_used, 1.0)
            if quality >= 85.0:
                self._model_weights[model_used] = min(current * 1.05, 2.0)
            else:
                self._model_weights[model_used] = max(current * 0.95, 0.2)
            strategic_memory.record("model_strategies", {
                "model_id": model_used,
                "new_weight": self._model_weights[model_used],
                "quality": quality,
            })

        # ── 3. Update universe performance scores ────────────────────────────
        prev = self._universe_scores.get(universe_id, quality)
        self._universe_scores[universe_id] = round((prev + quality) / 2, 2)

        # ── 4. Submit prompt library update recommendation ───────────────────
        if prompt_id and quality < 70.0:
            self.decision_engine.submit(Recommendation(
                source="ContinuousLearningEngine",
                priority="creative",
                action="retire_weak_prompt",
                target="prompt_library",
                payload={"prompt_id": prompt_id, "score": quality},
                estimated_impact=3.0,
            ))

        # ── 5. Submit model router weight recommendation ─────────────────────
        if model_used and quality >= 88.0:
            self.decision_engine.submit(Recommendation(
                source="ContinuousLearningEngine",
                priority="optimization",
                action="boost_model_priority",
                target="model_router",
                payload={"model_id": model_used, "weight": self._model_weights.get(model_used, 1.0)},
                estimated_impact=2.5,
            ))

    def get_learning_summary(self) -> dict[str, Any]:
        """Return current learning state statistics."""
        return {
            "episodes_processed": len(self._episode_history),
            "prompt_weights": dict(self._prompt_weights),
            "model_weights": dict(self._model_weights),
            "universe_avg_scores": dict(self._universe_scores),
            "high_priority_prompts": [
                pid for pid, w in self._prompt_weights.items() if w >= 1.5
            ],
            "low_priority_prompts": [
                pid for pid, w in self._prompt_weights.items() if w <= 0.3
            ],
        }
