import os
import uuid
import pytest
import asyncio
from datetime import datetime
from fastapi.testclient import TestClient

from core.database.session import Base
from core.database.models import (
    ResearchJob,
    KnowledgePackage,
    ScriptJob,
    ScriptPackage,
    ImageJob,
    ImagePackage,
    SceneAsset,
    VoiceJob,
    VoicePackage,
    SceneVoice,
    VideoJob,
    VideoPackage,
    SubtitleJob,
    SubtitlePackage,
    SceneSubtitle,
    MusicJob,
    MusicPackage,
    ThumbnailJob,
    ThumbnailPackage,
    ThumbnailVariant,
    ThumbnailAsset,
    QualityJob,
    QualityPackage,
    QualityCheck,
    QualityIssue,
    QualityEvidence,
    QualityRecommendation,
    RemediationTask,
    QualityPolicy,
    QualityRule,
    QualityVersion
)
from brain.agents.quality_agent import (
    is_valid_transition,
    is_transient_error,
    process_quality_job,
    get_or_create_default_policy
)
from providers.quality.registry import quality_registry
from providers.quality.engine import LocalPolicyQualityProvider
from providers.quality.mock import MockQualityProvider


# 1. State Transition Matrix Tests
def test_quality_state_transitions():
    assert is_valid_transition("QUEUED", "PROCESSING") is True
    assert is_valid_transition("QUEUED", "CANCELLED") is True
    assert is_valid_transition("PROCESSING", "SUCCESS") is True
    assert is_valid_transition("PROCESSING", "RETRYING") is True
    assert is_valid_transition("PROCESSING", "FAILED") is True
    assert is_valid_transition("FAILED", "QUEUED") is True
    assert is_valid_transition("CANCELLED", "QUEUED") is True
    
    assert is_valid_transition("SUCCESS", "PROCESSING") is False
    assert is_valid_transition("FAILED", "SUCCESS") is False


# 2. Error Classification Tests
def test_quality_error_classification():
    assert is_transient_error("Governance evaluator busy: connection timeout") is True
    assert is_transient_error("HTTP 429: Rate limit exceeded") is True
    assert is_transient_error("ValueError: Empty title text") is False


# 3. Provider Registry & Capability Inspection
def test_quality_provider_registry():
    engine_prov = quality_registry.get_provider("policy_engine")
    assert isinstance(engine_prov, LocalPolicyQualityProvider)
    assert engine_prov.supports_cross_package_validation() is True

    mock_prov = quality_registry.get_provider("mock")
    assert isinstance(mock_prov, MockQualityProvider)
    assert mock_prov.supports_policy_profiles() is True


# 4. QualityPolicy Profile Construction & Default Fallback
def test_quality_policy_default_construction(db):
    policy = get_or_create_default_policy(db, "youtube")
    assert policy.platform == "youtube"
    assert policy.min_readiness_score == 0.85
    assert len(policy.rules) >= 3


