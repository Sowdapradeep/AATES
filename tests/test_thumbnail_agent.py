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
    CompositionTemplate,
    ThumbnailAnalysis,
    ThumbnailScore,
    ThumbnailStyleProfile,
    ThumbnailVersion,
    ThumbnailExperiment
)
from brain.agents.thumbnail_agent import (
    is_valid_transition,
    is_transient_error,
    process_thumbnail_job,
    validate_thumbnail_quality
)
from providers.thumbnail.registry import thumbnail_registry
from providers.thumbnail.template import LocalTemplateThumbnailProvider
from providers.thumbnail.mock import MockThumbnailProvider


# 1. State Transition Matrix Tests
def test_thumbnail_state_transitions():
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
def test_thumbnail_error_classification():
    assert is_transient_error("Thumbnail renderer busy: connection timeout") is True
    assert is_transient_error("HTTP 429: Rate limit exceeded") is True
    assert is_transient_error("ValueError: Empty title text") is False


# 3. Provider Registry & Capability Inspection
def test_thumbnail_provider_registry():
    tmpl_prov = thumbnail_registry.get_provider("template")
    assert isinstance(tmpl_prov, LocalTemplateThumbnailProvider)
    assert tmpl_prov.supports_frame_extraction() is True

    mock_prov = thumbnail_registry.get_provider("mock")
    assert isinstance(mock_prov, MockThumbnailProvider)
    assert mock_prov.supports_scoring() is True


# 4. Multi-Source Selection & Scoring Tests
@pytest.mark.asyncio
async def test_thumbnail_scoring_engine():
    provider = LocalTemplateThumbnailProvider()
    os.makedirs("artifacts/thumbnails", exist_ok=True)
    test_img = "artifacts/thumbnails/test_score.png"
    with open(test_img, "wb") as f: f.write(b"PNG")

    text_data = {"primary_hook": "SECRET FORMULA", "secondary_hook": "AATES Engine"}
    scores = await provider.score(test_img, text_data, {})

    assert "contrast_score" in scores
    assert "heuristic_score" in scores
    assert "learned_score" in scores
    assert "overall_score" in scores
    assert scores["overall_score"] > 0.75


# 5. Quality Gate Rules Tests
def test_thumbnail_quality_gates():
    analysis = {"blur_score": 0.05, "contrast_ratio": 6.2}
    score_data = {"overall_score": 0.92}

    # Should pass
    validate_thumbnail_quality(analysis, score_data)

    # 1. Image blur (> 0.25)
    bad_blur = {"blur_score": 0.35, "contrast_ratio": 6.2}
    with pytest.raises(ValueError, match="Image blur"):
        validate_thumbnail_quality(bad_blur, score_data)

    # 2. Low contrast (< 4.5:1)
    bad_contrast = {"blur_score": 0.05, "contrast_ratio": 3.2}
    with pytest.raises(ValueError, match="WCAG contrast ratio"):
        validate_thumbnail_quality(bad_contrast, score_data)

    # 3. Low overall score (< 0.75)
    bad_score = {"overall_score": 0.65}
    with pytest.raises(ValueError, match="Overall score"):
        validate_thumbnail_quality(analysis, bad_score)


