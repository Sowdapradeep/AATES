import uuid
from datetime import datetime
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database.session import get_db
from core.database.models import (
    AutomationJob,
    AutomationPolicyModel,
    AutomationTrigger,
    AutomationDecision,
    AutomationWorkflowInstance,
    AutomationPackage,
    WorkerHeartbeat
)
from contracts.dto.automation import (
    AutomationJobCreateDTO,
    AutomationJobResponseDTO,
    AutomationMetricsDTO,
    AutomationPolicyCreateDTO,
    AutomationPolicyDTO,
    AutomationTriggerDTO,
    WorkflowInstanceDTO
)
from brain.agents.automation_agent import AGENT_STATE, _worker_tasks
from providers.automation.policy_engine import policy_engine, AutomationPolicy

router = APIRouter(prefix="/automation")

@router.post("", response_model=AutomationJobResponseDTO)
async def create_automation_job(payload: AutomationJobCreateDTO, db: Session = Depends(get_db)):
    """Enqueue a new policy-driven Automation Job."""
    job = AutomationJob(
        id=uuid.uuid4(),
        status="QUEUED",
        stage="WAITING",
        trigger_type=payload.trigger_type or "MANUAL_TRIGGER",
        source_package_id=payload.source_package_id,
        target_platform=payload.target_platform or "all",
        priority=payload.priority or 0,
        attempts=0,
        max_attempts=3
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.get("", response_model=List[AutomationJobResponseDTO])
async def list_automation_jobs(
    status: Optional[str] = None,
    trigger_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List queued, processing, or completed automation jobs."""
    query = db.query(AutomationJob)
    if status:
        query = query.filter(AutomationJob.status == status)
    if trigger_type:
        query = query.filter(AutomationJob.trigger_type == trigger_type)
    return query.order_by(AutomationJob.created_at.desc()).all()

@router.get("/metrics", response_model=AutomationMetricsDTO)
async def get_automation_metrics(db: Session = Depends(get_db)):
    """Fetch global Automation Engine telemetry, policy counts, and active worker heartbeats."""
    jobs_queued = db.query(AutomationJob).filter(AutomationJob.status == "QUEUED").count()
    jobs_processing = db.query(AutomationJob).filter(AutomationJob.status == "PROCESSING").count()
    jobs_succeeded = db.query(AutomationJob).filter(AutomationJob.status == "SUCCESS").count()
    jobs_failed = db.query(AutomationJob).filter(AutomationJob.status == "FAILED").count()

    total_pkgs = db.query(AutomationPackage).count()
    total_policies = len(policy_engine.list_policies())
    total_triggers = db.query(AutomationTrigger).count()

    packages = db.query(AutomationPackage).all()
    avg_conf = round(sum(p.execution_confidence for p in packages) / len(packages), 3) if packages else 0.95

    avg_dur = 0.0
    if AGENT_STATE["jobs_succeeded"] > 0:
        avg_dur = AGENT_STATE["total_duration_sec"] / AGENT_STATE["jobs_succeeded"]

    uptime = "offline"
    if AGENT_STATE["is_running"] and AGENT_STATE["started_at"]:
        uptime = str(datetime.utcnow() - AGENT_STATE["started_at"])

    heartbeats = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id.like("automation-worker-%")).all()
    active_hbs = [
        {
            "worker_id": hb.worker_id,
            "last_heartbeat_at": hb.last_heartbeat_at.isoformat() if hb.last_heartbeat_at else None,
            "is_alive": (datetime.utcnow() - hb.last_heartbeat_at).total_seconds() < 30 if hb.last_heartbeat_at else False
        } for hb in heartbeats
    ]

    return {
        "jobs_queued": jobs_queued,
        "jobs_processing": jobs_processing,
        "jobs_succeeded": jobs_succeeded,
        "jobs_failed": jobs_failed,
        "total_automation_packages": total_pkgs,
        "total_active_policies": total_policies,
        "total_triggers_received": total_triggers,
        "overall_execution_confidence": avg_conf,
        "average_duration_sec": round(avg_dur, 2),
        "current_worker_count": len(_worker_tasks),
        "worker_uptime": uptime,
        "worker_is_running": AGENT_STATE["is_running"],
        "worker_heartbeats": active_hbs
    }

@router.get("/policies", response_model=List[AutomationPolicyDTO])
async def list_policies(db: Session = Depends(get_db)):
    """List registered Automation Policies."""
    db_policies = db.query(AutomationPolicyModel).all()
    if db_policies:
        return db_policies

    # Fallback to in-memory PolicyEngine policies
    policies = policy_engine.list_policies()
    return [
        {
            "id": uuid.uuid4(),
            "policy_id": p.policy_id,
            "name": p.name,
            "enabled": p.enabled,
            "priority": p.priority,
            "trigger_types": p.trigger_types,
            "conditions": p.conditions,
            "target_workflow_id": p.target_workflow_id,
            "cooldown_sec": p.cooldown_sec,
            "platforms": p.platforms,
            "applicable_agents": p.applicable_agents,
            "created_at": datetime.utcnow()
        } for p in policies
    ]

@router.post("/policies", response_model=AutomationPolicyDTO)
async def create_policy(payload: AutomationPolicyCreateDTO, db: Session = Depends(get_db)):
    """Register or update a reusable Automation Policy."""
    new_pol = AutomationPolicy(
        policy_id=payload.policy_id,
        name=payload.name,
        enabled=payload.enabled if payload.enabled is not None else True,
        priority=payload.priority or 0,
        trigger_types=payload.trigger_types,
        conditions=payload.conditions,
        target_workflow_id=payload.target_workflow_id or "AUTONOMOUS_PUBLISHING",
        cooldown_sec=payload.cooldown_sec or 60
    )
    policy_engine.register_policy(new_pol)

    db_pol = AutomationPolicyModel(
        id=uuid.uuid4(),
        policy_id=new_pol.policy_id,
        name=new_pol.name,
        enabled=new_pol.enabled,
        priority=new_pol.priority,
        trigger_types=new_pol.trigger_types,
        conditions=new_pol.conditions,
        target_workflow_id=new_pol.target_workflow_id,
        cooldown_sec=new_pol.cooldown_sec,
        retry_rules=new_pol.retry_rules,
        platforms=new_pol.platforms,
        applicable_agents=new_pol.applicable_agents
    )
    db.add(db_pol)
    db.commit()
    db.refresh(db_pol)
    return db_pol

@router.get("/triggers", response_model=List[AutomationTriggerDTO])
async def list_triggers(db: Session = Depends(get_db)):
    """Query recent triggers intercepted by the TriggerManager."""
    return db.query(AutomationTrigger).order_by(AutomationTrigger.triggered_at.desc()).all()

@router.get("/{id}", response_model=AutomationJobResponseDTO)
async def get_automation_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve full details of an AutomationJob, including packages and workflow instances."""
    job = db.query(AutomationJob).filter(AutomationJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Automation job not found.")
    return job

@router.post("/{id}/execute", response_model=AutomationJobResponseDTO)
async def execute_manual_automation(id: uuid.UUID, db: Session = Depends(get_db)):
    """Manually trigger immediate workflow execution for an AutomationJob."""
    job = db.query(AutomationJob).filter(AutomationJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Automation job not found.")

    job.status = "QUEUED"
    job.stage = "WAITING"
    job.progress = 0.0
    job.attempts = 0
    job.trigger_type = "MANUAL_TRIGGER"
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.post("/{id}/enable")
async def enable_policy(id: str, db: Session = Depends(get_db)):
    """Enable an automation policy."""
    pol = policy_engine.get_policy(id)
    if pol:
        pol.enabled = True
    return {"policy_id": id, "enabled": True}

@router.post("/{id}/disable")
async def disable_policy(id: str, db: Session = Depends(get_db)):
    """Disable an automation policy."""
    pol = policy_engine.get_policy(id)
    if pol:
        pol.enabled = False
    return {"policy_id": id, "enabled": False}
