import os
import uuid
from datetime import UTC, datetime
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database.session import get_db
from core.database.models import (
    VideoJob, 
    VideoPackage, 
    SceneVideo, 
    TimelineEvent, 
    VideoVersion, 
    ScriptPackage, 
    ImagePackage,
    VoicePackage,
    WorkerHeartbeat
)
from contracts.dto.video import VideoJobCreateDTO, VideoJobResponseDTO, VideoMetricsDTO, VideoPackageDTO
from brain.agents.video_agent import is_valid_transition, AGENT_STATE, _agent_tasks
from providers.video.registry import video_registry
from core.config.settings import settings

router = APIRouter(prefix="/videos")

@router.post("", response_model=VideoJobResponseDTO)
async def create_video_job(payload: VideoJobCreateDTO, db: Session = Depends(get_db)):
    """Enqueue a new render compilation job merging Script, Image, and Voice packages."""
    script = db.query(ScriptPackage).filter(ScriptPackage.id == payload.script_package_id).first()
    images = db.query(ImagePackage).filter(ImagePackage.id == payload.image_package_id).first()
    voices = db.query(VoicePackage).filter(VoicePackage.id == payload.voice_package_id).first()

    if not script or not images or not voices:
        raise HTTPException(status_code=404, detail="Input packages (Script, Image, Voice) must all exist.")

    existing = db.query(VideoJob).filter(
        VideoJob.script_package_id == payload.script_package_id,
        VideoJob.status == "SUCCESS"
    ).first()
    if existing:
        return existing

    job = VideoJob(
        id=uuid.uuid4(),
        script_package_id=payload.script_package_id,
        image_package_id=payload.image_package_id,
        voice_package_id=payload.voice_package_id,
        renderer=payload.renderer or ("ffmpeg" if settings.app.env != "testing" else "mock"),
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

@router.get("", response_model=list[VideoJobResponseDTO])
async def list_video_jobs(
    status: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """List enqueued, processing, or completed video compilation jobs."""
    query = db.query(VideoJob)
    if status:
        query = query.filter(VideoJob.status == status)
    return query.order_by(VideoJob.created_at.desc()).all()

@router.get("/metrics", response_model=VideoMetricsDTO)
async def get_video_metrics(db: Session = Depends(get_db)):
    """Fetch AI Video Agent telemetry stats, active worker heartbeats, and queue depth monitors."""
    jobs_queued = db.query(VideoJob).filter(VideoJob.status == "QUEUED").count()
    jobs_processing = db.query(VideoJob).filter(VideoJob.status == "PROCESSING").count()
    jobs_succeeded = db.query(VideoJob).filter(VideoJob.status == "SUCCESS").count()
    jobs_failed = db.query(VideoJob).filter(VideoJob.status == "FAILED").count()
    jobs_retrying = db.query(VideoJob).filter(VideoJob.status == "RETRYING").count()
    jobs_cancelled = db.query(VideoJob).filter(VideoJob.status == "CANCELLED").count()

    avg_duration = 0.0
    if AGENT_STATE["jobs_succeeded"] > 0:
        avg_duration = AGENT_STATE["total_duration_sec"] / AGENT_STATE["jobs_succeeded"]

    uptime = "offline"
    if AGENT_STATE["is_running"] and AGENT_STATE["started_at"]:
        uptime = str(datetime.now(UTC).replace(tzinfo=None) - AGENT_STATE["started_at"])

    # Query heartbeats matching video agents
    heartbeats = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id.like("video-agent-%")).all()
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
        "jobs_retrying": jobs_retrying,
        "jobs_cancelled": jobs_cancelled,
        "average_duration_sec": round(avg_duration, 2),
        "current_worker_count": len(_agent_tasks),
        "worker_uptime": uptime,
        "worker_is_running": AGENT_STATE["is_running"],
        "worker_heartbeats": active_hbs
    }

