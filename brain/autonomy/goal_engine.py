"""
AutonomousGoalEngine — Goal-driven planning tied to the studio mission.

Goals are generated to advance the MissionEngine's current mission rather
than creating arbitrary objectives. Supports:
  - Goal decomposition into objectives → actions
  - Goal success evaluation against target metrics
  - Chained goal generation (completed goal spawns next)
  - All goal-driven mutations submitted via AutonomousDecisionEngine
"""
import datetime
from typing import Any

from brain.autonomy.decision_engine import AutonomousDecisionEngine, Recommendation
from brain.autonomy.mission_engine import MissionEngine
from brain.autonomy.lifelong_memory import lifelong_memory
from brain.autonomy.world_model import world_model


class AutonomousGoalEngine:
    """Generates and pursues autonomous goals aligned with the studio mission."""

    def __init__(
        self,
        decision_engine: AutonomousDecisionEngine,
        mission_engine: MissionEngine,
    ) -> None:
        self.decision_engine = decision_engine
        self.mission_engine = mission_engine
        self._goal_chain: list[dict[str, Any]] = []

    def generate_next_goal(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Generate the next autonomous goal. Uses WorldModel for current context
        if none provided, then delegates to MissionEngine for mission alignment.
        """
        if context is None:
            context = {
                "avg_retention_pct": world_model.get("audience_metrics", {}).get("avg_retention_pct", 65.0)
                    if isinstance(world_model.get("audience_metrics"), dict) else 65.0,
                "avg_quality_score": 82.0,
                "total_cost_usd": world_model.get("budgets", {}).get("spent_usd", 0.0)
                    if isinstance(world_model.get("budgets"), dict) else 0.0,
            }

        goal = self.mission_engine.generate_mission_aligned_goal(context)
        self._goal_chain.append(goal)

        # Submit any goal-driven strategy changes to decision engine
        for action_desc in goal.get("actions", []):
            if "economy" in action_desc.lower() or "routing" in action_desc.lower():
                self.decision_engine.submit(Recommendation(
                    source="AutonomousGoalEngine",
                    priority="optimization",
                    action="apply_goal_strategy",
                    target="model_router",
                    payload={"goal_id": goal["goal_id"], "action": action_desc},
                    estimated_impact=3.0,
                ))
            elif "story" in action_desc.lower() or "narrative" in action_desc.lower():
                self.decision_engine.submit(Recommendation(
                    source="AutonomousGoalEngine",
                    priority="creative",
                    action="apply_narrative_strategy",
                    target="story_bible",
                    payload={"goal_id": goal["goal_id"], "action": action_desc},
                    estimated_impact=4.0,
                ))

        lifelong_memory.remember("production_optimizations", {
            "type": "goal_generated",
            "goal_id": goal["goal_id"],
            "objective": goal["objective"],
        })

        return goal

    def evaluate_goal(self, goal_id: str, actual_metrics: dict[str, Any]) -> dict[str, Any]:
        """
        Evaluate whether a goal was achieved. If yes, record in lifelong memory
        and generate the next goal automatically.
        """
        goal = next((g for g in self._goal_chain if g["goal_id"] == goal_id), None)
        if not goal:
            return {"status": "goal_not_found", "goal_id": goal_id}

        targets = goal.get("metric_target", {})
        achieved = all(
            actual_metrics.get(k, 0) >= v
            for k, v in targets.items()
        )

        if achieved:
            self.mission_engine.record_mission_progress(goal_id, actual_metrics)
            lifelong_memory.remember("successful_prompts", {
                "type": "goal_achieved",
                "goal_id": goal_id,
                "objective": goal["objective"],
                "metrics": actual_metrics,
            })
            # Chain: generate next goal automatically
            next_goal = self.generate_next_goal(actual_metrics)
            return {
                "status": "achieved",
                "goal_id": goal_id,
                "next_goal_id": next_goal["goal_id"],
            }
        else:
            lifelong_memory.remember("failed_prompts", {
                "type": "goal_missed",
                "goal_id": goal_id,
                "targets": targets,
                "actuals": actual_metrics,
            })
            return {"status": "not_achieved", "goal_id": goal_id, "gap": {
                k: round(targets[k] - actual_metrics.get(k, 0), 2)
                for k in targets
            }}

    def get_goal_chain(self) -> list[dict[str, Any]]:
        return list(self._goal_chain)
