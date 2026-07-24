import asyncio
import datetime
import logging
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from core.database.session import SessionLocal
from core.database.models import (
    OrchestrationJob,
    ObjectiveModel,
    ExecutionPlanModel,
    ExecutionGraphModel,
    TaskNodeModel,
    OrchestrationPackage,
    OrchestrationVersion,
    WorkerHeartbeat
)
from providers.orchestration.objective_manager import objective_manager, Objective
from providers.orchestration.planning_engine import planning_engine
from providers.orchestration.task_graph_builder import task_graph_builder
from providers.orchestration.scheduler import scheduling_engine
from providers.orchestration.agent_coordinator import agent_coordinator
from providers.orchestration.monitor import execution_monitor
from providers.orchestration.replanner import adaptive_replanner

logger = logging.getLogger("orchestrator_agent")

AGENT_STATE = {
    "is_running": False,
    "started_at": None,
    "jobs_processed": 0,
    "jobs_succeeded": 0,
    "jobs_failed": 0,
    "total_duration_sec": 0.0
}

_worker_tasks = []

STAGES = {
    "OBJECTIVE_ANALYSIS": 0.1,
    "PLAN_GENERATION": 0.25,
    "TASK_GRAPH_BUILDING": 0.40,
    "RESOURCE_ALLOCATION": 0.55,
    "WORKFLOW_DISPATCH": 0.70,
    "EXECUTION_MONITORING": 0.85,
    "ADAPTIVE_REPLANNING": 0.90,
    "FINALIZATION": 0.95,
    "COMPLETED": 1.0
}

async def process_orchestration_job(db: Session, job: OrchestrationJob) -> None:
    start_time = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    job.started_at = start_time
    job.status = "PROCESSING"
    job.stage = "OBJECTIVE_ANALYSIS"
    job.progress = STAGES["OBJECTIVE_ANALYSIS"]
    db.commit()

    try:
        # Stage 1: OBJECTIVE_ANALYSIS
        obj = objective_manager.get_objective("obj_longform_001")
        if not obj:
            obj = objective_manager.create_objective(
                title=f"Orchestration Objective for Job {job.id}",
                objective_type=job.objective_type or "GENERATE_LONGFORM_VIDEO",
                target_platform=job.target_platform or "all"
            )

        # Stage 2: PLAN_GENERATION
        job.stage = "PLAN_GENERATION"
        job.progress = STAGES["PLAN_GENERATION"]
        db.commit()

        plan = planning_engine.generate_plan(obj)

        # Stage 3: TASK_GRAPH_BUILDING
        job.stage = "TASK_GRAPH_BUILDING"
        job.progress = STAGES["TASK_GRAPH_BUILDING"]
        db.commit()

        dag = task_graph_builder.build_graph(plan)

        # Stage 4: RESOURCE_ALLOCATION
        job.stage = "RESOURCE_ALLOCATION"
        job.progress = STAGES["RESOURCE_ALLOCATION"]
        db.commit()

        for node_id, node in dag.nodes.items():
            if node.resource_requirements:
                scheduling_engine.reserve_resources(node_id, node.resource_requirements)

        # Stage 5: WORKFLOW_DISPATCH
        job.stage = "WORKFLOW_DISPATCH"
        job.progress = STAGES["WORKFLOW_DISPATCH"]
        db.commit()

        for node_id, node in dag.nodes.items():
            node.status = "RUNNING"
            res, ok, err = await agent_coordinator.dispatch_task_node(node)
            if ok:
                node.status = "SUCCESS"
                node.result_data = res
            else:
                node.status = "FAILED"
                adaptive_replanner.handle_node_failure(dag, node_id, err or "Dispatch failure")

        # Stage 6: EXECUTION_MONITORING
        job.stage = "EXECUTION_MONITORING"
        job.progress = STAGES["EXECUTION_MONITORING"]
        db.commit()

        metrics = execution_monitor.monitor_dag_execution(dag)

        # Stage 7: ADAPTIVE_REPLANNING
        job.stage = "ADAPTIVE_REPLANNING"
        job.progress = STAGES["ADAPTIVE_REPLANNING"]
        db.commit()

        # Stage 8: FINALIZATION
        job.stage = "FINALIZATION"
        job.progress = STAGES["FINALIZATION"]
        db.commit()

        # Build Package Manifest
        manifest = {
            "package_type": "OrchestrationPackage",
            "version": "1.0",
            "objective_id": obj.objective_id,
            "plan_id": plan.plan_id,
            "graph_id": dag.graph_id,
            "total_nodes": metrics["total_nodes"],
            "completed_nodes": metrics["completed_nodes"]
        }

        telemetry = {
            "planning_metrics": {"plan_id": plan.plan_id, "required_agents": len(plan.required_agents)},
            "scheduling_metrics": {"resource_slots_allocated": len(dag.nodes)},
            "dispatch_metrics": {"successful_dispatches": metrics["completed_nodes"]},
            "resource_metrics": {"gpu_reservations": 1},
            "execution_metrics": metrics,
            "replanning_metrics": {"events_count": len(adaptive_replanner.list_events())},
            "critical_path_metrics": {"critical_path": dag.critical_path}
        }

        orchestration_pkg = OrchestrationPackage(
            id=uuid.uuid4(),
            job_id=job.id,
            objective_type=obj.objective_type,
            target_platform=job.target_platform,
            orchestration_confidence=0.96,
            executed_nodes_count=metrics["completed_nodes"],
            total_nodes_count=metrics["total_nodes"],
            plan_snapshot=plan.model_dump(),
            dag_snapshot=dag.model_dump(),
            package_manifest=manifest,
            version=1,
            source_agent="OrchestratorAgent",
            provider="DefaultOrchestratorProvider",
            model="AATES-Orchestrator-v1",
            prompt_version="v1.0",
            quality_score=0.96,
            telemetry_metadata=telemetry
        )
        db.add(orchestration_pkg)
        db.flush()

        version_snapshot = OrchestrationVersion(
            id=uuid.uuid4(),
            orchestration_package_id=orchestration_pkg.id,
            version=1,
            lineage_action="INITIAL",
            assets_snapshot=[manifest]
        )
        db.add(version_snapshot)

        # Stage 9: COMPLETED
        end_time = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        duration = (end_time - start_time).total_seconds()

        job.status = "SUCCESS"
        job.stage = "COMPLETED"
        job.progress = STAGES["COMPLETED"]
        job.completed_at = end_time
        job.duration_sec = duration
        db.commit()

        AGENT_STATE["jobs_processed"] += 1
        AGENT_STATE["jobs_succeeded"] += 1
        AGENT_STATE["total_duration_sec"] += duration
        logger.info(f"[OrchestratorAgent] Job {job.id} completed successfully in {duration:.2f}s")

    except Exception as e:
        db.rollback()
        end_time = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        duration = (end_time - start_time).total_seconds()

        job.status = "FAILED"
        job.failed_at = end_time
        job.duration_sec = duration
        job.error_code = "ORCHESTRATION_ERROR"
        job.error_message = str(e)
        db.commit()

        AGENT_STATE["jobs_processed"] += 1
        AGENT_STATE["jobs_failed"] += 1
        logger.error(f"[OrchestratorAgent] Job {job.id} failed: {e}", exc_info=True)

