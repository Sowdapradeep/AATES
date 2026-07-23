"""
runtime/autonomous_trigger_engine.py — CEO never waits for a prompt.

The trigger engine continuously evaluates:
  Current Mission → Business Goals → Publishing Calendar → Analytics
  → Audience Trends → Budget → Production Capacity
  → Generate New Goals → Schedule Production → Execute

Called every AROS cycle. Returns a plan of new productions to schedule.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("aros.trigger_engine")

# Minimum interval between new productions (cycles)
MIN_CYCLES_BETWEEN_PRODUCTIONS = 2


class AutonomousTriggerEngine:
    """
    Decides whether new productions should be triggered based on
    mission state, analytics, budget, and capacity.
    No human interaction ever required.
    """

    def __init__(
        self,
        mission_engine: Any,
        goal_engine: Any,
        scheduler: Any,
        decision_engine: Any,
    ) -> None:
        self.mission_engine = mission_engine
        self.goal_engine = goal_engine
        self.scheduler = scheduler
        self.decision_engine = decision_engine
        self._cycles_since_last_production = 0
        self._total_triggered = 0

    def evaluate(self) -> dict[str, Any]:
        """
        Evaluate whether new productions should start this cycle.
        Returns a plan with a list of productions to schedule.
        """
        self._cycles_since_last_production += 1
        new_productions: list[dict[str, Any]] = []

        if not self._capacity_ok():
            logger.debug("TriggerEngine: capacity full — deferring")
            return {"new_productions": []}

        if not self._budget_ok():
            logger.debug("TriggerEngine: budget limit — deferring")
            return {"new_productions": []}

        if self._cycles_since_last_production < MIN_CYCLES_BETWEEN_PRODUCTIONS:
            logger.debug("TriggerEngine: too soon since last production")
            return {"new_productions": []}

        # Generate a goal-driven production
        try:
            goal = self.goal_engine.generate_next_goal()
            production = {
                "type": "goal_production",
                "goal_id": goal.get("goal_id"),
                "objective": goal.get("objective"),
                "priority": 7,
            }
            new_productions.append(production)
            self._cycles_since_last_production = 0
            self._total_triggered += 1
            logger.info("TriggerEngine: new production triggered — goal=%s",
                        goal.get("goal_id"))
        except Exception as exc:
            logger.warning("TriggerEngine: goal generation error: %s", exc)

        return {"new_productions": new_productions}

    def _capacity_ok(self) -> bool:
        """Check if scheduler has room for a new production."""
        try:
            status = self.scheduler.get_status()
            return status.get("running", 0) < self.scheduler.max_concurrent
        except Exception:
            return True

    def _budget_ok(self) -> bool:
        """Check if scheduler still has budget available."""
        try:
            status = self.scheduler.get_status()
            spent = status.get("budget_spent_usd", 0.0)
            limit = status.get("budget_limit_usd", 5.0)
            return spent < limit * 0.9
        except Exception:
            return True

    def get_status(self) -> dict[str, Any]:
        return {
            "total_triggered": self._total_triggered,
            "cycles_since_last": self._cycles_since_last_production,
        }
