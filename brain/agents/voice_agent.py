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
from core.database.models import VoiceJob, VoicePackage, SceneVoice, VoiceVersion, ScriptPackage, WorkerHeartbeat
from providers.voice.registry import voice_registry

logger = logging.getLogger("voice_agent")

# Named progress stages
STAGES = {
    "VALIDATING": 0.1,
    "PLANNING": 0.2,
    "VOICE_SELECTION": 0.3,
    "GENERATING": 0.6,
    "ALIGNING": 0.8,
    "QUALITY_CHECK": 0.9,
    "OPTIMIZING": 0.95,
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
        orphans = db.query(VoiceJob).filter(VoiceJob.status == "PROCESSING").all()
        for job in orphans:
            logger.info(f"Resetting orphaned voice job {job.id} back to QUEUED.")
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
    return any(term in msg for term in ["timeout", "429", "throttling", "connection refused", "network", "service unavailable"])

def get_backoff_delay(attempts: int) -> int:
    backoffs = [30, 60, 120, 300]
    idx = min(attempts - 1, len(backoffs) - 1)
    return backoffs[idx]

def build_ssml_narration(text: str, speed: str, pitch: str, volume: str, dictionary: dict[str, str] | None) -> str:
    """SSML Builder applying pronunciation substitutions and wrapping prosody controls."""
    cleaned_text = text
    if dictionary:
        for word, sub in dictionary.items():
            cleaned_text = cleaned_text.replace(word, f"<sub alias='{sub}'>{word}</sub>")

    prosody_attrs = []
    if speed and speed != "1.0x":
        prosody_attrs.append(f"rate='{speed}'")
    if pitch and pitch != "+0%":
        prosody_attrs.append(f"pitch='{pitch}'")
    if volume and volume != "+0dB":
        prosody_attrs.append(f"volume='{volume}'")

    if prosody_attrs:
        return f"<speak><prosody {' '.join(prosody_attrs)}>{cleaned_text}</prosody></speak>"
    return f"<speak>{cleaned_text}</speak>"

def validate_scene_voice(asset_data: dict[str, Any]) -> None:
    """Verify scene voice asset passes standard quality rules before saving."""
    local_path = asset_data.get("local_path")
    if not local_path or not os.path.exists(local_path):
        raise ValueError("Voice quality check failed: Audio file is missing on local disk.")

    if not asset_data.get("word_alignment"):
        raise ValueError("Voice quality check failed: Missing word alignment timings.")

    if asset_data.get("quality_score", 1.0) < 0.7:
        raise ValueError(f"Voice quality check failed: Quality score {asset_data.get('quality_score')} falls below threshold 0.7.")

async def process_voice_job(db: Session, job: VoiceJob) -> None:
    correlation_id = str(uuid.uuid4())
    logger.info(json.dumps({
        "event": "Voice Synthesis Started",
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

        provider_instance = voice_registry.get_provider(job.provider)
        if not provider_instance:
            if settings.app.env != "testing":
                raise RuntimeError(f"Voice provider '{job.provider}' is not configured or available in {settings.app.env} mode.")
            provider_instance = voice_registry.get_provider("mock")
        
        # Stage 2: PLANNING
        job.stage = "PLANNING"
        job.progress = STAGES["PLANNING"]
        db.commit()
        await asyncio.sleep(0.5)

        # Speaker profile defaults
        voice_profile = {
            "voice_id": "Aditi" if job.language == "ta" else "Matthew",
            "provider": job.provider,
            "model": job.voice_model,
            "language": job.language,
            "emotion": "Narrative",
            "pitch": "+0%",
            "speed": "1.0x",
            "volume": "+0dB"
        }

        # Project level Tamil or technical pronunciation dictionary
        pronunciation_dict = {
            "AATES": "A-A-T-E-S",
            "Tokamak": "Toe-kah-mack"
        }

        # Create VoicePackage object
        pkg = VoicePackage(
            id=uuid.uuid4(),
            job_id=job.id,
            script_package_id=script.id,
            platform=script.platform,
            language=job.language,
            voice_profile=voice_profile,
            speaking_style="Narrative",
            overall_duration_ms=0,
            total_words=0,
            total_scenes=len(script.scene_breakdown),
            audio_format="mp3",
            sample_rate=44100,
            bitrate=192000,
            pronunciation_dictionary=pronunciation_dict,
            # BasePackageMixin columns
            version=1,
            parent_package_id=None,
            source_agent="voice_agent",
            provider=job.provider,
            model=job.voice_model,
            prompt_version="v1.0",
            quality_score=0.9,
            telemetry_metadata={"voice_id": voice_profile["voice_id"]}
        )
        db.add(pkg)
        db.flush()

        assets_snapshot = []
        overall_duration_ms = 0
        total_words = 0

        # Loop script scenes
        for scene in script.scene_breakdown:
            scene_number = scene.get("scene_number", 1)
            narration_text = scene.get("narration", "")
            
            # Stage 3: VOICE_SELECTION
            job.stage = "VOICE_SELECTION"
            job.progress = STAGES["VOICE_SELECTION"]
            db.commit()

            # Apply SSML prosody build
            ssml_text = build_ssml_narration(
                narration_text,
                speed=voice_profile["speed"],
                pitch=voice_profile["pitch"],
                volume=voice_profile["volume"],
                dictionary=pronunciation_dict
            )

            # Stage 4: GENERATING & ALIGNING
            job.stage = "GENERATING"
            job.progress = STAGES["GENERATING"]
            db.commit()

            options = {
                "language": job.language,
                "emotion": voice_profile["emotion"],
                "speaking_style": pkg.speaking_style,
                "pitch": voice_profile["pitch"],
                "speed": voice_profile["speed"],
                "volume": voice_profile["volume"]
            }

            gen_start = time.monotonic()
            # Synthesize narration speech
            asset_data = await provider_instance.generate(narration_text, voice_profile["voice_id"], options)
            duration_sec = time.monotonic() - gen_start

            # Stage 5: ALIGNING
            job.stage = "ALIGNING"
            job.progress = STAGES["ALIGNING"]
            db.commit()

            # Stage 6: QUALITY_CHECK
            job.stage = "QUALITY_CHECK"
            job.progress = STAGES["QUALITY_CHECK"]
            db.commit()

            validate_scene_voice(asset_data)

            # Stage 7: OPTIMIZING (SSML tuning if quality is low - simulated)
            iterations = 0
            while asset_data.get("quality_score", 1.0) < 0.8 and iterations < 2:
                iterations += 1
                job.stage = "OPTIMIZING"
                db.commit()
                # Tweak speed slightly for better synthesis
                options["speed"] = "1.05x"
                asset_data = await provider_instance.regenerate(narration_text, voice_profile["voice_id"], options)

            # Create SceneVoice
            asset = SceneVoice(
                id=uuid.uuid4(),
                voice_package_id=pkg.id,
                scene_number=scene_number,
                duration_ms=asset_data.get("duration_ms", 5000),
                narration=narration_text,
                local_path=asset_data["local_path"],
                storage_key=asset_data["storage_key"],
                public_url=asset_data.get("public_url"),
                preview_url=asset_data.get("preview_url"),
                voice_id=voice_profile["voice_id"],
                provider=provider_instance.name,
                model=asset_data.get("model", "mock-voice-model"),
                language=job.language,
                emotion=options["emotion"],
                speaking_style=pkg.speaking_style,
                pitch=options["pitch"],
                speed=options["speed"],
                volume=options["volume"],
                ssml=ssml_text,
                pause_map=asset_data.get("pause_map"),
                word_alignment=asset_data.get("word_alignment"),
                sentence_alignment=asset_data.get("sentence_alignment"),
                phoneme_alignment=asset_data.get("phoneme_alignment"),
                generation_duration_sec=duration_sec,
                quality_score=asset_data.get("quality_score", 0.95)
            )
            db.add(asset)
            db.flush()

            overall_duration_ms += asset.duration_ms
            total_words += len(narration_text.split())

            assets_snapshot.append({
                "scene_number": asset.scene_number,
                "local_path": asset.local_path,
                "narration": asset.narration,
                "duration_ms": asset.duration_ms,
                "quality_score": asset.quality_score
            })

        # Update VoicePackage cumulative details
        pkg.overall_duration_ms = overall_duration_ms
        pkg.total_words = total_words
        db.add(pkg)
        db.flush()

        # Save VoiceVersion
        ver = VoiceVersion(
            id=uuid.uuid4(),
            voice_package_id=pkg.id,
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
            "event": "Voice Synthesis Completed",
            "job_id": str(job.id),
            "platform": script.platform,
            "duration_sec": total_duration,
            "correlation_id": correlation_id
        }))

    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error(json.dumps({
            "event": "Voice Synthesis Failed",
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

async def voice_agent_poll_loop(agent_id: str) -> None:
    logger.info(f"Voice Agent loop started for agent ID: {agent_id}")
    while AGENT_STATE["is_running"]:
        db = SessionLocal()
        try:
            update_agent_heartbeat(db, agent_id)

            # Query queued script jobs
            query = db.query(VoiceJob).filter(
                VoiceJob.status.in_(["QUEUED", "RETRYING"]),
                (VoiceJob.scheduled_at == None) | (VoiceJob.scheduled_at <= datetime.datetime.now(datetime.UTC).replace(tzinfo=None))
            ).order_by(
                VoiceJob.priority.desc(),
                VoiceJob.created_at.asc()
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
                    await process_voice_job(db, job)
                else:
                    logger.warning(f"Invalid transition from {job.status} to PROCESSING for job {job.id}")
            
        except Exception as e:
            logger.error(f"Exception inside Voice Agent loop iteration: {str(e)}")
        finally:
            db.close()

        await asyncio.sleep(2.0)

async def start_voice_agent(concurrency: int = 1) -> None:
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
        agent_id = f"voice-agent-{i}"
        task = asyncio.create_task(voice_agent_poll_loop(agent_id))
        _agent_tasks.append(task)
    logger.info(f"Started {concurrency} concurrent background AI Voice Agents.")

async def stop_voice_agent() -> None:
    if not AGENT_STATE["is_running"]:
        return
    AGENT_STATE["is_running"] = False
    for task in _agent_tasks:
        task.cancel()
    if _agent_tasks:
        await asyncio.gather(*_agent_tasks, return_exceptions=True)
    _agent_tasks.clear()
    logger.info("Stopped background AI Voice Agents.")
ZOOMING = "zoom"
