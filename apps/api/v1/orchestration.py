import uuid
from datetime import datetime
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database.session import get_db
from core.database.models import (
    OrchestrationJob,
    ObjectiveModel,
    ExecutionPlanModel,
    ExecutionGraphModel,
    OrchestrationPackage,
    WorkerHeartbeat
)
from contracts.dto.orchestration import (
    OrchestrationJobCreateDTO,
    OrchestrationJobResponseDTO,
    OrchestrationMetricsDTO,
    ObjectiveDTO,
    ExecutionPlanDTO
)
from brain.agents.orchestrator_agent import AGENT_STATE, _worker_tasks
from providers.orchestration.objective_manager import objective_manager
from providers.orchestration.planning_engine import planning_engine

router = APIRouter(prefix="/orchestration")

@router.post("", response_model=OrchestrationJobResponseDTO)
async def create_orchestration_job(payload: OrchestrationJobCreateDTO, db: Session = Depends(get_db)):
    """Enqueue a new multi-agent strategic Orchestration Job."""
    job = OrchestrationJob(
        id=uuid.uuid4(),
        status="QUEUED",
        stage="OBJECTIVE_ANALYSIS",
        objective_type=payload.objective_type or "GENERATE_LONGFORM_VIDEO",
        target_platform=payload.target_platform or "all",
        priority=payload.priority or 5,
        attempts=0,
        max_attempts=3
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.get("", response_model=List[OrchestrationJobResponseDTO])
async def list_orchestration_jobs(
    status: Optional[str] = None,
    objective_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List queued, processing, or completed orchestration jobs."""
    query = db.query(OrchestrationJob)
    if status:
        query = query.filter(OrchestrationJob.status == status)
    if objective_type:
        query = query.filter(OrchestrationJob.objective_type == objective_type)
    return query.order_by(OrchestrationJob.created_at.desc()).all()

@router.get("/metrics", response_model=OrchestrationMetricsDTO)
async def get_orchestration_metrics(db: Session = Depends(get_db)):
    """Fetch global Multi-Agent Orchestrator metrics and active worker heartbeats."""
    jobs_queued = db.query(OrchestrationJob).filter(OrchestrationJob.status == "QUEUED").count()
    jobs_processing = db.query(OrchestrationJob).filter(OrchestrationJob.status == "PROCESSING").count()
    jobs_succeeded = db.query(OrchestrationJob).filter(OrchestrationJob.status == "SUCCESS").count()
    jobs_failed = db.query(OrchestrationJob).filter(OrchestrationJob.status == "FAILED").count()

    total_pkgs = db.query(OrchestrationPackage).count()
    total_objs = len(objective_manager.list_objectives())
    total_plans = db.query(ExecutionPlanModel).count()

    packages = db.query(OrchestrationPackage).all()
    avg_conf = round(sum(p.orchestration_confidence for p in packages) / len(packages), 3) if packages else 0.96

    avg_dur = 0.0
    if AGENT_STATE["jobs_succeeded"] > 0:
        avg_dur = AGENT_STATE["total_duration_sec"] / AGENT_STATE["jobs_succeeded"]

    uptime = "offline"
    if AGENT_STATE["is_running"] and AGENT_STATE["started_at"]:
        uptime = str(datetime.utcnow() - AGENT_STATE["started_at"])

    heartbeats = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id.like("orchestrator-worker-%")).all()
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
        "total_orchestration_packages": total_pkgs,
        "total_active_objectives": total_objs,
        "total_plans_generated": total_plans,
        "overall_orchestration_confidence": avg_conf,
        "average_duration_sec": round(avg_dur, 2),
        "current_worker_count": len(_worker_tasks),
        "worker_uptime": uptime,
        "worker_is_running": AGENT_STATE["is_running"],
        "worker_heartbeats": active_hbs
    }

@router.get("/objectives")
async def list_objectives(db: Session = Depends(get_db)):
    """Query active business objectives in ObjectiveManager."""
    db_objs = db.query(ObjectiveModel).all()
    if db_objs:
        return db_objs
    objs = objective_manager.list_objectives()
    return [
        {
            "id": uuid.uuid4(),
            "objective_id": o.objective_id,
            "title": o.title,
            "objective_type": o.objective_type,
            "target_platform": o.target_platform,
            "priority": o.priority,
            "target_kpi": o.target_kpi,
            "parameters": o.parameters,
            "status": o.status,
            "created_at": datetime.utcnow()
        } for o in objs
    ]

@router.get("/plans")
async def list_execution_plans(db: Session = Depends(get_db)):
    """Query multi-agent execution plans."""
    return db.query(ExecutionPlanModel).order_by(ExecutionPlanModel.created_at.desc()).all()

@router.get("/{id}", response_model=OrchestrationJobResponseDTO)
async def get_orchestration_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve full details of an OrchestrationJob."""
    job = db.query(OrchestrationJob).filter(OrchestrationJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Orchestration job not found.")
    return job

@router.post("/{id}/pause")
async def pause_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Pause execution of an OrchestrationJob."""
    job = db.query(OrchestrationJob).filter(OrchestrationJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Orchestration job not found.")
    job.status = "PAUSED"
    db.commit()
    return {"job_id": id, "status": "PAUSED"}

@router.post("/{id}/resume")
async def resume_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Resume execution of a paused OrchestrationJob."""
    job = db.query(OrchestrationJob).filter(OrchestrationJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Orchestration job not found.")
    job.status = "QUEUED"
    db.commit()
    return {"job_id": id, "status": "QUEUED"}

@router.post("/{id}/cancel")
async def cancel_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Cancel execution of an OrchestrationJob."""
    job = db.query(OrchestrationJob).filter(OrchestrationJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Orchestration job not found.")
    job.status = "CANCELLED"
    db.commit()
    return {"job_id": id, "status": "CANCELLED"}
