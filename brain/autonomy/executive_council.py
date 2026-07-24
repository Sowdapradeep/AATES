"""
AutonomousExecutiveCouncil — Post-episode CEO review and decision submission.

After every completed episode, the council reviews:
  - Quality scores (from MultiAgentReviewPipeline)
  - Production costs (from ModelRouter usage)
  - Production time (render latency)
  - Audience analytics
  - Critic reports

Then submits ONE recommendation per area to the AutonomousDecisionEngine.
No human approval. All decisions are logged via strategic memory.
"""
import datetime
from typing import Any

from brain.autonomy.decision_engine import AutonomousDecisionEngine, Recommendation
from brain.autonomy.strategic_memory import strategic_memory
from brain.autonomy.world_model import world_model


class AutonomousExecutiveCouncil:
    """Post-episode autonomous CEO review and strategic recommendation."""

    # Decision thresholds
    QUALITY_THRESHOLD = 80.0
    COST_THRESHOLD_USD = 2.0
    RETENTION_THRESHOLD_PCT = 60.0

    def __init__(self, decision_engine: AutonomousDecisionEngine) -> None:
        self.decision_engine = decision_engine
        self.review_log: list[dict[str, Any]] = []

    async def review_episode(self, episode_report: dict[str, Any]) -> dict[str, Any]:
        """
        Full post-episode executive review. Produces decisions across
        quality, cost, pacing, style, publishing frequency, and universe direction.
        """
        quality_score = episode_report.get("quality_score", 85.0)
        cost_usd = episode_report.get("cost_usd", 0.5)
        render_time_sec = episode_report.get("render_time_sec", 30.0)
        retention_pct = episode_report.get("audience_retention_pct", 65.0)
        revision_count = episode_report.get("revision_count", 0)
        episode_id = episode_report.get("episode_id", "unknown")

        submitted_recommendations = []

        # ── 1. Quality decision ──────────────────────────────────────────────
        if quality_score < self.QUALITY_THRESHOLD:
            rec = Recommendation(
                source="ExecutiveCouncil",
                priority="production",
                action="upgrade_dialogue_model",
                target="model_router",
                payload={"capability": "dialogue", "force_tier": "premium"},
                estimated_impact=8.0,
            )
            self.decision_engine.submit(rec)
            submitted_recommendations.append("upgrade_dialogue_model → model_router")

        # ── 2. Cost decision ─────────────────────────────────────────────────
        if cost_usd > self.COST_THRESHOLD_USD:
            rec = Recommendation(
                source="ExecutiveCouncil",
                priority="business",
                action="enable_economy_routing",
                target="model_router",
                payload={"prefer_economy": True, "capabilities": ["dialogue", "story"]},
                estimated_impact=6.0,
            )
            self.decision_engine.submit(rec)
            submitted_recommendations.append("enable_economy_routing → model_router")

        # ── 3. Audience retention decision ───────────────────────────────────
        if retention_pct < self.RETENTION_THRESHOLD_PCT:
            rec = Recommendation(
                source="ExecutiveCouncil",
                priority="creative",
                action="increase_story_intensity",
                target="story_bible",
                payload={"directive": "darker_arcs", "intensity_boost": 1.2},
                estimated_impact=7.5,
            )
            self.decision_engine.submit(rec)
            submitted_recommendations.append("increase_story_intensity → story_bible")

        # ── 4. Revision loop management ──────────────────────────────────────
        if revision_count > 2:
            rec = Recommendation(
                source="ExecutiveCouncil",
                priority="production",
                action="pre_screen_dialogue",
                target="production_queue",
                payload={"pre_screen": True, "critic": "Dialogue"},
                estimated_impact=5.0,
            )
            self.decision_engine.submit(rec)
            submitted_recommendations.append("pre_screen_dialogue → production_queue")

        # ── 5. Publishing frequency decision ─────────────────────────────────
        if retention_pct >= 75.0 and quality_score >= 85.0:
            rec = Recommendation(
                source="ExecutiveCouncil",
                priority="business",
                action="increase_publishing_frequency",
                target="publishing_schedule",
                payload={"episodes_per_week": 3},
                estimated_impact=4.0,
            )
            self.decision_engine.submit(rec)
            submitted_recommendations.append("increase_publishing_frequency → publishing_schedule")

        # Determine overall executive action
        if quality_score >= self.QUALITY_THRESHOLD and cost_usd <= self.COST_THRESHOLD_USD:
            executive_action = "continue"
        elif quality_score < self.QUALITY_THRESHOLD and revision_count == 0:
            executive_action = "regenerate"
        elif quality_score < 70.0:
            executive_action = "rewrite"
        else:
            executive_action = "continue_with_adjustments"

        review_entry = {
            "episode_id": episode_id,
            "executive_action": executive_action,
            "quality_score": quality_score,
            "cost_usd": cost_usd,
            "retention_pct": retention_pct,
            "recommendations_submitted": submitted_recommendations,
            "reviewed_at": datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat(),
        }
        self.review_log.append(review_entry)

        # Update world model audience metrics
        world_model.update_audience({"avg_retention_pct": retention_pct})

        # Record in strategic memory
        strategic_memory.record("ceo_objectives", {
            "episode_id": episode_id,
            "action": executive_action,
            "quality_score": quality_score,
        })

        return review_entry

    def get_review_log(self) -> list[dict[str, Any]]:
        return list(self.review_log)
