"""
AgentEvolutionTracker — Tracks per-agent performance over time and submits
configuration adjustment recommendations to the AutonomousDecisionEngine.

Each agent maintains:
  - confidence score (0.0 – 1.0)
  - historical accuracy
  - success rate
  - average quality score
  - average cost
  - average latency
"""
import datetime
from typing import Any

from brain.autonomy.decision_engine import AutonomousDecisionEngine, Recommendation


_AGENT_ROLES = [
    "CEO", "Creative Director", "Dialogue", "Story",
    "Visual", "Continuity", "Production",
]


class AgentProfile:
    """Performance profile for a single agent role."""

    def __init__(self, role: str) -> None:
        self.role = role
        self.runs: list[dict[str, Any]] = []

    def record_run(self, quality: float, cost: float, latency_ms: float, success: bool) -> None:
        self.runs.append({
            "quality": quality, "cost": cost,
            "latency_ms": latency_ms, "success": success,
            "at": datetime.datetime.utcnow().isoformat(),
        })

    @property
    def success_rate(self) -> float:
        if not self.runs:
            return 1.0
        return sum(1 for r in self.runs if r["success"]) / len(self.runs)

    @property
    def avg_quality(self) -> float:
        if not self.runs:
            return 0.0
        return round(sum(r["quality"] for r in self.runs) / len(self.runs), 2)

    @property
    def avg_cost(self) -> float:
        if not self.runs:
            return 0.0
        return round(sum(r["cost"] for r in self.runs) / len(self.runs), 6)

    @property
    def avg_latency_ms(self) -> float:
        if not self.runs:
            return 0.0
        return round(sum(r["latency_ms"] for r in self.runs) / len(self.runs), 1)

    @property
    def confidence(self) -> float:
        """Composite confidence: weighted success + quality."""
        return round(min(1.0, self.success_rate * 0.5 + (self.avg_quality / 100) * 0.5), 3)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "runs": len(self.runs),
            "success_rate": self.success_rate,
            "confidence": self.confidence,
            "avg_quality_score": self.avg_quality,
            "avg_cost_usd": self.avg_cost,
            "avg_latency_ms": self.avg_latency_ms,
        }


class AgentEvolutionTracker:
    """Manages performance profiles for all agent roles."""

    def __init__(self, decision_engine: AutonomousDecisionEngine) -> None:
        self.decision_engine = decision_engine
        self.profiles: dict[str, AgentProfile] = {
            role: AgentProfile(role) for role in _AGENT_ROLES
        }

    def record(self, role: str, quality: float, cost: float, latency_ms: float, success: bool) -> None:
        """Record an agent run and submit config adjustment if underperforming."""
        if role not in self.profiles:
            self.profiles[role] = AgentProfile(role)
        self.profiles[role].record_run(quality, cost, latency_ms, success)

        profile = self.profiles[role]
        if profile.confidence < 0.6 and len(profile.runs) >= 3:
            self.decision_engine.submit(Recommendation(
                source="AgentEvolutionTracker",
                priority="production",
                action="adjust_agent_config",
                target="agent_config",
                payload={
                    "role": role,
                    "adjustment": "increase_review_depth",
                    "confidence": profile.confidence,
                },
                estimated_impact=4.0,
            ))

    def get_all_profiles(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in self.profiles.values()]

    def get_profile(self, role: str) -> dict[str, Any]:
        return self.profiles.get(role, AgentProfile(role)).to_dict()
