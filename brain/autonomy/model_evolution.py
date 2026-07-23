"""
ModelEvolutionTracker — Dynamic model ranking engine wrapping the Phase 10 ModelRouter.

Tracks per model:
  - quality (avg score across invocations)
  - cost (cumulative and per-invocation)
  - latency (actual vs expected)
  - failures and retries
  - hallucination rate (flagged by critics)

Model rankings update dynamically. Best model per task type selected automatically.
Updates are submitted to the AutonomousDecisionEngine, not applied directly.
"""
import datetime
from typing import Any

from brain.autonomy.decision_engine import AutonomousDecisionEngine, Recommendation
from brain.autonomy.strategic_memory import strategic_memory


class ModelStats:
    def __init__(self, model_id: str) -> None:
        self.model_id = model_id
        self.invocations = 0
        self.total_quality = 0.0
        self.total_cost = 0.0
        self.total_latency_ms = 0.0
        self.failures = 0
        self.retries = 0
        self.hallucination_flags = 0
        self.ranking_weight = 1.0

    @property
    def avg_quality(self) -> float:
        return round(self.total_quality / self.invocations, 2) if self.invocations else 0.0

    @property
    def avg_cost(self) -> float:
        return round(self.total_cost / self.invocations, 6) if self.invocations else 0.0

    @property
    def avg_latency_ms(self) -> float:
        return round(self.total_latency_ms / self.invocations, 1) if self.invocations else 0.0

    @property
    def failure_rate(self) -> float:
        return round(self.failures / self.invocations, 3) if self.invocations else 0.0

    @property
    def hallucination_rate(self) -> float:
        return round(self.hallucination_flags / self.invocations, 3) if self.invocations else 0.0

    def composite_score(self) -> float:
        """Higher is better. Penalises failures and hallucinations."""
        if self.invocations == 0:
            return 0.5
        quality_norm = self.avg_quality / 100.0
        failure_penalty = self.failure_rate * 0.3
        hallucination_penalty = self.hallucination_rate * 0.4
        return max(0.0, round(quality_norm - failure_penalty - hallucination_penalty, 4))

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "invocations": self.invocations,
            "avg_quality": self.avg_quality,
            "avg_cost_usd": self.avg_cost,
            "avg_latency_ms": self.avg_latency_ms,
            "failure_rate": self.failure_rate,
            "hallucination_rate": self.hallucination_rate,
            "composite_score": self.composite_score(),
            "ranking_weight": self.ranking_weight,
        }


class ModelEvolutionTracker:
    """Tracks model performance and dynamically adjusts routing weights."""

    def __init__(self, decision_engine: AutonomousDecisionEngine) -> None:
        self.decision_engine = decision_engine
        self._stats: dict[str, ModelStats] = {}

    def _get_or_create(self, model_id: str) -> ModelStats:
        if model_id not in self._stats:
            self._stats[model_id] = ModelStats(model_id)
        return self._stats[model_id]

    def record_invocation(
        self,
        model_id: str,
        quality: float,
        cost_usd: float,
        latency_ms: float,
        failed: bool = False,
        retry: bool = False,
        hallucination: bool = False,
    ) -> None:
        """Record a Bedrock model invocation result."""
        stats = self._get_or_create(model_id)
        stats.invocations += 1
        stats.total_quality += quality
        stats.total_cost += cost_usd
        stats.total_latency_ms += latency_ms
        if failed:
            stats.failures += 1
        if retry:
            stats.retries += 1
        if hallucination:
            stats.hallucination_flags += 1

        # Recompute ranking weight
        stats.ranking_weight = round(stats.composite_score() * 2.0, 3)

        # Submit recommendation if model is underperforming
        if stats.invocations >= 5 and stats.composite_score() < 0.5:
            strategic_memory.record("model_strategies", {
                "model_id": model_id, "action": "deprioritize",
                "composite_score": stats.composite_score(),
            })
            self.decision_engine.submit(Recommendation(
                source="ModelEvolutionTracker",
                priority="optimization",
                action="deprioritize_model",
                target="model_router",
                payload={"model_id": model_id, "new_weight": stats.ranking_weight},
                estimated_impact=3.0,
            ))

    def get_rankings(self) -> list[dict[str, Any]]:
        """Return models sorted by composite score descending."""
        return sorted(
            [s.to_dict() for s in self._stats.values()],
            key=lambda m: m["composite_score"],
            reverse=True,
        )

    def best_model_for_task(self, capability: str) -> str | None:
        """Return the highest-ranked model that supports a given capability."""
        from brain.production.model_router import _MODEL_CATALOGUE
        eligible = [m["model_id"] for m in _MODEL_CATALOGUE if capability in m["capabilities"]]
        ranked = [s for s in self.get_rankings() if s["model_id"] in eligible]
        return ranked[0]["model_id"] if ranked else None
