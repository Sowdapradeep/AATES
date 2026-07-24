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
    InstagramPublishJob, 
    PublicationPackage, 
    InstagramPublication,
    InstagramMediaAsset,
    PublishingAttempt,
    InstagramInsightSnapshot,
    InstagramVersion,
    QualityPackage,
    ScriptPackage,
    VideoPackage,
    SubtitlePackage,
    MusicPackage,
    ThumbnailPackage,
    WorkerHeartbeat
)
from providers.publishing.instagram import InstagramPublishingProvider
from providers.publishing.platform_profile import platform_registry

logger = logging.getLogger("instagram_worker")

STAGES = {
    "VALIDATING": 0.1,
    "QUALITY_GATE": 0.2,
    "MEDIA_TRANSFORMATION": 0.35,
    "MEDIA_VALIDATION": 0.5,
    "UPLOAD": 0.65,
    "PUBLISH": 0.8,
    "STATUS_SYNC": 0.9,
    "INSIGHT_INITIALIZATION": 0.95,
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

_worker_tasks = []

def update_worker_heartbeat(db: Session, worker_id: str) -> None:
    try:
        hb = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id == worker_id).first()
        if not hb:
            hb = WorkerHeartbeat(worker_id=worker_id, last_heartbeat_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None))
            db.add(hb)
        else:
            hb.last_heartbeat_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Failed to update heartbeat for {worker_id}: {str(e)}")

def recover_orphaned_jobs(db: Session) -> None:
    try:
        orphans = db.query(InstagramPublishJob).filter(InstagramPublishJob.status == "PROCESSING").all()
        for job in orphans:
            logger.info(f"Resetting orphaned instagram publish job {job.id} back to QUEUED.")
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