# 5. Background Quality Job Processing & Matrix Verification
@pytest.mark.asyncio
async def test_quality_agent_job_processing(db):
    res_job = ResearchJob(id=uuid.uuid4(), topic="Quality Tech", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="Quality Tech", summary="Quality summary")
    db.add(kp)
    db.commit()

    script_job = ScriptJob(id=uuid.uuid4(), knowledge_package_id=kp.id, provider="mock", platform="youtube", status="SUCCESS")
    db.add(script_job)
    db.commit()

    script_pkg = ScriptPackage(
        id=uuid.uuid4(), job_id=script_job.id, knowledge_package_id=kp.id,
        title="Quality 101", platform="youtube", language="en", hook="Hook text", problem="Problem",
        story="Story", solution="Solution", cta="CTA", narration="Narration text.",
        scene_breakdown=[{"scene_number": 1, "narration": "Quality demonstration scene", "duration": 5.0}]
    )
    db.add(script_pkg)
    db.commit()

    img_job = ImageJob(id=uuid.uuid4(), script_package_id=script_pkg.id, provider="mock", status="SUCCESS")
    db.add(img_job)
    db.commit()

    img_pkg = ImagePackage(id=uuid.uuid4(), job_id=img_job.id, script_package_id=script_pkg.id, platform="youtube", resolution="1920x1080", aspect_ratio="16:9", style_preset="Photorealistic", quality_score=0.9)
    db.add(img_pkg)
    db.commit()

    voice_job = VoiceJob(id=uuid.uuid4(), script_package_id=script_pkg.id, provider="mock", voice_model="MockSpeech", language="en", status="SUCCESS")
    db.add(voice_job)
    db.commit()

    voice_pkg = VoicePackage(id=uuid.uuid4(), job_id=voice_job.id, script_package_id=script_pkg.id, platform="youtube", language="en", total_scenes=1, overall_duration_ms=5000, quality_score=0.9)
    db.add(voice_pkg)
    db.commit()

    video_job = VideoJob(id=uuid.uuid4(), script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, renderer="mock", status="SUCCESS")
    db.add(video_job)
    db.commit()

    video_pkg = VideoPackage(id=uuid.uuid4(), job_id=video_job.id, script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, platform="youtube", resolution="1920x1080", aspect_ratio="16:9", duration_ms=5000, storage_key="video/outputs/output_1.mp4", version=1, quality_score=0.9)
    db.add(video_pkg)
    db.commit()

    sub_job = SubtitleJob(id=uuid.uuid4(), voice_package_id=voice_pkg.id, video_package_id=video_pkg.id, provider="alignment", status="SUCCESS")
    db.add(sub_job)
    db.commit()

    sub_pkg = SubtitlePackage(id=uuid.uuid4(), job_id=sub_job.id, voice_package_id=voice_pkg.id, video_package_id=video_pkg.id, language="en", caption_style="YouTube", subtitle_formats=["srt"], scene_count=1, total_captions=1, total_words=2, quality_score=0.95)
    db.add(sub_pkg)
    db.commit()

    music_job = MusicJob(id=uuid.uuid4(), script_package_id=script_pkg.id, voice_package_id=voice_pkg.id, video_package_id=video_pkg.id, provider="library", status="SUCCESS")
    db.add(music_job)
    db.commit()

    music_pkg = MusicPackage(id=uuid.uuid4(), job_id=music_job.id, script_package_id=script_pkg.id, voice_package_id=voice_pkg.id, video_package_id=video_pkg.id, storage_key="artifacts/music/master.mp3", scene_count=1, duration_ms=5000, quality_score=0.96)
    db.add(music_pkg)
    db.commit()

    thumb_job = ThumbnailJob(id=uuid.uuid4(), script_package_id=script_pkg.id, image_package_id=img_pkg.id, video_package_id=video_pkg.id, provider="template", status="SUCCESS")
    db.add(thumb_job)
    db.commit()

    thumb_pkg = ThumbnailPackage(id=uuid.uuid4(), job_id=thumb_job.id, script_package_id=script_pkg.id, image_package_id=img_pkg.id, video_package_id=video_pkg.id, variant_count=1, quality_score=0.94)
    db.add(thumb_pkg)
    db.commit()

    # Quality Job
    quality_job = QualityJob(
        id=uuid.uuid4(),
        script_package_id=script_pkg.id,
        image_package_id=img_pkg.id,
        voice_package_id=voice_pkg.id,
        video_package_id=video_pkg.id,
        subtitle_package_id=sub_pkg.id,
        music_package_id=music_pkg.id,
        thumbnail_package_id=thumb_pkg.id,
        provider="policy_engine",
        status="PROCESSING",
        stage="VALIDATING"
    )
    db.add(quality_job)
    db.commit()

    # Process job
    await process_quality_job(db, quality_job)

    db.refresh(quality_job)
    assert quality_job.status == "SUCCESS"
    assert quality_job.stage == "COMPLETED"

    # Assert QualityPackage
    assert len(quality_job.packages) == 1
    pkg = quality_job.packages[0]
    assert pkg.version == 1
    assert pkg.production_readiness_score >= 0.85
    assert pkg.is_approved_for_publishing is True
    assert pkg.publishing_lifecycle_state == "Approved"
    assert pkg.package_manifest is not None
    assert pkg.package_manifest["package_type"] == "QualityPackage"
    
    # Assert QualityChecks
    assert len(pkg.checks) >= 6

    # Assert QualityVersion
    assert len(pkg.versions) == 1
    assert pkg.versions[0].lineage_action == "INITIAL"


