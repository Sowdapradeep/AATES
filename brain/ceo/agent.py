from typing import Any
from brain.agent_base import AgentBase
from runtime.registry.registry import agent_registry

class CEOAgent(AgentBase):
    """Chief Executive Officer Agent managing production flows, budgets, and release timelines."""
    
    def __init__(self) -> None:
        super().__init__(name="CEO Agent", version="1.0.0")
        agent_registry.register(self)
        self._quality_feedback: list[dict[str, Any]] = []

    async def run_task(self, task_payload: dict[str, Any]) -> dict[str, Any]:
        """Orchestrates episode queues and triggers production scheduler tasks."""
        self.metrics["execution_count"] += 1
        
        # Standard decision explainability logging
        await self.log_decision(
            decision_type="Episode Queue Scheduling",
            inputs=task_payload,
            constraints=["Allocated budget limit", "Target deadline"],
            alternatives=["Trigger episode production immediately", "Buffer task queue"],
            selected="Trigger episode production immediately",
            confidence=0.95
        )
        return {
            "status": "success",
            "actor": self.name,
            "result": "Triggered production pipeline execution."
        }

    async def ingest_quality_feedback(self, feedback: dict[str, Any]) -> dict[str, Any]:
        """
        Ingests production quality and performance metrics from the review pipeline.
        These metrics inform future episode planning decisions automatically.
        """
        self.metrics["execution_count"] += 1
        self._quality_feedback.append(feedback)

        # Derive planning adjustments from feedback
        avg_score = feedback.get("overall_score", 100.0)
        revision_count = feedback.get("revision_count", 0)

        # Log an explainable decision based on feedback
        adjustments = []
        if avg_score < 80:
            adjustments.append("Increase dialogue quality threshold for next episode.")
        if revision_count > 2:
            adjustments.append("Pre-screen dialogue with Dialogue Critic before full render.")

        await self.log_decision(
            decision_type="Quality Feedback Integration",
            inputs=feedback,
            constraints=["Quality threshold ≥ 80", "Max revisions ≤ 2"],
            alternatives=["Maintain current pipeline", "Adjust critic weights"],
            selected="Adjust critic weights" if adjustments else "Maintain current pipeline",
            confidence=0.88 if adjustments else 0.97
        )

        return {
            "status": "feedback_ingested",
            "adjustments_applied": adjustments,
            "total_feedback_records": len(self._quality_feedback),
        }

    def get_quality_feedback_summary(self) -> dict[str, Any]:
        """Returns summary of all quality feedback ingested by the CEO agent."""
        if not self._quality_feedback:
            return {"total_records": 0, "avg_score": None, "adjustments": []}
        scores = [f.get("overall_score", 0) for f in self._quality_feedback]
        return {
            "total_records": len(self._quality_feedback),
            "avg_score": round(sum(scores) / len(scores), 2),
            "latest_feedback": self._quality_feedback[-1],
        }

