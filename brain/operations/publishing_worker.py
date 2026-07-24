import os
import sys
import time
import json
import uuid
import logging
import asyncio
from datetime import UTC, datetime, timezone, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session
from core.database.session import SessionLocal
from core.database.models import PublishingJob, OperationsTimeline, WorkerHeartbeat
from brain.operations.queue import _PROVIDER_REGISTRY, _log_timeline_event
import httpx

logger = logging.getLogger("aros.publishing.worker")

# Global worker state tracker
WORKER_STATE = {
    "is_running": False,
    "started_at": None,
    "jobs_processed": 0,
    "jobs_succeeded": 0,
    "jobs_failed": 0,
    "jobs_retried": 0,
    "total_publish_time_sec": 0.0
}

_worker_tasks = []
_shutdown_event = asyncio.Event()


def is_valid_transition(current: str, target: str) -> bool:
    """Enforce valid state transitions for publishing jobs."""
    transitions = {
        "QUEUED": ["PROCESSING", "CANCELLED"],
        "RETRYING": ["PROCESSING", "CANCELLED"],
        "PROCESSING": ["SUCCESS", "RETRYING", "FAILED", "CANCELLED"],
        "FAILED": ["QUEUED"],
        "CANCELLED": ["QUEUED"]
    }
    return target in transitions.get(current, [])


def update_heartbeat(db: Session, worker_id: str) -> None:
    """Record worker heartbeat in the database for liveness checks."""
    try:
        hb = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id == worker_id).first()
        if not hb:
            hb = WorkerHeartbeat(worker_id=worker_id, last_heartbeat_at=datetime.now(UTC).replace(tzinfo=None))
            db.add(hb)
        else:
            hb.last_heartbeat_at = datetime.now(UTC).replace(tzinfo=None)
            db.add(hb)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to update worker heartbeat for {worker_id}: {e}")


def is_transient_error(exc: Exception) -> bool:
    """Classify exception as transient (should retry) or permanent."""
    if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError, asyncio.TimeoutError)):
        return True
    
    if hasattr(exc, "status_code"):
        status_code = getattr(exc, "status_code")
        if status_code in (429, 500, 502, 503, 504):
            return True
        if status_code in (400, 401, 403, 404):
            return False

    exc_str = str(exc).lower()
    for code in ["429", "500", "502", "503", "504"]:
        if f"status {code}" in exc_str or f"error {code}" in exc_str or f"http {code}" in exc_str:
            return True

    return False


async def recover_orphaned_jobs(db: Session) -> int:
    """Reset jobs that were left in PROCESSING state (e.g., due to crash) back to QUEUED."""
    orphaned_jobs = db.query(PublishingJob).filter(
        PublishingJob.status == "PROCESSING"
    ).all()
    for job in orphaned_jobs:
        job.status = "QUEUED"
        job.started_at = None
        db.add(job)
    db.commit()
    return len(orphaned_jobs)


async def process_job(db: Session, job: PublishingJob):
    """Execute a single publishing job with detailed structured logging, events, and retries."""
    if not is_valid_transition(job.status, "PROCESSING"):
        logger.warning(f"Aborting job {job.id} execution: Invalid state transition from {job.status} to PROCESSING")
        return

    correlation_id = str(uuid.uuid4())
    logger.info(json.dumps({
        "event": "Upload Started",
        "job_id": str(job.id),
        "content_id": job.content_id,
        "provider": job.provider,
        "tenant_id": job.tenant_id,
        "correlation_id": correlation_id
    }))

    job.status = "PROCESSING"
    job.started_at = datetime.now(UTC).replace(tzinfo=None)
    job.attempts += 1
    db.add(job)
    db.commit()

    _log_timeline_event(db, "job_started", {
        "job_id": str(job.id),
        "content_id": job.content_id,
        "provider": job.provider,
        "attempts": job.attempts
    })

    provider_instance = _PROVIDER_REGISTRY.get(job.provider)
    if not provider_instance:
        if is_valid_transition(job.status, "FAILED"):
            job.status = "FAILED"
            job.failed_at = datetime.now(UTC).replace(tzinfo=None)
            job.error_code = "PROVIDER_NOT_FOUND"
            job.error_message = f"Publishing provider '{job.provider}' not registered."
            db.add(job)
            db.commit()

        _log_timeline_event(db, "job_failed", {
            "job_id": str(job.id),
            "content_id": job.content_id,
            "error": job.error_message
        })
        return

    payload = job.payload or {}
    master_reel_path = payload.get("master_reel_path", "")
    caption = payload.get("caption", "")

    start_time = time.monotonic()
    try:
        # Execute the provider upload
        res = await provider_instance.upload(
            master_reel_path=master_reel_path,
            caption=caption,
            metadata=payload
        )

        duration = time.monotonic() - start_time
        video_id = res.get("video_id") or res.get("external_post_id")

        logger.info(json.dumps({
            "event": "Upload Finished",
            "job_id": str(job.id),
            "content_id": job.content_id,
            "provider": job.provider,
            "tenant_id": job.tenant_id,
            "video_id": video_id,
            "duration_sec": duration,
            "correlation_id": correlation_id
        }))

        if is_valid_transition(job.status, "SUCCESS"):
            job.status = "SUCCESS"
            job.completed_at = datetime.now(UTC).replace(tzinfo=None)
            job.video_id = video_id
            job.provider_response = res
            job.error_code = None
            job.error_message = None
            db.add(job)
            db.commit()

        WORKER_STATE["jobs_succeeded"] += 1
        WORKER_STATE["total_publish_time_sec"] += duration
        WORKER_STATE["jobs_processed"] += 1

        _log_timeline_event(db, "job_completed", {
            "job_id": str(job.id),
            "content_id": job.content_id,
            "provider": job.provider,
            "video_id": video_id
        })

    except Exception as e:
        duration = time.monotonic() - start_time
        error_msg = str(e)
        is_trans = is_transient_error(e)

        logger.error(json.dumps({
            "event": "Job Error",
            "job_id": str(job.id),
            "content_id": job.content_id,
            "provider": job.provider,
            "tenant_id": job.tenant_id,
            "error": error_msg,
            "is_transient": is_trans,
            "duration_sec": duration,
            "correlation_id": correlation_id
        }))

        if is_trans and job.attempts < job.max_attempts:
            backoff_intervals = [30, 60, 120, 300]
            backoff_idx = min(job.attempts - 1, len(backoff_intervals) - 1)
            backoff = backoff_intervals[backoff_idx]

            if is_valid_transition(job.status, "RETRYING"):
                job.status = "RETRYING"
                job.scheduled_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=backoff)
                job.error_code = "TRANSIENT_ERROR"
                job.error_message = error_msg
                db.add(job)
                db.commit()

            WORKER_STATE["jobs_retried"] += 1

            _log_timeline_event(db, "job_retried", {
                "job_id": str(job.id),
                "content_id": job.content_id,
                "attempts": job.attempts,
                "next_retry_in_sec": backoff,
                "error": error_msg
            })
        else:
            if is_valid_transition(job.status, "FAILED"):
                job.status = "FAILED"
                job.failed_at = datetime.now(UTC).replace(tzinfo=None)
                job.error_code = "PERMANENT_ERROR" if not is_trans else "MAX_ATTEMPTS_EXCEEDED"
                job.error_message = error_msg
                db.add(job)
                db.commit()

            WORKER_STATE["jobs_failed"] += 1
            WORKER_STATE["jobs_processed"] += 1

            _log_timeline_event(db, "job_failed", {
                "job_id": str(job.id),
                "content_id": job.content_id,
                "attempts": job.attempts,
                "error": error_msg
            })


