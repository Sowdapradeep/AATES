import asyncio
import datetime
import json
import logging
import time
import uuid
from typing import Any

from sqlalchemy.orm import Session

from core.database.session import SessionLocal
from core.database.models import (
    LearningJob,
    LearningDataset,
    LearningPackage,
    PerformanceSnapshot,
    LearningSignal,
    LearningRecommendation,
    ExperimentResult,
    LearningVersion,
    WorkerHeartbeat
)
from providers.analytics.collectors import analytics_collector
from providers.analytics.engine import analytics_engine
from providers.analytics.registry import analytics_registry

logger = logging.getLogger("learning_agent")

STAGES = {
    "COLLECTING": 0.15,
    "NORMALIZING": 0.30,
    "CORRELATING": 0.45,
    "PATTERN_DISCOVERY": 0.60,
    "EXPERIMENT_ANALYSIS": 0.75,
    "RECOMMENDATION_GENERATION": 0.88,
    "LEARNING_UPDATE": 0.95,
    "COMPLETED": 1.0,
    "FAILED": 1.0
}

_TRANSITIONS = {
    "QUEUED": {"PROCESSING", "CANCELLED"},
    "PROCESSING": {"SUCCESS", "FAILED", "CANCELLED"},
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
        orphans = db.query(LearningJob).filter(LearningJob.status == "PROCESSING").all()
        for job in orphans:
            logger.info(f"Resetting orphaned learning job {job.id} back to QUEUED.")
            job.status = "QUEUED"
            job.stage = "COLLECTING"
            job.progress = 0.0
            job.attempts += 1
            if job.attempts >= job.max_attempts:
                job.status = "FAILED"
                job.failed_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
                job.error_code = "ORPHANED_LIMIT"
                job.error_message = "Job orphaned repeatedly."
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Orphaned recovery failed: {str(e)}")

async def process_learning_job(db: Session, job: LearningJob) -> None:
    correlation_id = str(uuid.uuid4())
    logger.info(json.dumps({
        "event": "Learning Analysis Started",
        "job_id": str(job.id),
        "target_platform": job.target_platform,
        "mode": job.learning_mode,
        "correlation_id": correlation_id
    }))

    start_time = time.monotonic()
    job_id = job.id

    try:
        # Stage 1: COLLECTING
        job.stage = "COLLECTING"
        job.progress = STAGES["COLLECTING"]
        db.commit()

        feature_vectors = analytics_collector.collect_feature_dataset(
            db=db,
            target_platform=job.target_platform,
            learning_window_days=job.learning_window_days
        )
        job.dataset_size = len(feature_vectors)
        db.commit()

        # Stage 2: NORMALIZING
        job.stage = "NORMALIZING"
        job.progress = STAGES["NORMALIZING"]
        db.commit()

        dataset_snapshot = [v.model_dump() for v in feature_vectors]

        dataset = LearningDataset(
            id=uuid.uuid4(),
            job_id=job.id,
            dataset_name=f"AATES Dataset {job.target_platform.upper()} ({job.learning_mode})",
            sample_count=len(feature_vectors),
            start_date=datetime.datetime.now(datetime.UTC).replace(tzinfo=None) - datetime.timedelta(days=job.learning_window_days),
            end_date=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
            feature_vectors_snapshot=dataset_snapshot
        )
        db.add(dataset)
        db.flush()

        # Stage 3: CORRELATING & Stage 4: PATTERN_DISCOVERY
        job.stage = "CORRELATING"
        job.progress = STAGES["CORRELATING"]
        db.commit()

        job.stage = "PATTERN_DISCOVERY"
        job.progress = STAGES["PATTERN_DISCOVERY"]
        db.commit()

        # Stage 5: EXPERIMENT_ANALYSIS & Stage 6: RECOMMENDATION_GENERATION
        job.stage = "EXPERIMENT_ANALYSIS"
        job.progress = STAGES["EXPERIMENT_ANALYSIS"]
        db.commit()

        job.stage = "RECOMMENDATION_GENERATION"
        job.progress = STAGES["RECOMMENDATION_GENERATION"]
        db.commit()

        provider = analytics_registry.get_provider("default")
        eval_result = await provider.evaluate_learning(feature_vectors, job.target_platform)

        # Telemetry Metadata
        telemetry_metadata = {
            "collection_metrics": {"dataset_size": len(feature_vectors), "window_days": job.learning_window_days},
            "feature_extraction_metrics": {"features_extracted": 10, "normalization": "min_max"},
            "correlation_metrics": {"signals_discovered": len(eval_result["signals"])},
            "recommendation_metrics": {"recommendations_generated": len(eval_result["recommendations"])},
            "confidence_metrics": {"overall_confidence": eval_result["learning_confidence"]},
            "dataset_metrics": {"mode": job.learning_mode, "platform": job.target_platform}
        }

        # Shared Package Manifest
        package_manifest = {
            "package_type": "LearningPackage",
            "version": 1,
            "producer_agent": "learning_agent",
            "provider": "analytics_engine",
            "target_platform": job.target_platform,
            "learning_confidence": eval_result["learning_confidence"],
            "model_version": "v1.0",
            "signals_count": len(eval_result["signals"]),
            "recommendations_count": len(eval_result["recommendations"]),
            "created_at": datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat()
        }

        # Create LearningPackage
        learning_pkg = LearningPackage(
            id=uuid.uuid4(),
            job_id=job.id,
            dataset_id=dataset.id,
            target_platform=job.target_platform,
            learning_confidence=eval_result["learning_confidence"],
            model_version="v1.0",
            feature_importance_snapshot=eval_result["feature_importance"],
            package_manifest=package_manifest,
            # BasePackageMixin fields
            version=1,
            parent_package_id=None,
            source_agent="learning_agent",
            provider="analytics_engine",
            model="AATES-LearningEngine-v1.0",
            prompt_version="v1.0",
            quality_score=eval_result["learning_confidence"],
            telemetry_metadata=telemetry_metadata
        )
        db.add(learning_pkg)
        db.flush()

        # Create PerformanceSnapshot
        ps_data = eval_result["performance_snapshot"]
        perf = PerformanceSnapshot(
            id=uuid.uuid4(),
            learning_package_id=learning_pkg.id,
            platform=ps_data["platform"],
            window_days=ps_data["window_days"],
            total_publications=ps_data["total_publications"],
            total_views=ps_data["total_views"],
            total_reach=ps_data["total_reach"],
            avg_ctr=ps_data["avg_ctr"],
            avg_engagement_rate=ps_data["avg_engagement_rate"],
            avg_watch_time_ms=ps_data["avg_watch_time_ms"]
        )
        db.add(perf)

        # Create LearningSignals
        for sig_data in eval_result["signals"]:
            sig = LearningSignal(
                id=uuid.uuid4(),
                learning_package_id=learning_pkg.id,
                signal_key=sig_data["signal_key"],
                title=sig_data["title"],
                category=sig_data["category"],
                correlation_coefficient=sig_data["correlation_coefficient"],
                confidence_score=sig_data["confidence_score"],
                platform=sig_data["platform"],
                applicable_agents=sig_data["applicable_agents"],
                causality_level=sig_data["causality_level"],
                evidence_data=sig_data["evidence_data"]
            )
            db.add(sig)

        # Create Recommendations
        for rec_data in eval_result["recommendations"]:
            rec = LearningRecommendation(
                id=uuid.uuid4(),
                learning_package_id=learning_pkg.id,
                target_agent=rec_data["target_agent"],
                category=rec_data["category"],
                priority=rec_data["priority"],
                confidence_score=rec_data["confidence_score"],
                expected_impact=rec_data["expected_impact"],
                suggested_action=rec_data["suggested_action"],
                action_payload=rec_data["action_payload"],
                evidence_data=rec_data["evidence_data"]
            )
            db.add(rec)

        # Create ExperimentResults
        for exp_data in eval_result["experiment_results"]:
            exp = ExperimentResult(
                id=uuid.uuid4(),
                learning_package_id=learning_pkg.id,
                experiment_id=exp_data["experiment_id"],
                experiment_type=exp_data["experiment_type"],
                winning_variant_id=exp_data["winning_variant_id"],
                confidence_score=exp_data["confidence_score"],
                metric_lift_percent=exp_data["metric_lift_percent"],
                insights_snapshot=exp_data["insights_snapshot"]
            )
            db.add(exp)

        # Save LearningVersion
        ver_snapshot = [
            {
                "learning_confidence": learning_pkg.learning_confidence,
                "signals_count": len(eval_result["signals"]),
                "recommendations_count": len(eval_result["recommendations"])
            }
        ]
        ver = LearningVersion(
            id=uuid.uuid4(),
            learning_package_id=learning_pkg.id,
            version=1,
            parent_version=None,
            lineage_action="INITIAL",
            assets_snapshot=ver_snapshot
        )
        db.add(ver)

        # Stage 7: LEARNING_UPDATE & COMPLETED
        job.stage = "LEARNING_UPDATE"
        job.progress = STAGES["LEARNING_UPDATE"]
        db.commit()

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
            "event": "Learning Analysis Completed",
            "job_id": str(job.id),
            "confidence": eval_result["learning_confidence"],
            "duration_sec": total_duration,
            "correlation_id": correlation_id
        }))

    except Exception as e:
        error_msg = str(e)
        target_plat = job.target_platform
        win_days = job.learning_window_days
        mode = job.learning_mode

        try:
            db.rollback()
        except Exception:
            pass

        logger.error(json.dumps({
            "event": "Learning Analysis Failed",
            "job_id": str(job_id),
            "error": error_msg,
            "correlation_id": correlation_id
        }))

        job = db.query(LearningJob).filter(LearningJob.id == job_id).first()
        if not job:
            job = LearningJob(
                id=job_id,
                target_platform=target_plat,
                learning_window_days=win_days,
                learning_mode=mode
            )

        job.attempts += 1
        job.status = "FAILED"
        job.stage = "FAILED"
        job.progress = STAGES["FAILED"]
        job.failed_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        job.error_code = "ANALYSIS_ERROR"
        job.error_message = error_msg

        db.add(job)
        db.commit()
        AGENT_STATE["jobs_failed"] += 1
        AGENT_STATE["jobs_processed"] += 1