async def process_instagram_job(db: Session, job: InstagramPublishJob) -> None:
    correlation_id = str(uuid.uuid4())
    logger.info(json.dumps({
        "event": "Instagram Publishing Started",
        "job_id": str(job.id),
        "quality_package_id": str(job.quality_package_id),
        "media_type": job.platform_media_type,
        "correlation_id": correlation_id
    }))

    start_time = time.monotonic()

    job_id = job.id
    try:
        # Stage 1: VALIDATING & Stage 2: QUALITY_GATE
        job.stage = "VALIDATING"
        job.progress = STAGES["VALIDATING"]
        db.commit()

        quality_pkg = db.query(QualityPackage).filter(QualityPackage.id == job.quality_package_id).first()
        if not quality_pkg:
            raise ValueError("QualityPackage not found.")

        job.stage = "QUALITY_GATE"
        job.progress = STAGES["QUALITY_GATE"]
        db.commit()

        # Quality Gate Enforcer
        if not quality_pkg.is_approved_for_publishing:
            raise ValueError(f"Quality Gate Rejected: QualityPackage {quality_pkg.id} is not approved for publishing (readiness score: {quality_pkg.production_readiness_score}).")

        script_pkg = db.query(ScriptPackage).filter(ScriptPackage.id == quality_pkg.script_package_id).first()
        video_pkg = db.query(VideoPackage).filter(VideoPackage.id == quality_pkg.video_package_id).first()
        subtitle_pkg = db.query(SubtitlePackage).filter(SubtitlePackage.id == quality_pkg.subtitle_package_id).first() if quality_pkg.subtitle_package_id else None

        provider = InstagramPublishingProvider()

        # Stage 3: MEDIA_TRANSFORMATION
        job.stage = "MEDIA_TRANSFORMATION"
        job.progress = STAGES["MEDIA_TRANSFORMATION"]
        db.commit()

        profile_id = f"instagram_{job.platform_media_type.lower()}"
        transform_res = await provider.transform_media(
            video_pkg.storage_key if video_pkg else "artifacts/videos/sample.mp4",
            profile_id
        )

        # Stage 4: MEDIA_VALIDATION
        job.stage = "MEDIA_VALIDATION"
        job.progress = STAGES["MEDIA_VALIDATION"]
        db.commit()

        val_res = await provider.validate_media(transform_res["transformed_media_path"], profile_id)
        caption_info = await provider.prepare_caption(script_pkg, subtitle_pkg)

        # Stage 5: UPLOAD
        job.stage = "UPLOAD"
        job.progress = STAGES["UPLOAD"]
        db.commit()

        upload_start = time.monotonic()
        upload_res = await provider.upload_media(val_res, caption_info)
        upload_latency = int((time.monotonic() - upload_start) * 1000)

        # Record PublishingAttempt for upload
        att1 = PublishingAttempt(
            id=uuid.uuid4(),
            job_id=job.id,
            attempt_number=job.attempts + 1,
            api_endpoint=upload_res["api_endpoint"],
            http_status_code=200,
            latency_ms=upload_latency,
            api_response=upload_res
        )
        db.add(att1)
        db.commit()

        # Stage 6: PUBLISH & Stage 7: STATUS_SYNC
        job.stage = "PUBLISH"
        job.progress = STAGES["PUBLISH"]
        db.commit()

        pub_start = time.monotonic()
        pub_res = await provider.publish(upload_res["container_id"])
        pub_latency = int((time.monotonic() - pub_start) * 1000)

        # Record PublishingAttempt for publish
        att2 = PublishingAttempt(
            id=uuid.uuid4(),
            job_id=job.id,
            attempt_number=job.attempts + 1,
            api_endpoint=f"https://graph.facebook.com/v19.0/17841400000000000/media_publish",
            http_status_code=200,
            latency_ms=pub_latency,
            api_response=pub_res
        )
        db.add(att2)
        db.commit()

        job.stage = "STATUS_SYNC"
        job.progress = STAGES["STATUS_SYNC"]
        db.commit()

        # Stage 8: INSIGHT_INITIALIZATION
        job.stage = "INSIGHT_INITIALIZATION"
        job.progress = STAGES["INSIGHT_INITIALIZATION"]
        db.commit()

        insight_data = await provider.fetch_insights(pub_res["instagram_media_id"])

        # Publishing Telemetry
        telemetry_metadata = {
            "upload_metrics": {"latency_ms": upload_latency, "container_id": upload_res["container_id"]},
            "api_latency": {"upload_ms": upload_latency, "publish_ms": pub_latency},
            "retry_metrics": {"attempts": job.attempts + 1},
            "validation_metrics": val_res,
            "platform_metrics": {"platform": "instagram", "media_type": job.platform_media_type},
            "engagement_metrics": insight_data
        }

        # Shared Package Manifest
        package_manifest = {
            "package_type": "PublicationPackage",
            "version": 1,
            "parent_package_references": {
                "quality_package_id": str(quality_pkg.id),
                "script_package_id": str(quality_pkg.script_package_id),
                "video_package_id": str(quality_pkg.video_package_id)
            },
            "producer_agent": "instagram_worker",
            "provider": job.provider,
            "platform": "instagram",
            "platform_profile_id": profile_id,
            "instagram_media_id": pub_res["instagram_media_id"],
            "permalink": pub_res["permalink"],
            "publishing_lifecycle_state": "Published",
            "validation_status": "PASSED",
            "created_at": datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat()
        }

        # Create PublicationPackage
        pub_pkg = PublicationPackage(
            id=uuid.uuid4(),
            job_id=job.id,
            quality_package_id=quality_pkg.id,
            publishing_lifecycle_state="Published",
            platform_name="instagram",
            platform_profile_id=profile_id,
            publication_result=pub_res,
            package_manifest=package_manifest,
            # BasePackageMixin fields
            version=1,
            parent_package_id=None,
            source_agent="instagram_worker",
            provider=job.provider,
            model="InstagramGraphAPI-v19.0",
            prompt_version="v1.0",
            quality_score=quality_pkg.production_readiness_score,
            telemetry_metadata=telemetry_metadata
        )
        db.add(pub_pkg)
        db.flush()

        # Create InstagramPublication
        publication = InstagramPublication(
            id=uuid.uuid4(),
            publication_package_id=pub_pkg.id,
            instagram_media_id=pub_res["instagram_media_id"],
            container_id=upload_res["container_id"],
            permalink=pub_res["permalink"],
            caption=caption_info["caption"],
            hashtags=caption_info["hashtags"],
            alt_text=caption_info["alt_text"],
            published_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
            visibility="PUBLIC",
            publishing_result=pub_res
        )
        db.add(publication)
        db.flush()

        # Create InstagramMediaAsset
        media_asset = InstagramMediaAsset(
            id=uuid.uuid4(),
            publication_id=publication.id,
            video_asset_key=transform_res["transformed_media_path"],
            cover_image_key=transform_res["cover_image_path"],
            aspect_ratio=transform_res["aspect_ratio"],
            resolution=transform_res["resolution"],
            duration_ms=45000,
            codec="h264",
            bitrate=5000000,
            thumbnail_url=pub_res["permalink"]
        )
        db.add(media_asset)

        # Create InstagramInsightSnapshot
        snapshot = InstagramInsightSnapshot(
            id=uuid.uuid4(),
            publication_id=publication.id,
            captured_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
            views=insight_data["views"],
            reach=insight_data["reach"],
            impressions=insight_data["impressions"],
            likes=insight_data["likes"],
            comments=insight_data["comments"],
            shares=insight_data["shares"],
            saves=insight_data["saves"],
            profile_visits=insight_data["profile_visits"],
            follows_attributed=insight_data["follows_attributed"],
            watch_time_ms=insight_data["watch_time_ms"],
            engagement_rate=insight_data["engagement_rate"]
        )
        db.add(snapshot)

        # Save InstagramVersion
        ver_snapshot = [
            {
                "instagram_media_id": publication.instagram_media_id,
                "permalink": publication.permalink,
                "media_type": job.platform_media_type,
                "views": snapshot.views,
                "likes": snapshot.likes
            }
        ]
        ver = InstagramVersion(
            id=uuid.uuid4(),
            publication_package_id=pub_pkg.id,
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
            "event": "Instagram Publishing Completed",
            "job_id": str(job.id),
            "media_id": pub_res["instagram_media_id"],
            "permalink": pub_res["permalink"],
            "duration_sec": total_duration,
            "correlation_id": correlation_id
        }))

    except Exception as e:
        error_msg = str(e)
        quality_pkg_id = job.quality_package_id
        media_type = job.platform_media_type
        prov = job.provider
        attempts_count = job.attempts
        max_att = job.max_attempts

        try:
            db.rollback()
        except Exception:
            pass

        logger.error(json.dumps({
            "event": "Instagram Publishing Failed",
            "job_id": str(job_id),
            "error": error_msg,
            "correlation_id": correlation_id
        }))

        job = db.query(InstagramPublishJob).filter(InstagramPublishJob.id == job_id).first()
        if not job:
            job = InstagramPublishJob(
                id=job_id,
                quality_package_id=quality_pkg_id,
                platform_media_type=media_type,
                provider=prov,
                attempts=attempts_count,
                max_attempts=max_att
            )

        job.attempts += 1
        if is_transient_error(error_msg) and job.attempts < job.max_attempts:
            delay = get_backoff_delay(job.attempts)
            job.status = "RETRYING"
            job.scheduled_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None) + datetime.timedelta(seconds=delay)
            job.error_code = "TRANSIENT_ERROR"
            job.error_message = error_msg
        else:
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

