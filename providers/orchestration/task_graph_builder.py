import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from providers.orchestration.planning_engine import ExecutionPlan

logger = logging.getLogger("task_graph_builder")

class TaskNode(BaseModel):
    """Individual node in the Directed Acyclic Graph (DAG)."""
    node_id: str
    target_agent: str
    action_type: str
    depends_on: List[str] = Field(default_factory=list)
    estimated_duration_sec: int = 30
    priority: int = 5
    retry_policy: Dict[str, Any] = Field(default_factory=lambda: {"max_retries": 3, "backoff_sec": 5})
    resource_requirements: Dict[str, Any] = Field(default_factory=dict)
    status: str = "PENDING"  # PENDING, READY, RUNNING, SUCCESS, FAILED, SKIPPED, REPLANNED
    result_data: Optional[Dict[str, Any]] = None

class ExecutionDAG(BaseModel):
    """Directed Acyclic Graph (DAG) representation of orchestrated tasks."""
    graph_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: str
    nodes: Dict[str, TaskNode] = Field(default_factory=dict)
    critical_path: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class TaskGraphBuilder:
    """Task Graph Builder converting high-level ExecutionPlans into executable DAG graphs."""

    def build_graph(self, plan: ExecutionPlan) -> ExecutionDAG:
        nodes: Dict[str, TaskNode] = {}

        if "ResearchAgent" in plan.required_agents:
            nodes["node_research"] = TaskNode(
                node_id="node_research", target_agent="ResearchAgent", action_type="RUN_RESEARCH", estimated_duration_sec=40
            )

        script_deps = ["node_research"] if "node_research" in nodes else []
        nodes["node_script"] = TaskNode(
            node_id="node_script", target_agent="ScriptAgent", action_type="RUN_SCRIPT", depends_on=script_deps, estimated_duration_sec=30
        )

        nodes["node_image"] = TaskNode(
            node_id="node_image", target_agent="ImageAgent", action_type="RUN_IMAGE", depends_on=["node_script"], estimated_duration_sec=60, resource_requirements={"gpu": True}
        )

        nodes["node_voice"] = TaskNode(
            node_id="node_voice", target_agent="VoiceAgent", action_type="RUN_VOICE", depends_on=["node_script"], estimated_duration_sec=30
        )

        nodes["node_video"] = TaskNode(
            node_id="node_video", target_agent="VideoAgent", action_type="RUN_VIDEO", depends_on=["node_image", "node_voice"], estimated_duration_sec=90, resource_requirements={"gpu": True}
        )

        nodes["node_subtitle"] = TaskNode(
            node_id="node_subtitle", target_agent="SubtitleAgent", action_type="RUN_SUBTITLE", depends_on=["node_video"], estimated_duration_sec=20
        )

        nodes["node_music"] = TaskNode(
            node_id="node_music", target_agent="MusicAgent", action_type="RUN_MUSIC", depends_on=["node_video"], estimated_duration_sec=20
        )

        nodes["node_thumbnail"] = TaskNode(
            node_id="node_thumbnail", target_agent="ThumbnailAgent", action_type="RUN_THUMBNAIL", depends_on=["node_script"], estimated_duration_sec=25
        )

        nodes["node_quality"] = TaskNode(
            node_id="node_quality", target_agent="QualityAgent", action_type="RUN_QUALITY", depends_on=["node_subtitle", "node_music", "node_thumbnail"], estimated_duration_sec=15
        )

        nodes["node_publish"] = TaskNode(
            node_id="node_publish", target_agent="PublishingProvider", action_type="PUBLISH_CONTENT", depends_on=["node_quality"], estimated_duration_sec=40
        )

        critical_path = ["node_script", "node_image", "node_video", "node_quality", "node_publish"]

        dag = ExecutionDAG(
            graph_id=str(uuid.uuid4()),
            plan_id=plan.plan_id,
            nodes=nodes,
            critical_path=critical_path
        )

        logger.info(f"[TaskGraphBuilder] Built DAG '{dag.graph_id}' with {len(nodes)} nodes (Critical Path length: {len(critical_path)})")
        return dag

task_graph_builder = TaskGraphBuilder()
ZOOMING = "zoom"
