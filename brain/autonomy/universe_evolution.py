"""
UniverseEvolutionEngine — Makes CEO decisions about living universes.

Submits recommendations to AutonomousDecisionEngine for:
  - Expand universe (more episodes, more characters)
  - End universe (conclude the canon)
  - Create spin-offs
  - Merge universes
  - Introduce crossover events
  - Retire low-performing characters
  - Promote high-engagement side characters
  - Evolve lore entries

All Story Bible updates are submitted as recommendations, never applied directly.
"""
import datetime
from typing import Any

from brain.autonomy.decision_engine import AutonomousDecisionEngine, Recommendation
from brain.autonomy.strategic_memory import strategic_memory
from brain.autonomy.world_model import world_model


class UniverseEvolutionEngine:
    """CEO-driven living universe evolution decisions."""

    EXPAND_SCORE_THRESHOLD = 82.0
    END_SCORE_THRESHOLD = 55.0
    PROMOTE_ENGAGEMENT_THRESHOLD = 0.75

    def __init__(self, decision_engine: AutonomousDecisionEngine) -> None:
        self.decision_engine = decision_engine
        self._evolution_log: list[dict[str, Any]] = []

    def evaluate_universe(self, universe_id: str, universe_data: dict[str, Any]) -> dict[str, Any]:
        """
        Evaluate a universe and submit evolution recommendations.
        universe_data should contain: avg_quality, avg_engagement, episode_count,
        top_characters, underperforming_characters.
        """
        avg_quality = universe_data.get("avg_quality", 80.0)
        avg_engagement = universe_data.get("avg_engagement", 0.65)
        episode_count = universe_data.get("episode_count", 1)
        top_chars = universe_data.get("top_characters", [])
        weak_chars = universe_data.get("underperforming_characters", [])

        decisions_submitted = []

        # ── Expand vs End ────────────────────────────────────────────────────
        if avg_quality >= self.EXPAND_SCORE_THRESHOLD and avg_engagement >= 0.6:
            self.decision_engine.submit(Recommendation(
                source="UniverseEvolutionEngine",
                priority="creative",
                action="expand_universe",
                target="universe_registry",
                payload={"universe_id": universe_id, "directive": "add_season"},
                estimated_impact=6.0,
            ))
            decisions_submitted.append("expand_universe")

        elif avg_quality < self.END_SCORE_THRESHOLD or avg_engagement < 0.3:
            self.decision_engine.submit(Recommendation(
                source="UniverseEvolutionEngine",
                priority="business",
                action="conclude_universe",
                target="universe_registry",
                payload={"universe_id": universe_id, "directive": "wrap_canon"},
                estimated_impact=5.0,
            ))
            decisions_submitted.append("conclude_universe")

        # ── Spin-off if top character has high engagement ────────────────────
        if top_chars and avg_engagement >= self.PROMOTE_ENGAGEMENT_THRESHOLD:
            self.decision_engine.submit(Recommendation(
                source="UniverseEvolutionEngine",
                priority="creative",
                action="create_spinoff",
                target="universe_registry",
                payload={
                    "parent_universe_id": universe_id,
                    "spinoff_character": top_chars[0],
                },
                estimated_impact=7.0,
            ))
            decisions_submitted.append("create_spinoff")

        # ── Retire weak characters ───────────────────────────────────────────
        for char in weak_chars[:2]:
            self.decision_engine.submit(Recommendation(
                source="UniverseEvolutionEngine",
                priority="creative",
                action="retire_character",
                target="story_bible",
                payload={"universe_id": universe_id, "character": char},
                estimated_impact=2.0,
            ))
            decisions_submitted.append(f"retire_character:{char}")

        # ── Lore evolution after 5+ episodes ────────────────────────────────
        if episode_count >= 5:
            self.decision_engine.submit(Recommendation(
                source="UniverseEvolutionEngine",
                priority="creative",
                action="evolve_lore",
                target="story_bible",
                payload={
                    "universe_id": universe_id,
                    "lore_update": "Introduce second-generation characters with evolved world rules.",
                },
                estimated_impact=4.0,
            ))
            decisions_submitted.append("evolve_lore")

        entry = {
            "universe_id": universe_id,
            "avg_quality": avg_quality,
            "avg_engagement": avg_engagement,
            "decisions_submitted": decisions_submitted,
            "evaluated_at": datetime.datetime.utcnow().isoformat(),
        }
        self._evolution_log.append(entry)
        strategic_memory.record("universe_performance", {
            "universe_id": universe_id,
            "avg_quality": avg_quality,
            "decisions": decisions_submitted,
        })
        world_model.register_universe(universe_id, {"avg_quality": avg_quality, "episode_count": episode_count})
        return entry

    def get_evolution_log(self) -> list[dict[str, Any]]:
        return list(self._evolution_log)
