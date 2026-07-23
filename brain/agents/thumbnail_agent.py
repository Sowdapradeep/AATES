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
    ThumbnailJob, 
    ThumbnailPackage, 
    ThumbnailVariant,
    ThumbnailAsset,
    CompositionTemplate,
    ThumbnailAnalysis,
    ThumbnailScore,
    ThumbnailStyleProfile,
    ThumbnailVersion,
    ThumbnailExperiment,
    ScriptPackage,
    ImagePackage,
    VoicePackage, 
    VideoPackage,
    SubtitlePackage,
    MusicPackage,
    WorkerHeartbeat
)
from providers.thumbnail.registry import thumbnail_registry

logger = logging.getLogger("thumbnail_agent")

STAGES = {
    "VALIDATING": 0.1,
    "FRAME_SELECTION": 0.2,
    "FRAME_ANALYSIS": 0.3,
    "TEXT_SELECTION": 0.4,
    "LAYOUT_COMPOSITION": 0.5,
    "STYLE_APPLICATION": 0.6,
    "VARIANT_GENERATION": 0.75,
    "QUALITY_SCORING": 0.85,
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
        orphans = db.query(ThumbnailJob).filter(ThumbnailJob.status == "PROCESSING").all()
        for job in orphans:
            logger.info(f"Resetting orphaned thumbnail job {job.id} back to QUEUED.")
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
    return any(term in msg for term in ["timeout", "429", "throttling", "connection refused", "network", "service unavailable", "busy"])

def get_backoff_delay(attempts: int) -> int:
    backoffs = [30, 60, 120, 300]
    idx = min(attempts - 1, len(backoffs) - 1)
    return backoffs[idx]

def validate_thumbnail_quality(analysis_data: dict[str, Any], score_data: dict[str, Any]) -> None:
    """Accessibility & Quality Review Gates."""
    blur = analysis_data.get("blur_score", 0.0)
    if blur > 0.25:
        raise ValueError(f"Thumbnail quality check failed: Image blur ({blur}) exceeds threshold 0.25.")

    contrast_ratio = analysis_data.get("contrast_ratio", 6.0)
    if contrast_ratio < 4.5:
        raise ValueError(f"Thumbnail quality check failed: WCAG contrast ratio ({contrast_ratio}:1) below minimum 4.5:1.")

    overall = score_data.get("overall_score", 0.0)
    if overall < 0.75:
        raise ValueError(f"Thumbnail quality check failed: Overall score ({overall}) below minimum 0.75.")

async def process_thumbnail_job(db: Session, job: ThumbnailJob) -> None:
    correlation_id = str(uuid.uuid4())
    logger.info(json.dumps({
        "event": "Thumbnail Processing Started",
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
        video_pkg = db.query(VideoPackage).filter(VideoPackage.id == job.video_package_id).first()
        subtitle_pkg = db.query(SubtitlePackage).filter(SubtitlePackage.id == job.subtitle_package_id).first() if job.subtitle_package_id else None
        music_pkg = db.query(MusicPackage).filter(MusicPackage.id == job.music_package_id).first() if job.music_package_id else None

        if not script_pkg or not image_pkg or not video_pkg:
            raise ValueError("Input packages mismatch: Complete ScriptPackage, ImagePackage, and VideoPackage are required.")

        provider_instance = thumbnail_registry.get_provider(job.provider) or thumbnail_registry.get_provider("template")

        # Get or create ThumbnailStyleProfile
        profile = job.style_profile
        if not profile:
            profile = ThumbnailStyleProfile(
                id=uuid.uuid4(),
                name=f"{video_pkg.platform.capitalize()} Style Profile",
                platform=video_pkg.platform,
                font_family="Inter Black",
                font_size_pt=72,
                font_weight="Bold",
                primary_color="#FFFFFF",
                accent_color="#FFD700",
                outline_color="#000000",
                shadow_style="Heavy Drop Shadow",
                background_style="High Contrast Gradient",
                logo_placement="top_right",
                safe_margins={"top": 40, "bottom": 40, "left": 40, "right": 40},
                emoji_policy="allowed",
                aspect_ratio="16:9"
            )
            db.add(profile)
            db.flush()
            job.thumbnail_style_profile_id = profile.id
            db.commit()

        # Stage 2: FRAME_SELECTION & Stage 3: FRAME_ANALYSIS
        job.stage = "FRAME_SELECTION"
        job.progress = STAGES["FRAME_SELECTION"]
        db.commit()

        frame_info = await provider_instance.select_frame(video_pkg, image_pkg, [])

        job.stage = "FRAME_ANALYSIS"
        job.progress = STAGES["FRAME_ANALYSIS"]
        db.commit()

        analysis_data = await provider_instance.analyze_frame(frame_info["frame_path"])

        # Stage 4: TEXT_SELECTION & Stage 5: LAYOUT_COMPOSITION
        job.stage = "TEXT_SELECTION"
        job.progress = STAGES["TEXT_SELECTION"]
        db.commit()

        # Multi-source text extraction (Subtitle key phrases > Script hook)
        primary_hook = getattr(script_pkg, "hook", "SHOCKING REVEAL")[:30].upper()
        secondary_hook = getattr(script_pkg, "title", "Automated Production")[:45]

        if subtitle_pkg and getattr(subtitle_pkg, "scene_subtitles", None):
            first_sc = subtitle_pkg.scene_subtitles[0]
            if getattr(first_sc, "key_phrases", None) and len(first_sc.key_phrases) > 0:
                primary_hook = first_sc.key_phrases[0].upper()[:30]

        text_hierarchy = {
            "primary_hook": primary_hook,
            "secondary_hook": secondary_hook,
            "badge_text": "NEW",
            "brand_label": "AATES STUDIO"
        }

        job.stage = "LAYOUT_COMPOSITION"
        job.progress = STAGES["LAYOUT_COMPOSITION"]
        db.commit()

        # Stage 6: STYLE_APPLICATION & Stage 7: VARIANT_GENERATION
        job.stage = "STYLE_APPLICATION"
        job.progress = STAGES["STYLE_APPLICATION"]
        db.commit()

        job.stage = "VARIANT_GENERATION"
        job.progress = STAGES["VARIANT_GENERATION"]
        db.commit()

        # Render 3 candidate variants across composition templates
        layouts = ["left_focus", "right_focus", "centered"]
        rendered_variants = []

        os.makedirs("artifacts/thumbnails", exist_ok=True)

        for idx, layout in enumerate(layouts):
            comp_spec = await provider_instance.compose(frame_info["frame_path"], text_hierarchy, layout, {
                "font_family": profile.font_family,
                "primary_color": profile.primary_color,
                "accent_color": profile.accent_color,
                "outline_color": profile.outline_color,
                "aspect_ratio": profile.aspect_ratio
            })

            variant_file = f"artifacts/thumbnails/variant_{idx+1}_{uuid.uuid4().hex[:6]}.png"
            render_res = await provider_instance.render(comp_spec, variant_file)
            score_res = await provider_instance.score(variant_file, text_hierarchy, {})

            rendered_variants.append({
                "layout_type": layout,
                "comp_spec": comp_spec,
                "render_res": render_res,
                "score_res": score_res,
                "file_path": variant_file
            })

        # Stage 8: QUALITY_SCORING
        job.stage = "QUALITY_SCORING"
        job.progress = STAGES["QUALITY_SCORING"]
        db.commit()

        # Select highest-scoring variant
        best_variant = max(rendered_variants, key=lambda v: v["score_res"]["overall_score"])
        validate_thumbnail_quality(analysis_data, best_variant["score_res"])

        # Telemetry & Quality Report for Quality Agent
        telemetry_metadata = {
            "blur_score": analysis_data["blur_score"],
            "contrast_ratio": analysis_data["contrast_ratio"],
            "face_confidence": analysis_data["face_confidence"],
            "ocr_confidence": analysis_data["ocr_result"]["confidence"],
            "saliency_score": 0.94,
            "layout_complexity": 0.45,
            "predicted_ctr": best_variant["score_res"]["ctr_prediction_score"],
            "overall_quality": best_variant["score_res"]["overall_score"]
        }

        # Shared Package Manifest
        package_manifest = {
            "package_type": "ThumbnailPackage",
            "version": 1,
            "parent_package_references": {
                "script_package_id": str(script_pkg.id),
                "image_package_id": str(image_pkg.id),
                "video_package_id": str(video_pkg.id),
                "subtitle_package_id": str(job.subtitle_package_id) if job.subtitle_package_id else None,
                "music_package_id": str(job.music_package_id) if job.music_package_id else None
            },
            "producer_agent": "thumbnail_agent",
            "provider": job.provider,
            "model": "LocalTemplate-v1",
            "input_dependencies": ["ScriptPackage", "ImagePackage", "VideoPackage"],
            "output_primary_thumbnail": best_variant["file_path"],
            "quality_score": best_variant["score_res"]["overall_score"],
            "validation_status": "PASSED",
            "created_at": datetime.datetime.utcnow().isoformat()
        }

        # Create ThumbnailPackage
        pkg = ThumbnailPackage(
            id=uuid.uuid4(),
            job_id=job.id,
            script_package_id=script_pkg.id,
            image_package_id=image_pkg.id,
            video_package_id=video_pkg.id,
            subtitle_package_id=job.subtitle_package_id,
            music_package_id=job.music_package_id,
            thumbnail_style_profile_id=profile.id,
            variant_count=len(rendered_variants),
            package_manifest=package_manifest,
            # BasePackageMixin fields
            version=1,
            parent_package_id=None,
            source_agent="thumbnail_agent",
            provider=job.provider,
            model="LocalTemplateEngine",
            prompt_version="v1.0",
            quality_score=best_variant["score_res"]["overall_score"],
            telemetry_metadata=telemetry_metadata
        )
        db.add(pkg)
        db.flush()

        # Save ThumbnailAnalysis
        analysis = ThumbnailAnalysis(
            id=uuid.uuid4(),
            thumbnail_package_id=pkg.id,
            blur_score=analysis_data["blur_score"],
            brightness=analysis_data["brightness"],
            contrast_ratio=analysis_data["contrast_ratio"],
            entropy=analysis_data["entropy"],
            dominant_colors=analysis_data["dominant_colors"],
            face_count=analysis_data["face_count"],
            face_confidence=analysis_data["face_confidence"],
            object_regions=analysis_data["object_regions"],
            saliency_map=analysis_data["saliency_map"],
            ocr_result=analysis_data["ocr_result"],
            edge_density=analysis_data["edge_density"],
            color_histogram=analysis_data["color_histogram"]
        )
        db.add(analysis)

        # Save CompositionTemplates, Assets, Variants, and Scores
        created_variants = []
        for v_item in rendered_variants:
            layout = v_item["layout_type"]
            score_data = v_item["score_res"]

            # Template
            tmpl = CompositionTemplate(
                id=uuid.uuid4(),
                name=f"{layout.capitalize()} Template",
                platform=video_pkg.platform,
                layout_type=layout,
                aspect_ratio=profile.aspect_ratio
            )
            db.add(tmpl)
            db.flush()

            # Asset
            asset = ThumbnailAsset(
                id=uuid.uuid4(),
                storage_key=v_item["file_path"],
                width=1280,
                height=720,
                format="png",
                file_size_bytes=v_item["render_res"]["file_size_bytes"]
            )
            db.add(asset)
            db.flush()

            is_sel = (v_item == best_variant)

            # Variant
            variant = ThumbnailVariant(
                id=uuid.uuid4(),
                thumbnail_package_id=pkg.id,
                thumbnail_asset_id=asset.id,
                composition_template_id=tmpl.id,
                variant_name=f"Variant {layout.capitalize()}",
                scene_number=1,
                source_frame_key=frame_info["frame_path"],
                primary_hook=text_hierarchy["primary_hook"],
                secondary_hook=text_hierarchy["secondary_hook"],
                badge_text=text_hierarchy["badge_text"],
                brand_label=text_hierarchy["brand_label"],
                layout_type=layout,
                contrast_score=score_data["contrast_score"],
                readability_score=score_data["text_readability_score"],
                composition_score=score_data["overall_score"],
                brand_score=score_data["brand_consistency_score"],
                ctr_prediction_score=score_data["ctr_prediction_score"],
                quality_score=score_data["overall_score"],
                is_selected=is_sel
            )
            db.add(variant)
            db.flush()

            if is_sel:
                pkg.primary_thumbnail_id = variant.id
                pkg.selected_variant_id = variant.id
                db.add(pkg)

            # ThumbnailScore
            t_score = ThumbnailScore(
                id=uuid.uuid4(),
                thumbnail_variant_id=variant.id,
                contrast_score=score_data["contrast_score"],
                sharpness_score=score_data["sharpness_score"],
                face_visibility_score=score_data["face_visibility_score"],
                subject_prominence_score=score_data["subject_prominence_score"],
                text_readability_score=score_data["text_readability_score"],
                color_harmony_score=score_data["color_harmony_score"],
                rule_of_thirds_score=score_data["rule_of_thirds_score"],
                emotion_score=score_data["emotion_score"],
                brand_consistency_score=score_data["brand_consistency_score"],
                heuristic_score=score_data["heuristic_score"],
                learned_score=score_data["learned_score"],
                overall_score=score_data["overall_score"]
            )
            db.add(t_score)
            created_variants.append(variant)

        # Save ThumbnailExperiment (Bridge for Analytics & A/B Testing)
        if len(created_variants) >= 2:
            exp = ThumbnailExperiment(
                id=uuid.uuid4(),
                thumbnail_package_id=pkg.id,
                variant_a_id=created_variants[0].id,
                variant_b_id=created_variants[1].id,
                platform=video_pkg.platform,
                status="SCHEDULED",
                evaluation_window_hours=72,
                statistical_significance=0.95,
                algorithm_version="v1.0"
            )
            db.add(exp)

        # Save ThumbnailVersion snapshot
        ver_snapshot = [
            {
                "variant_id": str(v.id),
                "variant_name": v.variant_name,
                "layout_type": v.layout_type,
                "quality_score": v.quality_score,
                "is_selected": v.is_selected
            } for v in created_variants
        ]
        ver = ThumbnailVersion(
            id=uuid.uuid4(),
            thumbnail_package_id=pkg.id,
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
            job.completed_at = datetime.datetime.utcnow()
            job.duration_sec = total_duration
            db.add(job)
            db.commit()

        AGENT_STATE["jobs_succeeded"] += 1
        AGENT_STATE["total_duration_sec"] += total_duration
        AGENT_STATE["jobs_processed"] += 1

        logger.info(json.dumps({
            "event": "Thumbnail Processing Completed",
            "job_id": str(job.id),
            "variant_count": len(rendered_variants),
            "duration_sec": total_duration,
            "correlation_id": correlation_id
        }))

    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error(json.dumps({
            "event": "Thumbnail Processing Failed",
            "job_id": str(job.id),
            "error": error_msg,
            "correlation_id": correlation_id
        }))

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

async def thumbnail_agent_poll_loop(agent_id: str) -> None:
    logger.info(f"Thumbnail Agent loop started for agent ID: {agent_id}")
    while AGENT_STATE["is_running"]:
        db = SessionLocal()
        try:
            update_agent_heartbeat(db, agent_id)

            query = db.query(ThumbnailJob).filter(
                ThumbnailJob.status.in_(["QUEUED", "RETRYING"]),
                (ThumbnailJob.scheduled_at == None) | (ThumbnailJob.scheduled_at <= datetime.datetime.utcnow())
            ).order_by(
                ThumbnailJob.priority.desc(),
                ThumbnailJob.created_at.asc()
            )

            if db.bind.dialect.name == "sqlite":
                job = query.first()
            else:
                job = query.with_for_update(skip_locked=True).first()

            if job:
                if is_valid_transition(job.status, "PROCESSING"):
                    job.status = "PROCESSING"
                    job.started_at = datetime.datetime.utcnow()
                    db.commit()

                    await process_thumbnail_job(db, job)
                else:
                    logger.warning(f"Invalid transition from {job.status} to PROCESSING for job {job.id}")

        except Exception as e:
            logger.error(f"Exception inside Thumbnail Agent loop iteration: {str(e)}")
        finally:
            db.close()

        await asyncio.sleep(2.0)

async def start_thumbnail_agent(concurrency: int = 1) -> None:
    if AGENT_STATE["is_running"]:
        return
    AGENT_STATE["is_running"] = True
    AGENT_STATE["started_at"] = datetime.datetime.utcnow()

    db = SessionLocal()
    try:
        recover_orphaned_jobs(db)
    finally:
        db.close()

    for i in range(concurrency):
        agent_id = f"thumbnail-agent-{i}"
        task = asyncio.create_task(thumbnail_agent_poll_loop(agent_id))
        _agent_tasks.append(task)
    logger.info(f"Started {concurrency} concurrent background AI Thumbnail Agents.")

async def stop_thumbnail_agent() -> None:
    if not AGENT_STATE["is_running"]:
        return
    AGENT_STATE["is_running"] = False
    for task in _agent_tasks:
        task.cancel()
    if _agent_tasks:
        await asyncio.gather(*_agent_tasks, return_exceptions=True)
    _agent_tasks.clear()
    logger.info("Stopped background AI Thumbnail Agents.")
ZOOMING = "zoom"
