import os
import uuid
from datetime import datetime
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database.session import get_db
from core.database.models import VoiceJob, VoicePackage, SceneVoice, VoiceVersion, ScriptPackage, WorkerHeartbeat
from contracts.dto.voice import VoiceJobCreateDTO, VoiceJobResponseDTO, VoiceMetricsDTO, VoicePackageDTO
from brain.agents.voice_agent import is_valid_transition, AGENT_STATE, _agent_tasks
from providers.voice.registry import voice_registry
from core.config.settings import settings

router = APIRouter(prefix="/voices")

@router.post("", response_model=VoiceJobResponseDTO)
async def create_voice_job(payload: VoiceJobCreateDTO, db: Session = Depends(get_db)):
    """Enqueue a new speech synthesis job for a ScriptPackage."""
    script = db.query(ScriptPackage).filter(ScriptPackage.id == payload.script_package_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="ScriptPackage not found.")

    existing = db.query(VoiceJob).filter(
        VoiceJob.script_package_id == payload.script_package_id,
        VoiceJob.status == "SUCCESS"
    ).first()
    if existing:
        return existing

    job = VoiceJob(
        id=uuid.uuid4(),
        script_package_id=payload.script_package_id,
        provider="bedrock" if settings.app.env != "testing" else "mock",
        voice_model="Polly-Neural" if settings.app.env != "testing" else "MockSpeech-v2",
        language=payload.language or "en",
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

@router.get("", response_model=list[VoiceJobResponseDTO])
async def list_voice_jobs(
    status: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """List enqueued, processing, completed, or failed speech synthesis jobs."""
    query = db.query(VoiceJob)
    if status:
        query = query.filter(VoiceJob.status == status)
    return query.order_by(VoiceJob.created_at.desc()).all()

@router.get("/metrics", response_model=VoiceMetricsDTO)
async def get_voice_metrics(db: Session = Depends(get_db)):
    """Fetch AI Voice Agent metrics, active worker heartbeats, and queue depth stats."""
    jobs_queued = db.query(VoiceJob).filter(VoiceJob.status == "QUEUED").count()
    jobs_processing = db.query(VoiceJob).filter(VoiceJob.status == "PROCESSING").count()
    jobs_succeeded = db.query(VoiceJob).filter(VoiceJob.status == "SUCCESS").count()
    jobs_failed = db.query(VoiceJob).filter(VoiceJob.status == "FAILED").count()
    jobs_retrying = db.query(VoiceJob).filter(VoiceJob.status == "RETRYING").count()
    jobs_cancelled = db.query(VoiceJob).filter(VoiceJob.status == "CANCELLED").count()

    avg_duration = 0.0
    if AGENT_STATE["jobs_succeeded"] > 0:
        avg_duration = AGENT_STATE["total_duration_sec"] / AGENT_STATE["jobs_succeeded"]

    uptime = "offline"
    if AGENT_STATE["is_running"] and AGENT_STATE["started_at"]:
        uptime = str(datetime.utcnow() - AGENT_STATE["started_at"])

    # Query heartbeats matching voice agents
    heartbeats = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id.like("voice-agent-%")).all()
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

@router.get("/{id}", response_model=VoiceJobResponseDTO)
async def get_voice_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve full details of a voice generation job, including scene voices and version snapshot history."""
    job = db.query(VoiceJob).filter(VoiceJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Voice job not found.")
    return job

@router.delete("/{id}")
async def delete_voice_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Cancel a queued/retrying voice job, or delete completed records from DB."""
    job = db.query(VoiceJob).filter(VoiceJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Voice job not found.")

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

@router.post("/{id}/regenerate", response_model=VoicePackageDTO)
async def regenerate_scene_voice(
    id: uuid.UUID, 
    scene_number: Optional[int] = Query(None), 
    db: Session = Depends(get_db)
):
    """Regenerate specific scene voice narration (updates Active SceneVoice and adds VoiceVersion tracking record)."""
    job = db.query(VoiceJob).filter(VoiceJob.id == id).first()
    if not job or not job.packages:
        raise HTTPException(status_code=404, detail="Voice package not found.")
    
    pkg = job.packages[0]
    provider_instance = voice_registry.get_provider(job.provider) or voice_registry.get_provider("mock")
    
    target_scene = scene_number if scene_number else 1
    asset = db.query(SceneVoice).filter(
        SceneVoice.voice_package_id == pkg.id,
        SceneVoice.scene_number == target_scene
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail=f"Scene {target_scene} not found in package.")

    # Call regenerate on provider
    options = {
        "language": asset.language,
        "emotion": asset.emotion,
        "speaking_style": asset.speaking_style,
        "pitch": asset.pitch,
        "speed": asset.speed,
        "volume": asset.volume
    }
    
    asset_data = await provider_instance.regenerate(asset.narration, asset.voice_id, options)
    
    # Update active SceneVoice
    asset.local_path = asset_data["local_path"]
    asset.storage_key = asset_data["storage_key"]
    asset.public_url = asset_data.get("public_url")
    asset.preview_url = asset_data.get("preview_url")
    asset.duration_ms = asset_data["duration_ms"]
    asset.word_alignment = asset_data.get("word_alignment")
    asset.sentence_alignment = asset_data.get("sentence_alignment")
    asset.quality_score = asset_data.get("quality_score", 0.95)
    db.add(asset)
    db.flush()

    # Recalculate package duration
    assets = db.query(SceneVoice).filter(SceneVoice.voice_package_id == pkg.id).all()
    pkg.overall_duration_ms = sum(a.duration_ms for a in assets)

    # Save new version lineage snapshot
    new_ver_num = pkg.version + 1
    assets_snapshot = [
        {
            "scene_number": a.scene_number,
            "local_path": a.local_path,
            "narration": a.narration,
            "duration_ms": a.duration_ms,
            "quality_score": a.quality_score
        } for a in assets
    ]

    ver = VoiceVersion(
        id=uuid.uuid4(),
        voice_package_id=pkg.id,
        version=new_ver_num,
        parent_version=pkg.version,
        lineage_action="REGENERATED",
        scene_number=target_scene,
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

@router.post("/{id}/clone")
async def clone_voice_profile(
    id: uuid.UUID,
    name: str = Query(...),
    db: Session = Depends(get_db)
):
    """Clone a custom narrator voice from sample file paths."""
    job = db.query(VoiceJob).filter(VoiceJob.id == id).first()
    if not job or not job.packages:
        raise HTTPException(status_code=404, detail="Voice package not found.")
    
    pkg = job.packages[0]
    provider_instance = voice_registry.get_provider(job.provider) or voice_registry.get_provider("mock")
    
    # Use standard placeholder file
    sample_path = "./storage/audio/sample_voice.wav"
    os.makedirs("./storage/audio", exist_ok=True)
    with open(sample_path, "wb") as f:
        f.write(b"WAV_SAMPLE")

    voice_id = await provider_instance.clone_voice(sample_path, name)
    
    # Update speaker profile
    profile = pkg.voice_profile or {}
    profile["cloned_voice_id"] = voice_id
    profile["cloned_voice_name"] = name
    pkg.voice_profile = profile
    db.add(pkg)
    db.commit()

    return {
        "status": "cloned",
        "voice_id": voice_id,
        "name": name,
        "profile": profile
    }
