import asyncio
import datetime
import json
import logging
import random
import time
import uuid
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from core.config.settings import settings
from core.database.session import SessionLocal
from core.database.models import ScriptJob, ScriptPackage, ScriptVersion, KnowledgePackage, WorkerHeartbeat
from providers.script.registry import script_registry

logger = logging.getLogger("script_agent")

# Named progress stages
STAGES = {
    "VALIDATING": 0.1,
    "PLANNING": 0.2,
    "GENERATING": 0.5,
    "REVIEWING": 0.7,
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
    """Enforce strict state machine transitions."""
    if current == target:
        return True
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
    """Periodically writes heartbeats to worker_heartbeats table."""
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
    """Startup routine resetting hung PROCESSING jobs back to QUEUED."""
    try:
        orphans = db.query(ScriptJob).filter(ScriptJob.status == "PROCESSING").all()
        for job in orphans:
            logger.info(f"Resetting orphaned script job {job.id} back to QUEUED.")
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
    """Classifies if error is transient (network issues, throttling) or permanent."""
    msg = error_msg.lower()
    return any(term in msg for term in ["timeout", "429", "throttling", "connection refused", "network", "service unavailable"])

def get_backoff_delay(attempts: int) -> int:
    """Returns retry delay using exponential backoff schedule: 30s, 60s, 120s, 300s."""
    backoffs = [30, 60, 120, 300]
    idx = min(attempts - 1, len(backoffs) - 1)
    return backoffs[idx]

def validate_script_quality(script_data: dict[str, Any], review_report: dict[str, Any]) -> None:
    """Verify script package complies with all strict quality gates."""
    # 1. Missing Hook
    if not script_data.get("hook") or not script_data["hook"].strip():
        raise ValueError("Script validation failed: Missing Hook.")
    
    # 2. Missing CTA
    if not script_data.get("cta") or not script_data["cta"].strip():
        raise ValueError("Script validation failed: Missing CTA.")

    # 3. Missing Scene list or empty scenes
    scenes = script_data.get("scene_breakdown", [])
    if not scenes:
        raise ValueError("Script validation failed: Missing Scene List.")
    for scene in scenes:
        if not scene.get("visual_prompt") or not scene["visual_prompt"].strip():
            raise ValueError(f"Script validation failed: Scene {scene.get('scene_number')} has empty visual prompt.")
        if not scene.get("narration") or not scene["narration"].strip():
            # Support audio_narration fallback
            if not scene.get("audio_narration") or not scene["audio_narration"].strip():
                raise ValueError(f"Script validation failed: Scene {scene.get('scene_number')} has empty narration.")

    # 4. Missing Thumbnail prompt
    if not script_data.get("thumbnail_prompt") or not script_data["thumbnail_prompt"].strip():
        raise ValueError("Script validation failed: Missing Thumbnail Prompt.")

    # 5. Minimum Quality Score gate
    overall_score = review_report.get("overall_score", 0.0)
    if overall_score < 0.6:
        raise ValueError(f"Script validation failed: Quality score {overall_score} falls below minimum threshold 0.6.")

async def process_script_job(db: Session, job: ScriptJob) -> None:
    """Runs a single Script Agent lifecycle through validation, generation, review, and auto-improvement."""
    correlation_id = str(uuid.uuid4())
    logger.info(json.dumps({
        "event": "Script Generation Started",
        "job_id": str(job.id),
        "kp_id": str(job.knowledge_package_id),
        "correlation_id": correlation_id
    }))

    start_time = time.monotonic()
    
    try:
        # Stage 1: VALIDATING
        job.stage = "VALIDATING"
        job.progress = STAGES["VALIDATING"]
        db.commit()

        kp = db.query(KnowledgePackage).filter(KnowledgePackage.id == job.knowledge_package_id).first()
        if not kp:
            raise ValueError(f"KnowledgePackage {job.knowledge_package_id} not found in database.")

        provider_instance = script_registry.get_provider(job.provider)
        if not provider_instance:
            if settings.app.env != "testing":
                raise RuntimeError(f"Script provider '{job.provider}' is not configured or available in {settings.app.env} mode.")
            provider_instance = script_registry.get_provider("mock")
        
        # Stage 2: PLANNING
        job.stage = "PLANNING"
        job.progress = STAGES["PLANNING"]
        db.commit()
        await asyncio.sleep(0.5)  # Simulate planning phase

        # Stage 3: GENERATING (Initial generation)
        job.stage = "GENERATING"
        job.progress = STAGES["GENERATING"]
        db.commit()

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

        gen_start = time.monotonic()
        script_data = await provider_instance.generate(kp_dict, job.platform, job.language)
        gen_duration = time.monotonic() - gen_start

        # Stage 4: REVIEWING (Initial Quality review)
        job.stage = "REVIEWING"
        job.progress = STAGES["REVIEWING"]
        db.commit()
        review_data = await provider_instance.review(script_data, job.platform)

        # Stage 5: OPTIMIZING (Closed-Loop Auto-Improvement)
        job.stage = "OPTIMIZING"
        job.progress = STAGES["OPTIMIZING"]
        db.commit()

        iterations = 0
        max_iterations = 3
        target_threshold = 0.8

        while review_data.get("overall_score", 0.0) < target_threshold and iterations < max_iterations:
            iterations += 1
            logger.info(f"Quality score {review_data.get('overall_score')} below threshold. Triggering Auto-Improvement (Iteration {iterations})...")
            
            # Improve only weak sections
            script_data = await provider_instance.improve(script_data, review_data, job.platform)
            # Re-review
            review_data = await provider_instance.review(script_data, job.platform)

        # Final quality gate validation
        validate_script_quality(script_data, review_data)

        # Save ScriptPackage
        meta = script_data.get("metadata", {})
        meta.update({
            "model_id": meta.get("model_id", "bedrock-claude-3-5"),
            "provider": job.provider,
            "prompt_version": meta.get("prompt_version", "v1.0"),
            "temperature": meta.get("temperature", 0.3),
            "generation_time_sec": round(gen_duration, 2),
            "improvement_count": iterations
        })

        # Set fallback visual_prompts if missing in schema
        scenes = script_data.get("scene_breakdown", [])
        visual_prompts_list = [s.get("visual_prompt", "") for s in scenes]
        on_screen_text_list = [s.get("onscreen_text", "") for s in scenes]

        pkg = ScriptPackage(
            id=uuid.uuid4(),
            job_id=job.id,
            knowledge_package_id=kp.id,
            title=script_data.get("title", f"Script for {kp.topic}"),
            platform=job.platform,
            language=job.language,
            target_audience=kp.audience,
            tone=script_data.get("tone", "Informative"),
            style=script_data.get("style", "Cinematic"),
            estimated_duration_sec=script_data.get("estimated_duration_sec", 60.0),
            word_count=script_data.get("word_count", 150),
            reading_time_sec=script_data.get("reading_time_sec", 60.0),
            hook=script_data.get("hook", ""),
            opening=script_data.get("opening", ""),
            problem=script_data.get("problem", ""),
            story=script_data.get("story", ""),
            solution=script_data.get("solution", ""),
            cta=script_data.get("cta", ""),
            narration=script_data.get("narration", ""),
            scene_breakdown=scenes,
            on_screen_text=on_screen_text_list,
            visual_prompts=visual_prompts_list,
            thumbnail_prompt=script_data.get("thumbnail_prompt", ""),
            description=script_data.get("description", ""),
            tags=script_data.get("tags", []),
            hashtags=script_data.get("hashtags", []),
            references=kp.references,
            telemetry_metadata=meta,
            version=1,
            parent_package_id=None,
            source_agent="script_agent",
            provider=job.provider,
            model=meta.get("model_id", "bedrock-claude-3-5"),
            prompt_version=meta.get("prompt_version", "v1.0"),
            quality_score=review_data.get("overall_score", 0.0),
            review_report=review_data
        )
        db.add(pkg)
        db.flush()

        # Save ScriptVersion lineage
        ver = ScriptVersion(
            id=uuid.uuid4(),
            script_package_id=pkg.id,
            version=1,
            parent_version=None,
            lineage_action="INITIAL" if iterations == 0 else "IMPROVED",
            title=pkg.title,
            hook=pkg.hook,
            opening=pkg.opening,
            problem=pkg.problem,
            story=pkg.story,
            solution=pkg.solution,
            cta=pkg.cta,
            narration=pkg.narration,
            scene_breakdown=pkg.scene_breakdown,
            thumbnail_prompt=pkg.thumbnail_prompt,
            description=pkg.description,
            tags=pkg.tags,
            hashtags=pkg.hashtags,
            quality_score=pkg.quality_score,
            review_report=pkg.review_report
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
            "event": "Script Generation Completed",
            "job_id": str(job.id),
            "platform": job.platform,
            "duration_sec": total_duration,
            "review_score": pkg.quality_score,
            "improvement_count": iterations,
            "correlation_id": correlation_id
        }))

    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error(json.dumps({
            "event": "Script Generation Failed",
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
                logger.info(f"Script job {job.id} scheduled for retry in {delay}s (attempt {job.attempts})")
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

async def script_agent_poll_loop(agent_id: str) -> None:
    """Infinite polling loop fetching and processing queued script generation jobs."""
    logger.info(f"Script Agent loop started for agent ID: {agent_id}")
    while AGENT_STATE["is_running"]:
        db = SessionLocal()
        try:
            update_agent_heartbeat(db, agent_id)

            # Query queued script jobs
            query = db.query(ScriptJob).filter(
                ScriptJob.status.in_(["QUEUED", "RETRYING"]),
                (ScriptJob.scheduled_at == None) | (ScriptJob.scheduled_at <= datetime.datetime.utcnow())
            ).order_by(
                ScriptJob.priority.desc(),
                ScriptJob.created_at.asc()
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
                    await process_script_job(db, job)
                else:
                    logger.warning(f"Invalid transition from {job.status} to PROCESSING for job {job.id}")
            
        except Exception as e:
            logger.error(f"Exception inside Script Agent loop iteration: {str(e)}")
        finally:
            db.close()

        await asyncio.sleep(2.0)

async def start_script_agent(concurrency: int = 1) -> None:
    """Spawn specified background Script Agent worker tasks."""
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
        agent_id = f"script-agent-{i}"
        task = asyncio.create_task(script_agent_poll_loop(agent_id))
        _agent_tasks.append(task)
    logger.info(f"Started {concurrency} concurrent background AI Script Agents.")

async def stop_script_agent() -> None:
    """Terminate and join active background Script Agent worker tasks."""
    if not AGENT_STATE["is_running"]:
        return
    AGENT_STATE["is_running"] = False
    for task in _agent_tasks:
        task.cancel()
    if _agent_tasks:
        await asyncio.gather(*_agent_tasks, return_exceptions=True)
    _agent_tasks.clear()
    logger.info("Stopped background AI Script Agents.")
