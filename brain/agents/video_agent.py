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
from core.database.models import (
    VideoJob, 
    VideoPackage, 
    SceneVideo, 
    TimelineEvent, 
    VideoVersion, 
    ScriptPackage, 
    ImagePackage,
    VoicePackage,
    WorkerHeartbeat,
    RenderProfile
)
from providers.video.registry import video_registry

logger = logging.getLogger("video_agent")

STAGES = {
    "VALIDATING": 0.1,
    "TIMELINE_BUILDING": 0.2,
    "SCENE_COMPOSITION": 0.3,
    "MOTION_RENDERING": 0.4,
    "TRANSITION_RENDERING": 0.5,
    "AUDIO_SYNCHRONIZATION": 0.7,
    "FINAL_RENDER": 0.8,
    "QUALITY_CHECK": 0.9,
    "OPTIMIZING": 0.95,
    "COMPLETED": 1.0,
    "FAILED": 1.0
}

_TRANSITIONS = {
    "QUEUED": {"PROCESSING", "CANCELLED"},
    "RETRYING": {"PROCESSING", "CANCELLED"},
    "PROCESSING": {"SUCCESS", "RETRYING", "FAILED", "CANCELLED"},
    "FAILED": {"QUEUED"},
    "CANCELLED": {"QUEUED"},
    "SUCCESS": set()
}

def is_valid_transition(current: str, target: str) -> bool:
    return target in _TRANSITIONS.get(current, set())

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
            hb = WorkerHeartbeat(worker_id=agent_id, last_heartbeat_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None))
            db.add(hb)
        else:
            hb.last_heartbeat_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Failed to update heartbeat for {agent_id}: {str(e)}")

def recover_orphaned_jobs(db: Session) -> None:
    try:
        orphans = db.query(VideoJob).filter(VideoJob.status == "PROCESSING").all()
        for job in orphans:
            logger.info(f"Resetting orphaned video job {job.id} back to QUEUED.")
            job.status = "QUEUED"
            job.stage = "VALIDATING"
            job.progress = 0.0
            job.attempts += 1
            if job.attempts >= job.max_attempts:
                job.status = "FAILED"
                job.failed_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
                job.error_code = "ORPHANED_LIMIT"
                job.error_message = "Job orphaned repeatedly and exceeded max attempts."
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Orphaned recovery failed: {str(e)}")

def is_transient_error(error_msg: str) -> bool:
    msg = error_msg.lower()
    return any(term in msg for term in ["timeout", "429", "throttling", "connection refused", "network", "service unavailable", "busy"])

def get_backoff_delay(attempts: int) -> int:
    backoffs = [30, 60, 120, 300]
    idx = min(attempts - 1, len(backoffs) - 1)
    return backoffs[idx]

def validate_timeline_nodes(nodes: list[dict[str, Any]]) -> None:
    """Enhanced timeline engine validation."""
    if not nodes:
        raise ValueError("Video timeline validation failed: Timeline has no scene graph nodes.")
        
    for idx, node in enumerate(nodes):
        # 1. Missing input assets
        if not node.get("image_path") or not os.path.exists(node["image_path"]):
            raise ValueError(f"Video timeline validation failed: Missing image asset for scene {node['scene_number']}.")
        if not node.get("voice_path") or not os.path.exists(node["voice_path"]):
            raise ValueError(f"Video timeline validation failed: Missing voice audio asset for scene {node['scene_number']}.")
            
        # 2. Negative duration
        duration_ms = node.get("duration_ms", 0)
        if duration_ms <= 0:
            raise ValueError(f"Video timeline validation failed: Invalid duration ({duration_ms} ms) for scene {node['scene_number']}.")
            
        # 3. Gaps and overlap checks
        if idx > 0:
            prev = nodes[idx - 1]
            if node["timeline_start_ms"] < prev["timeline_end_ms"]:
                raise ValueError(f"Video timeline validation failed: Overlap detected between scene {prev['scene_number']} and {node['scene_number']}.")
            if node["timeline_start_ms"] > prev["timeline_end_ms"]:
                raise ValueError(f"Video timeline validation failed: Gap detected between scene {prev['scene_number']} and {node['scene_number']}.")

def validate_rendered_video(package_data: dict[str, Any]) -> None:
    """Verify final composite video passes quality gate checks."""
    local_path = package_data.get("local_path")
    if not local_path or not os.path.exists(local_path):
        raise ValueError("Video quality check failed: Output MP4 video file is missing on local disk.")

    if not package_data.get("metadata_artifacts"):
        raise ValueError("Video quality check failed: Missing rendering keyframes and subtitle boundaries metadata.")

    if package_data.get("quality_score", 1.0) < 0.7:
        raise ValueError(f"Video quality check failed: Quality score {package_data.get('quality_score')} falls below threshold 0.7.")