@router.get("/{id}", response_model=VideoJobResponseDTO)
async def get_video_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve full details of a video compilation job, including scene videos and version snapshot history."""
    job = db.query(VideoJob).filter(VideoJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found.")
    return job

@router.post("/{id}/render", response_model=VideoJobResponseDTO)
async def trigger_video_render(id: uuid.UUID, db: Session = Depends(get_db)):
    """Force compilation render start for a queued/failed job."""
    job = db.query(VideoJob).filter(VideoJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found.")
    
    if job.status not in ("QUEUED", "FAILED", "CANCELLED"):
        raise HTTPException(status_code=400, detail="Job must be in QUEUED, FAILED, or CANCELLED status to render.")

    job.status = "QUEUED"
    job.stage = "VALIDATING"
    job.progress = 0.0
    job.attempts = 0
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.post("/{id}/preview")
async def trigger_video_preview(id: uuid.UUID, db: Session = Depends(get_db)):
    """Generate and return low-resolution lightweight preview copy path."""
    job = db.query(VideoJob).filter(VideoJob.id == id).first()
    if not job or not job.packages:
        raise HTTPException(status_code=404, detail="Video package not found.")
    
    pkg = job.packages[0]
    provider_instance = video_registry.get_provider(job.renderer) or video_registry.get_provider("mock")
    
    preview_path = await provider_instance.render_preview(pkg.storage_key)
    pkg.preview_video = preview_path
    db.add(pkg)
    db.commit()

    return {"preview_path": preview_path, "status": "success"}

@router.post("/{id}/regenerate", response_model=VideoPackageDTO)
async def regenerate_scene_video(
    id: uuid.UUID, 
    scene_number: Optional[int] = Query(None), 
    db: Session = Depends(get_db)
):
    """Regenerate specific scene video clip (updates Active SceneVideo and adds VideoVersion snapshot tracking)."""
    job = db.query(VideoJob).filter(VideoJob.id == id).first()
    if not job or not job.packages:
        raise HTTPException(status_code=404, detail="Video package not found.")
    
    pkg = job.packages[0]
    provider_instance = video_registry.get_provider(job.renderer) or video_registry.get_provider("mock")
    
    target_scene = scene_number if scene_number else 1
    asset = db.query(SceneVideo).filter(
        SceneVideo.video_package_id == pkg.id,
        SceneVideo.scene_number == target_scene
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail=f"Scene {target_scene} not found in package.")

    # Call render_scene on provider
    options = {
        "fps": pkg.fps,
        "codec": pkg.codec
    }
    
    node = {
        "scene_number": asset.scene_number,
        "timeline_start_ms": asset.timeline_start_ms,
        "timeline_end_ms": asset.timeline_end_ms,
        "duration_ms": asset.duration_ms,
        "image_asset_id": str(asset.image_asset_id) if asset.image_asset_id else None,
        "voice_asset_id": str(asset.voice_asset_id) if asset.voice_asset_id else None,
        "motion_preset": asset.motion_preset,
        "transition_preset": asset.transition_preset
    }
    
    scene_clip = await provider_instance.render_scene(node, options)
    
    # Update active SceneVideo
    asset.rendered_clip = scene_clip["local_path"]
    asset.storage_key = scene_clip["storage_key"]
    asset.preview_url = scene_clip.get("preview_url")
    asset.render_metadata = scene_clip.get("render_metadata")
    asset.quality_score = scene_clip.get("quality_score", 0.95)
    db.add(asset)
    db.flush()

    # Recalculate package duration
    assets = db.query(SceneVideo).filter(SceneVideo.video_package_id == pkg.id).all()
    pkg.duration_ms = sum(a.duration_ms for a in assets)

    # Save new version lineage snapshot
    new_ver_num = pkg.version + 1
    assets_snapshot = [
        {
            "scene_number": a.scene_number,
            "rendered_clip": a.rendered_clip,
            "duration_ms": a.duration_ms,
            "quality_score": a.quality_score
        } for a in assets
    ]

    ver = VideoVersion(
        id=uuid.uuid4(),
        video_package_id=pkg.id,
        version=new_ver_num,
        parent_version=pkg.version,
        lineage_action="REGENERATED",
        assets_snapshot=assets_snapshot
    )
    db.add(ver)

    # Update mixin package values
    pkg.version = new_ver_num
    pkg.parent_package_id = pkg.id
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg

@router.delete("/{id}")
async def delete_video_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Cancel a queued/retrying video job, or delete completed records from DB."""
    job = db.query(VideoJob).filter(VideoJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found.")

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
