import uuid
from datetime import UTC, datetime
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database.session import get_db
from core.database.models import ScriptJob, ScriptPackage, ScriptVersion, KnowledgePackage, WorkerHeartbeat
from contracts.dto.script import ScriptJobCreateDTO, ScriptJobResponseDTO, ScriptMetricsDTO, ScriptPackageDTO
from brain.agents.script_agent import is_valid_transition, AGENT_STATE, _agent_tasks
from providers.script.registry import script_registry

router = APIRouter(prefix="/scripts")

@router.post("", response_model=ScriptJobResponseDTO)
async def create_script_job(payload: ScriptJobCreateDTO, db: Session = Depends(get_db)):
    """Enqueue a new script generation job for a KnowledgePackage."""
    kp = db.query(KnowledgePackage).filter(KnowledgePackage.id == payload.knowledge_package_id).first()
    if not kp:
        raise HTTPException(status_code=404, detail="KnowledgePackage not found.")

    existing = db.query(ScriptJob).filter(
        ScriptJob.knowledge_package_id == payload.knowledge_package_id,
        ScriptJob.platform == payload.platform,
        ScriptJob.status == "SUCCESS"
    ).first()
    if existing:
        return existing

    job = ScriptJob(
        id=uuid.uuid4(),
        knowledge_package_id=payload.knowledge_package_id,
        provider="bedrock" if settings.app.env != "testing" else "mock",
        platform=payload.platform,
        language=payload.language,
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

@router.get("", response_model=list[ScriptJobResponseDTO])
async def list_script_jobs(
    status: Optional[str] = None, 
    platform: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """List enqueued, processing, completed, or failed script generation jobs."""
    query = db.query(ScriptJob)
    if status:
        query = query.filter(ScriptJob.status == status)
    if platform:
        query = query.filter(ScriptJob.platform == platform)
    return query.order_by(ScriptJob.created_at.desc()).all()

@router.get("/metrics", response_model=ScriptMetricsDTO)
async def get_script_metrics(db: Session = Depends(get_db)):
    """Fetch AI Script Agent metrics, active worker heartbeats, and queue depth stats."""
    jobs_queued = db.query(ScriptJob).filter(ScriptJob.status == "QUEUED").count()
    jobs_processing = db.query(ScriptJob).filter(ScriptJob.status == "PROCESSING").count()
    jobs_succeeded = db.query(ScriptJob).filter(ScriptJob.status == "SUCCESS").count()
    jobs_failed = db.query(ScriptJob).filter(ScriptJob.status == "FAILED").count()
    jobs_retrying = db.query(ScriptJob).filter(ScriptJob.status == "RETRYING").count()
    jobs_cancelled = db.query(ScriptJob).filter(ScriptJob.status == "CANCELLED").count()

    avg_duration = 0.0
    if AGENT_STATE["jobs_succeeded"] > 0:
        avg_duration = AGENT_STATE["total_duration_sec"] / AGENT_STATE["jobs_succeeded"]

    uptime = "offline"
    if AGENT_STATE["is_running"] and AGENT_STATE["started_at"]:
        uptime = str(datetime.now(UTC).replace(tzinfo=None) - AGENT_STATE["started_at"])

    # Query heartbeats matching script agents
    heartbeats = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id.like("script-agent-%")).all()
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

@router.get("/{id}", response_model=ScriptJobResponseDTO)
async def get_script_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve full details of a script generation job, including its compiled ScriptPackage and version history."""
    job = db.query(ScriptJob).filter(ScriptJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Script job not found.")
    return job

@router.delete("/{id}")
async def delete_script_job(id: uuid.UUID, db: Session = Depends(get_db)):
    """Cancel a queued/retrying script job, or delete completed records from DB."""
    job = db.query(ScriptJob).filter(ScriptJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Script job not found.")

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

@router.post("/{id}/regenerate", response_model=ScriptPackageDTO)
async def regenerate_script_package(id: uuid.UUID, db: Session = Depends(get_db)):
    """Explicitly regenerate script package to append a new version (Version Lineage tracking)."""
    # Fetch job first
    job = db.query(ScriptJob).filter(ScriptJob.id == id).first()
    if not job or not job.packages:
        raise HTTPException(status_code=404, detail="Script package not found.")
    
    pkg = job.packages[0]
    kp = db.query(KnowledgePackage).filter(KnowledgePackage.id == pkg.knowledge_package_id).first()
    if not kp:
        raise HTTPException(status_code=404, detail="KnowledgePackage not found.")

    provider_instance = script_registry.get_provider(job.provider) or script_registry.get_provider("mock")
    
    # Process regeneration
    kp_dict = {
        "topic": kp.topic,
        "summary": kp.summary,
        "keywords": kp.keywords,
        "audience": kp.audience,
        "pain_points": kp.pain_points,
        "statistics": kp.statistics,
        "story_structure": kp.story_structure,
        "visual_ideas": kp.visual_ideas,
        "references": kp.references
    }
    
    script_data = await provider_instance.generate(kp_dict, pkg.platform, pkg.language)
    review_data = await provider_instance.review(script_data, pkg.platform)

    new_ver_num = pkg.version + 1
    
    # Save ScriptVersion lineage
    ver = ScriptVersion(
        id=uuid.uuid4(),
        script_package_id=pkg.id,
        version=new_ver_num,
        parent_version=pkg.version,
        lineage_action="REGENERATED",
        title=script_data.get("title", pkg.title),
        hook=script_data.get("hook", ""),
        opening=script_data.get("opening", ""),
        problem=script_data.get("problem", ""),
        story=script_data.get("story", ""),
        solution=script_data.get("solution", ""),
        cta=script_data.get("cta", ""),
        narration=script_data.get("narration", ""),
        scene_breakdown=script_data.get("scene_breakdown", []),
        thumbnail_prompt=script_data.get("thumbnail_prompt", ""),
        description=script_data.get("description", ""),
        tags=script_data.get("tags", []),
        hashtags=script_data.get("hashtags", []),
        quality_score=review_data.get("overall_score", 0.0),
        review_report=review_data
    )
    db.add(ver)

    # Update active ScriptPackage fields
    pkg.version = new_ver_num
    pkg.parent_package_id = pkg.id
    pkg.source_agent = "script_agent"
    pkg.provider = job.provider
    meta = script_data.get("metadata", {})
    pkg.model = meta.get("model_id", "bedrock-claude-3-5")
    pkg.prompt_version = meta.get("prompt_version", "v1.0")
    pkg.telemetry_metadata = meta
    pkg.title = ver.title
    pkg.hook = ver.hook
    pkg.opening = ver.opening
    pkg.problem = ver.problem
    pkg.story = ver.story
    pkg.solution = ver.solution
    pkg.cta = ver.cta
    pkg.narration = ver.narration
    pkg.scene_breakdown = ver.scene_breakdown
    pkg.thumbnail_prompt = ver.thumbnail_prompt
    pkg.description = ver.description
    pkg.tags = ver.tags
    pkg.hashtags = ver.hashtags
    pkg.quality_score = ver.quality_score
    pkg.review_report = ver.review_report
    
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg

from core.config.settings import settings
