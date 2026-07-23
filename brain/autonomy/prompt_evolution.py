"""
PromptEvolutionEngine — Versioned prompt management with automatic promotion
and retirement based on quality, cost, latency, and audience metrics.

Extends Phase 10 PromptOptimizationEngine with full version lineage tracking
and submission of changes via the AutonomousDecisionEngine.
"""
import datetime
from typing import Any

from brain.autonomy.decision_engine import AutonomousDecisionEngine, Recommendation
from brain.autonomy.strategic_memory import strategic_memory

RETIRE_THRESHOLD = 65.0   # prompts below this are retired
PROMOTE_THRESHOLD = 88.0  # prompts above this are promoted to preferred


class PromptVersionRecord:
    def __init__(self, prompt_id: str, version: str, template: str) -> None:
        self.prompt_id = prompt_id
        self.version = version
        self.template = template
        self.scores: list[float] = []
        self.costs: list[float] = []
        self.latencies_ms: list[float] = []
        self.audience_scores: list[float] = []
        self.status = "active"  # active | promoted | retired
        self.created_at = datetime.datetime.utcnow().isoformat()

    @property
    def avg_score(self) -> float:
        return round(sum(self.scores) / len(self.scores), 2) if self.scores else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "version": self.version,
            "template": self.template,
            "avg_score": self.avg_score,
            "runs": len(self.scores),
            "status": self.status,
            "created_at": self.created_at,
        }


class PromptEvolutionEngine:
    """Manages prompt version lineages with automatic promotion and retirement."""

    def __init__(self, decision_engine: AutonomousDecisionEngine) -> None:
        self.decision_engine = decision_engine
        self._registry: dict[str, list[PromptVersionRecord]] = {}

    def register(self, prompt_id: str, version: str, template: str) -> None:
        """Register a new prompt version."""
        if prompt_id not in self._registry:
            self._registry[prompt_id] = []
        self._registry[prompt_id].append(PromptVersionRecord(prompt_id, version, template))

    def record_run(
        self,
        prompt_id: str,
        version: str,
        quality: float,
        cost: float = 0.0,
        latency_ms: float = 0.0,
        audience_score: float = 0.0,
    ) -> None:
        """Record outcome of a prompt run and evaluate promotion/retirement."""
        records = self._registry.get(prompt_id, [])
        record = next((r for r in records if r.version == version), None)
        if record is None:
            self.register(prompt_id, version, f"auto-registered-{prompt_id}-{version}")
            record = self._registry[prompt_id][-1]

        record.scores.append(quality)
        record.costs.append(cost)
        record.latencies_ms.append(latency_ms)
        record.audience_scores.append(audience_score)

        # Evaluate after 3+ runs
        if len(record.scores) >= 3:
            avg = record.avg_score
            if avg >= PROMOTE_THRESHOLD and record.status == "active":
                record.status = "promoted"
                strategic_memory.record("successful_experiments", {
                    "prompt_id": prompt_id, "version": version, "avg_score": avg,
                    "action": "promoted",
                })
                self.decision_engine.submit(Recommendation(
                    source="PromptEvolutionEngine",
                    priority="creative",
                    action="promote_prompt_version",
                    target="prompt_library",
                    payload={"prompt_id": prompt_id, "version": version, "avg_score": avg},
                    estimated_impact=3.5,
                ))
            elif avg < RETIRE_THRESHOLD and record.status == "active":
                record.status = "retired"
                strategic_memory.record("failed_experiments", {
                    "prompt_id": prompt_id, "version": version, "avg_score": avg,
                    "action": "retired",
                })
                self.decision_engine.submit(Recommendation(
                    source="PromptEvolutionEngine",
                    priority="creative",
                    action="retire_prompt_version",
                    target="prompt_library",
                    payload={"prompt_id": prompt_id, "version": version, "avg_score": avg},
                    estimated_impact=2.0,
                ))

    def get_registry(self) -> list[dict[str, Any]]:
        result = []
        for versions in self._registry.values():
            result.extend(v.to_dict() for v in versions)
        return result

    def get_active_best(self, prompt_id: str) -> dict[str, Any] | None:
        """Return the highest-scoring active or promoted version."""
        versions = self._registry.get(prompt_id, [])
        eligible = [v for v in versions if v.status in ("active", "promoted")]
        if not eligible:
            return None
        return max(eligible, key=lambda v: v.avg_score).to_dict()
