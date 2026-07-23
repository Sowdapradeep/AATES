import asyncio
import datetime
import json
import logging
import time
import uuid
from typing import Any, List, Optional

from sqlalchemy.orm import Session

from core.database.session import SessionLocal
from core.database.models import (
    AutomationJob,
    AutomationTrigger,
    AutomationDecision,
    AutomationWorkflowInstance,
    AutomationWorkflowStepExecution,
    AutomationPackage,
    AutomationVersion,
    WorkerHeartbeat
)
from providers.automation.trigger_manager import trigger_manager, TriggerEvent
from providers.automation.policy_engine import policy_engine
from providers.automation.decision_engine import decision_engine
from providers.automation.workflow_definition import workflow_registry
from providers.automation.workflow_executor import workflow_executor, WorkflowInstance
from providers.automation.context import ExecutionContext

logger = logging.getLogger("automation_agent")

STAGES = {
    "WAITING": 0.10,
    "TRIGGER_EVALUATION": 0.25,
    "POLICY_MATCHING": 0.40,
    "DECISION_GENERATION": 0.55,
    "ACTION_EXECUTION": 0.75,
    "OUTCOME_VALIDATION": 0.90,
    "AUDIT_LOGGING": 0.95,
    "COMPLETED": 1.0,
    "FAILED": 1.0
}

_TRANSITIONS = {
    "QUEUED": {"PROCESSING", "CANCELLED"},
    "PROCESSING": {"SUCCESS", "FAILED", "CANCELLED"},
    "FAILED": {"QUEUED"},
    "CANCELLED": {"QUEUED"},
    "SUCCESS": set()
}

def is_valid_transition(current: str, target: str) -> bool:
    return target in _TRANSITIONS.get(current, set())

AGENT_STATE = {
    "is_running": False,
    "started_at": None,
    "jobs_processed": 0,
    "jobs_succeeded": 0,
    "jobs_failed": 0,
    "total_duration_sec": 0.0
}

_worker_tasks = []

def update_worker_heartbeat(db: Session, worker_id: str) -> None:
    try:
        hb = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id == worker_id).first()
        if not hb:
            hb = WorkerHeartbeat(worker_id=worker_id, last_heartbeat_at=datetime.datetime.utcnow())
            db.add(hb)
        else:
            hb.last_heartbeat_at = datetime.datetime.utcnow()
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Failed to update heartbeat for {worker_id}: {str(e)}")

def recover_orphaned_jobs(db: Session) -> None:
    try:
        orphans = db.query(AutomationJob).filter(AutomationJob.status == "PROCESSING").all()
        for job in orphans:
            logger.info(f"Resetting orphaned automation job {job.id} back to QUEUED.")
            job.status = "QUEUED"
            job.stage = "WAITING"
            job.progress = 0.0
            job.attempts += 1
            if job.attempts >= job.max_attempts:
                job.status = "FAILED"
                job.failed_at = datetime.datetime.utcnow()
                job.error_code = "ORPHANED_LIMIT"
                job.error_message = "Job orphaned repeatedly."
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Orphaned recovery failed: {str(e)}")