# 6. Background Thumbnail Job Processing Tests
@pytest.mark.asyncio
async def test_thumbnail_agent_job_processing(db):
    res_job = ResearchJob(id=uuid.uuid4(), topic="Thumbnails Tech", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="Thumbnails Tech", summary="Thumbnails summary")
    db.add(kp)
    db.commit()

    script_job = ScriptJob(id=uuid.uuid4(), knowledge_package_id=kp.id, provider="mock", platform="youtube", status="SUCCESS")
    db.add(script_job)
    db.commit()

    script_pkg = ScriptPackage(
        id=uuid.uuid4(), job_id=script_job.id, knowledge_package_id=kp.id,
        title="Thumbnails 101", platform="youtube", language="en", hook="Hook text", problem="Problem",
        story="Story", solution="Solution", cta="CTA", narration="Narration text.",
        scene_breakdown=[{"scene_number": 1, "narration": "Thumbnail demonstration scene", "duration": 5.0}]
    )
    db.add(script_pkg)
    db.commit()

    img_job = ImageJob(id=uuid.uuid4(), script_package_id=script_pkg.id, provider="mock", status="SUCCESS")
    db.add(img_job)
    db.commit()

    img_pkg = ImagePackage(id=uuid.uuid4(), job_id=img_job.id, script_package_id=script_pkg.id, platform="youtube", resolution="1920x1080", aspect_ratio="16:9", style_preset="Photorealistic", quality_score=0.9)
    db.add(img_pkg)
    db.flush()

    sc_asset = SceneAsset(
        id=uuid.uuid4(), image_package_id=img_pkg.id, scene_number=1,
        local_path="artifacts/images/scene_1.png", storage_key="images/scene_1.png",
        aspect_ratio="16:9", resolution="1920x1080",
        prompt="Prompt", provider="mock", model="Mock"
    )
    db.add(sc_asset)
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
    db.flush()

    sc_sub = SceneSubtitle(
        id=uuid.uuid4(), subtitle_package_id=sub_pkg.id, scene_number=1, caption_text="Keyphrase text",
        word_timings=[], sentence_timings=[],
        key_phrases=["KEYPHRASE"], importance_score=0.95
    )
    db.add(sc_sub)
    db.commit()

    music_job = MusicJob(id=uuid.uuid4(), script_package_id=script_pkg.id, voice_package_id=voice_pkg.id, video_package_id=video_pkg.id, provider="library", status="SUCCESS")
    db.add(music_job)
    db.commit()

    music_pkg = MusicPackage(id=uuid.uuid4(), job_id=music_job.id, script_package_id=script_pkg.id, voice_package_id=voice_pkg.id, video_package_id=video_pkg.id, storage_key="artifacts/music/master.mp3", scene_count=1, duration_ms=5000, quality_score=0.96)
    db.add(music_pkg)
    db.commit()

    # Thumbnail Job
    thumb_job = ThumbnailJob(
        id=uuid.uuid4(),
        script_package_id=script_pkg.id,
        image_package_id=img_pkg.id,
        video_package_id=video_pkg.id,
        subtitle_package_id=sub_pkg.id,
        music_package_id=music_pkg.id,
        provider="template",
        status="PROCESSING",
        stage="VALIDATING"
    )
    db.add(thumb_job)
    db.commit()

    # Process job
    await process_thumbnail_job(db, thumb_job)

    db.refresh(thumb_job)
    assert thumb_job.status == "SUCCESS"
    assert thumb_job.stage == "COMPLETED"

    # Assert ThumbnailPackage
    assert len(thumb_job.packages) == 1
    pkg = thumb_job.packages[0]
    assert pkg.version == 1
    assert pkg.variant_count == 3
    assert pkg.primary_thumbnail_id is not None
    assert pkg.package_manifest is not None
    assert pkg.package_manifest["package_type"] == "ThumbnailPackage"
    
    # Assert ThumbnailVariant & ThumbnailScore
    assert len(pkg.variants) == 3
    selected_var = next(v for v in pkg.variants if v.is_selected)
    assert selected_var.score is not None
    assert selected_var.score.heuristic_score > 0.0

    # Assert ThumbnailAnalysis & ThumbnailExperiment
    assert pkg.analysis is not None
    assert pkg.analysis.contrast_ratio >= 4.5
    assert len(pkg.experiments) == 1

    # Assert ThumbnailVersion
    assert len(pkg.versions) == 1
    assert pkg.versions[0].lineage_action == "INITIAL"


