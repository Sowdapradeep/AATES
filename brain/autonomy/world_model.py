"""
WorldModel — Continuously updated internal representation of the studio's state.

Every executive decision references this model rather than querying
each subsystem independently. Modules update their slice of the world
model after every significant operation.
"""
import datetime
from typing import Any


class WorldModel:
    """Single up-to-date snapshot of all studio dimensions."""

    def __init__(self) -> None:
        self._state: dict[str, Any] = {
            "universes": {},           # universe_id -> metadata
            "story_bible_state": {},   # universe_id -> key sections
            "production_queues": [],   # pending episode tasks
            "assets": {},              # asset_id -> metadata
            "budgets": {               # cost tracking
                "total_budget_usd": 5.00,
                "spent_usd": 0.0,
                "remaining_usd": 5.00,
            },
            "aws_resources": {
                "s3_bucket": "",
                "region": "us-east-1",
                "bedrock_available": True,
                "secrets_manager_available": True,
            },
            "provider_health": {},     # model_id -> health status
            "audience_metrics": {
                "total_views": 0,
                "avg_retention_pct": 0.0,
                "avg_completion_pct": 0.0,
                "avg_watch_time_sec": 0.0,
                "engagement_score": 0.0,
            },
            "active_goals": [],        # current goal chain
            "production_capacity": {
                "max_concurrent_renders": 4,
                "current_renders": 0,
            },
            "last_updated": None,
        }

    def update(self, dimension: str, value: Any) -> None:
        """Update a specific world model dimension."""
        if dimension in self._state and isinstance(self._state[dimension], dict) and isinstance(value, dict):
            self._state[dimension].update(value)
        else:
            self._state[dimension] = value
        self._state["last_updated"] = datetime.datetime.utcnow().isoformat()

    def snapshot(self) -> dict[str, Any]:
        """Return a copy of the current world state."""
        return dict(self._state)

    def get(self, dimension: str, default: Any = None) -> Any:
        """Get a specific dimension of the world model."""
        return self._state.get(dimension, default)

    def register_universe(self, universe_id: str, metadata: dict[str, Any]) -> None:
        self._state["universes"][universe_id] = {
            **metadata,
            "registered_at": datetime.datetime.utcnow().isoformat(),
        }
        self._state["last_updated"] = datetime.datetime.utcnow().isoformat()

    def record_spend(self, amount_usd: float) -> None:
        """Update budget tracking after a Bedrock invocation."""
        self._state["budgets"]["spent_usd"] = round(
            self._state["budgets"].get("spent_usd", 0.0) + amount_usd, 6
        )
        self._state["budgets"]["remaining_usd"] = round(
            self._state["budgets"]["total_budget_usd"] - self._state["budgets"]["spent_usd"], 6
        )
        self._state["last_updated"] = datetime.datetime.utcnow().isoformat()

    def update_audience(self, metrics: dict[str, Any]) -> None:
        """Merge new audience metrics into the world model."""
        self._state["audience_metrics"].update(metrics)
        self._state["last_updated"] = datetime.datetime.utcnow().isoformat()


# Module-level singleton
world_model = WorldModel()