async def process_automation_job(db: Session, job: AutomationJob, worker_id: str = "automation-worker-0") -> None:
    correlation_id = str(uuid.uuid4())
    logger.info(json.dumps({
        "event": "Automation Workflow Execution Started",
        "job_id": str(job.id),
        "trigger_type": job.trigger_type,
        "worker_id": worker_id,
        "correlation_id": correlation_id
    }))

    start_time = time.monotonic()
    job_id = job.id

    try:
        # Stage 1: TRIGGER_EVALUATION
        job.stage = "TRIGGER_EVALUATION"
        job.progress = STAGES["TRIGGER_EVALUATION"]
        db.commit()

        trigger = TriggerEvent(
            trigger_id=str(uuid.uuid4()),
            trigger_type=job.trigger_type,
            source_component="AutomationJobWorker",
            source_package_id=str(job.source_package_id) if job.source_package_id else None,
            target_platform=job.target_platform
        )

        db_trig = AutomationTrigger(
            id=uuid.uuid4(),
            trigger_id=trigger.trigger_id,
            trigger_type=trigger.trigger_type,
            source_component=trigger.source_component,
            source_package_id=job.source_package_id,
            target_platform=trigger.target_platform,
            event_data=trigger.event_data
        )
        db.add(db_trig)

        # Stage 2: POLICY_MATCHING
        job.stage = "POLICY_MATCHING"
        job.progress = STAGES["POLICY_MATCHING"]
        db.commit()

        matched_policies = policy_engine.match_policies(trigger)
        selected_policy = matched_policies[0] if matched_policies else policy_engine.list_policies()[0]

        # Stage 3: DECISION_GENERATION
        job.stage = "DECISION_GENERATION"
        job.progress = STAGES["DECISION_GENERATION"]
        db.commit()

        decision = decision_engine.evaluate_decision(
            trigger=trigger,
            policy=selected_policy,
            package_context={"quality_score": 0.92, "learning_confidence": 0.88, "package_id": str(job.source_package_id) if job.source_package_id else None}
        )

        db_dec = AutomationDecision(
            id=uuid.uuid4(),
            policy_id=decision.policy_id,
            workflow_id=decision.workflow_id,
            is_approved=decision.is_approved,
            decision_reason=decision.decision_reason,
            confidence_score=decision.confidence_score,
            condition_evaluations=decision.condition_evaluations,
            resource_lock_acquired=decision.resource_lock_acquired
        )
        db.add(db_dec)
        db.flush()

        if not decision.is_approved:
            job.status = "FAILED"
            job.stage = "FAILED"
            job.failed_at = datetime.datetime.utcnow()
            job.error_code = "DECISION_REJECTED"
            job.error_message = decision.decision_reason
            db.commit()
            return

        # Stage 4: ACTION_EXECUTION
        job.stage = "ACTION_EXECUTION"
        job.progress = STAGES["ACTION_EXECUTION"]
        db.commit()

        wf_def = workflow_registry.get(decision.workflow_id) or workflow_registry.get("E2E_CONTENT_GENERATION")

        context = ExecutionContext(
            workflow_instance_id=str(uuid.uuid4()),
            trigger_data=trigger.model_dump(),
            package_references={"source_package_id": str(job.source_package_id)} if job.source_package_id else {},
            decision_outputs=decision.model_dump()
        )

        instance = WorkflowInstance(
            instance_id=context.workflow_instance_id,
            workflow_id=wf_def.workflow_id,
            trigger_id=trigger.trigger_id,
            policy_id=selected_policy.policy_id,
            execution_owner=worker_id,
            worker_lease_expires_at=(datetime.datetime.utcnow() + datetime.timedelta(seconds=120)).isoformat(),
            context=context
        )

        updated_instance = await workflow_executor.execute_workflow_instance(instance, wf_def)

        # Stage 5: OUTCOME_VALIDATION
        job.stage = "OUTCOME_VALIDATION"
        job.progress = STAGES["OUTCOME_VALIDATION"]
        db.commit()

        # Persist AutomationWorkflowInstance & StepExecutions
        db_instance = AutomationWorkflowInstance(
            id=uuid.uuid4(),
            instance_id=updated_instance.instance_id,
            workflow_id=updated_instance.workflow_id,
            trigger_id=updated_instance.trigger_id,
            policy_id=updated_instance.policy_id,
            status=updated_instance.status,
            current_step=updated_instance.current_step,
            execution_owner=updated_instance.execution_owner,
            started_at=datetime.datetime.fromisoformat(updated_instance.started_at) if updated_instance.started_at else None,
            completed_at=datetime.datetime.fromisoformat(updated_instance.completed_at) if updated_instance.completed_at else None,
            context_snapshot=updated_instance.context.model_dump(),
            compensation_log=updated_instance.compensation_log
        )
        db.add(db_instance)
        db.flush()

        for s_exec in updated_instance.step_executions:
            db_step = AutomationWorkflowStepExecution(
                id=uuid.uuid4(),
                instance_id=db_instance.id,
                step_id=s_exec.step_id,
                action_type=s_exec.action_type,
                target_agent=s_exec.target_agent,
                idempotency_key=s_exec.idempotency_key,
                status=s_exec.status,
                execution_ms=s_exec.execution_ms,
                result_data=s_exec.result_data,
                error_message=s_exec.error_message,
                compensation_executed=s_exec.compensation_executed
            )
            db.add(db_step)

        # Stage 6: AUDIT_LOGGING & Package Creation
        job.stage = "AUDIT_LOGGING"
        job.progress = STAGES["AUDIT_LOGGING"]
        db.commit()

        telemetry_metadata = {
            "trigger_metrics": {"trigger_type": job.trigger_type, "trigger_id": trigger.trigger_id},
            "policy_metrics": {"policy_id": selected_policy.policy_id, "priority": selected_policy.priority},
            "decision_metrics": {"is_approved": decision.is_approved, "confidence": decision.confidence_score},
            "workflow_metrics": {"workflow_id": wf_def.workflow_id, "steps_total": len(wf_def.steps)},
            "action_metrics": {"steps_executed": len(updated_instance.step_executions)},
            "compensation_metrics": {"compensations_triggered": len(updated_instance.compensation_log)},
            "retry_metrics": {"attempts": job.attempts},
            "resource_lock_metrics": {"lock_acquired": decision.resource_lock_acquired}
        }

        package_manifest = {
            "package_type": "AutomationPackage",
            "version": 1,
            "producer_agent": "automation_agent",
            "provider": "default_automation_provider",
            "workflow_id": wf_def.workflow_id,
            "policy_id": selected_policy.policy_id,
            "executed_actions_count": len(updated_instance.step_executions),
            "created_at": datetime.datetime.utcnow().isoformat()
        }

        auto_pkg = AutomationPackage(
            id=uuid.uuid4(),
            job_id=job.id,
            workflow_id=wf_def.workflow_id,
            policy_id=selected_policy.policy_id,
            target_platform=job.target_platform,
            execution_confidence=decision.confidence_score,
            executed_actions_count=len(updated_instance.step_executions),
            execution_context_snapshot=updated_instance.context.model_dump(),
            package_manifest=package_manifest,
            # BasePackageMixin fields
            version=1,
            parent_package_id=None,
            source_agent="automation_agent",
            provider="default_automation_provider",
            model="AATES-AutomationEngine-v1.0",
            prompt_version="v1.0",
            quality_score=decision.confidence_score,
            telemetry_metadata=telemetry_metadata
        )
        db.add(auto_pkg)
        db.flush()

        ver = AutomationVersion(
            id=uuid.uuid4(),
            automation_package_id=auto_pkg.id,
            version=1,
            parent_version=None,
            lineage_action="INITIAL",
            assets_snapshot=[{"workflow_id": wf_def.workflow_id, "status": updated_instance.status}]
        )
        db.add(ver)

        total_duration = time.monotonic() - start_time

        if is_valid_transition(job.status, "SUCCESS"):
            job.status = "SUCCESS"
            job.stage = "COMPLETED"
            job.progress = STAGES["COMPLETED"]
            job.completed_at = datetime.datetime.utcnow()
            job.duration_sec = total_duration
            db.add(job)
            db.commit()

        AGENT_STATE["jobs_succeeded"] += 1
        AGENT_STATE["total_duration_sec"] += total_duration
        AGENT_STATE["jobs_processed"] += 1

        logger.info(json.dumps({
            "event": "Automation Workflow Execution Completed",
            "job_id": str(job.id),
            "status": updated_instance.status,
            "duration_sec": total_duration,
            "correlation_id": correlation_id
        }))

    except Exception as e:
        error_msg = str(e)
        trig_type = job.trigger_type
        target_plat = job.target_platform

        try:
            db.rollback()
        except Exception:
            pass

        logger.error(json.dumps({
            "event": "Automation Workflow Execution Failed",
            "job_id": str(job_id),
            "error": error_msg,
            "correlation_id": correlation_id
        }))

        job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
        if not job:
            job = AutomationJob(
                id=job_id,
                trigger_type=trig_type,
                target_platform=target_plat
            )

        job.attempts += 1
        job.status = "FAILED"
        job.stage = "FAILED"
        job.progress = STAGES["FAILED"]
        job.failed_at = datetime.datetime.utcnow()
        job.error_code = "WORKFLOW_EXECUTION_ERROR"
        job.error_message = error_msg

        db.add(job)
        db.commit()
        AGENT_STATE["jobs_failed"] += 1
        AGENT_STATE["jobs_processed"] += 1

