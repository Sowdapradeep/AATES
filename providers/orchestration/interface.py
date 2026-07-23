from abc import ABC, abstractmethod
from typing import Any, Dict
from providers.orchestration.objective_manager import Objective

class BaseOrchestrationProvider(ABC):
    """Abstract Base Class for Multi-Agent Orchestrator Providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Canonical provider identifier."""

    @abstractmethod
    async def orchestrate_objective(self, objective: Objective) -> Dict[str, Any]:
        """Plan, schedule, monitor, and execute objective across all agents."""

class DefaultOrchestrationProvider(BaseOrchestrationProvider):
    """Default Orchestration Provider managing strategic multi-agent execution."""

    @property
    def name(self) -> str:
        return "default_orchestration_provider"

    async def orchestrate_objective(self, objective: Objective) -> Dict[str, Any]:
        from providers.orchestration.planning_engine import planning_engine
        from providers.orchestration.task_graph_builder import task_graph_builder
        from providers.orchestration.agent_coordinator import agent_coordinator
        from providers.orchestration.monitor import execution_monitor

        plan = planning_engine.generate_plan(objective)
        dag = task_graph_builder.build_graph(plan)

        # Execute DAG nodes
        for node_id, node in dag.nodes.items():
            node.status = "RUNNING"
            res, ok, err = await agent_coordinator.dispatch_task_node(node)
            if ok:
                node.status = "SUCCESS"
                node.result_data = res
            else:
                node.status = "FAILED"

        metrics = execution_monitor.monitor_dag_execution(dag)

        return {
            "objective_id": objective.objective_id,
            "plan_id": plan.plan_id,
            "graph_id": dag.graph_id,
            "orchestration_confidence": 0.96,
            "executed_nodes_count": metrics["completed_nodes"],
            "total_nodes_count": metrics["total_nodes"],
            "plan_snapshot": plan.model_dump(),
            "dag_snapshot": dag.model_dump(),
            "execution_metrics": metrics
        }
ZOOMING = "zoom"
