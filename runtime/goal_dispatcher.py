"""
runtime/goal_dispatcher.py — Converts active goals into executable workflows.

Hierarchy:
  Mission → Goal → Objective → Workflow → Episode → Scene → Task → Execution

The dispatcher reads all active goals from the MissionEngine, enriches each
goal with the concrete workflow steps required to fulfill it, and returns
ready-to-schedule Workflow objects.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

logger = logging.getLogger("aros.goal_dispatcher")


class WorkflowSpec:
    """Fully described, executable workflow produced from a goal."""

    def __init__(
        self,
        goal_id: str,
        objective: str,
        episodes: list[dict[str, Any]],
        universe_id: str = "default",
        priority: int = 5,
    ) -> None:
        self.workflow_id = f"wf-{uuid.uuid4().hex[:8]}"
        self.goal_id = goal_id
        self.objective = objective
        self.episodes = episodes  # list of episode specs
        self.universe_id = universe_id
        self.priority = priority
        self.status = "ready"

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "goal_id": self.goal_id,
            "objective": self.objective,
            "universe_id": self.universe_id,
            "priority": self.priority,
            "episode_count": len(self.episodes),
            "status": self.status,
        }


class GoalDispatcher:
    """
    Reads active goals and converts them into executable WorkflowSpecs.

    Flow:
        active_goals = mission_engine.get_active_goals()
        for goal → WorkflowSpec (episodes, scenes, tasks)
        return WorkflowSpecs ready for WorkflowRuntime
    """

    # Default episode count per objective type
    _EPISODE_COUNT = {
        "retention": 2,
        "quality": 1,
        "growth": 3,
        "cost": 1,
        "engagement": 2,
    }

    def __init__(self, mission_engine: Any, world_model: Any) -> None:
        self.mission_engine = mission_engine
        self.world_model = world_model
        self._dispatched: list[WorkflowSpec] = []

    def dispatch(self) -> list[WorkflowSpec]:
        """Convert all active goals into workflow specs."""
        active = self.mission_engine.get_active_goals()
        specs: list[WorkflowSpec] = []

        for goal in active:
            spec = self._goal_to_workflow(goal)
            self._dispatched.append(spec)
            specs.append(spec)
            logger.info("Dispatched workflow %s for goal %s",
                        spec.workflow_id, goal.get("goal_id"))
        return specs

    def _goal_to_workflow(self, goal: dict[str, Any]) -> WorkflowSpec:
        goal_id: str = goal.get("goal_id", "unknown")
        objective: str = goal.get("objective", "Generate content")
        actions: list[str] = goal.get("actions", [])

        # Determine episode count from goal type
        goal_type = goal_id.split("-")[0] if "-" in goal_id else "quality"
        n_episodes = self._EPISODE_COUNT.get(goal_type, 1)

        episodes = []
        for i in range(n_episodes):
            episode = {
                "episode_id": f"ep-{uuid.uuid4().hex[:8]}",
                "goal_id": goal_id,
                "index": i + 1,
                "scenes": self._build_scenes(actions),
                "budget_usd": 1.5,
            }
            episodes.append(episode)

        return WorkflowSpec(
            goal_id=goal_id,
            objective=objective,
            episodes=episodes,
            universe_id=goal.get("universe_id", "default"),
            priority=goal.get("priority", 5),
        )

    def _build_scenes(self, actions: list[str]) -> list[dict[str, Any]]:
        """Build scene specs from goal actions."""
        base_scenes = [
            {"scene_id": f"sc-{uuid.uuid4().hex[:6]}", "type": "story_generation"},
            {"scene_id": f"sc-{uuid.uuid4().hex[:6]}", "type": "dialogue_generation"},
            {"scene_id": f"sc-{uuid.uuid4().hex[:6]}", "type": "image_generation"},
            {"scene_id": f"sc-{uuid.uuid4().hex[:6]}", "type": "voice_generation"},
            {"scene_id": f"sc-{uuid.uuid4().hex[:6]}", "type": "music_generation"},
            {"scene_id": f"sc-{uuid.uuid4().hex[:6]}", "type": "video_assembly"},
        ]
        return base_scenes

    def get_dispatched(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._dispatched]