# 7. API Routing & Endpoints Tests
def test_api_thumbnail_routes(client, db):
    res_job = ResearchJob(id=uuid.uuid4(), topic="API Thumbnails", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="API Thumbnails", summary="Summary API")
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

    # 1. POST /v1/thumbnails (create)
    resp = client.post("/v1/thumbnails", json={
        "script_package_id": str(script_pkg.id),
        "image_package_id": str(img_pkg.id),
        "video_package_id": str(video_pkg.id),
        "provider": "template",
        "priority": 1
    })
    assert resp.status_code == 200
    job_data = resp.json()
    job_id = job_data["id"]
    assert job_data["status"] == "QUEUED"

    # 2. GET /v1/thumbnails (list)
    resp = client.get("/v1/thumbnails")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 3. GET /v1/thumbnails/metrics (metrics)
    resp = client.get("/v1/thumbnails/metrics")
    assert resp.status_code == 200
    assert resp.json()["jobs_queued"] >= 1

    # 4. GET /v1/thumbnails/{id} (detail)
    resp = client.get(f"/v1/thumbnails/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id

    # 5. Delete job
    resp = client.delete(f"/v1/thumbnails/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


# 8. Regenerate & Score Endpoints Tests
def test_api_thumbnail_regenerate_and_score(client, db):
    res_job = ResearchJob(id=uuid.uuid4(), topic="Regen Test", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="Regen Test", summary="Summary Regen")
    db.add(kp)
    db.commit()

    script_job = ScriptJob(id=uuid.uuid4(), knowledge_package_id=kp.id, provider="mock", platform="youtube", status="SUCCESS")
    db.add(script_job)
    db.commit()

    script_pkg = ScriptPackage(id=uuid.uuid4(), job_id=script_job.id, knowledge_package_id=kp.id, title="Title", platform="youtube", language="en", hook="H", problem="P", story="S", solution="Sol", cta="C", narration="Regen text.", scene_breakdown=[{"scene_number": 1, "duration": 4.0}])
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

    # Thumbnail Job and ThumbnailPackage
    thumb_job = ThumbnailJob(
        id=uuid.uuid4(), script_package_id=script_pkg.id, image_package_id=img_pkg.id, video_package_id=video_pkg.id,
        provider="template", status="SUCCESS", stage="COMPLETED"
    )
    db.add(thumb_job)
    db.commit()

    os.makedirs("artifacts/thumbnails", exist_ok=True)
    thumb_p = "artifacts/thumbnails/test_route_primary.png"
    with open(thumb_p, "wb") as f: f.write(b"PRIMARY")

    pkg = ThumbnailPackage(
        id=uuid.uuid4(), job_id=thumb_job.id, script_package_id=script_pkg.id, image_package_id=img_pkg.id, video_package_id=video_pkg.id,
        variant_count=1, version=1, quality_score=0.94
    )
    db.add(pkg)
    db.commit()

    asset = ThumbnailAsset(id=uuid.uuid4(), storage_key=thumb_p, width=1280, height=720, format="png")
    db.add(asset)
    db.commit()

    variant = ThumbnailVariant(
        id=uuid.uuid4(), thumbnail_package_id=pkg.id, thumbnail_asset_id=asset.id,
        variant_name="Variant 1", scene_number=1, primary_hook="HOOK", layout_type="left_focus", is_selected=True
    )
    db.add(variant)
    db.commit()

    pkg.primary_thumbnail_id = variant.id
    pkg.selected_variant_id = variant.id
    db.add(pkg)
    db.commit()

    # 1. POST /v1/thumbnails/{id}/preview
    resp = client.post(f"/v1/thumbnails/{thumb_job.id}/preview")
    assert resp.status_code == 200

    # 2. POST /v1/thumbnails/{id}/score
    resp = client.post(f"/v1/thumbnails/{thumb_job.id}/score")
    assert resp.status_code == 200

    # 3. POST /v1/thumbnails/{id}/regenerate
    resp = client.post(f"/v1/thumbnails/{thumb_job.id}/regenerate?layout_type=centered")
    assert resp.status_code == 200
    assert resp.json()["version"] == 2