async def worker_poll_loop(worker_id: str, shutdown_event: asyncio.Event):
    """Loop polling the database for pending or retryable jobs."""
    try:
        db = SessionLocal()
        recovered = await recover_orphaned_jobs(db)
        if recovered > 0:
            logger.info(f"Orphaned recovery: Re-queued {recovered} stuck jobs.")
        update_heartbeat(db, worker_id)
        db.close()
    except Exception as e:
        logger.error(f"Orphaned recovery exception: {e}")

    while not shutdown_event.is_set():
        try:
            db = SessionLocal()
            update_heartbeat(db, worker_id)

            now = datetime.now(UTC).replace(tzinfo=None)

            # FIFO + Priority + Scheduled query
            query = db.query(PublishingJob).filter(
                PublishingJob.status.in_(["QUEUED", "RETRYING"]),
                (PublishingJob.scheduled_at == None) | (PublishingJob.scheduled_at <= now)
            ).order_by(
                PublishingJob.priority.desc(),
                PublishingJob.scheduled_at.asc(),
                PublishingJob.created_at.asc()
            )

            # Skip Locked for Concurrent worker scaling
            if db.bind.dialect.name == "postgresql":
                query = query.with_for_update(skip_locked=True)
            else:
                query = query.with_for_update()

            job = query.first()

            if job:
                # Lock job atomically in database
                if is_valid_transition(job.status, "PROCESSING"):
                    job.status = "PROCESSING"
                    db.add(job)
                    db.commit()

                    # Process the job
                    await process_job(db, job)
                else:
                    logger.warning(f"Worker skipping job {job.id}: Invalid transition from {job.status} to PROCESSING")
            else:
                # Poll interval
                await asyncio.sleep(2.0)

            db.close()
        except Exception as loop_err:
            logger.error(f"Exception inside worker loop iteration: {loop_err}", exc_info=True)
            await asyncio.sleep(5.0)


async def start_worker(num_workers: int = 2):
    """Initialize and run concurrent worker loops."""
    global _worker_tasks, _shutdown_event
    if _worker_tasks:
        logger.warning("Publishing workers are already active.")
        return

    _shutdown_event.clear()
    WORKER_STATE["is_running"] = True
    WORKER_STATE["started_at"] = datetime.now(UTC).replace(tzinfo=None)

    for i in range(num_workers):
        worker_id = f"worker-{i}"
        task = asyncio.create_task(worker_poll_loop(worker_id, _shutdown_event))
        _worker_tasks.append(task)
    logger.info(f"Started {num_workers} concurrent background publishing workers.")


async def stop_worker():
    """Trigger graceful worker shutdown and wait for current processes to finish."""
    global _worker_tasks, _shutdown_event
    if not _worker_tasks:
        return

    logger.info("Gracefully shutting down background publishing workers...")
    _shutdown_event.set()
    await asyncio.gather(*_worker_tasks, return_exceptions=True)
    _worker_tasks.clear()
    WORKER_STATE["is_running"] = False
    logger.info("All publishing workers shutdown successfully.")
