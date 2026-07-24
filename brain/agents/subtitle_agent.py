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
from providers.subtitle.registry import subtitle_registry

logger = logging.getLogger("subtitle_agent")

STAGES = {
    "VALIDATING": 0.1,
    "ALIGNMENT_LOADING": 0.2,
    "SEGMENTING": 0.35,
    "LINE_BREAK_OPTIMIZATION": 0.5,
    "STYLE_APPLICATION": 0.6,
    "FORMAT_GENERATION": 0.75,
    "QUALITY_CHECK": 0.88,
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
        orphans = db.query(SubtitleJob).filter(SubtitleJob.status == "PROCESSING").all()
        for job in orphans:
            logger.info(f"Resetting orphaned subtitle job {job.id} back to QUEUED.")
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

def validate_subtitle_segments(segments: list[dict[str, Any]], video_duration_ms: int = 0) -> None:
    """Enhanced Subtitle Validation Rules."""
    if not segments:
        raise ValueError("Subtitle validation failed: No caption segments were generated.")

    seen_texts = set()
    for idx, seg in enumerate(segments):
        text = seg.get("text", "").strip()
        start_ms = seg.get("start_ms", 0)
        end_ms = seg.get("end_ms", 0)
        dur_ms = end_ms - start_ms

        # 1. Empty caption
        if not text:
            raise ValueError(f"Subtitle validation failed: Empty caption at segment {seg.get('segment_number', idx + 1)}.")

        # 2. Caption flashes (< 200ms)
        if dur_ms < 200:
            raise ValueError(f"Subtitle validation failed: Caption flash detected ({dur_ms}ms < 200ms) at segment {seg.get('segment_number', idx + 1)}.")

        # 3. Excessive caption duration (> 7000ms)
        if dur_ms > 7000:
            raise ValueError(f"Subtitle validation failed: Long on-screen caption ({dur_ms}ms > 7000ms) at segment {seg.get('segment_number', idx + 1)}.")

        # 4. Excessive CPS (Characters per Second > 30)
        cps = seg.get("reading_speed_cps", 0.0)
        if cps > 30.0:
            raise ValueError(f"Subtitle validation failed: Excessive reading speed ({cps} CPS > 30 CPS) at segment {seg.get('segment_number', idx + 1)}.")

        # 5. Overlapping timings
        if idx > 0:
            prev = segments[idx - 1]
            if start_ms < prev.get("end_ms", 0):
                raise ValueError(f"Subtitle validation failed: Timing overlap between segment {prev.get('segment_number')} and {seg.get('segment_number')}.")

        # 6. Timing outside video duration
        if video_duration_ms > 0 and end_ms > video_duration_ms + 1000:
            raise ValueError(f"Subtitle validation failed: Caption end time ({end_ms}ms) exceeds video duration ({video_duration_ms}ms).")

        seen_texts.add(text)

async def process_subtitle_job(db: Session, job: SubtitleJob) -> None:
    correlation_id = str(uuid.uuid4())
    logger.info(json.dumps({
        "event": "Subtitle Processing Started",
        "job_id": str(job.id),
        "voice_id": str(job.voice_package_id),
        "video_id": str(job.video_package_id),
        "correlation_id": correlation_id
    }))

    start_time = time.monotonic()

    try:
        # Stage 1: VALIDATING
        job.stage = "VALIDATING"
        job.progress = STAGES["VALIDATING"]
        db.commit()

        voice_pkg = db.query(VoicePackage).filter(VoicePackage.id == job.voice_package_id).first()
        video_pkg = db.query(VideoPackage).filter(VideoPackage.id == job.video_package_id).first()

        if not voice_pkg or not video_pkg:
            raise ValueError("Input packages mismatch: Complete Voice and Video packages are required.")

        provider_instance = subtitle_registry.get_provider(job.provider) or subtitle_registry.get_provider("alignment")

        # Stage 2: ALIGNMENT_LOADING
        job.stage = "ALIGNMENT_LOADING"
        job.progress = STAGES["ALIGNMENT_LOADING"]
        db.commit()

        aligned_data = await provider_instance.generate(voice_pkg, video_pkg, {})
        scenes = aligned_data.get("scenes", [])

        # Get or create CaptionStyleProfile
        style_profile = db.query(CaptionStyleProfile).filter(CaptionStyleProfile.platform == video_pkg.platform).first()
        if not style_profile:
            style_profile = CaptionStyleProfile(
                id=uuid.uuid4(),
                name=f"{video_pkg.platform.capitalize()} Subtitle Style",
                platform=video_pkg.platform,
                font_family="Inter",
                font_size=24,
                font_weight="Bold",
                text_color="#FFFFFF",
                outline_color="#000000",
                outline_width=2,
                alignment="center",
                vertical_position="bottom"
            )
            db.add(style_profile)
            db.flush()

        # Stage 3: SEGMENTING & Stage 4: LINE_BREAK_OPTIMIZATION
        job.stage = "SEGMENTING"
        job.progress = STAGES["SEGMENTING"]
        db.commit()

        all_segments = []
        total_word_count = 0
        scene_subtitles_list = []

        for sc in scenes:
            raw_segs = await provider_instance.segment(sc["caption_text"], sc["word_timings"], {
                "max_cpl": 37,
                "max_lines": 2
            })
            
            # Stage 4: LINE_BREAK_OPTIMIZATION
            job.stage = "LINE_BREAK_OPTIMIZATION"
            job.progress = STAGES["LINE_BREAK_OPTIMIZATION"]
            db.commit()

            opt_segs = await provider_instance.optimize(raw_segs, {
                "font": style_profile.font_family,
                "size": style_profile.font_size
            })

            sc["segments"] = opt_segs
            scene_subtitles_list.append(sc)
            for seg in opt_segs:
                all_segments.append(seg)
                total_word_count += len(seg.get("words", []))

        # Stage 5: STYLE_APPLICATION & Stage 6: FORMAT_GENERATION
        job.stage = "STYLE_APPLICATION"
        job.progress = STAGES["STYLE_APPLICATION"]
        db.commit()

        job.stage = "FORMAT_GENERATION"
        job.progress = STAGES["FORMAT_GENERATION"]
        db.commit()

        # Export multi-format tracks (.srt, .vtt, .ass, .json)
        base_filename = f"subtitles_{job.id.hex[:8]}"
        srt_file = os.path.join("artifacts/subtitles", f"{base_filename}.srt")
        vtt_file = os.path.join("artifacts/subtitles", f"{base_filename}.vtt")
        ass_file = os.path.join("artifacts/subtitles", f"{base_filename}.ass")
        json_file = os.path.join("artifacts/subtitles", f"{base_filename}.json")

        await provider_instance.export(all_segments, "srt", srt_file)
        await provider_instance.export(all_segments, "vtt", vtt_file)
        await provider_instance.export(all_segments, "ass", ass_file, style_profile.__dict__)
        await provider_instance.export(all_segments, "json", json_file)

        # Stage 7: QUALITY_CHECK
        job.stage = "QUALITY_CHECK"
        job.progress = STAGES["QUALITY_CHECK"]
        db.commit()

        validate_subtitle_segments(all_segments, video_pkg.duration_ms)

        # Shared Package Manifest
        package_manifest = {
            "package_type": "SubtitlePackage",
            "version": 1,
            "parent_package_references": {
                "voice_package_id": str(voice_pkg.id),
                "video_package_id": str(video_pkg.id)
            },
            "producer_agent": "subtitle_agent",
            "provider": job.provider,
            "model": "Alignment-v1",
            "input_dependencies": ["VoicePackage", "VideoPackage"],
            "output_artifacts": {
                "srt": srt_file,
                "vtt": vtt_file,
                "ass": ass_file,
                "json": json_file
            },
            "quality_score": 0.95,
            "validation_status": "PASSED",
            "created_at": datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat()
        }

        # Create SubtitlePackage
        pkg = SubtitlePackage(
            id=uuid.uuid4(),
            job_id=job.id,
            voice_package_id=voice_pkg.id,
            video_package_id=video_pkg.id,
            language=aligned_data.get("language", "en"),
            caption_style=style_profile.name,
            subtitle_formats=["srt", "vtt", "ass", "json"],
            scene_count=len(scenes),
            total_captions=len(all_segments),
            total_words=total_word_count,
            metadata_artifacts={
                "srt_path": srt_file,
                "webvtt_path": vtt_file,
                "ass_path": ass_file,
                "json_timeline_path": json_file
            },
            package_manifest=package_manifest,
            # BasePackageMixin fields
            version=1,
            parent_package_id=None,
            source_agent="subtitle_agent",
            provider=job.provider,
            model="AlignmentEngine-v1",
            prompt_version="v1.0",
            quality_score=0.95
        )
        db.add(pkg)
        db.flush()

        # Save SceneSubtitle & CaptionSegment records
        for sc in scene_subtitles_list:
            sc_sub = SceneSubtitle(
                id=uuid.uuid4(),
                subtitle_package_id=pkg.id,
                scene_number=sc["scene_number"],
                caption_text=sc["caption_text"],
                word_timings=sc["word_timings"],
                sentence_timings=sc["sentence_timings"],
                caption_position="bottom",
                safe_region="80% safety window",
                reading_speed_wpm=sc["segments"][0]["reading_speed_wpm"] if sc["segments"] else 0.0,
                reading_speed_cps=sc["segments"][0]["reading_speed_cps"] if sc["segments"] else 0.0,
                reading_speed_cpl=sc["segments"][0]["reading_speed_cpl"] if sc["segments"] else 0.0,
                confidence=1.0,
                language=pkg.language,
                key_phrases=sc.get("key_phrases", []),
                importance_score=sc.get("importance_score", 0.85),
                quality_score=0.95
            )
            db.add(sc_sub)
            db.flush()

            for seg in sc["segments"]:
                c_seg = CaptionSegment(
                    id=uuid.uuid4(),
                    scene_subtitle_id=sc_sub.id,
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

        # Save SubtitleTrack record
        track = SubtitleTrack(
            id=uuid.uuid4(),
            subtitle_package_id=pkg.id,
            style_profile_id=style_profile.id,
            track_name=f"{aligned_data.get('language', 'en').upper()} Standard Track",
            language=aligned_data.get("language", "en"),
            is_default=True,
            is_original=True,
            is_translated=False,
            is_auto_generated=True,
            is_human_edited=False,
            srt_path=srt_file,
            webvtt_path=vtt_file,
            ass_path=ass_file,
            json_timeline_path=json_file,
            burned_caption_metadata={"style": style_profile.name, "font": style_profile.font_family}
        )
        db.add(track)

        # Save SubtitleVersion snapshot
        ver_snapshot = [
            {
                "scene_number": sc["scene_number"],
                "text": sc["caption_text"],
                "total_segments": len(sc["segments"]),
                "key_phrases": sc.get("key_phrases", [])
            } for sc in scene_subtitles_list
        ]
        ver = SubtitleVersion(
            id=uuid.uuid4(),
            subtitle_package_id=pkg.id,
            version=1,
            parent_version=None,
            lineage_action="INITIAL",
            assets_snapshot=ver_snapshot
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
            "event": "Subtitle Processing Completed",
            "job_id": str(job.id),
            "captions_count": len(all_segments),
            "duration_sec": total_duration,
            "correlation_id": correlation_id
        }))

    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error(json.dumps({
            "event": "Subtitle Processing Failed",
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

async def subtitle_agent_poll_loop(agent_id: str) -> None:
    logger.info(f"Subtitle Agent loop started for agent ID: {agent_id}")
    while AGENT_STATE["is_running"]:
        db = SessionLocal()
        try:
            update_agent_heartbeat(db, agent_id)

            query = db.query(SubtitleJob).filter(
                SubtitleJob.status.in_(["QUEUED", "RETRYING"]),
                (SubtitleJob.scheduled_at == None) | (SubtitleJob.scheduled_at <= datetime.datetime.now(datetime.UTC).replace(tzinfo=None))
            ).order_by(
                SubtitleJob.priority.desc(),
                SubtitleJob.created_at.asc()
            )

            if db.bind.dialect.name == "sqlite":
                job = query.first()
            else:
                job = query.with_for_update(skip_locked=True).first()

            if job:
                if is_valid_transition(job.status, "PROCESSING"):
                    job.status = "PROCESSING"
                    job.started_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
                    db.commit()

                    await process_subtitle_job(db, job)
                else:
                    logger.warning(f"Invalid transition from {job.status} to PROCESSING for job {job.id}")

        except Exception as e:
            logger.error(f"Exception inside Subtitle Agent loop iteration: {str(e)}")
        finally:
            db.close()

        await asyncio.sleep(2.0)

async def start_subtitle_agent(concurrency: int = 1) -> None:
    if AGENT_STATE["is_running"]:
        return
    AGENT_STATE["is_running"] = True
    AGENT_STATE["started_at"] = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

    db = SessionLocal()
    try:
        recover_orphaned_jobs(db)
    finally:
        db.close()

    for i in range(concurrency):
        agent_id = f"subtitle-agent-{i}"
        task = asyncio.create_task(subtitle_agent_poll_loop(agent_id))
        _agent_tasks.append(task)
    logger.info(f"Started {concurrency} concurrent background AI Subtitle Agents.")

async def stop_subtitle_agent() -> None:
    if not AGENT_STATE["is_running"]:
        return
    AGENT_STATE["is_running"] = False
    for task in _agent_tasks:
        task.cancel()
    if _agent_tasks:
        await asyncio.gather(*_agent_tasks, return_exceptions=True)
    _agent_tasks.clear()
    logger.info("Stopped background AI Subtitle Agents.")
ZOOMING = "zoom"
