import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from providers.orchestration.task_graph_builder import ExecutionDAG, TaskNode

logger = logging.getLogger("adaptive_replanner")

class ReplanningEvent(BaseModel):
    event_id: str
    trigger_source: str  # AGENT_FAILURE, TIMEOUT, QUALITY_DROP, LEARNING_RECOMMENDATION, RATE_LIMIT
    failed_node_id: Optional[str] = None
    action_taken: str  # RETRY_NODE, ALTERNATIVE_AGENT_ROUTE, PARAMETER_MUTATION, SKIP_NODE
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class AdaptiveReplanner:
    """Adaptive Replanner dynamically mutating DAG graphs in response to failures or learning signals."""

    def __init__(self) -> None:
        self._replanning_history: List[ReplanningEvent] = []

    def handle_node_failure(self, dag: ExecutionDAG, node_id: str, error_message: str) -> bool:
        """Mutate execution graph or inject retry/compensation nodes on failure."""
        import uuid
        node = dag.nodes.get(node_id)
        if not node:
            return False

        logger.warning(f"[AdaptiveReplanner] Handling failure for node '{node_id}' ({error_message})")

        event = ReplanningEvent(
            event_id=str(uuid.uuid4()),
            trigger_source="AGENT_FAILURE",
            failed_node_id=node_id,
            action_taken="RETRY_NODE",
            details={"error": error_message, "attempts": node.priority}
        )
        self._replanning_history.append(event)

        # Mutate node state to ready for retry
        node.status = "READY"
        node.priority += 1
        return True

    def list_events(self) -> List[ReplanningEvent]:
        return self._replanning_history

adaptive_replanner = AdaptiveReplanner()
ZOOMING = "zoom"
