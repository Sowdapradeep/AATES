import uuid
from datetime import UTC, datetime
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database.session import get_db
from core.database.models import (
    LearningJob,
    LearningPackage,
    LearningSignal,
    LearningRecommendation,
    RecommendationFeedback,
    WorkerHeartbeat
)
from contracts.dto.learning import (
    LearningJobCreateDTO,
    LearningJobResponseDTO,
    LearningMetricsDTO,
    LearningSignalDTO,
    RecommendationDTO,
    RecommendationFeedbackCreateDTO,
    RecommendationFeedbackDTO
)
from brain.agents.learning_agent import AGENT_STATE, _worker_tasks

router = APIRouter(prefix="/learning")

@router.post("", response_model=LearningJobResponseDTO)
async def create_learning_job(payload: LearningJobCreateDTO, db: Session = Depends(get_db)):
    """Enqueue a new Analytics & Learning job to discover patterns and generate agent recommendations."""
    job = LearningJob(
        id=uuid.uuid4(),
        status="QUEUED",
        stage="COLLECTING",
        target_platform=payload.target_platform or "all",
        learning_window_days=payload.learning_window_days or 30,
        learning_mode=payload.learning_mode or "batch",
        priority=payload.priority or 0,
        attempts=0,
        max_attempts=3
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.get("", response_model=List[LearningJobResponseDTO])
async def list_learning_jobs(
    status: Optional[str] = None,
    target_platform: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List queued, processing, or completed learning jobs."""
    query = db.query(LearningJob)
    if status:
        query = query.filter(LearningJob.status == status)
    if target_platform:
        query = query.filter(LearningJob.target_platform == target_platform)
    return query.order_by(LearningJob.created_at.desc()).all()

@router.get("/metrics", response_model=LearningMetricsDTO)
async def get_learning_metrics(db: Session = Depends(get_db)):
    """Fetch global Analytics & Learning Engine telemetry, worker heartbeats, and total signals."""
    jobs_queued = db.query(LearningJob).filter(LearningJob.status == "QUEUED").count()
    jobs_processing = db.query(LearningJob).filter(LearningJob.status == "PROCESSING").count()
    jobs_succeeded = db.query(LearningJob).filter(LearningJob.status == "SUCCESS").count()
    jobs_failed = db.query(LearningJob).filter(LearningJob.status == "FAILED").count()

    total_pkgs = db.query(LearningPackage).count()
    total_signals = db.query(LearningSignal).count()
    total_recs = db.query(LearningRecommendation).count()

    packages = db.query(LearningPackage).all()
    avg_conf = round(sum(p.learning_confidence for p in packages) / len(packages), 3) if packages else 0.85

    avg_dur = 0.0
    if AGENT_STATE["jobs_succeeded"] > 0:
        avg_dur = AGENT_STATE["total_duration_sec"] / AGENT_STATE["jobs_succeeded"]

    uptime = "offline"
    if AGENT_STATE["is_running"] and AGENT_STATE["started_at"]:
        uptime = str(datetime.now(UTC).replace(tzinfo=None) - AGENT_STATE["started_at"])

    heartbeats = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id.like("learning-worker-%")).all()
    active_hbs = [
        {
            "worker_id": hb.worker_id,
            "last_heartbeat_at": hb.last_heartbeat_at.isoformat() if hb.last_heartbeat_at else None,
            "is_alive": (datetime.now(UTC).replace(tzinfo=None) - hb.last_heartbeat_at).total_seconds() < 30 if hb.last_heartbeat_at else False
        } for hb in heartbeats
    ]

    return {
        "jobs_queued": jobs_queued,
        "jobs_processing": jobs_processing,
        "jobs_succeeded": jobs_succeeded,
        "jobs_failed": jobs_failed,
        "total_learning_packages": total_pkgs,
        "total_signals_discovered": total_signals,
        "total_recommendations_generated": total_recs,
        "overall_learning_confidence": avg_conf,
        "average_duration_sec": round(avg_dur, 2),
        "current_worker_count": len(_worker_tasks),
        "worker_uptime": uptime,
        "worker_is_running": AGENT_STATE["is_running"],
        "worker_heartbeats": active_hbs
    }

@router.get("/signals", response_model=List[LearningSignalDTO])
async def list_learning_signals(
    category: Optional[str] = None,
    platform: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Query discovered Learning Signals filtered by category or target platform."""
    query = db.query(LearningSignal)
    if category:
        query = query.filter(LearningSignal.category == category)
    if platform and platform != "all":
        query = query.filter(LearningSignal.platform.in_([platform, "all"]))
    return query.order_by(LearningSignal.confidence_score.desc()).all()

@router.get("/recommendations", response_model=List[RecommendationDTO])
async def list_recommendations(
    target_agent: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Query targeted agent recommendations filtered by target_agent or priority."""
    query = db.query(LearningRecommendation)
    if target_agent:
        query = query.filter(LearningRecommendation.target_agent == target_agent)
    if priority:
        query = query.filter(LearningRecommendation.priority == priority)
    return query.order_by(LearningRecommendation.confidence_score.desc()).all()

@router.post("/recommendations/feedback", response_model=RecommendationFeedbackDTO)
async def submit_recommendation_feedback(payload: RecommendationFeedbackCreateDTO, db: Session = Depends(get_db)):
    """Submit adoption feedback and measured outcome impact for a recommendation."""
    rec = db.query(LearningRecommendation).filter(LearningRecommendation.id == payload.recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found.")

    fb = RecommendationFeedback(
        id=uuid.uuid4(),
        recommendation_id=payload.recommendation_id,
        applied_at=datetime.now(UTC).replace(tzinfo=None),
        status=payload.status,
        initial_metric=payload.initial_metric or 0.0,
        measured_metric=payload.measured_metric or 0.0,
        impact_percent=payload.impact_percent or 0.0,
        confidence_update=0.05 if payload.status == "SUCCESSFUL" else -0.05
    )
    db.add(fb)

    # Update recommendation confidence
    rec.confidence_score = min(0.99, max(0.50, rec.confidence_score + fb.confidence_update))
    db.commit()
    db.refresh(fb)
    return fb

@router.get("/{id}", response_model=LearningJobResponseDTO)
async def get_learning_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve full details of a LearningJob, including packages, signals, and recommendations."""
    job = db.query(LearningJob).filter(LearningJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Learning job not found.")
    return job

@router.post("/{id}/refresh", response_model=LearningJobResponseDTO)
async def refresh_learning_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Re-enqueue a learning job to execute incremental learning with fresh analytics data."""
    job = db.query(LearningJob).filter(LearningJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Learning job not found.")

    job.status = "QUEUED"
    job.stage = "COLLECTING"
    job.progress = 0.0
    job.attempts = 0
    job.learning_mode = "incremental"
    db.add(job)
    db.commit()
    db.refresh(job)
    return job