async def instagram_worker_poll_loop(worker_id: str) -> None:
    logger.info(f"Instagram Publishing Worker loop started for worker ID: {worker_id}")
    while AGENT_STATE["is_running"]:
        db = SessionLocal()
        try:
            update_worker_heartbeat(db, worker_id)

            query = db.query(InstagramPublishJob).filter(
                InstagramPublishJob.status.in_(["QUEUED", "RETRYING"]),
                (InstagramPublishJob.scheduled_at == None) | (InstagramPublishJob.scheduled_at <= datetime.datetime.now(datetime.UTC).replace(tzinfo=None))
            ).order_by(
                InstagramPublishJob.priority.desc(),
                InstagramPublishJob.created_at.asc()
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

                    await process_instagram_job(db, job)
                else:
                    logger.warning(f"Invalid transition from {job.status} to PROCESSING for job {job.id}")

        except Exception as e:
            logger.error(f"Exception inside Instagram Worker loop iteration: {str(e)}")
        finally:
            db.close()

        await asyncio.sleep(2.0)

async def start_instagram_worker(concurrency: int = 1) -> None:
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
        w_id = f"instagram-worker-{i}"
        task = asyncio.create_task(instagram_worker_poll_loop(w_id))
        _worker_tasks.append(task)
    logger.info(f"Started {concurrency} concurrent background Instagram Publishing Workers.")

async def stop_instagram_worker() -> None:
    if not AGENT_STATE["is_running"]:
        return
    AGENT_STATE["is_running"] = False
    for task in _worker_tasks:
        task.cancel()
    if _worker_tasks:
        await asyncio.gather(*_worker_tasks, return_exceptions=True)
    _worker_tasks.clear()
    logger.info("Stopped background Instagram Publishing Workers.")
ZOOMING = "zoom"