async def process_video_job(db: Session, job: VideoJob) -> None:
    correlation_id = str(uuid.uuid4())
    logger.info(json.dumps({
        "event": "Video Composition Started",
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
        images = db.query(ImagePackage).filter(ImagePackage.id == job.image_package_id).first()
        voices = db.query(VoicePackage).filter(VoicePackage.id == job.voice_package_id).first()

        if not script or not images or not voices:
            raise ValueError("Input packages mismatch: Complete Script, Image, and Voice packages are all required.")

        provider_instance = video_registry.get_provider(job.renderer)
        if not provider_instance:
            if settings.app.env != "testing":
                raise RuntimeError(f"Video provider '{job.renderer}' is not configured or available in {settings.app.env} mode.")
            provider_instance = video_registry.get_provider("mock")

        # Stage 2: TIMELINE_BUILDING
        job.stage = "TIMELINE_BUILDING"
        job.progress = STAGES["TIMELINE_BUILDING"]
        db.commit()

        # Build timeline nodes
        nodes = await provider_instance.build_timeline(script, images, voices)
        validate_timeline_nodes(nodes)

        # Get or create render profile
        profile = job.profile
        if not profile:
            profile = RenderProfile(
                id=uuid.uuid4(),
                name="HD Landscape Preset",
                platform=script.platform,
                resolution="1920x1080",
                aspect_ratio="16:9",
                fps=30,
                codec="h264",
                bitrate=5000000,
                container="mp4"
            )
            db.add(profile)
            db.flush()
            job.render_profile_id = profile.id
            db.commit()

        # Create VideoPackage
        pkg = VideoPackage(
            id=uuid.uuid4(),
            job_id=job.id,
            script_package_id=script.id,
            image_package_id=images.id,
            voice_package_id=voices.id,
            platform=script.platform,
            resolution=profile.resolution,
            aspect_ratio=profile.aspect_ratio,
            fps=profile.fps,
            codec=profile.codec,
            bitrate=profile.bitrate,
            container=profile.container,
            duration_ms=0,
            storage_key="",
            scene_count=len(nodes),
            timeline_version=1,
            # BasePackageMixin columns
            version=1,
            parent_package_id=None,
            source_agent="video_agent",
            provider=job.renderer,
            model="FFmpeg-v6",
            prompt_version="v1.0",
            quality_score=0.9
        )
        db.add(pkg)
        db.flush()

        rendered_scenes = []
        overall_duration_ms = 0

        # Rendering loops
        for node in nodes:
            scene_num = node["scene_number"]
            
            # Stage 3: SCENE_COMPOSITION
            job.stage = "SCENE_COMPOSITION"
            job.progress = STAGES["SCENE_COMPOSITION"]
            db.commit()

            # Stage 4: MOTION_RENDERING & Stage 5: TRANSITION_RENDERING
            job.stage = "MOTION_RENDERING"
            job.progress = STAGES["MOTION_RENDERING"]
            db.commit()

            # Stage 5: TRANSITION_RENDERING
            job.stage = "TRANSITION_RENDERING"
            job.progress = STAGES["TRANSITION_RENDERING"]
            db.commit()

            # Render individual scene clip
            options = {
                "fps": profile.fps,
                "codec": profile.codec,
                "preset": profile.preset
            }
            
            scene_clip = await provider_instance.render_scene(node, options)
            
            sv = SceneVideo(
                id=uuid.uuid4(),
                video_package_id=pkg.id,
                scene_number=scene_num,
                timeline_start_ms=node["timeline_start_ms"],
                timeline_end_ms=node["timeline_end_ms"],
                duration_ms=node["duration_ms"],
                image_asset_id=uuid.UUID(node["image_asset_id"]) if node.get("image_asset_id") else None,
                voice_asset_id=uuid.UUID(node["voice_asset_id"]) if node.get("voice_asset_id") else None,
                motion_preset=node["motion_preset"],
                transition_preset=node["transition_preset"],
                rendered_clip=scene_clip["local_path"],
                storage_key=scene_clip["storage_key"],
                preview_url=scene_clip.get("preview_url"),
                render_metadata=scene_clip.get("render_metadata"),
                quality_score=scene_clip.get("quality_score", 0.95)
            )
            db.add(sv)
            db.flush()

            # Save TimelineEvent
            te = TimelineEvent(
                id=uuid.uuid4(),
                video_package_id=pkg.id,
                scene_number=scene_num,
                start_time_ms=sv.timeline_start_ms,
                end_time_ms=sv.timeline_end_ms,
                voice_offset_ms=0,
                transition_start_ms=sv.timeline_start_ms,
                transition_end_ms=sv.timeline_start_ms + 500, # 500ms transition curve
                motion_start_ms=sv.timeline_start_ms,
                motion_end_ms=sv.timeline_end_ms,
                caption_region="bottom"
            )
            db.add(te)
            db.flush()

            overall_duration_ms += sv.duration_ms
            rendered_scenes.append({
                "scene_number": sv.scene_number,
                "rendered_clip": sv.rendered_clip,
                "timeline_start_ms": sv.timeline_start_ms,
                "timeline_end_ms": sv.timeline_end_ms,
                "duration_ms": sv.duration_ms
            })

        # Stage 6: AUDIO_SYNCHRONIZATION & Stage 7: FINAL_RENDER
        job.stage = "AUDIO_SYNCHRONIZATION"
        job.progress = STAGES["AUDIO_SYNCHRONIZATION"]
        db.commit()

        job.stage = "FINAL_RENDER"
        job.progress = STAGES["FINAL_RENDER"]
        db.commit()

        # Combine scenes
        final_video = await provider_instance.render_video(rendered_scenes, {
            "fps": profile.fps,
            "codec": profile.codec
        })

        # Generate low res preview
        preview_video_path = await provider_instance.render_preview(final_video["local_path"])

        # Stage 8: QUALITY_CHECK
        job.stage = "QUALITY_CHECK"
        job.progress = STAGES["QUALITY_CHECK"]
        db.commit()

        validate_rendered_video(final_video)

        # Update package detail
        pkg.duration_ms = overall_duration_ms
        pkg.storage_key = final_video["storage_key"]
        pkg.preview_video = preview_video_path
        pkg.thumbnail_frame = final_video.get("thumbnail_frame")
        pkg.metadata_artifacts = final_video.get("metadata_artifacts")
        pkg.quality_score = final_video.get("quality_score", 0.95)
        db.add(pkg)
        db.flush()

        # Save VideoVersion
        assets_snapshot = [
            {
                "scene_number": s["scene_number"],
                "rendered_clip": s["rendered_clip"],
                "duration_ms": s["duration_ms"],
                "quality_score": 0.95
            } for s in rendered_scenes
        ]
        
        ver = VideoVersion(
            id=uuid.uuid4(),
            video_package_id=pkg.id,
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
            job.completed_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
            job.duration_sec = total_duration
            db.add(job)
            db.commit()

        AGENT_STATE["jobs_succeeded"] += 1
        AGENT_STATE["total_duration_sec"] += total_duration
        AGENT_STATE["jobs_processed"] += 1

        logger.info(json.dumps({
            "event": "Video Composition Completed",
            "job_id": str(job.id),
            "platform": script.platform,
            "duration_sec": total_duration,
            "correlation_id": correlation_id
        }))

    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error(json.dumps({
            "event": "Video Composition Failed",
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
                job.scheduled_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None) + datetime.timedelta(seconds=delay)
                job.error_code = "TRANSIENT_ERROR"
                job.error_message = error_msg
                db.add(job)
                db.commit()
        else:
            if is_valid_transition(job.status, "FAILED"):
                job.status = "FAILED"
                job.stage = "FAILED"
                job.progress = STAGES["FAILED"]
                job.failed_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
                job.error_code = "PERMANENT_ERROR"
                job.error_message = error_msg
                db.add(job)
                db.commit()
            AGENT_STATE["jobs_failed"] += 1
            AGENT_STATE["jobs_processed"] += 1

async def video_agent_poll_loop(agent_id: str) -> None:
    logger.info(f"Video Agent loop started for agent ID: {agent_id}")
    while AGENT_STATE["is_running"]:
        db = SessionLocal()
        try:
            update_agent_heartbeat(db, agent_id)

            # Query queued video jobs
            query = db.query(VideoJob).filter(
                VideoJob.status.in_(["QUEUED", "RETRYING"]),
                (VideoJob.scheduled_at == None) | (VideoJob.scheduled_at <= datetime.datetime.now(datetime.UTC).replace(tzinfo=None))
            ).order_by(
                VideoJob.priority.desc(),
                VideoJob.created_at.asc()
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
                    job.started_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
                    db.commit()

                    # Run processing
                    await process_video_job(db, job)
                else:
                    logger.warning(f"Invalid transition from {job.status} to PROCESSING for job {job.id}")
            
        except Exception as e:
            logger.error(f"Exception inside Video Agent loop iteration: {str(e)}")
        finally:
            db.close()

        await asyncio.sleep(2.0)

async def start_video_agent(concurrency: int = 1) -> None:
    if AGENT_STATE["is_running"]:
        return
    AGENT_STATE["is_running"] = True
    AGENT_STATE["started_at"] = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

    # Reset hung jobs
    db = SessionLocal()
    try:
        recover_orphaned_jobs(db)
    finally:
        db.close()

    for i in range(concurrency):
        agent_id = f"video-agent-{i}"
        task = asyncio.create_task(video_agent_poll_loop(agent_id))
        _agent_tasks.append(task)
    logger.info(f"Started {concurrency} concurrent background AI Video Agents.")

async def stop_video_agent() -> None:
    if not AGENT_STATE["is_running"]:
        return
    AGENT_STATE["is_running"] = False
    for task in _agent_tasks:
        task.cancel()
    if _agent_tasks:
        await asyncio.gather(*_agent_tasks, return_exceptions=True)
    _agent_tasks.clear()
    logger.info("Stopped background AI Video Agents.")
ZOOMING = "zoom"
