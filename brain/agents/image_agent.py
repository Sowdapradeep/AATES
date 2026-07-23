import asyncio
import datetime
import json
import logging
import os
import time
import uuid
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from core.config.settings import settings
from core.database.session import SessionLocal
from core.database.models import ImageJob, ImagePackage, SceneAsset, ImageVersion, ScriptPackage, WorkerHeartbeat
from providers.image.registry import image_registry

logger = logging.getLogger("image_agent")

# Named progress stages
STAGES = {
    "VALIDATING": 0.1,
    "PLANNING": 0.2,
    "PROMPTING": 0.3,
    "GENERATING": 0.7,
    "QUALITY_CHECK": 0.8,
    "OPTIMIZING": 0.9,
    "COMPLETED": 1.0,
    "FAILED": 1.0
}

# State Transitions Matrix
_TRANSITIONS = {
    "QUEUED": {"PROCESSING", "CANCELLED"},
    "RETRYING": {"PROCESSING", "CANCELLED"},
    "PROCESSING": {"SUCCESS", "RETRYING", "FAILED", "CANCELLED"},
    "FAILED": {"QUEUED"},
    "CANCELLED": {"QUEUED"},
    "SUCCESS": set()  # Terminal state
}

def is_valid_transition(current: str, target: str) -> bool:
    return target in _TRANSITIONS.get(current, set())

# Global state tracking for agent telemetry
AGENT_STATE = {
    "is_running": False,
    "started_at": None,
    "jobs_processed": 0,
    "jobs_succeeded": 0,
    "jobs_failed": 0,
    "total_duration_sec": 0.0
}

_agent_tasks = []

def update_agent_heartbeat(db: Session, agent_id: str) -> None:
    try:
        hb = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id == agent_id).first()
        if not hb:
            hb = WorkerHeartbeat(worker_id=agent_id, last_heartbeat_at=datetime.datetime.utcnow())
            db.add(hb)
        else:
            hb.last_heartbeat_at = datetime.datetime.utcnow()
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Failed to update heartbeat for {agent_id}: {str(e)}")

def recover_orphaned_jobs(db: Session) -> None:
    try:
        orphans = db.query(ImageJob).filter(ImageJob.status == "PROCESSING").all()
        for job in orphans:
            logger.info(f"Resetting orphaned image job {job.id} back to QUEUED.")
            job.status = "QUEUED"
            job.stage = "VALIDATING"
            job.progress = 0.0
            job.attempts += 1
            if job.attempts >= job.max_attempts:
                job.status = "FAILED"
                job.failed_at = datetime.datetime.utcnow()
                job.error_code = "ORPHANED_LIMIT"
                job.error_message = "Job orphaned repeatedly and exceeded max attempts."
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Orphaned recovery failed: {str(e)}")

def is_transient_error(error_msg: str) -> bool:
    msg = error_msg.lower()
    return any(term in msg for term in ["timeout", "429", "throttling", "connection refused", "network", "service unavailable"])

def get_backoff_delay(attempts: int) -> int:
    backoffs = [30, 60, 120, 300]
    idx = min(attempts - 1, len(backoffs) - 1)
    return backoffs[idx]

def build_scene_prompt(scene: dict[str, Any], style_preset: str) -> str:
    """Prompt Builder composing scene visual context, camera composition, and style preset."""
    visual_context = scene.get("visual_prompt") or scene.get("prompt") or "Abstract visual composition"
    camera_angle = scene.get("camera_angle") or "Cinematic shot"
    lighting = scene.get("lighting") or "Dramatic ambient light"
    background = scene.get("background") or ""
    emotion = scene.get("emotion") or "Inspiring"
    
    parts = [
        f"A {style_preset} style image of {visual_context}.",
        f"Composition: {camera_angle}.",
        f"Lighting: {lighting}.",
        f"Mood: {emotion}."
    ]
    if background:
        parts.append(f"Setting: {background}.")
        
    return " ".join(parts)

def validate_scene_asset(asset_data: dict[str, Any], aspect_ratio: str) -> None:
    """Verify scene asset passes standard quality rules before saving."""
    local_path = asset_data.get("local_path")
    if not local_path or not os.path.exists(local_path):
        raise ValueError("Image quality check failed: Image file is missing on local disk.")

    if not asset_data.get("prompt") or not asset_data["prompt"].strip():
        raise ValueError("Image quality check failed: Missing Prompt text.")

    if asset_data.get("quality_score", 1.0) < 0.7:
        raise ValueError(f"Image quality check failed: Quality score {asset_data.get('quality_score')} falls below threshold 0.7.")

