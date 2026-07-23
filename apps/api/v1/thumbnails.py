import os
import uuid
from datetime import datetime
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from core.database.session import get_db
from core.database.models import (
    ThumbnailJob, 
    ThumbnailPackage, 
    ThumbnailVariant,
    ThumbnailAsset,
    CompositionTemplate,
    ThumbnailAnalysis,
    ThumbnailScore,
    ThumbnailStyleProfile,
    ThumbnailVersion,
    ThumbnailExperiment,
    ScriptPackage,
    ImagePackage,
    VideoPackage,
    WorkerHeartbeat
)
from contracts.dto.thumbnail import ThumbnailJobCreateDTO, ThumbnailJobResponseDTO, ThumbnailMetricsDTO, ThumbnailPackageDTO
from brain.agents.thumbnail_agent import is_valid_transition, AGENT_STATE, _agent_tasks
from providers.thumbnail.registry import thumbnail_registry

router = APIRouter(prefix="/thumbnails")

@router.post("", response_model=ThumbnailJobResponseDTO)
async def create_thumbnail_job(payload: ThumbnailJobCreateDTO, db: Session = Depends(get_db)):
    """Enqueue a new AI Thumbnail generation job combining Script, Image, Video, Subtitle, and Music packages."""
    script_pkg = db.query(ScriptPackage).filter(ScriptPackage.id == payload.script_package_id).first()
    image_pkg = db.query(ImagePackage).filter(ImagePackage.id == payload.image_package_id).first()
    video_pkg = db.query(VideoPackage).filter(VideoPackage.id == payload.video_package_id).first()

    if not script_pkg or not image_pkg or not video_pkg:
        raise HTTPException(status_code=404, detail="Input packages (ScriptPackage, ImagePackage, VideoPackage) must exist.")

    existing = db.query(ThumbnailJob).filter(
        ThumbnailJob.script_package_id == payload.script_package_id,
        ThumbnailJob.image_package_id == payload.image_package_id,
        ThumbnailJob.video_package_id == payload.video_package_id,
        ThumbnailJob.status == "SUCCESS"
    ).first()
    if existing:
        return existing

    job = ThumbnailJob(
        id=uuid.uuid4(),
        script_package_id=payload.script_package_id,
        image_package_id=payload.image_package_id,
        video_package_id=payload.video_package_id,
        subtitle_package_id=payload.subtitle_package_id,
        music_package_id=payload.music_package_id,
        provider=payload.provider or "template",
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

@router.get("", response_model=list[ThumbnailJobResponseDTO])
async def list_thumbnail_jobs(
    status: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """List enqueued, processing, or completed thumbnail jobs."""
    query = db.query(ThumbnailJob)
    if status:
        query = query.filter(ThumbnailJob.status == status)
    return query.order_by(ThumbnailJob.created_at.desc()).all()

@router.get("/metrics", response_model=ThumbnailMetricsDTO)
async def get_thumbnail_metrics(db: Session = Depends(get_db)):
    """Fetch AI Thumbnail Agent telemetry stats, active worker heartbeats, and queue depth."""
    jobs_queued = db.query(ThumbnailJob).filter(ThumbnailJob.status == "QUEUED").count()
    jobs_processing = db.query(ThumbnailJob).filter(ThumbnailJob.status == "PROCESSING").count()
    jobs_succeeded = db.query(ThumbnailJob).filter(ThumbnailJob.status == "SUCCESS").count()
    jobs_failed = db.query(ThumbnailJob).filter(ThumbnailJob.status == "FAILED").count()
    jobs_retrying = db.query(ThumbnailJob).filter(ThumbnailJob.status == "RETRYING").count()
    jobs_cancelled = db.query(ThumbnailJob).filter(ThumbnailJob.status == "CANCELLED").count()

    avg_duration = 0.0
    if AGENT_STATE["jobs_succeeded"] > 0:
        avg_duration = AGENT_STATE["total_duration_sec"] / AGENT_STATE["jobs_succeeded"]

    uptime = "offline"
    if AGENT_STATE["is_running"] and AGENT_STATE["started_at"]:
        uptime = str(datetime.utcnow() - AGENT_STATE["started_at"])

    heartbeats = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id.like("thumbnail-agent-%")).all()
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

@router.get("/{id}", response_model=ThumbnailJobResponseDTO)
async def get_thumbnail_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve full details of a thumbnail job, including variants, composition templates, scores, and version history."""
    job = db.query(ThumbnailJob).filter(ThumbnailJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Thumbnail job not found.")
    return job

@router.post("/{id}/regenerate", response_model=ThumbnailPackageDTO)
async def regenerate_thumbnail_variants(
    id: uuid.UUID, 
    layout_type: Optional[str] = Query("centered"),
    db: Session = Depends(get_db)
):
    """Regenerate candidate variants with a custom layout and update version lineage."""
    job = db.query(ThumbnailJob).filter(ThumbnailJob.id == id).first()
    if not job or not job.packages:
        raise HTTPException(status_code=404, detail="Thumbnail package not found.")

    pkg = job.packages[0]
    provider_instance = thumbnail_registry.get_provider(job.provider) or thumbnail_registry.get_provider("template")

    os.makedirs("artifacts/thumbnails", exist_ok=True)
    new_variant_file = f"artifacts/thumbnails/variant_regen_{uuid.uuid4().hex[:6]}.png"

    comp_spec = await provider_instance.compose(pkg.variants[0].source_frame_key if pkg.variants else "", {
        "primary_hook": pkg.variants[0].primary_hook if pkg.variants else "REGENERATED THUMBNAIL"
    }, layout_type, {})

    render_res = await provider_instance.render(comp_spec, new_variant_file)
    score_res = await provider_instance.score(new_variant_file, comp_spec, {})

    # Create new Asset and Variant
    asset = ThumbnailAsset(
        id=uuid.uuid4(),
        storage_key=new_variant_file,
        width=1280,
        height=720,
        format="png",
        file_size_bytes=render_res["file_size_bytes"]
    )
    db.add(asset)
    db.flush()

    variant = ThumbnailVariant(
        id=uuid.uuid4(),
        thumbnail_package_id=pkg.id,
        thumbnail_asset_id=asset.id,
        variant_name=f"Regenerated {layout_type.capitalize()}",
        scene_number=1,
        source_frame_key=comp_spec.get("frame_path"),
        primary_hook=comp_spec["primary_hook"],
        secondary_hook=comp_spec.get("secondary_hook"),
        badge_text="REGEN",
        brand_label="AATES STUDIO",
        layout_type=layout_type,
        contrast_score=score_res["contrast_score"],
        readability_score=score_res["text_readability_score"],
        composition_score=score_res["overall_score"],
        brand_score=score_res["brand_consistency_score"],
        ctr_prediction_score=score_res["ctr_prediction_score"],
        quality_score=score_res["overall_score"],
        is_selected=True
    )
    db.add(variant)
    db.flush()

    # Update selected variant
    for v in pkg.variants:
        v.is_selected = (v.id == variant.id)
        db.add(v)

    pkg.primary_thumbnail_id = variant.id
    pkg.selected_variant_id = variant.id
    pkg.version += 1

    # Save ThumbnailVersion
    ver_snapshot = [{"variant_id": str(v.id), "layout_type": v.layout_type, "quality_score": v.quality_score} for v in pkg.variants]
    ver = ThumbnailVersion(
        id=uuid.uuid4(),
        thumbnail_package_id=pkg.id,
        version=pkg.version,
        parent_version=pkg.version - 1,
        lineage_action="REGENERATED",
        assets_snapshot=ver_snapshot
    )
    db.add(ver)
    db.commit()
    db.refresh(pkg)
    return pkg

@router.post("/{id}/score")
async def score_thumbnail_package(id: uuid.UUID, db: Session = Depends(get_db)):
    """Recalculate dual heuristic & learned CTR scores for all variants."""
    job = db.query(ThumbnailJob).filter(ThumbnailJob.id == id).first()
    if not job or not job.packages:
        raise HTTPException(status_code=404, detail="Thumbnail package not found.")

    pkg = job.packages[0]
    provider_instance = thumbnail_registry.get_provider(job.provider) or thumbnail_registry.get_provider("template")

    scores_list = []
    for v in pkg.variants:
        res = await provider_instance.score(v.asset.storage_key if v.asset else "", {"primary_hook": v.primary_hook}, {})
        if v.score:
            v.score.heuristic_score = res["heuristic_score"]
            v.score.learned_score = res["learned_score"]
            v.score.overall_score = res["overall_score"]
            db.add(v.score)
        scores_list.append({"variant_id": str(v.id), "scores": res})

    db.commit()
    return {"status": "success", "scored_variants": scores_list}

@router.post("/{id}/preview")
async def generate_thumbnail_preview(id: uuid.UUID, db: Session = Depends(get_db)):
    """Generate and return preview file path for primary thumbnail."""
    job = db.query(ThumbnailJob).filter(ThumbnailJob.id == id).first()
    if not job or not job.packages:
        raise HTTPException(status_code=404, detail="Thumbnail package not found.")

    pkg = job.packages[0]
    sel_variant = next((v for v in pkg.variants if v.is_selected), pkg.variants[0] if pkg.variants else None)
    if not sel_variant or not sel_variant.asset:
        raise HTTPException(status_code=404, detail="Primary thumbnail variant asset missing.")

    return {"preview_path": sel_variant.asset.storage_key, "status": "success"}

@router.delete("/{id}")
async def delete_thumbnail_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Cancel a queued/retrying thumbnail job, or delete completed records from DB."""
    job = db.query(ThumbnailJob).filter(ThumbnailJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Thumbnail job not found.")

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