# 6. API Routing & Endpoints Tests
def test_api_quality_routes(client, db):
    res_job = ResearchJob(id=uuid.uuid4(), topic="API Quality", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="API Quality", summary="Summary API Quality")
    db.add(kp)
    db.commit()

    script_job = ScriptJob(id=uuid.uuid4(), knowledge_package_id=kp.id, provider="mock", platform="youtube", status="SUCCESS")
    db.add(script_job)
    db.commit()

    script_pkg = ScriptPackage(id=uuid.uuid4(), job_id=script_job.id, knowledge_package_id=kp.id, title="Title", platform="youtube", language="en", hook="H", problem="P", story="S", solution="Sol", cta="C", narration="N.", scene_breakdown=[{"scene_number": 1, "duration": 4.0}])
    db.add(script_pkg)
    db.commit()

    img_job = ImageJob(id=uuid.uuid4(), script_package_id=script_pkg.id, provider="mock", status="SUCCESS")
    db.add(img_job)
    db.commit()

    img_pkg = ImagePackage(id=uuid.uuid4(), job_id=img_job.id, script_package_id=script_pkg.id, platform="youtube", resolution="1920x1080", aspect_ratio="16:9", style_preset="Photorealistic", quality_score=0.9)
    db.add(img_pkg)
    db.commit()

    voice_job = VoiceJob(id=uuid.uuid4(), script_package_id=script_pkg.id, provider="mock", voice_model="MockSpeech", language="en", status="SUCCESS")
    db.add(voice_job)
    db.commit()

    voice_pkg = VoicePackage(id=uuid.uuid4(), job_id=voice_job.id, script_package_id=script_pkg.id, platform="youtube", language="en", total_scenes=1, overall_duration_ms=4000, quality_score=0.9)
    db.add(voice_pkg)
    db.commit()

    video_job = VideoJob(id=uuid.uuid4(), script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, renderer="mock", status="SUCCESS")
    db.add(video_job)
    db.commit()

    video_pkg = VideoPackage(id=uuid.uuid4(), job_id=video_job.id, script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, platform="youtube", resolution="1920x1080", aspect_ratio="16:9", duration_ms=4000, storage_key="video/outputs/output_1.mp4", version=1, quality_score=0.9)
    db.add(video_pkg)
    db.commit()

    # 1. POST /v1/quality (create)
    resp = client.post("/v1/quality", json={
        "script_package_id": str(script_pkg.id),
        "image_package_id": str(img_pkg.id),
        "voice_package_id": str(voice_pkg.id),
        "video_package_id": str(video_pkg.id),
        "provider": "policy_engine",
        "priority": 1
    })
    assert resp.status_code == 200
    job_data = resp.json()
    job_id = job_data["id"]
    assert job_data["status"] == "QUEUED"

    # 2. GET /v1/quality (list)
    resp = client.get("/v1/quality")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 3. GET /v1/quality/policies (policies)
    resp = client.get("/v1/quality/policies")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 4. GET /v1/quality/metrics (metrics)
    resp = client.get("/v1/quality/metrics")
    assert resp.status_code == 200
    assert resp.json()["jobs_queued"] >= 1

    # 5. GET /v1/quality/{id} (detail)
    resp = client.get(f"/v1/quality/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id

    # 6. Delete job
    resp = client.delete(f"/v1/quality/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


# 7. Re-evaluate Endpoint Test
def test_api_quality_reevaluate(client, db):
    res_job = ResearchJob(id=uuid.uuid4(), topic="Re-evaluate Test", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="Re-evaluate Test", summary="Summary Re-evaluate")
    db.add(kp)
    db.commit()

    script_job = ScriptJob(id=uuid.uuid4(), knowledge_package_id=kp.id, provider="mock", platform="youtube", status="SUCCESS")
    db.add(script_job)
    db.commit()

    script_pkg = ScriptPackage(id=uuid.uuid4(), job_id=script_job.id, knowledge_package_id=kp.id, title="Title", platform="youtube", language="en", hook="H", problem="P", story="S", solution="Sol", cta="C", narration="Re-eval text.", scene_breakdown=[{"scene_number": 1, "duration": 4.0}])
    db.add(script_pkg)
    db.commit()

    img_job = ImageJob(id=uuid.uuid4(), script_package_id=script_pkg.id, provider="mock", status="SUCCESS")
    db.add(img_job)
    db.commit()

    img_pkg = ImagePackage(id=uuid.uuid4(), job_id=img_job.id, script_package_id=script_pkg.id, platform="youtube", resolution="1920x1080", aspect_ratio="16:9", style_preset="Photorealistic", quality_score=0.9)
    db.add(img_pkg)
    db.commit()

    voice_job = VoiceJob(id=uuid.uuid4(), script_package_id=script_pkg.id, provider="mock", voice_model="MockSpeech", language="en", status="SUCCESS")
    db.add(voice_job)
    db.commit()

    voice_pkg = VoicePackage(id=uuid.uuid4(), job_id=voice_job.id, script_package_id=script_pkg.id, platform="youtube", language="en", total_scenes=1, overall_duration_ms=4000, quality_score=0.9)
    db.add(voice_pkg)
    db.commit()

    video_job = VideoJob(id=uuid.uuid4(), script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, renderer="mock", status="SUCCESS")
    db.add(video_job)
    db.commit()

    video_pkg = VideoPackage(id=uuid.uuid4(), job_id=video_job.id, script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, platform="youtube", resolution="1920x1080", aspect_ratio="16:9", duration_ms=4000, storage_key="video/outputs/output_1.mp4", version=1, quality_score=0.9)
    db.add(video_pkg)
    db.commit()

    quality_job = QualityJob(
        id=uuid.uuid4(), script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, video_package_id=video_pkg.id,
        provider="policy_engine", status="SUCCESS", stage="COMPLETED"
    )
    db.add(quality_job)
    db.commit()

    pkg = QualityPackage(
        id=uuid.uuid4(), job_id=quality_job.id, script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, video_package_id=video_pkg.id,
        production_readiness_score=0.94, is_approved_for_publishing=True, publishing_lifecycle_state="Approved", version=1, quality_score=0.94
    )
    db.add(pkg)
    db.commit()

    # POST /v1/quality/{id}/re-evaluate
    resp = client.post(f"/v1/quality/{quality_job.id}/re-evaluate")
    assert resp.status_code == 200
    assert resp.json()["version"] == 2