async def process_image_job(db: Session, job: ImageJob) -> None:
    correlation_id = str(uuid.uuid4())
    logger.info(json.dumps({
        "event": "Image Generation Started",
        "job_id": str(job.id),
        "script_id": str(job.script_package_id),
        "correlation_id": correlation_id
    }))

    start_time = time.monotonic()
    
    try:
        # Stage 1: VALIDATING
        job.stage = "VALIDATING"
        job.progress = STAGES["VALIDATING"]
        db.commit()

        script = db.query(ScriptPackage).filter(ScriptPackage.id == job.script_package_id).first()
        if not script:
            raise ValueError(f"ScriptPackage {job.script_package_id} not found in database.")

        provider_instance = image_registry.get_provider(job.provider)
        if not provider_instance:
            if settings.app.env != "testing":
                raise RuntimeError(f"Image provider '{job.provider}' is not configured or available in {settings.app.env} mode.")
            provider_instance = image_registry.get_provider("mock")
        
        # Stage 2: PLANNING
        job.stage = "PLANNING"
        job.progress = STAGES["PLANNING"]
        db.commit()
        await asyncio.sleep(0.5)

        # Aspect ratios mapping
        aspect_ratio = "9:16" if "short" in script.platform.lower() or "reel" in script.platform.lower() else "16:9"
        resolution = "1080x1920" if aspect_ratio == "9:16" else "1920x1080"
        style_preset = script.style or "Cinematic"

        # Create ImagePackage object
        pkg = ImagePackage(
            id=uuid.uuid4(),
            job_id=job.id,
            script_package_id=script.id,
            platform=script.platform,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            style_preset=style_preset,
            overall_theme=f"Consistent style theme aligned with {style_preset}",
            image_count=len(script.scene_breakdown),
            generation_settings={"provider": provider_instance.name},
            character_profile=script.target_audience, # Mock list
            character_reference_images=[],
            character_id=f"char-{uuid.uuid4().hex[:6]}",
            # BasePackageMixin columns
            version=1,
            parent_package_id=None,
            source_agent="image_agent",
            provider=job.provider,
            model="mock-sdxl-v2" if settings.app.env == "testing" else settings.ai.bedrock_image_model,
            prompt_version="v1.0",
            quality_score=0.9,
            telemetry_metadata={"style": style_preset}
        )
        db.add(pkg)
        db.flush()

        assets_snapshot = []

        # Loop script scenes
        previous_asset_id = None
        for scene in script.scene_breakdown:
            scene_number = scene.get("scene_number", 1)
            
            # Stage 3: PROMPTING
            job.stage = "PROMPTING"
            job.progress = STAGES["PROMPTING"]
            db.commit()

            prompt = build_scene_prompt(scene, style_preset)
            negative_prompt = "blurry, low quality, distorted, missing details"

            # Stage 4: GENERATING
            job.stage = "GENERATING"
            job.progress = STAGES["GENERATING"]
            db.commit()

            options = {
                "negative_prompt": negative_prompt,
                "camera_angle": scene.get("camera_angle"),
                "lighting": scene.get("lighting"),
                "background": scene.get("background"),
                "emotion": scene.get("emotion"),
                "style": style_preset
            }

            gen_start = time.monotonic()
            asset_data = await provider_instance.generate(prompt, aspect_ratio, options)
            duration = time.monotonic() - gen_start

            # Stage 5: QUALITY_CHECK
            job.stage = "QUALITY_CHECK"
            job.progress = STAGES["QUALITY_CHECK"]
            db.commit()

            validate_scene_asset(asset_data, aspect_ratio)

            # Stage 6: OPTIMIZING (Prompt improvement on low quality scores - simulated in loop)
            iterations = 0
            while asset_data.get("quality_score", 1.0) < 0.8 and iterations < 2:
                iterations += 1
                job.stage = "OPTIMIZING"
                db.commit()
                # Regenerate with slightly adjusted prompt
                prompt = f"[OPTIMIZED PROMPT] " + prompt
                asset_data = await provider_instance.regenerate(prompt, aspect_ratio, options)

            # Create SceneAsset
            asset = SceneAsset(
                id=uuid.uuid4(),
                image_package_id=pkg.id,
                scene_number=scene_number,
                duration=scene.get("duration", 5.0),
                prompt=prompt,
                negative_prompt=negative_prompt,
                seed=asset_data.get("seed"),
                provider=provider_instance.name,
                model=asset_data.get("model", "mock-model"),
                model_version=asset_data.get("model_version"),
                prompt_version=asset_data.get("prompt_version"),
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                style=style_preset,
                camera_angle=asset_data.get("camera_angle"),
                character_reference=pkg.character_id,
                background=asset_data.get("background"),
                emotion=asset_data.get("emotion"),
                lighting=asset_data.get("lighting"),
                color_palette=asset_data.get("color_palette"),
                local_path=asset_data.get("local_path"),
                storage_key=asset_data.get("storage_key"),
                public_url=asset_data.get("public_url"),
                thumbnail_url=asset_data.get("thumbnail_url"),
                preview_url=asset_data.get("preview_url"),
                previous_scene_id=previous_asset_id,
                transition_suggestion="Cross dissolve",
                generation_duration_sec=duration,
                quality_score=asset_data.get("quality_score", 0.9)
            )
            db.add(asset)
            db.flush()

            # link relationship chains
            if previous_asset_id:
                prev_asset = db.query(SceneAsset).filter(SceneAsset.id == previous_asset_id).first()
                if prev_asset:
                    prev_asset.next_scene_id = asset.id

            previous_asset_id = asset.id

            assets_snapshot.append({
                "scene_number": asset.scene_number,
                "local_path": asset.local_path,
                "prompt": asset.prompt,
                "seed": asset.seed,
                "quality_score": asset.quality_score
            })

        # Save ImageVersion
        ver = ImageVersion(
            id=uuid.uuid4(),
            image_package_id=pkg.id,
            version=1,
            parent_version=None,
            lineage_action="INITIAL",
            assets_snapshot=assets_snapshot
        )
        db.add(ver)

        total_duration = time.monotonic() - start_time

        # Update Job status to SUCCESS
        if is_valid_transition(job.status, "SUCCESS"):
            job.status = "SUCCESS"
            job.stage = "COMPLETED"
            job.progress = STAGES["COMPLETED"]
            job.completed_at = datetime.datetime.utcnow()
            job.duration_sec = total_duration
            db.add(job)
            db.commit()

        AGENT_STATE["jobs_succeeded"] += 1
        AGENT_STATE["total_duration_sec"] += total_duration
        AGENT_STATE["jobs_processed"] += 1

        logger.info(json.dumps({
            "event": "Image Generation Completed",
            "job_id": str(job.id),
            "platform": script.platform,
            "duration_sec": total_duration,
            "correlation_id": correlation_id
        }))

    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error(json.dumps({
            "event": "Image Generation Failed",
            "job_id": str(job.id),
            "error": error_msg,
            "correlation_id": correlation_id
        }))

        # Handle retry logic
        job.attempts += 1
        if is_transient_error(error_msg) and job.attempts < job.max_attempts:
            delay = get_backoff_delay(job.attempts)
            if is_valid_transition(job.status, "RETRYING"):
                job.status = "RETRYING"
                job.scheduled_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=delay)
                job.error_code = "TRANSIENT_ERROR"
                job.error_message = error_msg
                db.add(job)
                db.commit()
        else:
            if is_valid_transition(job.status, "FAILED"):
                job.status = "FAILED"
                job.stage = "FAILED"
                job.progress = STAGES["FAILED"]
                job.failed_at = datetime.datetime.utcnow()
                job.error_code = "PERMANENT_ERROR"
                job.error_message = error_msg
                db.add(job)
                db.commit()
            AGENT_STATE["jobs_failed"] += 1
            AGENT_STATE["jobs_processed"] += 1

