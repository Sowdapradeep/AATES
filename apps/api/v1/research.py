import uuid
from datetime import datetime
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database.session import get_db
from core.database.models import ResearchJob, KnowledgePackage, ResearchSource, Keyword, Competitor, WorkerHeartbeat
from contracts.dto.research import ResearchJobCreateDTO, ResearchJobResponseDTO, ResearchMetricsDTO
from brain.operations.research_agent import is_valid_transition, AGENT_STATE, _agent_tasks

router = APIRouter(prefix="/research")

@router.post("", response_model=ResearchJobResponseDTO)
async def create_research_job(payload: ResearchJobCreateDTO, db: Session = Depends(get_db)):
    """Enqueue a new topic research job. Returns existing SUCCESS job if duplicate to avoid duplicate API cost."""
    existing = db.query(ResearchJob).filter(
        ResearchJob.topic == payload.topic,
        ResearchJob.status == "SUCCESS"
    ).first()
    if existing:
        return existing

    job = ResearchJob(
        id=uuid.uuid4(),
        tenant_id=payload.tenant_id,
        topic=payload.topic,
        status="QUEUED",
        stage="DISCOVERING",
        priority=payload.priority,
        attempts=0,
        max_attempts=5
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.get("", response_model=list[ResearchJobResponseDTO])
async def list_research_jobs(
    status: Optional[str] = None, 
    topic: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """List enqueued, processing, completed, or failed topic research jobs."""
    query = db.query(ResearchJob)
    if status:
        query = query.filter(ResearchJob.status == status)
    if topic:
        query = query.filter(ResearchJob.topic.ilike(f"%{topic}%"))
    return query.order_by(ResearchJob.created_at.desc()).all()

@router.get("/metrics", response_model=ResearchMetricsDTO)
async def get_research_metrics(db: Session = Depends(get_db)):
    """Fetch AI Research Agent telemetry metrics, worker heartbeats, and queue depth stats."""
    jobs_queued = db.query(ResearchJob).filter(ResearchJob.status == "QUEUED").count()
    jobs_processing = db.query(ResearchJob).filter(ResearchJob.status == "PROCESSING").count()
    jobs_succeeded = db.query(ResearchJob).filter(ResearchJob.status == "SUCCESS").count()
    jobs_failed = db.query(ResearchJob).filter(ResearchJob.status == "FAILED").count()
    jobs_retrying = db.query(ResearchJob).filter(ResearchJob.status == "RETRYING").count()
    jobs_cancelled = db.query(ResearchJob).filter(ResearchJob.status == "CANCELLED").count()

    avg_duration = 0.0
    if AGENT_STATE["jobs_succeeded"] > 0:
        avg_duration = AGENT_STATE["total_duration_sec"] / AGENT_STATE["jobs_succeeded"]

    uptime = "offline"
    if AGENT_STATE["is_running"] and AGENT_STATE["started_at"]:
        uptime = str(datetime.utcnow() - AGENT_STATE["started_at"])

    # Query heartbeats matching research agents
    heartbeats = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id.like("research-agent-%")).all()
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
        "jobs_retrying": jobs_retrying,
        "jobs_cancelled": jobs_cancelled,
        "average_duration_sec": round(avg_duration, 2),
        "current_worker_count": len(_agent_tasks),
        "worker_uptime": uptime,
        "worker_is_running": AGENT_STATE["is_running"],
        "worker_heartbeats": active_hbs
    }

@router.get("/{id}", response_model=ResearchJobResponseDTO)
async def get_research_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve full details of a research job, including its generated KnowledgePackage."""
    job = db.query(ResearchJob).filter(ResearchJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Research job not found.")
    return job

@router.delete("/{id}")
async def delete_research_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Cancel a queued/retrying research job, or delete completed records from DB."""
    job = db.query(ResearchJob).filter(ResearchJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Research job not found.")

    if job.status in ("QUEUED", "RETRYING"):
        if not is_valid_transition(job.status, "CANCELLED"):
            raise HTTPException(status_code=400, detail="Invalid transition to CANCELLED.")
        job.status = "CANCELLED"
        job.stage = "FAILED"
        job.progress = 1.0
        db.add(job)
        db.commit()
        return {"status": "cancelled", "job_id": str(job.id)}

    if job.status == "PROCESSING":
        raise HTTPException(status_code=400, detail="Cannot cancel a job that is currently processing.")

    db.delete(job)
    db.commit()
    return {"status": "deleted", "job_id": str(id)}

@router.post("/{id}/retry", response_model=ResearchJobResponseDTO)
async def retry_research_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Manually trigger a retry for a failed or cancelled research job."""
    job = db.query(ResearchJob).filter(ResearchJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Research job not found.")

    if not is_valid_transition(job.status, "QUEUED"):
        raise HTTPException(status_code=400, detail=f"Cannot retry a job in status '{job.status}'.")

    # Clean old references before re-queuing
    db.query(ResearchSource).filter(ResearchSource.job_id == id).delete()
    db.query(KnowledgePackage).filter(KnowledgePackage.job_id == id).delete()
    db.query(Keyword).filter(Keyword.job_id == id).delete()
    db.query(Competitor).filter(Competitor.job_id == id).delete()

    job.status = "QUEUED"
    job.stage = "DISCOVERING"
    job.progress = 0.0
    job.attempts = 0
    job.scheduled_at = None
    job.failed_at = None
    job.error_code = None
    job.error_message = None
    db.add(job)
    db.commit()
    db.refresh(job)
    return job
