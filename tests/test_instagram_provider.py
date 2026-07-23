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
    VoiceJob,
    VoicePackage,
    VideoJob,
    VideoPackage,
    QualityJob,
    QualityPackage,
    InstagramPublishJob,
    PublicationPackage,
    InstagramPublication,
    InstagramMediaAsset,
    PublishingAttempt,
    InstagramInsightSnapshot,
    InstagramVersion
)
from providers.publishing.platform_profile import platform_registry, PlatformProfile
from providers.publishing.instagram import InstagramPublishingProvider
from brain.operations.instagram_worker import is_valid_transition, is_transient_error, process_instagram_job


# 1. PlatformProfile & Registry Tests
def test_platform_profile_registry():
    capabilities = platform_registry.get_capabilities("instagram")
    assert capabilities is not None
    assert capabilities.supports_carousel is True

    reels_profile = platform_registry.get_profile("instagram_reels")
    assert reels_profile is not None
    assert reels_profile.max_duration_sec == 90.0
    assert reels_profile.max_hashtags == 30

    feed_profile = platform_registry.get_profile("instagram_feed")
    assert feed_profile is not None
    assert feed_profile.max_duration_sec == 60.0


# 2. Instagram Provider Framework Tests
@pytest.mark.asyncio
async def test_instagram_provider_methods():
    provider = InstagramPublishingProvider()
    auth_res = await provider.authenticate()
    assert auth_res["status"] == "authenticated"

    os.makedirs("artifacts/videos", exist_ok=True)
    test_vid = "artifacts/videos/test_ig_provider.mp4"
    with open(test_vid, "wb") as f: f.write(b"SAMPLE")

    val_res = await provider.validate_media(test_vid, "instagram_reels")
    assert val_res["status"] == "valid"

    trans_res = await provider.transform_media(test_vid, "instagram_reels")
    assert "transformed_media_path" in trans_res
    assert "cover_image_path" in trans_res

    caption_res = await provider.prepare_caption(None, None, max_hashtags=30)
    assert len(caption_res["hashtags"]) <= 30
    assert "AATES" in caption_res["caption"]

    upload_res = await provider.upload_media(val_res, caption_res)
    assert "container_id" in upload_res

    pub_res = await provider.publish(upload_res["container_id"])
    assert "instagram_media_id" in pub_res
    assert "instagram.com" in pub_res["permalink"]

    insights_res = await provider.fetch_insights(pub_res["instagram_media_id"])
    assert insights_res["views"] > 0
    assert insights_res["likes"] >= 0


# 3. Quality Gate Enforcer Test
@pytest.mark.asyncio
async def test_quality_gate_enforcer(db):
    res_job = ResearchJob(id=uuid.uuid4(), topic="Quality Gate IG", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="Quality Gate IG", summary="Summary")
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

    quality_job = QualityJob(id=uuid.uuid4(), script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, video_package_id=video_pkg.id, provider="policy_engine", status="SUCCESS")
    db.add(quality_job)
    db.commit()

    # Unapproved QualityPackage
    unapproved_pkg = QualityPackage(
        id=uuid.uuid4(), job_id=quality_job.id, script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, video_package_id=video_pkg.id,
        production_readiness_score=0.60, is_approved_for_publishing=False, publishing_lifecycle_state="Draft", quality_score=0.60
    )
    db.add(unapproved_pkg)
    db.commit()

    ig_job = InstagramPublishJob(id=uuid.uuid4(), quality_package_id=unapproved_pkg.id, platform_media_type="Reels", status="PROCESSING")
    db.add(ig_job)
    db.commit()

    ig_job_id = ig_job.id
    # Should fail at Quality Gate stage
    await process_instagram_job(db, ig_job)

    ig_job = db.query(InstagramPublishJob).filter(InstagramPublishJob.id == ig_job_id).first()
    assert ig_job is not None
    assert ig_job.status == "FAILED"
    assert "Quality Gate Rejected" in ig_job.error_message


# 4. Background Instagram Worker Processing Test
@pytest.mark.asyncio
async def test_instagram_worker_job_processing(db):
    res_job = ResearchJob(id=uuid.uuid4(), topic="Worker IG", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="Worker IG", summary="Summary")
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

    quality_job = QualityJob(id=uuid.uuid4(), script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, video_package_id=video_pkg.id, provider="policy_engine", status="SUCCESS")
    db.add(quality_job)
    db.commit()

    approved_pkg = QualityPackage(
        id=uuid.uuid4(), job_id=quality_job.id, script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, video_package_id=video_pkg.id,
        production_readiness_score=0.94, is_approved_for_publishing=True, publishing_lifecycle_state="Approved", quality_score=0.94
    )
    db.add(approved_pkg)
    db.commit()

    ig_job = InstagramPublishJob(id=uuid.uuid4(), quality_package_id=approved_pkg.id, platform_media_type="Reels", status="PROCESSING", stage="VALIDATING")
    db.add(ig_job)
    db.commit()

    await process_instagram_job(db, ig_job)

    db.refresh(ig_job)
    assert ig_job.status == "SUCCESS"
    assert ig_job.stage == "COMPLETED"

    # Assert PublicationPackage
    assert len(ig_job.packages) == 1
    pub_pkg = ig_job.packages[0]
    assert pub_pkg.platform_name == "instagram"
    assert pub_pkg.package_manifest is not None

    # Assert InstagramPublication
    assert len(pub_pkg.publications) == 1
    pub = pub_pkg.publications[0]
    assert "instagram.com" in pub.permalink

    # Assert MediaAsset, Attempts, Insights, Version
    assert len(pub.media_assets) == 1
    assert len(ig_job.attempts_history) == 2
    assert len(pub.insights) == 1
    assert len(pub_pkg.versions) == 1


# 5. REST API Routing & Endpoints Tests
def test_api_instagram_routes(client, db):
    res_job = ResearchJob(id=uuid.uuid4(), topic="API IG", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="API IG", summary="Summary")
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

    quality_job = QualityJob(id=uuid.uuid4(), script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, video_package_id=video_pkg.id, provider="policy_engine", status="SUCCESS")
    db.add(quality_job)
    db.commit()

    approved_pkg = QualityPackage(
        id=uuid.uuid4(), job_id=quality_job.id, script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, video_package_id=video_pkg.id,
        production_readiness_score=0.94, is_approved_for_publishing=True, publishing_lifecycle_state="Approved", quality_score=0.94
    )
    db.add(approved_pkg)
    db.commit()

    # 1. POST /v1/publishing/instagram (create)
    resp = client.post("/v1/publishing/instagram", json={
        "quality_package_id": str(approved_pkg.id),
        "platform_media_type": "Reels",
        "provider": "instagram_provider",
        "priority": 1
    })
    assert resp.status_code == 200
    job_data = resp.json()
    job_id = job_data["id"]
    assert job_data["status"] == "QUEUED"

    # 2. GET /v1/publishing/instagram (list)
    resp = client.get("/v1/publishing/instagram")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 3. GET /v1/publishing/instagram/metrics (metrics)
    resp = client.get("/v1/publishing/instagram/metrics")
    assert resp.status_code == 200
    assert resp.json()["jobs_queued"] >= 1

    # 4. GET /v1/publishing/instagram/{id} (detail)
    resp = client.get(f"/v1/publishing/instagram/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id

    # 5. Delete job
    resp = client.delete(f"/v1/publishing/instagram/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"
