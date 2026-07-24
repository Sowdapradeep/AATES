"""
BusinessIntelligenceEngine — CEO-level business metrics monitoring.

Continuously monitors:
  - Production costs
  - Budget consumption
  - Audience growth
  - Retention rate
  - Completion rate
  - Watch time
  - Engagement score

Automatically adjusts:
  - Investment (budget allocation)
  - Production scale (episodes per month)
  - Model usage tier
  - Quality thresholds

All adjustments submitted via AutonomousDecisionEngine.
"""
import datetime
from typing import Any

from brain.autonomy.decision_engine import AutonomousDecisionEngine, Recommendation
from brain.autonomy.strategic_memory import strategic_memory
from brain.autonomy.world_model import world_model


class BusinessIntelligenceEngine:
    """Autonomous business metrics monitoring and adjustment engine."""

    def __init__(self, decision_engine: AutonomousDecisionEngine) -> None:
        self.decision_engine = decision_engine
        self._snapshots: list[dict[str, Any]] = []

    def ingest_metrics(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """
        Ingest a business metrics snapshot and submit adjustment recommendations.

        Expected keys: total_cost_usd, budget_usd, audience_growth_pct,
        avg_retention_pct, avg_completion_pct, avg_watch_time_sec, engagement_score.
        """
        snapshot = {**metrics, "recorded_at": datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat()}
        self._snapshots.append(snapshot)

        cost = metrics.get("total_cost_usd", 0.0)
        budget = metrics.get("budget_usd", 5.0)
        retention = metrics.get("avg_retention_pct", 65.0)
        engagement = metrics.get("engagement_score", 0.6)
        growth = metrics.get("audience_growth_pct", 5.0)

        recommendations_submitted = []

        # ── Budget guard ─────────────────────────────────────────────────────
        if cost > budget * 0.8:
            self.decision_engine.submit(Recommendation(
                source="BusinessIntelligenceEngine",
                priority="business",
                action="reduce_production_scale",
                target="production_queue",
                payload={"max_episodes_per_cycle": 1, "reason": "budget_threshold_80pct"},
                estimated_impact=7.0,
            ))
            recommendations_submitted.append("reduce_production_scale")
            world_model.update("budgets", {"alert": "80pct_consumed"})

        # ── Quality investment increase on high engagement ───────────────────
        if engagement > 0.8 and retention > 70.0:
            self.decision_engine.submit(Recommendation(
                source="BusinessIntelligenceEngine",
                priority="business",
                action="increase_quality_threshold",
                target="budget_engine",
                payload={"new_quality_threshold": 85.0, "increase_budget_by_usd": 2.0},
                estimated_impact=5.0,
            ))
            recommendations_submitted.append("increase_quality_threshold")

        # ── Scale up if growth is strong and within budget ───────────────────
        if growth > 20.0 and cost < budget * 0.5:
            self.decision_engine.submit(Recommendation(
                source="BusinessIntelligenceEngine",
                priority="business",
                action="scale_production_up",
                target="production_queue",
                payload={"max_episodes_per_cycle": 3},
                estimated_impact=6.0,
            ))
            recommendations_submitted.append("scale_production_up")

        # ── Downgrade model tier if retention is poor ────────────────────────
        if retention < 45.0:
            self.decision_engine.submit(Recommendation(
                source="BusinessIntelligenceEngine",
                priority="production",
                action="force_creative_rewrite",
                target="story_bible",
                payload={"directive": "restructure_narrative_arc"},
                estimated_impact=8.0,
            ))
            recommendations_submitted.append("force_creative_rewrite")

        strategic_memory.record("multi_month_trends", {
            "cost": cost, "retention": retention,
            "engagement": engagement, "recommendations": recommendations_submitted,
        })

        return {
            "snapshot_recorded": True,
            "recommendations_submitted": recommendations_submitted,
            "budget_consumed_pct": round((cost / budget) * 100, 1) if budget else 0.0,
        }

    def get_business_dashboard(self) -> dict[str, Any]:
        if not self._snapshots:
            return {"total_snapshots": 0}
        latest = self._snapshots[-1]
        retentions = [s.get("avg_retention_pct", 0) for s in self._snapshots]
        engagements = [s.get("engagement_score", 0) for s in self._snapshots]
        return {
            "total_snapshots": len(self._snapshots),
            "latest_snapshot": latest,
            "avg_retention_pct": round(sum(retentions) / len(retentions), 2),
            "avg_engagement": round(sum(engagements) / len(engagements), 3),
            "world_model_budgets": world_model.get("budgets"),
        }
