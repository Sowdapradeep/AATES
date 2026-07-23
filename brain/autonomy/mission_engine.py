"""
MissionEngine — Keeps autonomous goal generation aligned with the studio's
long-term mission rather than creating unrelated objectives.

Mission hierarchy:
  Mission
    └── Goals (multi-episode strategic targets)
          └── Objectives (single-episode concrete tasks)
                └── Plans (execution steps)
                      └── Episodes (generated content)
                            └── Analytics (measurement)
                                  └── Learning (update mission progress)
"""
import datetime
from typing import Any


STUDIO_MISSION = (
    "Become the leading autonomous Tamil entertainment studio "
    "by continuously producing high-quality, culturally resonant content "
    "that grows audience retention and expands the universe canon."
)


class MissionEngine:
    """Manages the studio mission hierarchy and tracks progress."""

    def __init__(self) -> None:
        self.mission = STUDIO_MISSION
        self.goals: list[dict[str, Any]] = []
        self.mission_progress: list[dict[str, Any]] = []

    def generate_mission_aligned_goal(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Generate a new strategic goal aligned with the studio mission.
        Context should include current audience metrics, costs, and quality scores.
        """
        avg_retention = context.get("avg_retention_pct", 0.0)
        avg_quality = context.get("avg_quality_score", 0.0)
        total_cost = context.get("total_cost_usd", 0.0)

        # Determine the most impactful goal based on current metrics
        if avg_retention < 60.0:
            goal = {
                "goal_id": f"goal-retention-{len(self.goals)+1}",
                "objective": "Increase audience retention",
                "strategy": "Create darker, higher-stakes story arcs",
                "actions": [
                    "Introduce a stronger antagonist",
                    "Increase episode emotional intensity",
                    "Shorten scenes with low engagement",
                ],
                "metric_target": {"avg_retention_pct": 75.0},
                "mission_alignment": "Grow audience retention",
            }
        elif avg_quality < 80.0:
            goal = {
                "goal_id": f"goal-quality-{len(self.goals)+1}",
                "objective": "Improve overall content quality",
                "strategy": "Elevate dialogue and visual fidelity",
                "actions": [
                    "Upgrade dialogue model to premium tier",
                    "Add Dialogue Critic pre-screening",
                    "Increase storyboard panel density",
                ],
                "metric_target": {"avg_quality_score": 88.0},
                "mission_alignment": "High-quality culturally resonant content",
            }
        elif total_cost > 3.0:
            goal = {
                "goal_id": f"goal-cost-{len(self.goals)+1}",
                "objective": "Reduce production cost per episode",
                "strategy": "Maximize asset reuse and economy model routing",
                "actions": [
                    "Enable economy routing for dialogue tasks",
                    "Increase asset reuse cache hit rate",
                    "Reduce redundant Bedrock calls",
                ],
                "metric_target": {"cost_per_episode_usd": 0.50},
                "mission_alignment": "Sustainable autonomous production",
            }
        else:
            goal = {
                "goal_id": f"goal-expansion-{len(self.goals)+1}",
                "objective": "Expand universe canon",
                "strategy": "Launch Season 2 and introduce spin-off",
                "actions": [
                    "Generate Season 2 story arc",
                    "Create spin-off character backstory",
                    "Introduce crossover event with existing universe",
                ],
                "metric_target": {"universe_episodes_total": 20},
                "mission_alignment": "Expand the universe canon",
            }

        goal["created_at"] = datetime.datetime.utcnow().isoformat()
        goal["status"] = "active"
        self.goals.append(goal)
        return goal

    def record_mission_progress(self, goal_id: str, outcome: dict[str, Any]) -> None:
        """Record the measured outcome of a completed goal."""
        self.mission_progress.append({
            "goal_id": goal_id,
            "outcome": outcome,
            "recorded_at": datetime.datetime.utcnow().isoformat(),
        })
        # Mark goal as completed
        for g in self.goals:
            if g["goal_id"] == goal_id:
                g["status"] = "completed"
                g["outcome"] = outcome

    def get_active_goals(self) -> list[dict[str, Any]]:
        return [g for g in self.goals if g.get("status") == "active"]

    def get_mission_summary(self) -> dict[str, Any]:
        return {
            "mission": self.mission,
            "total_goals": len(self.goals),
            "active_goals": len(self.get_active_goals()),
            "completed_goals": len([g for g in self.goals if g.get("status") == "completed"]),
            "progress_records": len(self.mission_progress),
        }


# Module-level singleton
mission_engine = MissionEngine()