async def learning_worker_poll_loop(worker_id: str) -> None:
    logger.info(f"Learning Agent worker loop started for worker ID: {worker_id}")
    while AGENT_STATE["is_running"]:
        db = SessionLocal()
        try:
            update_worker_heartbeat(db, worker_id)

            query = db.query(LearningJob).filter(
                LearningJob.status == "QUEUED"
            ).order_by(
                LearningJob.priority.desc(),
                LearningJob.created_at.asc()
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

                    await process_learning_job(db, job)
                else:
                    logger.warning(f"Invalid transition from {job.status} to PROCESSING for job {job.id}")

        except Exception as e:
            logger.error(f"Exception inside Learning Worker loop iteration: {str(e)}")
        finally:
            db.close()

        await asyncio.sleep(2.0)

async def start_learning_agent(concurrency: int = 1) -> None:
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
        w_id = f"learning-worker-{i}"
        task = asyncio.create_task(learning_worker_poll_loop(w_id))
        _worker_tasks.append(task)
    logger.info(f"Started {concurrency} concurrent background Learning Agent workers.")

async def stop_learning_agent() -> None:
    if not AGENT_STATE["is_running"]:
        return
    AGENT_STATE["is_running"] = False
    for task in _worker_tasks:
        task.cancel()
    if _worker_tasks:
        await asyncio.gather(*_worker_tasks, return_exceptions=True)
    _worker_tasks.clear()
    logger.info("Stopped background Learning Agent workers.")
ZOOMING = "zoom"
