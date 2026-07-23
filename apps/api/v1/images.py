import uuid
from datetime import datetime
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database.session import get_db
from core.database.models import ImageJob, ImagePackage, SceneAsset, ImageVersion, ScriptPackage, WorkerHeartbeat
from contracts.dto.image import ImageJobCreateDTO, ImageJobResponseDTO, ImageMetricsDTO, ImagePackageDTO, SceneAssetDTO
from brain.agents.image_agent import is_valid_transition, AGENT_STATE, _agent_tasks
from providers.image.registry import image_registry

router = APIRouter(prefix="/images")

@router.post("", response_model=ImageJobResponseDTO)
async def create_image_job(payload: ImageJobCreateDTO, db: Session = Depends(get_db)):
    """Enqueue a new scene image generation job for a ScriptPackage."""
    script = db.query(ScriptPackage).filter(ScriptPackage.id == payload.script_package_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="ScriptPackage not found.")

    existing = db.query(ImageJob).filter(
        ImageJob.script_package_id == payload.script_package_id,
        ImageJob.status == "SUCCESS"
    ).first()
    if existing:
        return existing

    job = ImageJob(
        id=uuid.uuid4(),
        script_package_id=payload.script_package_id,
        provider=settings.ai.image_provider if settings.app.env != "testing" else "mock",
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

@router.get("", response_model=list[ImageJobResponseDTO])
async def list_image_jobs(
    status: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """List enqueued, processing, completed, or failed image generation jobs."""
    query = db.query(ImageJob)
    if status:
        query = query.filter(ImageJob.status == status)
    return query.order_by(ImageJob.created_at.desc()).all()

@router.get("/metrics", response_model=ImageMetricsDTO)
async def get_image_metrics(db: Session = Depends(get_db)):
    """Fetch AI Image Agent metrics, active worker heartbeats, and queue depth stats."""
    jobs_queued = db.query(ImageJob).filter(ImageJob.status == "QUEUED").count()
    jobs_processing = db.query(ImageJob).filter(ImageJob.status == "PROCESSING").count()
    jobs_succeeded = db.query(ImageJob).filter(ImageJob.status == "SUCCESS").count()
    jobs_failed = db.query(ImageJob).filter(ImageJob.status == "FAILED").count()
    jobs_retrying = db.query(ImageJob).filter(ImageJob.status == "RETRYING").count()
    jobs_cancelled = db.query(ImageJob).filter(ImageJob.status == "CANCELLED").count()

    avg_duration = 0.0
    if AGENT_STATE["jobs_succeeded"] > 0:
        avg_duration = AGENT_STATE["total_duration_sec"] / AGENT_STATE["jobs_succeeded"]

    uptime = "offline"
    if AGENT_STATE["is_running"] and AGENT_STATE["started_at"]:
        uptime = str(datetime.utcnow() - AGENT_STATE["started_at"])

    # Query heartbeats matching image agents
    heartbeats = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id.like("image-agent-%")).all()
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

@router.get("/{id}", response_model=ImageJobResponseDTO)
async def get_image_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve full details of an image generation job, including scene assets and version snapshot history."""
    job = db.query(ImageJob).filter(ImageJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Image job not found.")
    return job

@router.delete("/{id}")
async def delete_image_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Cancel a queued/retrying image job, or delete completed records from DB."""
    job = db.query(ImageJob).filter(ImageJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Image job not found.")

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

@router.post("/{id}/regenerate", response_model=ImagePackageDTO)
async def regenerate_scene_image(
    id: uuid.UUID, 
    scene_number: Optional[int] = Query(None), 
    db: Session = Depends(get_db)
):
    """Regenerate a specific scene visual asset (creates new ImageVersion snapshot with lineage tracking)."""
    job = db.query(ImageJob).filter(ImageJob.id == id).first()
    if not job or not job.packages:
        raise HTTPException(status_code=404, detail="Image package not found.")
    
    pkg = job.packages[0]
    provider_instance = image_registry.get_provider(job.provider) or image_registry.get_provider("mock")
    
    # Generate new image for targeted scene (or default to scene 1)
    target_scene = scene_number if scene_number else 1
    asset = db.query(SceneAsset).filter(
        SceneAsset.image_package_id == pkg.id,
        SceneAsset.scene_number == target_scene
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail=f"Scene {target_scene} not found in package.")

    # Call regenerate on provider
    options = {
        "camera_angle": asset.camera_angle,
        "lighting": asset.lighting,
        "background": asset.background,
        "emotion": asset.emotion,
        "style": asset.style
    }
    
    asset_data = await provider_instance.regenerate(asset.prompt, asset.aspect_ratio, options)
    
    # Update active SceneAsset
    asset.local_path = asset_data["local_path"]
    asset.storage_key = asset_data["storage_key"]
    asset.public_url = asset_data.get("public_url")
    asset.thumbnail_url = asset_data.get("thumbnail_url")
    asset.preview_url = asset_data.get("preview_url")
    asset.seed = asset_data.get("seed")
    asset.quality_score = asset_data.get("quality_score", 0.95)
    db.add(asset)
    db.flush()

    # Save new version lineage snapshot
    new_ver_num = pkg.version + 1
    assets = db.query(SceneAsset).filter(SceneAsset.image_package_id == pkg.id).all()
    assets_snapshot = [
        {
            "scene_number": a.scene_number,
            "local_path": a.local_path,
            "prompt": a.prompt,
            "seed": a.seed,
            "quality_score": a.quality_score
        } for a in assets
    ]

    ver = ImageVersion(
        id=uuid.uuid4(),
        image_package_id=pkg.id,
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

@router.post("/{id}/upscale")
async def upscale_scene_image(
    id: uuid.UUID, 
    scene_number: int = Query(...), 
    db: Session = Depends(get_db)
):
    """Upscale scene image from high resolution to print/publish standard."""
    job = db.query(ImageJob).filter(ImageJob.id == id).first()
    if not job or not job.packages:
        raise HTTPException(status_code=404, detail="Image package not found.")
    
    pkg = job.packages[0]
    asset = db.query(SceneAsset).filter(
        SceneAsset.image_package_id == pkg.id,
        SceneAsset.scene_number == scene_number
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail=f"Scene {scene_number} not found in package.")

    provider_instance = image_registry.get_provider(job.provider) or image_registry.get_provider("mock")
    upscaled_path = await provider_instance.upscale(asset.local_path)
    
    return {
        "status": "upscaled",
        "scene_number": scene_number,
        "original_path": asset.local_path,
        "upscaled_path": upscaled_path
    }

from core.config.settings import settings
