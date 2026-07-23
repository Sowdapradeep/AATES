import uuid
import pytest
import asyncio
from datetime import datetime

from core.database.models import (
    OrchestrationJob,
    ObjectiveModel,
    ExecutionPlanModel,
    ExecutionGraphModel,
    TaskNodeModel,
    OrchestrationPackage,
    OrchestrationVersion,
    ResourceReservationModel
)
from providers.orchestration.objective_manager import objective_manager, Objective
from providers.orchestration.planning_engine import planning_engine, ExecutionPlan
from providers.orchestration.task_graph_builder import task_graph_builder, ExecutionDAG, TaskNode
from providers.orchestration.scheduler import scheduling_engine
from providers.orchestration.agent_coordinator import agent_coordinator
from providers.orchestration.monitor import execution_monitor
from providers.orchestration.replanner import adaptive_replanner
from providers.orchestration.resource_manager import orchestrator_resource_manager
from brain.agents.orchestrator_agent import process_orchestration_job


# 1. Objective Manager Tests
def test_objective_manager():
    objs = objective_manager.list_objectives()
    assert len(objs) >= 3  # 3 pre-registered defaults

    custom = objective_manager.create_objective(
        title="Test Bulk Campaign",
        objective_type="BULK_CAMPAIGN_EXECUTION",
        target_platform="instagram",
        priority=10,
        parameters={"campaign_size": 5}
    )
    assert custom.objective_type == "BULK_CAMPAIGN_EXECUTION"
    assert custom.target_platform == "instagram"

    fetched = objective_manager.get_objective(custom.objective_id)
    assert fetched is not None
    assert fetched.title == "Test Bulk Campaign"


# 2. Planning Engine Tests
def test_planning_engine():
    obj = objective_manager.get_objective("obj_longform_001")
    assert obj is not None

    plan = planning_engine.generate_plan(obj)
    assert plan.plan_id is not None
    assert plan.objective_id == obj.objective_id
    assert "ResearchAgent" in plan.required_agents
    assert plan.estimated_duration_sec == 420
    assert plan.risk_score <= 0.15
    assert plan.parallelism_factor >= 2

    shorts_obj = objective_manager.create_objective(
        title="Shorts Pipeline",
        objective_type="GENERATE_SHORTS",
        target_platform="instagram"
    )
    shorts_plan = planning_engine.generate_plan(shorts_obj)
    assert "SubtitleAgent" in shorts_plan.required_agents
    assert shorts_plan.estimated_duration_sec == 180


# 3. Task Graph Builder (DAG) Tests
def test_task_graph_builder():
    obj = objective_manager.get_objective("obj_longform_001")
    plan = planning_engine.generate_plan(obj)

    dag = task_graph_builder.build_graph(plan)
    assert dag.graph_id is not None
    assert dag.plan_id == plan.plan_id
    assert len(dag.nodes) >= 8
    assert "node_script" in dag.nodes
    assert "node_video" in dag.nodes
    assert "node_quality" in dag.nodes
    assert "node_publish" in dag.nodes

    # Critical path validation
    assert len(dag.critical_path) >= 3
    assert "node_video" in dag.critical_path
    assert "node_quality" in dag.critical_path
    assert "node_publish" in dag.critical_path

    # Dependency resolution test
    video_node = dag.nodes["node_video"]
    assert "node_image" in video_node.depends_on
    assert "node_voice" in video_node.depends_on


# 4. Scheduling Engine Tests
def test_scheduling_engine():
    initial_gpu = scheduling_engine.available_gpu_slots
    initial_workers = scheduling_engine.available_worker_slots

    # Reserve GPU resource
    res = scheduling_engine.reserve_resources("node_video", {"gpu": True})
    assert res is not None
    assert res.resource_type == "GPU"
    assert scheduling_engine.available_gpu_slots == initial_gpu - 1

    # Reserve worker resource
    worker_res = scheduling_engine.reserve_resources("node_script", {})
    assert worker_res is not None
    assert worker_res.resource_type == "WORKER_SLOT"
    assert scheduling_engine.available_worker_slots == initial_workers - 1

    # Release GPU reservation
    scheduling_engine.release_reservation(res.reservation_id)
    assert scheduling_engine.available_gpu_slots == initial_gpu

    # Release worker reservation
    scheduling_engine.release_reservation(worker_res.reservation_id)
    assert scheduling_engine.available_worker_slots == initial_workers


