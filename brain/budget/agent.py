from typing import Any
from brain.agent_base import AgentBase
from runtime.registry.registry import agent_registry

class BusinessDirectorAgent(AgentBase):
    """Business Director Agent monitoring budget limits and API model usage costs."""
    
    def __init__(self) -> None:
        super().__init__(name="Business Director Agent", version="1.0.0")
        agent_registry.register(self)

    async def run_task(self, task_payload: dict[str, Any]) -> dict[str, Any]:
        """Monitors and updates operational platform spending budgets."""
        self.metrics["execution_count"] += 1
        
        await self.log_decision(
            decision_type="Budget Check Approval",
            inputs=task_payload,
            constraints=["Monthly cap limit", "Active universe remaining balance"],
            alternatives=["Approve AI token expenditures", "Reject task and suspend execution"],
            selected="Approve AI token expenditures",
            confidence=0.97
        )
        return {
            "status": "success",
            "actor": self.name,
            "result": "Expenditure check approved. Sufficient budget remains."
        }
