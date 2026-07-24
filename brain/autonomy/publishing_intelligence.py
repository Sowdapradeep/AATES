"""
PublishingIntelligenceEngine — Autonomous publishing strategy determination.

Based on historical analytics, determines:
  - Best publishing day of week
  - Best publishing hour
  - Optimal hashtags
  - Captions style
  - Thumbnail style
  - Trailer timing

Submits schedule recommendations via AutonomousDecisionEngine.
"""
import datetime
from typing import Any

from brain.autonomy.decision_engine import AutonomousDecisionEngine, Recommendation
from brain.autonomy.strategic_memory import strategic_memory


_DEFAULT_SCHEDULE = {
    "best_day": "Friday",
    "best_hour_utc": 14,
    "hashtags": ["#Tamil", "#TamilSeries", "#AATES", "#AutonomousStudio"],
    "caption_style": "emotional_hook_first",
    "thumbnail_style": "character_close_up",
    "trailer_timing_hrs_before": 24,
}


class PublishingIntelligenceEngine:
    """Determines optimal publishing strategy from analytics history."""

    def __init__(self, decision_engine: AutonomousDecisionEngine) -> None:
        self.decision_engine = decision_engine
        self._analytics_history: list[dict[str, Any]] = []
        self._current_schedule: dict[str, Any] = dict(_DEFAULT_SCHEDULE)

    def record_publish_outcome(self, episode_id: str, publish_data: dict[str, Any]) -> None:
        """Ingest post-publish analytics and update schedule recommendations."""
        self._analytics_history.append({
            "episode_id": episode_id,
            **publish_data,
            "recorded_at": datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat(),
        })

        engagement = publish_data.get("engagement_score", 0.5)
        day = publish_data.get("publish_day", "Friday")
        hour = publish_data.get("publish_hour_utc", 14)

        # If this publish significantly outperformed, promote its schedule
        if engagement > 0.75:
            self._current_schedule["best_day"] = day
            self._current_schedule["best_hour_utc"] = hour
            strategic_memory.record("publishing_strategies", {
                "episode_id": episode_id,
                "best_day": day,
                "best_hour_utc": hour,
                "engagement": engagement,
            })
            self.decision_engine.submit(Recommendation(
                source="PublishingIntelligenceEngine",
                priority="business",
                action="update_publish_schedule",
                target="publishing_schedule",
                payload={"best_day": day, "best_hour_utc": hour, "engagement": engagement},
                estimated_impact=4.0,
            ))

        # Hashtag evolution: add show-specific tags after 5+ episodes
        if len(self._analytics_history) == 5:
            self._current_schedule["hashtags"].append("#KarnanChronicles")
            self.decision_engine.submit(Recommendation(
                source="PublishingIntelligenceEngine",
                priority="creative",
                action="update_hashtag_set",
                target="publishing_schedule",
                payload={"hashtags": self._current_schedule["hashtags"]},
                estimated_impact=1.5,
            ))

    def get_recommended_schedule(self) -> dict[str, Any]:
        return dict(self._current_schedule)

    def get_analytics_summary(self) -> dict[str, Any]:
        if not self._analytics_history:
            return {"total_publishes": 0, "avg_engagement": 0.0}
        scores = [h.get("engagement_score", 0.0) for h in self._analytics_history]
        return {
            "total_publishes": len(self._analytics_history),
            "avg_engagement": round(sum(scores) / len(scores), 3),
            "current_schedule": self._current_schedule,
        }
