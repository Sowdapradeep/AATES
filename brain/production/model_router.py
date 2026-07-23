"""
Model Router — dynamically selects the most appropriate Amazon Bedrock model
based on task capability requirements, quality tier, estimated latency, and cost.
"""
from typing import Any

# Model catalogue: each entry describes capability, quality tier, cost per 1K tokens,
# and average response latency (ms). Costs in USD.
_MODEL_CATALOGUE: list[dict[str, Any]] = [
    {
        "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
        "capabilities": ["dialogue", "story", "planning", "review", "bible"],
        "quality_tier": "premium",
        "cost_per_1k_tokens": 0.003,
        "avg_latency_ms": 1200,
    },
    {
        "model_id": "anthropic.claude-3-haiku-20240307-v1:0",
        "capabilities": ["dialogue", "story", "planning", "review"],
        "quality_tier": "standard",
        "cost_per_1k_tokens": 0.00025,
        "avg_latency_ms": 400,
    },
    {
        "model_id": "amazon.titan-image-generator-v1",
        "capabilities": ["image", "storyboard", "visual"],
        "quality_tier": "standard",
        "cost_per_1k_tokens": 0.001,
        "avg_latency_ms": 3000,
    },
    {
        "model_id": "amazon.titan-tg1-large",
        "capabilities": ["dialogue", "story"],
        "quality_tier": "economy",
        "cost_per_1k_tokens": 0.0002,
        "avg_latency_ms": 600,
    },
]

# Usage counters for analytics
_usage_counters: dict[str, int] = {}
_cost_tracker: dict[str, float] = {}


class ModelRouter:
    """Routes generation requests to the optimal Bedrock model for cost and quality."""

    def route(
        self,
        capability: str,
        quality_tier: str = "standard",
        max_latency_ms: int | None = None,
        prefer_economy: bool = False,
    ) -> str:
        """
        Returns the best-matching model_id for the requested capability.

        Priority order:
          1. Must support the requested capability.
          2. Must match quality_tier (or fall back to any tier if no exact match).
          3. If prefer_economy=True, picks cheapest. Otherwise picks by quality tier.
          4. Optionally filters by max_latency_ms.
        """
        candidates = [
            m for m in _MODEL_CATALOGUE
            if capability in m["capabilities"]
        ]

        if not candidates:
            # Fall back to Claude Sonnet as general-purpose model
            return "anthropic.claude-3-sonnet-20240229-v1:0"

        # Filter by latency if requested
        if max_latency_ms is not None:
            fast = [m for m in candidates if m["avg_latency_ms"] <= max_latency_ms]
            if fast:
                candidates = fast

        # Filter by quality tier preference
        tier_match = [m for m in candidates if m["quality_tier"] == quality_tier]
        if tier_match:
            candidates = tier_match

        # Sort by cost or quality
        if prefer_economy:
            candidates.sort(key=lambda m: m["cost_per_1k_tokens"])
        else:
            tier_order = {"premium": 0, "standard": 1, "economy": 2}
            candidates.sort(key=lambda m: tier_order.get(m["quality_tier"], 99))

        selected = candidates[0]["model_id"]

        # Track usage
        _usage_counters[selected] = _usage_counters.get(selected, 0) + 1

        return selected

    def record_cost(self, model_id: str, tokens_used: int) -> None:
        """Records the estimated cost of a model invocation."""
        model = next((m for m in _MODEL_CATALOGUE if m["model_id"] == model_id), None)
        if model:
            cost = (tokens_used / 1000) * model["cost_per_1k_tokens"]
            _cost_tracker[model_id] = _cost_tracker.get(model_id, 0.0) + cost

    def get_usage_summary(self) -> dict[str, Any]:
        """Returns model usage distribution and total estimated costs."""
        total_cost = sum(_cost_tracker.values())
        return {
            "model_usage_distribution": dict(_usage_counters),
            "model_cost_breakdown_usd": {k: round(v, 6) for k, v in _cost_tracker.items()},
            "total_estimated_cost_usd": round(total_cost, 6),
        }


model_router = ModelRouter()
