import os
import uuid
from datetime import datetime
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from core.database.session import get_db
from core.database.models import (
    SubtitleJob, 
    SubtitlePackage, 
    SceneSubtitle, 
    CaptionSegment,
    SubtitleTrack, 
    CaptionStyleProfile,
    SubtitleVersion, 
    VoicePackage, 
    VideoPackage,
    WorkerHeartbeat
)
from contracts.dto.subtitle import SubtitleJobCreateDTO, SubtitleJobResponseDTO, SubtitleMetricsDTO, SubtitlePackageDTO
from brain.agents.subtitle_agent import is_valid_transition, AGENT_STATE, _agent_tasks
from providers.subtitle.registry import subtitle_registry

router = APIRouter(prefix="/subtitles")

@router.post("", response_model=SubtitleJobResponseDTO)
async def create_subtitle_job(payload: SubtitleJobCreateDTO, db: Session = Depends(get_db)):
    """Enqueue a new AI Subtitle generation job merging Voice and Video packages."""
    voice_pkg = db.query(VoicePackage).filter(VoicePackage.id == payload.voice_package_id).first()
    video_pkg = db.query(VideoPackage).filter(VideoPackage.id == payload.video_package_id).first()

    if not voice_pkg or not video_pkg:
        raise HTTPException(status_code=404, detail="Input packages (VoicePackage, VideoPackage) must exist.")

    existing = db.query(SubtitleJob).filter(
        SubtitleJob.voice_package_id == payload.voice_package_id,
        SubtitleJob.video_package_id == payload.video_package_id,
        SubtitleJob.status == "SUCCESS"
    ).first()
    if existing:
        return existing

    job = SubtitleJob(
        id=uuid.uuid4(),
        voice_package_id=payload.voice_package_id,
        video_package_id=payload.video_package_id,
        language=payload.language or "en",
        provider=payload.provider or "alignment",
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

@router.get("", response_model=list[SubtitleJobResponseDTO])
async def list_subtitle_jobs(
    status: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """List enqueued, processing, or completed subtitle jobs."""
    query = db.query(SubtitleJob)
    if status:
        query = query.filter(SubtitleJob.status == status)
    return query.order_by(SubtitleJob.created_at.desc()).all()

@router.get("/metrics", response_model=SubtitleMetricsDTO)
async def get_subtitle_metrics(db: Session = Depends(get_db)):
    """Fetch AI Subtitle Agent telemetry stats, active worker heartbeats, and queue monitors."""
    jobs_queued = db.query(SubtitleJob).filter(SubtitleJob.status == "QUEUED").count()
    jobs_processing = db.query(SubtitleJob).filter(SubtitleJob.status == "PROCESSING").count()
    jobs_succeeded = db.query(SubtitleJob).filter(SubtitleJob.status == "SUCCESS").count()
    jobs_failed = db.query(SubtitleJob).filter(SubtitleJob.status == "FAILED").count()
    jobs_retrying = db.query(SubtitleJob).filter(SubtitleJob.status == "RETRYING").count()
    jobs_cancelled = db.query(SubtitleJob).filter(SubtitleJob.status == "CANCELLED").count()

    avg_duration = 0.0
    if AGENT_STATE["jobs_succeeded"] > 0:
        avg_duration = AGENT_STATE["total_duration_sec"] / AGENT_STATE["jobs_succeeded"]

    uptime = "offline"
    if AGENT_STATE["is_running"] and AGENT_STATE["started_at"]:
        uptime = str(datetime.utcnow() - AGENT_STATE["started_at"])

    heartbeats = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id.like("subtitle-agent-%")).all()
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

@router.get("/{id}", response_model=SubtitleJobResponseDTO)
async def get_subtitle_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve full details of a subtitle job, including scene subtitles, tracks, and version snapshot history."""
    job = db.query(SubtitleJob).filter(SubtitleJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Subtitle job not found.")
    return job

@router.post("/{id}/regenerate", response_model=SubtitlePackageDTO)
async def regenerate_subtitle_package(
    id: uuid.UUID, 
    max_cpl: Optional[int] = Query(37),
    db: Session = Depends(get_db)
):
    """Re-segment captions and re-optimize line breaks for an existing SubtitlePackage."""
    job = db.query(SubtitleJob).filter(SubtitleJob.id == id).first()
    if not job or not job.packages:
        raise HTTPException(status_code=404, detail="Subtitle package not found.")

    pkg = job.packages[0]
    provider_instance = subtitle_registry.get_provider(job.provider) or subtitle_registry.get_provider("alignment")

    all_segments = []
    total_words = 0
    scenes = db.query(SceneSubtitle).filter(SceneSubtitle.subtitle_package_id == pkg.id).all()

    for sc in scenes:
        new_segs = await provider_instance.segment(sc.caption_text, sc.word_timings, {"max_cpl": max_cpl})
        opt_segs = await provider_instance.optimize(new_segs, {})

        # Clear existing segments and re-add
        db.query(CaptionSegment).filter(CaptionSegment.scene_subtitle_id == sc.id).delete()
        for seg in opt_segs:
            c_seg = CaptionSegment(
                id=uuid.uuid4(),
                scene_subtitle_id=sc.id,
                segment_number=seg["segment_number"],
                start_ms=seg["start_ms"],
                end_ms=seg["end_ms"],
                text=seg["text"],
                words=seg.get("words", []),
                reading_speed_wpm=seg.get("reading_speed_wpm", 0.0),
                reading_speed_cps=seg.get("reading_speed_cps", 0.0),
                reading_speed_cpl=seg.get("reading_speed_cpl", 0.0),
                confidence=seg.get("confidence", 1.0)
            )
            db.add(c_seg)
            all_segments.append(seg)
            total_words += len(seg.get("words", []))

    # Re-export tracks
    base_filename = f"subtitles_{job.id.hex[:8]}"
    srt_file = os.path.join("artifacts/subtitles", f"{base_filename}.srt")
    vtt_file = os.path.join("artifacts/subtitles", f"{base_filename}.vtt")
    ass_file = os.path.join("artifacts/subtitles", f"{base_filename}.ass")
    json_file = os.path.join("artifacts/subtitles", f"{base_filename}.json")

    await provider_instance.export(all_segments, "srt", srt_file)
    await provider_instance.export(all_segments, "vtt", vtt_file)
    await provider_instance.export(all_segments, "ass", ass_file)
    await provider_instance.export(all_segments, "json", json_file)

    # Add SubtitleVersion
    new_ver_num = pkg.version + 1
    ver_snapshot = [
        {
            "scene_number": sc.scene_number,
            "caption_text": sc.caption_text,
            "total_segments": len(sc.segments),
            "key_phrases": sc.key_phrases
        } for sc in scenes
    ]
    ver = SubtitleVersion(
        id=uuid.uuid4(),
        subtitle_package_id=pkg.id,
        version=new_ver_num,
        parent_version=pkg.version,
        lineage_action="REGENERATED",
        assets_snapshot=ver_snapshot
    )
    db.add(ver)

    pkg.version = new_ver_num
    pkg.total_captions = len(all_segments)
    pkg.total_words = total_words
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg

@router.post("/{id}/export")
async def export_subtitle_track(
    id: uuid.UUID,
    format_type: str = Query("srt", regex="^(srt|vtt|ass|json)$"),
    db: Session = Depends(get_db)
):
    """Export and download subtitle file in target format (.srt, .vtt, .ass, .json)."""
    job = db.query(SubtitleJob).filter(SubtitleJob.id == id).first()
    if not job or not job.packages:
        raise HTTPException(status_code=404, detail="Subtitle package not found.")

    pkg = job.packages[0]
    track = db.query(SubtitleTrack).filter(SubtitleTrack.subtitle_package_id == pkg.id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Subtitle track files missing.")

    file_map = {
        "srt": track.srt_path,
        "vtt": track.webvtt_path,
        "ass": track.ass_path,
        "json": track.json_timeline_path
    }

    target_path = file_map.get(format_type)
    if not target_path or not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail=f"Target subtitle file format '{format_type}' not found on disk.")

    filename = os.path.basename(target_path)
    return FileResponse(path=target_path, filename=filename, media_type="application/octet-stream")

@router.delete("/{id}")
async def delete_subtitle_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Cancel a queued/retrying subtitle job, or delete completed records from DB."""
    job = db.query(SubtitleJob).filter(SubtitleJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Subtitle job not found.")

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
