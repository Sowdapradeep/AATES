"""
ProductionOptimizer — Continuously optimizes render order, queue priority,
asset reuse, caching, Bedrock routing, and AWS costs.

Learns from episode timing histories to make future runs faster and cheaper.
Submits all changes via the AutonomousDecisionEngine.
"""
import datetime
from typing import Any

from brain.autonomy.decision_engine import AutonomousDecisionEngine, Recommendation
from brain.autonomy.strategic_memory import strategic_memory


class ProductionOptimizer:
    """Autonomous production efficiency optimizer."""

    def __init__(self, decision_engine: AutonomousDecisionEngine) -> None:
        self.decision_engine = decision_engine
        self._render_history: list[dict[str, Any]] = []
        self._reuse_hits = 0
        self._reuse_misses = 0

    def record_render(
        self,
        episode_id: str,
        render_time_sec: float,
        cost_usd: float,
        asset_reuse_hits: int,
        asset_reuse_misses: int,
    ) -> None:
        """Record episode render statistics and submit optimization recommendations."""
        self._render_history.append({
            "episode_id": episode_id,
            "render_time_sec": render_time_sec,
            "cost_usd": cost_usd,
            "asset_reuse_hits": asset_reuse_hits,
            "recorded_at": datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat(),
        })
        self._reuse_hits += asset_reuse_hits
        self._reuse_misses += asset_reuse_misses

        # Compute reuse hit rate
        total = self._reuse_hits + self._reuse_misses
        hit_rate = self._reuse_hits / total if total else 0.0

        # Submit queue priority optimization if render time is high
        if render_time_sec > 60.0:
            self.decision_engine.submit(Recommendation(
                source="ProductionOptimizer",
                priority="optimization",
                action="reorder_render_queue",
                target="production_queue",
                payload={"strategy": "shortest_first", "episode_id": episode_id},
                estimated_impact=3.0,
            ))

        # Submit cache warming if reuse rate is low
        if hit_rate < 0.4 and total >= 5:
            self.decision_engine.submit(Recommendation(
                source="ProductionOptimizer",
                priority="optimization",
                action="warm_asset_cache",
                target="asset_library",
                payload={"top_n_assets": 20, "strategy": "preload_common_scenes"},
                estimated_impact=2.5,
            ))
            strategic_memory.record("cost_optimizations", {
                "action": "warm_asset_cache", "hit_rate_before": hit_rate,
            })

        # Submit Bedrock routing optimization if cost is high
        if cost_usd > 1.5:
            self.decision_engine.submit(Recommendation(
                source="ProductionOptimizer",
                priority="business",
                action="switch_to_economy_routing",
                target="model_router",
                payload={"prefer_economy": True, "cost_trigger_usd": cost_usd},
                estimated_impact=5.0,
            ))

    def get_optimization_summary(self) -> dict[str, Any]:
        total = self._reuse_hits + self._reuse_misses
        return {
            "episodes_optimized": len(self._render_history),
            "asset_reuse_hit_rate": round(self._reuse_hits / total, 3) if total else 0.0,
            "avg_render_time_sec": round(
                sum(r["render_time_sec"] for r in self._render_history) / len(self._render_history), 1
            ) if self._render_history else 0.0,
            "avg_cost_per_episode_usd": round(
                sum(r["cost_usd"] for r in self._render_history) / len(self._render_history), 4
            ) if self._render_history else 0.0,
        }

    def optimize_queue(self, queue_status: dict[str, Any]) -> None:
        """
        Called each AROS cycle from ContinuousRuntimeLoop._optimize().
        Submits queue-level optimization recommendations to the DecisionEngine.
        """
        pending = queue_status.get("pending", 0)
        if pending > 10:
            self.decision_engine.submit(Recommendation(
                source="ProductionOptimizer",
                priority="production",
                action="increase_worker_concurrency",
                target="worker_runtime",
                payload={"reason": f"queue_depth={pending}"},
                estimated_impact=4.0,
            ))