async def image_agent_poll_loop(agent_id: str) -> None:
    logger.info(f"Image Agent loop started for agent ID: {agent_id}")
    while AGENT_STATE["is_running"]:
        db = SessionLocal()
        try:
            update_agent_heartbeat(db, agent_id)

            # Query queued script jobs
            query = db.query(ImageJob).filter(
                ImageJob.status.in_(["QUEUED", "RETRYING"]),
                (ImageJob.scheduled_at == None) | (ImageJob.scheduled_at <= datetime.datetime.utcnow())
            ).order_by(
                ImageJob.priority.desc(),
                ImageJob.created_at.asc()
            )

            # Locking
            if db.bind.dialect.name == "sqlite":
                job = query.first()
            else:
                job = query.with_for_update(skip_locked=True).first()

            if job:
                # Transition to PROCESSING
                if is_valid_transition(job.status, "PROCESSING"):
                    job.status = "PROCESSING"
                    job.started_at = datetime.datetime.utcnow()
                    db.commit()

                    # Run processing
                    await process_image_job(db, job)
                else:
                    logger.warning(f"Invalid transition from {job.status} to PROCESSING for job {job.id}")
            
        except Exception as e:
            logger.error(f"Exception inside Image Agent loop iteration: {str(e)}")
        finally:
            db.close()

        await asyncio.sleep(2.0)

async def start_image_agent(concurrency: int = 1) -> None:
    if AGENT_STATE["is_running"]:
        return
    AGENT_STATE["is_running"] = True
    AGENT_STATE["started_at"] = datetime.datetime.utcnow()

    # Reset hung jobs
    db = SessionLocal()
    try:
        recover_orphaned_jobs(db)
    finally:
        db.close()

    for i in range(concurrency):
        agent_id = f"image-agent-{i}"
        task = asyncio.create_task(image_agent_poll_loop(agent_id))
        _agent_tasks.append(task)
    logger.info(f"Started {concurrency} concurrent background AI Image Agents.")

async def stop_image_agent() -> None:
    if not AGENT_STATE["is_running"]:
        return
    AGENT_STATE["is_running"] = False
    for task in _agent_tasks:
        task.cancel()
    if _agent_tasks:
        await asyncio.gather(*_agent_tasks, return_exceptions=True)
    _agent_tasks.clear()
    logger.info("Stopped background AI Image Agents.")
ZOOMING = "zoom"
