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
    QualityJob, 
    QualityPackage, 
    QualityCheck,
    QualityIssue,
    QualityEvidence,
    QualityRecommendation,
    RemediationTask,
    QualityPolicy,
    QualityRule,
    QualityVersion,
    ScriptPackage,
    ImagePackage,
    VoicePackage, 
    VideoPackage,
    SubtitlePackage,
    MusicPackage,
    ThumbnailPackage,
    WorkerHeartbeat
)
from providers.quality.registry import quality_registry

logger = logging.getLogger("quality_agent")

STAGES = {
    "VALIDATING": 0.1,
    "GRAPH_CONSTRUCTION": 0.2,
    "TELEMETRY_AGGREGATION": 0.35,
    "POLICY_EVALUATION": 0.5,
    "CROSS_PACKAGE_CHECK": 0.65,
    "ISSUE_CLASSIFICATION": 0.8,
    "SCORING": 0.9,
    "REPORT_GENERATION": 0.95,
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
        orphans = db.query(QualityJob).filter(QualityJob.status == "PROCESSING").all()
        for job in orphans:
            logger.info(f"Resetting orphaned quality job {job.id} back to QUEUED.")
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

def get_or_create_default_policy(db: Session, platform: str) -> QualityPolicy:
    policy = db.query(QualityPolicy).filter(QualityPolicy.platform == platform).first()
    if not policy:
        policy = QualityPolicy(
            id=uuid.uuid4(),
            name=f"{platform.capitalize()} Production Policy",
            platform=platform,
            policy_version="v1.0",
            rule_set_version="v1.0",
            description=f"Standard governance quality policy for {platform} publishing.",
            min_readiness_score=0.85,
            allow_critical_issues=False,
            dimension_weights={
                "Content": 0.15,
                "Media": 0.20,
                "Accessibility": 0.15,
                "Brand": 0.15,
                "Metadata": 0.15,
                "Technical": 0.10,
                "Publishing": 0.10
            }
        )
        db.add(policy)
        db.flush()

        # Add default rules
        rules = [
            QualityRule(id=uuid.uuid4(), quality_policy_id=policy.id, rule_name="Narration Completeness", dimension="Content", target_package="VoicePackage", metric_name="voice_duration_ms", operator=">", threshold_value="0", severity="CRITICAL"),
            QualityRule(id=uuid.uuid4(), quality_policy_id=policy.id, rule_name="Audio LUFS Target", dimension="Media", target_package="MusicPackage", metric_name="lufs", operator="==", threshold_value="-14.0", severity="MAJOR"),
            QualityRule(id=uuid.uuid4(), quality_policy_id=policy.id, rule_name="WCAG Thumbnail Contrast", dimension="Accessibility", target_package="ThumbnailPackage", metric_name="contrast_ratio", operator=">=", threshold_value="4.5", severity="MAJOR")
        ]
        db.add_all(rules)
        db.commit()
    return policy

async def process_quality_job(db: Session, job: QualityJob) -> None:
    correlation_id = str(uuid.uuid4())
    logger.info(json.dumps({
        "event": "Quality Evaluation Processing Started",
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
        image_pkg = db.query(ImagePackage).filter(ImagePackage.id == job.image_package_id).first()
        voice_pkg = db.query(VoicePackage).filter(VoicePackage.id == job.voice_package_id).first()
        video_pkg = db.query(VideoPackage).filter(VideoPackage.id == job.video_package_id).first()
        subtitle_pkg = db.query(SubtitlePackage).filter(SubtitlePackage.id == job.subtitle_package_id).first() if job.subtitle_package_id else None
        music_pkg = db.query(MusicPackage).filter(MusicPackage.id == job.music_package_id).first() if job.music_package_id else None
        thumbnail_pkg = db.query(ThumbnailPackage).filter(ThumbnailPackage.id == job.thumbnail_package_id).first() if job.thumbnail_package_id else None

        if not script_pkg or not image_pkg or not voice_pkg or not video_pkg:
            raise ValueError("Input dependency graph incomplete: ScriptPackage, ImagePackage, VoicePackage, and VideoPackage are required.")

        # Stage 2: GRAPH_CONSTRUCTION & Stage 3: TELEMETRY_AGGREGATION
        job.stage = "GRAPH_CONSTRUCTION"
        job.progress = STAGES["GRAPH_CONSTRUCTION"]
        db.commit()

        packages_graph = {
            "script": script_pkg,
            "image": image_pkg,
            "voice": voice_pkg,
            "video": video_pkg,
            "subtitle": subtitle_pkg,
            "music": music_pkg,
            "thumbnail": thumbnail_pkg
        }

        job.stage = "TELEMETRY_AGGREGATION"
        job.progress = STAGES["TELEMETRY_AGGREGATION"]
        db.commit()

        # Stage 4: POLICY_EVALUATION & Stage 5: CROSS_PACKAGE_CHECK
        job.stage = "POLICY_EVALUATION"
        job.progress = STAGES["POLICY_EVALUATION"]
        db.commit()

        policy = job.policy or get_or_create_default_policy(db, video_pkg.platform)
        job.quality_policy_id = policy.id
        db.commit()

        provider_instance = quality_registry.get_provider(job.provider) or quality_registry.get_provider("policy_engine")

        job.stage = "CROSS_PACKAGE_CHECK"
        job.progress = STAGES["CROSS_PACKAGE_CHECK"]
        db.commit()

        eval_res = await provider_instance.evaluate(packages_graph, policy)

        # Stage 6: ISSUE_CLASSIFICATION & Stage 7: SCORING
        job.stage = "ISSUE_CLASSIFICATION"
        job.progress = STAGES["ISSUE_CLASSIFICATION"]
        db.commit()

        job.stage = "SCORING"
        job.progress = STAGES["SCORING"]
        db.commit()

        # Shared Package Manifest
        package_manifest = {
            "package_type": "QualityPackage",
            "version": 1,
            "parent_package_references": {
                "script_package_id": str(script_pkg.id),
                "image_package_id": str(image_pkg.id),
                "voice_package_id": str(voice_pkg.id),
                "video_package_id": str(video_pkg.id),
                "subtitle_package_id": str(job.subtitle_package_id) if job.subtitle_package_id else None,
                "music_package_id": str(job.music_package_id) if job.music_package_id else None,
                "thumbnail_package_id": str(job.thumbnail_package_id) if job.thumbnail_package_id else None
            },
            "producer_agent": "quality_agent",
            "provider": job.provider,
            "policy_version": policy.policy_version,
            "rule_set_version": policy.rule_set_version,
            "production_readiness_score": eval_res["production_readiness_score"],
            "is_approved_for_publishing": eval_res["is_approved_for_publishing"],
            "publishing_lifecycle_state": eval_res["publishing_lifecycle_state"],
            "validation_status": "PASSED" if eval_res["is_approved_for_publishing"] else "FLAGGED",
            "created_at": datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat()
        }

        # Create QualityPackage
        pkg = QualityPackage(
            id=uuid.uuid4(),
            job_id=job.id,
            script_package_id=script_pkg.id,
            image_package_id=image_pkg.id,
            voice_package_id=voice_pkg.id,
            video_package_id=video_pkg.id,
            subtitle_package_id=job.subtitle_package_id,
            music_package_id=job.music_package_id,
            thumbnail_package_id=job.thumbnail_package_id,
            quality_policy_id=policy.id,
            publishing_lifecycle_state=eval_res["publishing_lifecycle_state"],
            production_readiness_score=eval_res["production_readiness_score"],
            is_approved_for_publishing=eval_res["is_approved_for_publishing"],
            critical_issue_count=eval_res["critical_issue_count"],
            major_issue_count=eval_res["major_issue_count"],
            minor_issue_count=eval_res["minor_issue_count"],
            dimension_scores=eval_res["dimension_scores"],
            aggregated_telemetry=eval_res["aggregated_telemetry"],
            package_manifest=package_manifest,
            # BasePackageMixin fields
            version=1,
            parent_package_id=None,
            source_agent="quality_agent",
            provider=job.provider,
            model="LocalPolicyEngine",
            prompt_version="v1.0",
            quality_score=eval_res["production_readiness_score"],
            telemetry_metadata=eval_res["aggregated_telemetry"]
        )
        db.add(pkg)
        db.flush()

        # Save QualityChecks
        check_id_map = {}
        for chk_data in eval_res["checks"]:
            chk = QualityCheck(
                id=uuid.uuid4(),
                quality_package_id=pkg.id,
                package_type=chk_data["package_type"],
                dimension=chk_data["dimension"],
                check_name=chk_data["check_name"],
                status=chk_data["status"],
                evaluated_value=str(chk_data["evaluated_value"]),
                target_threshold=str(chk_data["target_threshold"]),
                execution_ms=chk_data["execution_ms"]
            )
            db.add(chk)
            db.flush()
            check_id_map[chk_data["check_name"]] = chk.id

        # Save QualityIssues, Evidence, Recommendations, & Remediation Tasks
        for iss_data in eval_res["issues"]:
            chk_id = check_id_map.get(iss_data.get("check_name"))
            iss = QualityIssue(
                id=uuid.uuid4(),
                quality_package_id=pkg.id,
                quality_check_id=chk_id,
                issue_code=iss_data["issue_code"],
                category=iss_data["category"],
                severity=iss_data["severity"],
                description=iss_data["description"],
                impacted_component=iss_data["impacted_component"],
                remediation_suggestion=iss_data.get("remediation_suggestion")
            )
            db.add(iss)
            db.flush()

            # Save Evidence
            ev_data = iss_data.get("evidence")
            if ev_data:
                ev = QualityEvidence(
                    id=uuid.uuid4(),
                    quality_issue_id=iss.id,
                    source_package=ev_data["source_package"],
                    artifact_path=ev_data.get("artifact_path"),
                    timestamp_ms=ev_data.get("timestamp_ms"),
                    metric_name=ev_data["metric_name"],
                    observed_value=str(ev_data["observed_value"]),
                    expected_value=str(ev_data["expected_value"]),
                    snapshot_data=ev_data.get("snapshot_data")
                )
                db.add(ev)

            # Save Recommendation
            rec_data = iss_data.get("recommendation")
            if rec_data:
                rec = QualityRecommendation(
                    id=uuid.uuid4(),
                    quality_issue_id=iss.id,
                    recommendation_type=rec_data["recommendation_type"],
                    priority=rec_data["priority"],
                    target_agent=rec_data["target_agent"],
                    auto_fix_available=rec_data.get("auto_fix_available", True),
                    estimated_impact=rec_data.get("estimated_impact"),
                    action_payload=rec_data.get("action_payload")
                )
                db.add(rec)

                # Save Remediation Task for Auto-Fix
                rem_task = RemediationTask(
                    id=uuid.uuid4(),
                    quality_package_id=pkg.id,
                    target_agent=rec_data["target_agent"],
                    status="PENDING",
                    action_type=rec_data["recommendation_type"],
                    payload=rec_data.get("action_payload")
                )
                db.add(rem_task)

        # Stage 8: REPORT_GENERATION
        job.stage = "REPORT_GENERATION"
        job.progress = STAGES["REPORT_GENERATION"]
        db.commit()

        # Save QualityVersion snapshot
        ver_snapshot = [
            {
                "readiness_score": pkg.production_readiness_score,
                "is_approved": pkg.is_approved_for_publishing,
                "lifecycle_state": pkg.publishing_lifecycle_state,
                "critical_issues": pkg.critical_issue_count,
                "major_issues": pkg.major_issue_count
            }
        ]
        ver = QualityVersion(
            id=uuid.uuid4(),
            quality_package_id=pkg.id,
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
            "event": "Quality Evaluation Completed",
            "job_id": str(job.id),
            "readiness_score": eval_res["production_readiness_score"],
            "is_approved": eval_res["is_approved_for_publishing"],
            "duration_sec": total_duration,
            "correlation_id": correlation_id
        }))

    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error(json.dumps({
            "event": "Quality Evaluation Failed",
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

async def quality_agent_poll_loop(agent_id: str) -> None:
    logger.info(f"Quality Agent loop started for agent ID: {agent_id}")
    while AGENT_STATE["is_running"]:
        db = SessionLocal()
        try:
            update_agent_heartbeat(db, agent_id)

            query = db.query(QualityJob).filter(
                QualityJob.status.in_(["QUEUED", "RETRYING"]),
                (QualityJob.scheduled_at == None) | (QualityJob.scheduled_at <= datetime.datetime.now(datetime.UTC).replace(tzinfo=None))
            ).order_by(
                QualityJob.priority.desc(),
                QualityJob.created_at.asc()
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

                    await process_quality_job(db, job)
                else:
                    logger.warning(f"Invalid transition from {job.status} to PROCESSING for job {job.id}")

        except Exception as e:
            logger.error(f"Exception inside Quality Agent loop iteration: {str(e)}")
        finally:
            db.close()

        await asyncio.sleep(2.0)

async def start_quality_agent(concurrency: int = 1) -> None:
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
        agent_id = f"quality-agent-{i}"
        task = asyncio.create_task(quality_agent_poll_loop(agent_id))
        _agent_tasks.append(task)
    logger.info(f"Started {concurrency} concurrent background AI Quality Agents.")

async def stop_quality_agent() -> None:
    if not AGENT_STATE["is_running"]:
        return
    AGENT_STATE["is_running"] = False
    for task in _agent_tasks:
        task.cancel()
    if _agent_tasks:
        await asyncio.gather(*_agent_tasks, return_exceptions=True)
    _agent_tasks.clear()
    logger.info("Stopped background AI Quality Agents.")
ZOOMING = "zoom"