async def _orchestrator_worker_loop(worker_id: str) -> None:
    logger.info(f"[OrchestratorAgent] Starting background worker loop: {worker_id}")
    while AGENT_STATE["is_running"]:
        db = SessionLocal()
        try:
            hb = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id == worker_id).first()
            if not hb:
                hb = WorkerHeartbeat(worker_id=worker_id, last_heartbeat_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None))
                db.add(hb)
            else:
                hb.last_heartbeat_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
            db.commit()

            job = db.query(OrchestrationJob).filter(OrchestrationJob.status == "QUEUED").order_by(OrchestrationJob.priority.desc(), OrchestrationJob.created_at.asc()).with_for_update(skip_locked=True).first()
            if job:
                job.worker_id = worker_id
                db.commit()
                await process_orchestration_job(db, job)
            else:
                await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"[OrchestratorAgent] Error in worker loop {worker_id}: {e}", exc_info=True)
            await asyncio.sleep(3)
        finally:
            db.close()

async def start_orchestrator_agent() -> None:
    if AGENT_STATE["is_running"]:
        return
    AGENT_STATE["is_running"] = True
    AGENT_STATE["started_at"] = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    logger.info("[OrchestratorAgent] Initializing background daemon...")
    for i in range(2):
        worker_id = f"orchestrator-worker-{i}"
        task = asyncio.create_task(_orchestrator_worker_loop(worker_id))
        _worker_tasks.append(task)

async def stop_orchestrator_agent() -> None:
    if not AGENT_STATE["is_running"]:
        return
    AGENT_STATE["is_running"] = False
    for task in _worker_tasks:
        task.cancel()
    _worker_tasks.clear()
    logger.info("[OrchestratorAgent] Stopped background daemon.")
ZOOMING = "zoom"
