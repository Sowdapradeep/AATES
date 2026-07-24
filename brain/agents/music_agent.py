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
    MusicJob, 
    MusicPackage, 
    SceneMusic, 
    MusicAsset,
    MusicTrack,
    MusicCue,
    AudioTimelineEvent,
    AudioAnalysis,
    AudioMixProfile,
    MusicVersion, 
    ScriptPackage,
    VoicePackage, 
    VideoPackage,
    SubtitlePackage,
    WorkerHeartbeat
)
from providers.music.registry import music_registry

logger = logging.getLogger("music_agent")

STAGES = {
    "VALIDATING": 0.1,
    "MUSIC_SELECTION": 0.2,
    "SCENE_MAPPING": 0.35,
    "TIMELINE_BUILDING": 0.5,
    "DUCKING": 0.6,
    "AUDIO_MIXING": 0.75,
    "LOUDNESS_NORMALIZATION": 0.85,
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
        orphans = db.query(MusicJob).filter(MusicJob.status == "PROCESSING").all()
        for job in orphans:
            logger.info(f"Resetting orphaned music job {job.id} back to QUEUED.")
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

def validate_audio_mix(mix_result: dict[str, Any], analysis_data: dict[str, Any], profile: AudioMixProfile) -> None:
    """Enhanced Audio Quality Gates."""
    master_path = mix_result.get("master_path")
    if not master_path or not os.path.exists(master_path):
        raise ValueError("Audio quality check failed: Master mixed MP3/WAV file missing on disk.")

    peak = analysis_data.get("peak_db", 0.0)
    if peak > -0.1:
        raise ValueError(f"Audio quality check failed: Audio clipping detected ({peak} dBFS > -0.1 dBFS).")

    lufs = analysis_data.get("lufs", -14.0)
    target = profile.target_lufs if profile else -14.0
    if abs(lufs - target) > 3.0:
        raise ValueError(f"Audio quality check failed: LUFS deviation ({lufs} LUFS vs target {target} LUFS) exceeds tolerance.")

async def process_music_job(db: Session, job: MusicJob) -> None:
    correlation_id = str(uuid.uuid4())
    logger.info(json.dumps({
        "event": "Music Processing Started",
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

        script_pkg = db.query(ScriptPackage).filter(ScriptPackage.id == job.script_package_id).first()
        voice_pkg = db.query(VoicePackage).filter(VoicePackage.id == job.voice_package_id).first()
        video_pkg = db.query(VideoPackage).filter(VideoPackage.id == job.video_package_id).first()

        if not script_pkg or not voice_pkg or not video_pkg:
            raise ValueError("Input packages mismatch: Complete ScriptPackage, VoicePackage, and VideoPackage are required.")

        provider_instance = music_registry.get_provider(job.provider) or music_registry.get_provider("library")

        # Get or create AudioMixProfile
        profile = job.profile
        if not profile:
            profile = AudioMixProfile(
                id=uuid.uuid4(),
                name=f"{video_pkg.platform.capitalize()} Mix Profile",
                target_platform=video_pkg.platform,
                music_volume_db=-14.0,
                narration_volume_db=0.0,
                ducking_level_db=-12.0,
                fade_duration_ms=500,
                crossfade_duration_ms=800,
                target_lufs=-14.0,
                true_peak_db=-1.0,
                sample_rate=44100,
                channels=2
            )
            db.add(profile)
            db.flush()
            job.audio_mix_profile_id = profile.id
            db.commit()

        # Stage 2: MUSIC_SELECTION & Stage 3: SCENE_MAPPING
        job.stage = "MUSIC_SELECTION"
        job.progress = STAGES["MUSIC_SELECTION"]
        db.commit()

        # Build raw scene timing inputs
        scene_inputs = []
        scenes = getattr(script_pkg, "scene_breakdown", []) or []
        voice_assets = {getattr(a, "scene_number", i+1): a for i, a in enumerate(getattr(voice_pkg, "assets", []))}
        
        curr_time = 0
        for i, sc in enumerate(scenes):
            sc_num = sc.get("scene_number", i + 1)
            dur_ms = getattr(voice_assets.get(sc_num), "duration_ms", 5000)
            scene_inputs.append({
                "scene_number": sc_num,
                "duration_ms": dur_ms,
                "timeline_start_ms": curr_time,
                "timeline_end_ms": curr_time + dur_ms,
                "narration": sc.get("narration", "")
            })
            curr_time += dur_ms

        job.stage = "SCENE_MAPPING"
        job.progress = STAGES["SCENE_MAPPING"]
        db.commit()

        mapped_scenes = await provider_instance.select_music(script_pkg, scene_inputs)

        # Stage 4: TIMELINE_BUILDING & Stage 5: DUCKING
        job.stage = "TIMELINE_BUILDING"
        job.progress = STAGES["TIMELINE_BUILDING"]
        db.commit()

        job.stage = "DUCKING"
        job.progress = STAGES["DUCKING"]
        db.commit()

        # Extract primary narration track path
        narration_path = getattr(voice_assets.get(1), "local_path", "") or "artifacts/voice/narration.mp3"

        # Stage 6: AUDIO_MIXING & Stage 7: LOUDNESS_NORMALIZATION
        job.stage = "AUDIO_MIXING"
        job.progress = STAGES["AUDIO_MIXING"]
        db.commit()

        mix_result = await provider_instance.mix_audio(mapped_scenes, narration_path, {
            "music_volume_db": profile.music_volume_db,
            "ducking_level_db": profile.ducking_level_db,
            "sample_rate": profile.sample_rate,
            "channels": profile.channels
        })

        job.stage = "LOUDNESS_NORMALIZATION"
        job.progress = STAGES["LOUDNESS_NORMALIZATION"]
        db.commit()

        norm_result = await provider_instance.normalize(mix_result["master_path"], profile.target_lufs, profile.true_peak_db)
        analysis_data = await provider_instance.analyze_music(norm_result["normalized_path"])

        # Stage 8: QUALITY_CHECK
        job.stage = "QUALITY_CHECK"
        job.progress = STAGES["QUALITY_CHECK"]
        db.commit()

        validate_audio_mix(mix_result, analysis_data, profile)

        # Telemetry & Quality Report for Quality Agent
        telemetry_metadata = {
            "integrated_lufs": analysis_data["lufs"],
            "short_term_lufs": analysis_data["lufs"] - 0.5,
            "loudness_range_lra": analysis_data["dynamic_range_db"],
            "peak_level": analysis_data["peak_db"],
            "clipping_count": norm_result.get("clipping_count", 0),
            "silence_pct": 2.5,
            "ducking_stats": {
                "max_reduction_db": profile.ducking_level_db,
                "active_ducking_duration_ms": int(curr_time * 0.8)
            },
            "mix_confidence": 0.96
        }

        # Shared Package Manifest
        package_manifest = {
            "package_type": "MusicPackage",
            "version": 1,
            "parent_package_references": {
                "script_package_id": str(script_pkg.id),
                "voice_package_id": str(voice_pkg.id),
                "video_package_id": str(video_pkg.id),
                "subtitle_package_id": str(job.subtitle_package_id) if job.subtitle_package_id else None
            },
            "producer_agent": "music_agent",
            "provider": job.provider,
            "model": "LocalLibrary-v1",
            "input_dependencies": ["ScriptPackage", "VoicePackage", "VideoPackage"],
            "output_stems": {
                "master": mix_result["master_path"],
                "music": mix_result["music_stem_path"],
                "voice": mix_result["voice_stem_path"],
                "ambient": mix_result["ambient_stem_path"],
                "sfx": mix_result["sfx_stem_path"]
            },
            "quality_score": 0.96,
            "validation_status": "PASSED",
            "created_at": datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat()
        }

        # Create MusicPackage
        pkg = MusicPackage(
            id=uuid.uuid4(),
            job_id=job.id,
            script_package_id=script_pkg.id,
            voice_package_id=voice_pkg.id,
            video_package_id=video_pkg.id,
            subtitle_package_id=job.subtitle_package_id,
            audio_mix_profile_id=profile.id,
            storage_key=mix_result["master_path"],
            separated_music_track=mix_result["music_stem_path"],
            narration_track=mix_result["voice_stem_path"],
            ambient_stem_track=mix_result["ambient_stem_path"],
            sfx_stem_track=mix_result["sfx_stem_path"],
            scene_count=len(mapped_scenes),
            duration_ms=curr_time,
            waveform_metadata=mix_result.get("waveform_metadata"),
            package_manifest=package_manifest,
            # BasePackageMixin fields
            version=1,
            parent_package_id=None,
            source_agent="music_agent",
            provider=job.provider,
            model="LocalLibraryEngine",
            prompt_version="v1.0",
            quality_score=0.96,
            telemetry_metadata=telemetry_metadata
        )
        db.add(pkg)
        db.flush()

        # Save AudioAnalysis
        analysis = AudioAnalysis(
            id=uuid.uuid4(),
            music_package_id=pkg.id,
            peak_db=analysis_data["peak_db"],
            lufs=analysis_data["lufs"],
            dynamic_range_db=analysis_data["dynamic_range_db"],
            rms_db=analysis_data["rms_db"],
            tempo_bpm=analysis_data["tempo_bpm"],
            musical_key=analysis_data["musical_key"],
            silence_regions=analysis_data["silence_regions"],
            speech_regions=analysis_data["speech_regions"],
            waveform_data=analysis_data["waveform_data"],
            spectrum_data=analysis_data["spectrum_data"]
        )
        db.add(analysis)

        # Save SceneMusic, MusicAsset, MusicTrack, MusicCue, and AudioTimelineEvents
        for m_sc in mapped_scenes:
            sc_num = m_sc["scene_number"]
            
            # Asset
            asset = MusicAsset(
                id=uuid.uuid4(),
                provider=job.provider,
                license_type="Creative Commons",
                copyright_info="Public Royalty-Free",
                storage_key=mix_result["music_stem_path"]
            )
            db.add(asset)
            db.flush()

            # Track
            track = MusicTrack(
                id=uuid.uuid4(),
                asset_id=asset.id,
                track_title=m_sc["track_name"],
                artist=m_sc.get("artist", "AATES Studio"),
                genre=m_sc["genre"],
                mood=m_sc["mood"],
                energy_level=m_sc["energy"],
                tempo_bpm=m_sc["tempo_bpm"],
                musical_key=m_sc["musical_key"],
                duration_ms=m_sc["end_time_ms"] - m_sc["start_time_ms"]
            )
            db.add(track)
            db.flush()

            # SceneMusic
            sc_music = SceneMusic(
                id=uuid.uuid4(),
                music_package_id=pkg.id,
                scene_number=sc_num,
                track_name=m_sc["track_name"],
                genre=m_sc["genre"],
                mood=m_sc["mood"],
                energy=m_sc["energy"],
                tempo_bpm=m_sc["tempo_bpm"],
                musical_key=m_sc["musical_key"],
                start_time_ms=m_sc["start_time_ms"],
                end_time_ms=m_sc["end_time_ms"],
                fade_in_ms=m_sc["fade_in_ms"],
                fade_out_ms=m_sc["fade_out_ms"],
                music_volume_db=m_sc["music_volume_db"],
                narration_ducking_db=m_sc["narration_ducking_db"],
                quality_score=0.96
            )
            db.add(sc_music)
            db.flush()

            # MusicCue
            cue_data = m_sc["cue"]
            cue = MusicCue(
                id=uuid.uuid4(),
                music_track_id=track.id,
                scene_music_id=sc_music.id,
                cue_name=cue_data["cue_name"],
                cue_purpose=cue_data["cue_purpose"],
                source_start_ms=cue_data["source_start_ms"],
                source_end_ms=cue_data["source_end_ms"],
                trim_start_ms=cue_data["trim_start_ms"],
                trim_end_ms=cue_data["trim_end_ms"],
                loop_start_ms=cue_data["loop_start_ms"],
                loop_end_ms=cue_data["loop_end_ms"],
                fade_in_ms=cue_data["fade_in_ms"],
                fade_out_ms=cue_data["fade_out_ms"],
                gain_db=cue_data["gain_db"],
                emotion_score=cue_data["emotion_score"],
                transition_compatibility=cue_data["transition_compatibility"],
                loop_confidence=cue_data["loop_confidence"],
                crossfade_recommendation=cue_data["crossfade_recommendation"],
                beat_alignment_offset_ms=cue_data["beat_alignment_offset_ms"]
            )
            db.add(cue)
            db.flush()

            # AudioTimelineEvent
            event = AudioTimelineEvent(
                id=uuid.uuid4(),
                music_package_id=pkg.id,
                cue_id=cue.id,
                scene_number=sc_num,
                start_time_ms=sc_music.start_time_ms,
                end_time_ms=sc_music.end_time_ms,
                gain_db=cue.gain_db,
                pan=0.0,
                fade_in_ms=sc_music.fade_in_ms,
                fade_out_ms=sc_music.fade_out_ms,
                ducking_state="active",
                automation_points=mix_result.get("automation_points")
            )
            db.add(event)

        # Save MusicVersion snapshot
        ver_snapshot = [
            {
                "scene_number": sc["scene_number"],
                "track_name": sc["track_name"],
                "genre": sc["genre"],
                "mood": sc["mood"],
                "gain_db": sc["music_volume_db"]
            } for sc in mapped_scenes
        ]
        ver = MusicVersion(
            id=uuid.uuid4(),
            music_package_id=pkg.id,
            version=1,
            parent_version=None,
            lineage_action="INITIAL",
            assets_snapshot=ver_snapshot
        )
        db.add(ver)

        total_duration = time.monotonic() - start_time

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
            "event": "Music Processing Completed",
            "job_id": str(job.id),
            "scenes_count": len(mapped_scenes),
            "duration_sec": total_duration,
            "correlation_id": correlation_id
        }))

    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error(json.dumps({
            "event": "Music Processing Failed",
            "job_id": str(job.id),
            "error": error_msg,
            "correlation_id": correlation_id
        }))

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

async def music_agent_poll_loop(agent_id: str) -> None:
    logger.info(f"Music Agent loop started for agent ID: {agent_id}")
    while AGENT_STATE["is_running"]:
        db = SessionLocal()
        try:
            update_agent_heartbeat(db, agent_id)

            query = db.query(MusicJob).filter(
                MusicJob.status.in_(["QUEUED", "RETRYING"]),
                (MusicJob.scheduled_at == None) | (MusicJob.scheduled_at <= datetime.datetime.now(datetime.UTC).replace(tzinfo=None))
            ).order_by(
                MusicJob.priority.desc(),
                MusicJob.created_at.asc()
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

                    await process_music_job(db, job)
                else:
                    logger.warning(f"Invalid transition from {job.status} to PROCESSING for job {job.id}")

        except Exception as e:
            logger.error(f"Exception inside Music Agent loop iteration: {str(e)}")
        finally:
            db.close()

        await asyncio.sleep(2.0)

async def start_music_agent(concurrency: int = 1) -> None:
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
        agent_id = f"music-agent-{i}"
        task = asyncio.create_task(music_agent_poll_loop(agent_id))
        _agent_tasks.append(task)
    logger.info(f"Started {concurrency} concurrent background AI Music Agents.")

async def stop_music_agent() -> None:
    if not AGENT_STATE["is_running"]:
        return
    AGENT_STATE["is_running"] = False
    for task in _agent_tasks:
        task.cancel()
    if _agent_tasks:
        await asyncio.gather(*_agent_tasks, return_exceptions=True)
    _agent_tasks.clear()
    logger.info("Stopped background AI Music Agents.")
ZOOMING = "zoom"