async def automation_worker_poll_loop(worker_id: str) -> None:
    logger.info(f"Automation Agent worker loop started for worker ID: {worker_id}")
    while AGENT_STATE["is_running"]:
        db = SessionLocal()
        try:
            update_worker_heartbeat(db, worker_id)

            query = db.query(AutomationJob).filter(
                AutomationJob.status == "QUEUED"
            ).order_by(
                AutomationJob.priority.desc(),
                AutomationJob.created_at.asc()
            )

            if db.bind.dialect.name == "sqlite":
                job = query.first()
            else:
                job = query.with_for_update(skip_locked=True).first()

            if job:
                if is_valid_transition(job.status, "PROCESSING"):
                    job.status = "PROCESSING"
                    job.started_at = datetime.datetime.utcnow()
                    db.commit()

                    await process_automation_job(db, job, worker_id)
                else:
                    logger.warning(f"Invalid transition from {job.status} to PROCESSING for job {job.id}")

        except Exception as e:
            logger.error(f"Exception inside Automation Worker loop iteration: {str(e)}")
        finally:
            db.close()

        await asyncio.sleep(2.0)

async def start_automation_agent(concurrency: int = 1) -> None:
    if AGENT_STATE["is_running"]:
        return
    AGENT_STATE["is_running"] = True
    AGENT_STATE["started_at"] = datetime.datetime.utcnow()

    db = SessionLocal()
    try:
        recover_orphaned_jobs(db)
    finally:
        db.close()

    for i in range(concurrency):
        w_id = f"automation-worker-{i}"
        task = asyncio.create_task(automation_worker_poll_loop(w_id))
        _worker_tasks.append(task)
    logger.info(f"Started {concurrency} concurrent background Automation Agent workers.")

async def stop_automation_agent() -> None:
    if not AGENT_STATE["is_running"]:
        return
    AGENT_STATE["is_running"] = False
    for task in _worker_tasks:
        task.cancel()
    if _worker_tasks:
        await asyncio.gather(*_worker_tasks, return_exceptions=True)
    _worker_tasks.clear()
    logger.info("Stopped background Automation Agent workers.")
ZOOMING = "zoom"
