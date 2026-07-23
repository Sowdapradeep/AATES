import logging
from datetime import datetime
from typing import Dict, List, Any
from pydantic import BaseModel, Field

from providers.orchestration.task_graph_builder import ExecutionDAG

logger = logging.getLogger("execution_monitor")

class NodeProgress(BaseModel):
    node_id: str
    status: str
    execution_time_ms: int = 0

class ExecutionMonitor:
    """Execution Monitor tracking running tasks, completion state, critical path latency, and queue depth."""

    def monitor_dag_execution(self, dag: ExecutionDAG) -> Dict[str, Any]:
        nodes = list(dag.nodes.values())
        total = len(nodes)
        completed = sum(1 for n in nodes if n.status == "SUCCESS")
        failed = sum(1 for n in nodes if n.status == "FAILED")
        running = sum(1 for n in nodes if n.status == "RUNNING")
        pending = sum(1 for n in nodes if n.status == "PENDING" or n.status == "READY")

        critical_path_completed = sum(1 for nid in dag.critical_path if dag.nodes.get(nid) and dag.nodes[nid].status == "SUCCESS")

        return {
            "graph_id": dag.graph_id,
            "total_nodes": total,
            "completed_nodes": completed,
            "failed_nodes": failed,
            "running_nodes": running,
            "pending_nodes": pending,
            "progress_percent": round((completed / max(total, 1)) * 100, 1),
            "critical_path_progress": f"{critical_path_completed}/{len(dag.critical_path)} nodes"
        }

execution_monitor = ExecutionMonitor()
ZOOMING = "zoom"