# 5. Agent Coordinator Dispatch Tests
@pytest.mark.asyncio
async def test_agent_coordinator():
    node = TaskNode(
        node_id="node_test_dispatch",
        target_agent="ScriptAgent",
        action_type="RUN_SCRIPT",
        estimated_duration_sec=30
    )
    result, ok, err = await agent_coordinator.dispatch_task_node(node)

    assert ok is True
    assert err is None
    assert result["node_id"] == "node_test_dispatch"
    assert result["target_agent"] == "ScriptAgent"
    assert result["status"] == "COMPLETED"


# 6. Execution Monitor Tests
def test_execution_monitor():
    obj = objective_manager.get_objective("obj_longform_001")
    plan = planning_engine.generate_plan(obj)
    dag = task_graph_builder.build_graph(plan)

    # Mark some nodes complete
    dag.nodes["node_script"].status = "SUCCESS"
    dag.nodes["node_image"].status = "SUCCESS"

    metrics = execution_monitor.monitor_dag_execution(dag)

    assert metrics["total_nodes"] == len(dag.nodes)
    assert metrics["completed_nodes"] == 2
    assert metrics["progress_percent"] > 0.0


# 7. Adaptive Replanner Tests
def test_adaptive_replanner():
    obj = objective_manager.get_objective("obj_longform_001")
    plan = planning_engine.generate_plan(obj)
    dag = task_graph_builder.build_graph(plan)

    # Simulate a node failure
    dag.nodes["node_voice"].status = "FAILED"
    result = adaptive_replanner.handle_node_failure(dag, "node_voice", "VoiceAgent timeout after 30s")

    assert result is True
    assert dag.nodes["node_voice"].status == "READY"

    events = adaptive_replanner.list_events()
    assert len(events) >= 1
    assert events[-1].failed_node_id == "node_voice"
    assert events[-1].trigger_source == "AGENT_FAILURE"
    assert events[-1].action_taken == "RETRY_NODE"


# 8. Background Orchestrator Agent Worker Processing
@pytest.mark.asyncio
async def test_orchestrator_agent_job_processing(db):
    job = OrchestrationJob(
        id=uuid.uuid4(),
        status="PROCESSING",
        stage="OBJECTIVE_ANALYSIS",
        objective_type="GENERATE_LONGFORM_VIDEO",
        target_platform="all"
    )
    db.add(job)
    db.commit()

    await process_orchestration_job(db, job)

    db.refresh(job)
    assert job.status == "SUCCESS"
    assert job.stage == "COMPLETED"
    assert job.progress == 1.0

    # Verify OrchestrationPackage was created
    assert len(job.packages) == 1
    pkg = job.packages[0]
    assert pkg.orchestration_confidence >= 0.90
    assert pkg.executed_nodes_count >= 1
    assert pkg.package_manifest["package_type"] == "OrchestrationPackage"
    assert pkg.package_manifest["objective_id"] is not None


# 9. REST API Endpoints Tests
def test_api_orchestration_routes(client, db):
    # 1. POST /v1/orchestration (create)
    resp = client.post("/v1/orchestration", json={
        "objective_type": "GENERATE_LONGFORM_VIDEO",
        "target_platform": "youtube",
        "priority": 8
    })
    assert resp.status_code == 200
    job_data = resp.json()
    job_id = job_data["id"]
    assert job_data["status"] == "QUEUED"
    assert job_data["objective_type"] == "GENERATE_LONGFORM_VIDEO"

    # 2. GET /v1/orchestration (list)
    resp = client.get("/v1/orchestration")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 3. GET /v1/orchestration/metrics (metrics)
    resp = client.get("/v1/orchestration/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_active_objectives" in data
    assert data["total_active_objectives"] >= 3

    # 4. GET /v1/orchestration/objectives
    resp = client.get("/v1/orchestration/objectives")
    assert resp.status_code == 200
    assert len(resp.json()) >= 3

    # 5. GET /v1/orchestration/plans
    resp = client.get("/v1/orchestration/plans")
    assert resp.status_code == 200

    # 6. GET /v1/orchestration/{id} (detail)
    resp = client.get(f"/v1/orchestration/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id

    # 7. POST /v1/orchestration/{id}/pause
    resp = client.post(f"/v1/orchestration/{job_id}/pause")
    assert resp.status_code == 200
    assert resp.json()["status"] == "PAUSED"

    # 8. POST /v1/orchestration/{id}/resume
    resp = client.post(f"/v1/orchestration/{job_id}/resume")
    assert resp.status_code == 200
    assert resp.json()["status"] == "QUEUED"

    # 9. POST /v1/orchestration/{id}/cancel
    resp = client.post(f"/v1/orchestration/{job_id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"
