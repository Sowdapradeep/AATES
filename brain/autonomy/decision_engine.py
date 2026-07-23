"""
AutonomousDecisionEngine — The single strategic commit authority for the
AATES autonomous studio.

All autonomous modules (learning, business intelligence, universe evolution,
publishing intelligence, model evolution, etc.) submit RECOMMENDATIONS here.
This engine resolves conflicts, prioritizes by impact, and commits approved
changes to the appropriate platform components.

Decision priority (higher index wins conflicts):
  5. Critical  (safety, compliance)
  4. Business  (budget, costs)
  3. Production (quality, rendering)
  2. Creative  (style, tone, pacing)
  1. Optimization (speed, efficiency)

NO module may directly mutate: Story Bible, Prompt Library, Model Router
weights, Budget Engine, Publishing Schedule, or Production Queue.
All such changes must be submitted here as recommendations.
"""
import datetime
from typing import Any

from brain.autonomy.strategic_memory import strategic_memory
from brain.autonomy.world_model import world_model

# Decision priority levels
PRIORITY = {
    "critical": 5,
    "business": 4,
    "production": 3,
    "creative": 2,
    "optimization": 1,
}


class Recommendation:
    """A structured recommendation submitted by an autonomous module."""

    def __init__(
        self,
        source: str,
        priority: str,
        action: str,
        target: str,
        payload: dict[str, Any],
        estimated_impact: float = 0.0,
    ) -> None:
        self.source = source
        self.priority = priority
        self.priority_level = PRIORITY.get(priority, 1)
        self.action = action
        self.target = target          # e.g. "story_bible", "prompt_library", "model_router"
        self.payload = payload
        self.estimated_impact = estimated_impact
        self.submitted_at = datetime.datetime.utcnow().isoformat()


class AutonomousDecisionEngine:
    """
    Central autonomous decision authority.
    Receives recommendations, resolves conflicts, and executes approved changes.
    """

    VALID_TARGETS = {
        "story_bible", "prompt_library", "model_router",
        "budget_engine", "publishing_schedule", "production_queue",
        "agent_config", "universe_registry", "asset_library",
    }

    def __init__(self) -> None:
        self._pending: list[Recommendation] = []
        self._committed: list[dict[str, Any]] = []
        self._rejected: list[dict[str, Any]] = []

    def submit(self, recommendation: Recommendation) -> str:
        """Accept a recommendation from an autonomous module."""
        if recommendation.target not in self.VALID_TARGETS:
            return f"rejected:invalid_target:{recommendation.target}"
        self._pending.append(recommendation)
        return f"queued:{recommendation.action}@{recommendation.target}"

    def process_cycle(self) -> dict[str, Any]:
        """
        Process all pending recommendations in one decision cycle.
        Resolves conflicts by priority, deduplicates targets, and commits.
        """
        if not self._pending:
            return {"committed": 0, "rejected": 0, "skipped": 0}

        # Sort by priority descending, then impact descending
        sorted_recs = sorted(
            self._pending,
            key=lambda r: (r.priority_level, r.estimated_impact),
            reverse=True,
        )

        committed_targets: set[str] = set()
        committed_count = 0
        rejected_count = 0
        skipped_count = 0

        cycle_decisions = []

        for rec in sorted_recs:
            target_key = f"{rec.target}:{rec.action}"

            # Conflict resolution: only highest-priority recommendation per target wins
            if target_key in committed_targets:
                self._rejected.append({
                    "source": rec.source,
                    "action": rec.action,
                    "target": rec.target,
                    "reason": "conflict:lower_priority",
                    "at": datetime.datetime.utcnow().isoformat(),
                })
                rejected_count += 1
                continue

            # Commit the recommendation
            committed_entry = {
                "source": rec.source,
                "priority": rec.priority,
                "action": rec.action,
                "target": rec.target,
                "payload": rec.payload,
                "estimated_impact": rec.estimated_impact,
                "committed_at": datetime.datetime.utcnow().isoformat(),
            }
            self._committed.append(committed_entry)
            committed_targets.add(target_key)
            committed_count += 1
            cycle_decisions.append(committed_entry)

            # Write to strategic memory for long-term learning
            strategic_memory.record("successful_experiments", {
                "decision": rec.action,
                "target": rec.target,
                "impact": rec.estimated_impact,
                "source": rec.source,
            })

            # Update world model where applicable
            if rec.target == "budget_engine":
                world_model.update("budgets", rec.payload)

        self._pending.clear()

        return {
            "committed": committed_count,
            "rejected": rejected_count,
            "skipped": skipped_count,
            "decisions": cycle_decisions,
        }

    def get_decision_log(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return the most recent committed decisions."""
        return self._committed[-limit:]

    def get_rejected_log(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return the most recent rejected recommendations."""
        return self._rejected[-limit:]

    def summary(self) -> dict[str, Any]:
        return {
            "pending": len(self._pending),
            "committed_total": len(self._committed),
            "rejected_total": len(self._rejected),
        }


# Module-level singleton
autonomous_decision_engine = AutonomousDecisionEngine()
