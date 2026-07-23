import os
import uuid
from datetime import datetime
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database.session import get_db
from core.database.models import (
    InstagramPublishJob, 
    PublicationPackage, 
    InstagramPublication,
    InstagramInsightSnapshot,
    QualityPackage,
    WorkerHeartbeat
)
from contracts.dto.instagram_publishing import (
    InstagramPublishJobCreateDTO, 
    InstagramJobResponseDTO, 
    InstagramMetricsDTO, 
    PublicationPackageDTO
)
from brain.operations.instagram_worker import is_valid_transition, AGENT_STATE, _worker_tasks
from providers.publishing.instagram import InstagramPublishingProvider

router = APIRouter(prefix="/publishing/instagram")

@router.post("", response_model=InstagramJobResponseDTO)
async def create_instagram_job(payload: InstagramPublishJobCreateDTO, db: Session = Depends(get_db)):
    """Enqueue a new Instagram publishing job for an approved QualityPackage."""
    quality_pkg = db.query(QualityPackage).filter(QualityPackage.id == payload.quality_package_id).first()
    if not quality_pkg:
        raise HTTPException(status_code=404, detail="QualityPackage not found.")

    if not quality_pkg.is_approved_for_publishing:
        raise HTTPException(status_code=400, detail="Quality Gate Rejected: QualityPackage is not approved for publishing.")

    existing = db.query(InstagramPublishJob).filter(
        InstagramPublishJob.quality_package_id == payload.quality_package_id,
        InstagramPublishJob.platform_media_type == payload.platform_media_type,
        InstagramPublishJob.status == "SUCCESS"
    ).first()
    if existing:
        return existing

    job = InstagramPublishJob(
        id=uuid.uuid4(),
        quality_package_id=payload.quality_package_id,
        platform_media_type=payload.platform_media_type or "Reels",
        provider=payload.provider or "instagram_provider",
        status="QUEUED",
        stage="VALIDATING",
        priority=payload.priority,
        attempts=0,
        max_attempts=5
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.get("", response_model=list[InstagramJobResponseDTO])
async def list_instagram_jobs(
    status: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """List enqueued, uploading, published, or failed Instagram publishing jobs."""
    query = db.query(InstagramPublishJob)
    if status:
        query = query.filter(InstagramPublishJob.status == status)
    return query.order_by(InstagramPublishJob.created_at.desc()).all()

@router.get("/metrics", response_model=InstagramMetricsDTO)
async def get_instagram_metrics(db: Session = Depends(get_db)):
    """Fetch Instagram publishing telemetry stats, active worker heartbeats, total views, and queue depth."""
    jobs_queued = db.query(InstagramPublishJob).filter(InstagramPublishJob.status == "QUEUED").count()
    jobs_processing = db.query(InstagramPublishJob).filter(InstagramPublishJob.status == "PROCESSING").count()
    jobs_succeeded = db.query(InstagramPublishJob).filter(InstagramPublishJob.status == "SUCCESS").count()
    jobs_failed = db.query(InstagramPublishJob).filter(InstagramPublishJob.status == "FAILED").count()
    jobs_retrying = db.query(InstagramPublishJob).filter(InstagramPublishJob.status == "RETRYING").count()
    jobs_cancelled = db.query(InstagramPublishJob).filter(InstagramPublishJob.status == "CANCELLED").count()

    total_publications = db.query(InstagramPublication).count()
    snapshots = db.query(InstagramInsightSnapshot).all()
    
    total_views = sum(s.views for s in snapshots)
    total_reach = sum(s.reach for s in snapshots)
    avg_engagement = round(sum(s.engagement_rate for s in snapshots) / len(snapshots), 3) if snapshots else 0.0

    avg_duration = 0.0
    if AGENT_STATE["jobs_succeeded"] > 0:
        avg_duration = AGENT_STATE["total_duration_sec"] / AGENT_STATE["jobs_succeeded"]

    uptime = "offline"
    if AGENT_STATE["is_running"] and AGENT_STATE["started_at"]:
        uptime = str(datetime.utcnow() - AGENT_STATE["started_at"])

    heartbeats = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id.like("instagram-worker-%")).all()
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
        "total_publications": total_publications,
        "total_views": total_views,
        "total_reach": total_reach,
        "average_engagement_rate": avg_engagement,
        "average_duration_sec": round(avg_duration, 2),
        "current_worker_count": len(_worker_tasks),
        "worker_uptime": uptime,
        "worker_is_running": AGENT_STATE["is_running"],
        "worker_heartbeats": active_hbs
    }

@router.get("/{id}", response_model=InstagramJobResponseDTO)
async def get_instagram_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve full details of an Instagram publishing job, including attempt history, media assets, and insight snapshots."""
    job = db.query(InstagramPublishJob).filter(InstagramPublishJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Instagram publish job not found.")
    return job

@router.post("/{id}/retry", response_model=InstagramJobResponseDTO)
async def retry_instagram_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Re-enqueue a failed or cancelled Instagram publishing job."""
    job = db.query(InstagramPublishJob).filter(InstagramPublishJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Instagram publish job not found.")

    if not is_valid_transition(job.status, "QUEUED"):
        raise HTTPException(status_code=400, detail=f"Cannot retry job in status {job.status}.")

    job.status = "QUEUED"
    job.stage = "VALIDATING"
    job.progress = 0.0
    job.attempts = 0
    job.scheduled_at = datetime.utcnow()
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.post("/{id}/sync")
async def sync_instagram_publication(id: uuid.UUID, db: Session = Depends(get_db)):
    """Fetch updated engagement insights and status from Graph API."""
    job = db.query(InstagramPublishJob).filter(InstagramPublishJob.id == id).first()
    if not job or not job.packages:
        raise HTTPException(status_code=404, detail="Publication package not found.")

    pkg = job.packages[0]
    if not pkg.publications:
        raise HTTPException(status_code=404, detail="No publication record found.")

    pub = pkg.publications[0]
    provider = InstagramPublishingProvider()
    insight_data = await provider.fetch_insights(pub.instagram_media_id)

    snapshot = InstagramInsightSnapshot(
        id=uuid.uuid4(),
        publication_id=pub.id,
        captured_at=datetime.utcnow(),
        views=insight_data["views"],
        reach=insight_data["reach"],
        impressions=insight_data["impressions"],
        likes=insight_data["likes"],
        comments=insight_data["comments"],
        shares=insight_data["shares"],
        saves=insight_data["saves"],
        profile_visits=insight_data["profile_visits"],
        follows_attributed=insight_data["follows_attributed"],
        watch_time_ms=insight_data["watch_time_ms"],
        engagement_rate=insight_data["engagement_rate"]
    )
    db.add(snapshot)
    db.commit()
    return {"status": "synced", "snapshot": insight_data}

@router.delete("/{id}")
async def delete_instagram_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Cancel a queued/retrying publishing job, or delete completed records from DB."""
    job = db.query(InstagramPublishJob).filter(InstagramPublishJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Instagram publish job not found.")

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
