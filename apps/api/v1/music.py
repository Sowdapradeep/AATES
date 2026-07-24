import os
import uuid
from datetime import UTC, datetime
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from core.database.session import get_db
from core.database.models import (
    MusicJob, 
    MusicPackage, 
    SceneMusic, 
    MusicAsset,
    MusicTrack,
    MusicCue,
    AudioTimelineEvent,
    AudioAnalysis,
    AudioMixProfile,
    MusicVersion, 
    ScriptPackage,
    VoicePackage, 
    VideoPackage,
    WorkerHeartbeat
)
from contracts.dto.music import MusicJobCreateDTO, MusicJobResponseDTO, MusicMetricsDTO, MusicPackageDTO
from brain.agents.music_agent import is_valid_transition, AGENT_STATE, _agent_tasks
from providers.music.registry import music_registry

router = APIRouter(prefix="/music")

@router.post("", response_model=MusicJobResponseDTO)
async def create_music_job(payload: MusicJobCreateDTO, db: Session = Depends(get_db)):
    """Enqueue a new AI Music compilation job merging Script, Voice, Video, and Subtitle packages."""
    script_pkg = db.query(ScriptPackage).filter(ScriptPackage.id == payload.script_package_id).first()
    voice_pkg = db.query(VoicePackage).filter(VoicePackage.id == payload.voice_package_id).first()
    video_pkg = db.query(VideoPackage).filter(VideoPackage.id == payload.video_package_id).first()

    if not script_pkg or not voice_pkg or not video_pkg:
        raise HTTPException(status_code=404, detail="Input packages (ScriptPackage, VoicePackage, VideoPackage) must exist.")

    existing = db.query(MusicJob).filter(
        MusicJob.script_package_id == payload.script_package_id,
        MusicJob.voice_package_id == payload.voice_package_id,
        MusicJob.video_package_id == payload.video_package_id,
        MusicJob.status == "SUCCESS"
    ).first()
    if existing:
        return existing

    job = MusicJob(
        id=uuid.uuid4(),
        script_package_id=payload.script_package_id,
        voice_package_id=payload.voice_package_id,
        video_package_id=payload.video_package_id,
        subtitle_package_id=payload.subtitle_package_id,
        provider=payload.provider or "library",
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

@router.get("", response_model=list[MusicJobResponseDTO])
async def list_music_jobs(
    status: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """List enqueued, processing, or completed music jobs."""
    query = db.query(MusicJob)
    if status:
        query = query.filter(MusicJob.status == status)
    return query.order_by(MusicJob.created_at.desc()).all()

@router.get("/metrics", response_model=MusicMetricsDTO)
async def get_music_metrics(db: Session = Depends(get_db)):
    """Fetch AI Music Agent telemetry stats, active worker heartbeats, and queue monitors."""
    jobs_queued = db.query(MusicJob).filter(MusicJob.status == "QUEUED").count()
    jobs_processing = db.query(MusicJob).filter(MusicJob.status == "PROCESSING").count()
    jobs_succeeded = db.query(MusicJob).filter(MusicJob.status == "SUCCESS").count()
    jobs_failed = db.query(MusicJob).filter(MusicJob.status == "FAILED").count()
    jobs_retrying = db.query(MusicJob).filter(MusicJob.status == "RETRYING").count()
    jobs_cancelled = db.query(MusicJob).filter(MusicJob.status == "CANCELLED").count()

    avg_duration = 0.0
    if AGENT_STATE["jobs_succeeded"] > 0:
        avg_duration = AGENT_STATE["total_duration_sec"] / AGENT_STATE["jobs_succeeded"]

    uptime = "offline"
    if AGENT_STATE["is_running"] and AGENT_STATE["started_at"]:
        uptime = str(datetime.now(UTC).replace(tzinfo=None) - AGENT_STATE["started_at"])

    heartbeats = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id.like("music-agent-%")).all()
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

@router.get("/{id}", response_model=MusicJobResponseDTO)
async def get_music_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve full details of a music job, including scene musics, cues, timeline events, audio analysis, and version history."""
    job = db.query(MusicJob).filter(MusicJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Music job not found.")
    return job

@router.post("/{id}/remix", response_model=MusicPackageDTO)
async def remix_music_package(
    id: uuid.UUID, 
    music_volume_db: Optional[float] = Query(-14.0),
    ducking_level_db: Optional[float] = Query(-12.0),
    db: Session = Depends(get_db)
):
    """Remix scene music tracks, updating ducking attenuation levels and creating a new MusicVersion snapshot."""
    job = db.query(MusicJob).filter(MusicJob.id == id).first()
    if not job or not job.packages:
        raise HTTPException(status_code=404, detail="Music package not found.")

    pkg = job.packages[0]
    provider_instance = music_registry.get_provider(job.provider) or music_registry.get_provider("library")

    # Update SceneMusics
    scenes = db.query(SceneMusic).filter(SceneMusic.music_package_id == pkg.id).all()
    for sc in scenes:
        sc.music_volume_db = music_volume_db
        sc.narration_ducking_db = ducking_level_db
        db.add(sc)

    # Re-mix audio stems
    mapped_scenes = [
        {
            "scene_number": sc.scene_number,
            "track_name": sc.track_name,
            "start_time_ms": sc.start_time_ms,
            "end_time_ms": sc.end_time_ms,
            "music_volume_db": music_volume_db,
            "ducking_level_db": ducking_level_db
        } for sc in scenes
    ]

    mix_result = await provider_instance.mix_audio(mapped_scenes, pkg.narration_track or "", {
        "music_volume_db": music_volume_db,
        "ducking_level_db": ducking_level_db
    })

    # Save new version lineage
    new_ver_num = pkg.version + 1
    ver_snapshot = [
        {
            "scene_number": sc.scene_number,
            "track_name": sc.track_name,
            "music_volume_db": sc.music_volume_db,
            "narration_ducking_db": sc.narration_ducking_db
        } for sc in scenes
    ]
    ver = MusicVersion(
        id=uuid.uuid4(),
        music_package_id=pkg.id,
        version=new_ver_num,
        parent_version=pkg.version,
        lineage_action="REMIXED",
        assets_snapshot=ver_snapshot
    )
    db.add(ver)

    pkg.version = new_ver_num
    pkg.storage_key = mix_result["master_path"]
    pkg.separated_music_track = mix_result["music_stem_path"]
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg

@router.post("/{id}/normalize")
async def normalize_music_package(
    id: uuid.UUID,
    target_lufs: Optional[float] = Query(-14.0),
    true_peak_db: Optional[float] = Query(-1.0),
    db: Session = Depends(get_db)
):
    """Re-normalize loudness (LUFS & True Peak) of master audio mix."""
    job = db.query(MusicJob).filter(MusicJob.id == id).first()
    if not job or not job.packages:
        raise HTTPException(status_code=404, detail="Music package not found.")

    pkg = job.packages[0]
    provider_instance = music_registry.get_provider(job.provider) or music_registry.get_provider("library")

    norm_res = await provider_instance.normalize(pkg.storage_key, target_lufs, true_peak_db)
    
    # Update analysis if present
    if pkg.analysis:
        pkg.analysis.lufs = norm_res.get("achieved_lufs", target_lufs)
        pkg.analysis.peak_db = norm_res.get("achieved_true_peak_db", true_peak_db)
        db.add(pkg.analysis)

    db.commit()
    return norm_res

@router.post("/{id}/preview")
async def generate_music_preview(id: uuid.UUID, db: Session = Depends(get_db)):
    """Generate and return preview path for master audio mix."""
    job = db.query(MusicJob).filter(MusicJob.id == id).first()
    if not job or not job.packages:
        raise HTTPException(status_code=404, detail="Music package not found.")

    pkg = job.packages[0]
    if not os.path.exists(pkg.storage_key):
        raise HTTPException(status_code=404, detail="Master audio mix file not found on disk.")

    return {"preview_path": pkg.storage_key, "status": "success"}

@router.delete("/{id}")
async def delete_music_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Cancel a queued/retrying music job, or delete completed records from DB."""
    job = db.query(MusicJob).filter(MusicJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Music job not found.")

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
