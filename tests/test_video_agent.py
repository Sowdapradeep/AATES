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
    SceneVideo,
    TimelineEvent,
    VideoVersion,
    RenderProfile
)
from brain.agents.video_agent import (
    is_valid_transition,
    is_transient_error,
    process_video_job,
    validate_timeline_nodes,
    validate_rendered_video
)
from providers.video.registry import video_registry
from providers.video.mock import MockVideoProvider
from providers.video.ffmpeg import FFmpegVideoProvider

# 1. State Transition Matrix Tests
def test_video_state_transitions():
    assert is_valid_transition("QUEUED", "PROCESSING") is True
    assert is_valid_transition("QUEUED", "CANCELLED") is True
    assert is_valid_transition("PROCESSING", "SUCCESS") is True
    assert is_valid_transition("PROCESSING", "RETRYING") is True
    assert is_valid_transition("PROCESSING", "FAILED") is True
    assert is_valid_transition("FAILED", "QUEUED") is True
    assert is_valid_transition("CANCELLED", "QUEUED") is True
    
    assert is_valid_transition("SUCCESS", "PROCESSING") is False
    assert is_valid_transition("FAILED", "SUCCESS") is False


# 2. Transient Error Classification
def test_video_error_classification():
    assert is_transient_error("Subprocess thread busy: connection timeout") is True
    assert is_transient_error("HTTP 429: Rate limit exceeded") is True
    assert is_transient_error("ValueError: Invalid frame rate setting") is False


# 3. Provider Registry & Capabilities Verification
def test_video_provider_registry():
    mock_prov = video_registry.get_provider("mock")
    assert isinstance(mock_prov, MockVideoProvider)
    assert mock_prov.supports_gpu() is True
    
    ffmpeg_prov = video_registry.get_provider("ffmpeg")
    assert isinstance(ffmpeg_prov, FFmpegVideoProvider)
    assert ffmpeg_prov.supports_motion() is True
    assert ffmpeg_prov.supports_transitions() is True


# 4. Timeline Engine & Validation Checks
def test_video_timeline_validation():
    # Setup temporary image and audio file paths
    os.makedirs("artifacts/video", exist_ok=True)
    temp_img = "artifacts/video/test_scene_img.jpg"
    temp_voice = "artifacts/video/test_scene_voice.mp3"
    with open(temp_img, "wb") as f: f.write(b"JPG")
    with open(temp_voice, "wb") as f: f.write(b"MP3")

    valid_nodes = [
        {
            "scene_number": 1,
            "timeline_start_ms": 0,
            "timeline_end_ms": 4000,
            "duration_ms": 4000,
            "image_path": temp_img,
            "voice_path": temp_voice
        },
        {
            "scene_number": 2,
            "timeline_start_ms": 4000,
            "timeline_end_ms": 9000,
            "duration_ms": 5000,
            "image_path": temp_img,
            "voice_path": temp_voice
        }
    ]
    
    # Should pass
    validate_timeline_nodes(valid_nodes)

    # 1. Missing image asset file
    bad = [dict(valid_nodes[0], image_path="artifacts/video/non_existent.jpg")]
    with pytest.raises(ValueError, match="Missing image asset"):
        validate_timeline_nodes(bad)

    # 2. Negative duration
    bad = [dict(valid_nodes[0], duration_ms=-1000)]
    with pytest.raises(ValueError, match="Invalid duration"):
        validate_timeline_nodes(bad)

    # 3. Gap detected
    bad = [
        valid_nodes[0],
        dict(valid_nodes[1], timeline_start_ms=5000) # Gap from 4000 to 5000
    ]
    with pytest.raises(ValueError, match="Gap detected"):
        validate_timeline_nodes(bad)

    # 4. Overlap detected
    bad = [
        valid_nodes[0],
        dict(valid_nodes[1], timeline_start_ms=3000) # Overlap
    ]
    with pytest.raises(ValueError, match="Overlap detected"):
        validate_timeline_nodes(bad)


# 5. Quality Gate Rules Checks
def test_video_quality_gates():
    os.makedirs("artifacts/video", exist_ok=True)
    temp_file = "artifacts/video/test_scene_gate.mp4"
    with open(temp_file, "wb") as f:
        f.write(b"MP4")

    valid_package = {
        "local_path": temp_file,
        "metadata_artifacts": {"keyframes": [0, 4000]},
        "quality_score": 0.88
    }
    
    validate_rendered_video(valid_package)

    # 1. Missing output video file
    bad = dict(valid_package, local_path="artifacts/video/does_not_exist.mp4")
    with pytest.raises(ValueError, match="Output MP4 video file is missing"):
        validate_rendered_video(bad)

    # 2. Missing metadata artifacts
    bad = dict(valid_package, metadata_artifacts=None)
    with pytest.raises(ValueError, match="Missing rendering keyframes"):
        validate_rendered_video(bad)

    # 3. Low Quality Score
    bad = dict(valid_package, quality_score=0.6)
    with pytest.raises(ValueError, match="falls below threshold 0.7"):
        validate_rendered_video(bad)


# 6. Database Operations & Version Lineage Tests
@pytest.mark.asyncio
async def test_video_agent_job_processing(db):
    # Setup inputs chain
    res_job = ResearchJob(id=uuid.uuid4(), topic="SpaceX Mars", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="SpaceX Mars", summary="Mars summary")
    db.add(kp)
    db.commit()

    script_job = ScriptJob(id=uuid.uuid4(), knowledge_package_id=kp.id, provider="mock", platform="youtube", status="SUCCESS")
    db.add(script_job)
    db.commit()

    script_pkg = ScriptPackage(
        id=uuid.uuid4(), job_id=script_job.id, knowledge_package_id=kp.id,
        title="Going to Mars", platform="youtube", language="en", hook="Hook text", problem="Problem text",
        story="Story text", solution="Solution text", cta="CTA text", narration="Narration text.",
        scene_breakdown=[{"scene_number": 1, "narration": "Rover landing scene", "duration": 5.0}]
    )
    db.add(script_pkg)
    db.commit()

    # Image package setup
    img_job = ImageJob(id=uuid.uuid4(), script_package_id=script_pkg.id, provider="mock", status="SUCCESS")
    db.add(img_job)
    db.commit()

    os.makedirs("artifacts/video", exist_ok=True)
    temp_img = "artifacts/video/test_mars_img.jpg"
    with open(temp_img, "wb") as f: f.write(b"JPG")

    img_pkg = ImagePackage(
        id=uuid.uuid4(), job_id=img_job.id, script_package_id=script_pkg.id,
        platform="youtube", resolution="1920x1080", aspect_ratio="16:9", style_preset="Photorealistic", quality_score=0.9
    )
    db.add(img_pkg)
    db.flush()

    from core.database.models import SceneAsset
    sa = SceneAsset(
        id=uuid.uuid4(), image_package_id=img_pkg.id, scene_number=1, duration=5.0,
        prompt="Mars rover landing", provider="mock", model="mock-titan", aspect_ratio="16:9",
        resolution="1920x1080", local_path=temp_img, storage_key="images/test_mars_img.jpg"
    )
    db.add(sa)
    db.commit()

    # Voice package setup
    voice_job = VoiceJob(id=uuid.uuid4(), script_package_id=script_pkg.id, provider="mock", voice_model="MockSpeech", language="en", status="SUCCESS")
    db.add(voice_job)
    db.commit()

    temp_voice = "artifacts/video/test_mars_voice.mp3"
    with open(temp_voice, "wb") as f: f.write(b"MP3")

    voice_pkg = VoicePackage(
        id=uuid.uuid4(), job_id=voice_job.id, script_package_id=script_pkg.id,
        platform="youtube", language="en", total_scenes=1, overall_duration_ms=5000, quality_score=0.9
    )
    db.add(voice_pkg)
    db.flush()

    sv_voice = SceneVoice(
        id=uuid.uuid4(), voice_package_id=voice_pkg.id, scene_number=1, duration_ms=5000,
        narration="Rover landing scene", local_path=temp_voice, storage_key="audio/test_mars_voice.mp3",
        voice_id="Matthew", provider="mock", model="MockSpeech", language="en"
    )
    db.add(sv_voice)
    db.commit()

    # Video job setup
    video_job = VideoJob(
        id=uuid.uuid4(),
        script_package_id=script_pkg.id,
        image_package_id=img_pkg.id,
        voice_package_id=voice_pkg.id,
        renderer="mock",
        status="PROCESSING",
        stage="VALIDATING"
    )
    db.add(video_job)
    db.commit()

    # Run processing
    await process_video_job(db, video_job)

    db.refresh(video_job)
    assert video_job.status == "SUCCESS"
    assert video_job.stage == "COMPLETED"
    
    # Assert package details
    assert len(video_job.packages) == 1
    pkg = video_job.packages[0]
    assert pkg.version == 1
    assert pkg.duration_ms == 5000
    
    # Assert scene video and events
    assert len(pkg.assets) == 1
    sv_asset = pkg.assets[0]
    assert sv_asset.scene_number == 1
    assert sv_asset.duration_ms == 5000
    assert sv_asset.storage_key.startswith("video/clips/")
    
    # Assert TimelineEvent
    assert len(pkg.events) == 1
    event = pkg.events[0]
    assert event.start_time_ms == 0
    assert event.end_time_ms == 5000
    
    # Assert VideoVersion
    assert len(pkg.versions) == 1
    assert pkg.versions[0].version == 1
    assert pkg.versions[0].lineage_action == "INITIAL"


# 7. API Routing & Endpoints Tests
def test_api_videos_routes(client, db):
    # Setup inputs
    res_job = ResearchJob(id=uuid.uuid4(), topic="AI Code", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="AI Code", summary="Summary AI")
    db.add(kp)
    db.commit()

    script_job = ScriptJob(id=uuid.uuid4(), knowledge_package_id=kp.id, provider="mock", platform="youtube", status="SUCCESS")
    db.add(script_job)
    db.commit()

    script_pkg = ScriptPackage(
        id=uuid.uuid4(), job_id=script_job.id, knowledge_package_id=kp.id,
        title="AI Coding Tools", platform="youtube", language="en", hook="Hook", problem="Problem",
        story="Story", solution="Solution", cta="CTA", narration="Original narration.",
        scene_breakdown=[{"scene_number": 1, "narration": "Coding screen", "duration": 4.0}]
    )
    db.add(script_pkg)
    db.commit()

    # Image package
    img_job = ImageJob(id=uuid.uuid4(), script_package_id=script_pkg.id, provider="mock", status="SUCCESS")
    db.add(img_job)
    db.commit()

    img_pkg = ImagePackage(id=uuid.uuid4(), job_id=img_job.id, script_package_id=script_pkg.id, platform="youtube", resolution="1920x1080", aspect_ratio="16:9", style_preset="Photorealistic", quality_score=0.9)
    db.add(img_pkg)
    db.commit()

    # Voice package
    voice_job = VoiceJob(id=uuid.uuid4(), script_package_id=script_pkg.id, provider="mock", voice_model="MockSpeech", language="en", status="SUCCESS")
    db.add(voice_job)
    db.commit()

    voice_pkg = VoicePackage(id=uuid.uuid4(), job_id=voice_job.id, script_package_id=script_pkg.id, platform="youtube", language="en", total_scenes=1, overall_duration_ms=4000, quality_score=0.9)
    db.add(voice_pkg)
    db.commit()

    # 1. POST /v1/videos (create)
    resp = client.post("/v1/videos", json={
        "script_package_id": str(script_pkg.id),
        "image_package_id": str(img_pkg.id),
        "voice_package_id": str(voice_pkg.id),
        "renderer": "mock",
        "priority": 1
    })
    assert resp.status_code == 200
    job_data = resp.json()
    job_id = job_data["id"]
    assert job_data["status"] == "QUEUED"

    # 2. GET /v1/videos (list)
    resp = client.get("/v1/videos")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 3. GET /v1/videos/metrics (metrics)
    resp = client.get("/v1/videos/metrics")
    assert resp.status_code == 200
    metrics = resp.json()
    assert metrics["jobs_queued"] >= 1

    # 4. GET /v1/videos/{id} (detail)
    resp = client.get(f"/v1/videos/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id

    # 5. Cancel or Delete job
    resp = client.delete(f"/v1/videos/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


# 8. Render, Preview and Scene Regeneration API Tests
def test_api_videos_render_and_regenerate(client, db):
    # Setup inputs
    res_job = ResearchJob(id=uuid.uuid4(), topic="GPU Render", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="GPU Render", summary="Summary GPU")
    db.add(kp)
    db.commit()

    script_job = ScriptJob(id=uuid.uuid4(), knowledge_package_id=kp.id, provider="mock", platform="youtube", status="SUCCESS")
    db.add(script_job)
    db.commit()

    script_pkg = ScriptPackage(
        id=uuid.uuid4(), job_id=script_job.id, knowledge_package_id=kp.id,
        title="GPU Speed limits", platform="youtube", language="en", hook="Hook", problem="Problem",
        story="Story", solution="Solution", cta="CTA", narration="Narration GPU.",
        scene_breakdown=[{"scene_number": 1, "narration": "GPU chip close up", "duration": 5.0}]
    )
    db.add(script_pkg)
    db.commit()

    # Image package
    img_job = ImageJob(id=uuid.uuid4(), script_package_id=script_pkg.id, provider="mock", status="SUCCESS")
    db.add(img_job)
    db.commit()

    img_pkg = ImagePackage(id=uuid.uuid4(), job_id=img_job.id, script_package_id=script_pkg.id, platform="youtube", resolution="1920x1080", aspect_ratio="16:9", style_preset="Photorealistic", quality_score=0.9)
    db.add(img_pkg)
    db.commit()

    # Voice package
    voice_job = VoiceJob(id=uuid.uuid4(), script_package_id=script_pkg.id, provider="mock", voice_model="MockSpeech", language="en", status="SUCCESS")
    db.add(voice_job)
    db.commit()

    voice_pkg = VoicePackage(id=uuid.uuid4(), job_id=voice_job.id, script_package_id=script_pkg.id, platform="youtube", language="en", total_scenes=1, overall_duration_ms=5000, quality_score=0.9)
    db.add(voice_pkg)
    db.commit()

    # Success VideoJob and VideoPackage
    job = VideoJob(
        id=uuid.uuid4(), script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id,
        renderer="mock", status="SUCCESS", stage="COMPLETED"
    )
    db.add(job)
    db.commit()

    pkg = VideoPackage(
        id=uuid.uuid4(), job_id=job.id, script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id,
        platform="youtube", resolution="1920x1080", aspect_ratio="16:9", duration_ms=5000, storage_key="video/outputs/output_1.mp4",
        version=1, quality_score=0.9
    )
    db.add(pkg)
    db.commit()

    os.makedirs("artifacts/video", exist_ok=True)
    temp_clip = "artifacts/video/test_scene_clip_1.mp4"
    with open(temp_clip, "wb") as f: f.write(b"MP4_CLIP")

    sv = SceneVideo(
        id=uuid.uuid4(), video_package_id=pkg.id, scene_number=1, timeline_start_ms=0, timeline_end_ms=5000,
        duration_ms=5000, rendered_clip=temp_clip, storage_key="video/clips/test_scene_clip_1.mp4",
        quality_score=0.9
    )
    db.add(sv)
    db.commit()

    ver = VideoVersion(
        id=uuid.uuid4(), video_package_id=pkg.id, version=1, parent_version=None, lineage_action="INITIAL",
        assets_snapshot=[{"scene_number": 1, "rendered_clip": temp_clip, "duration_ms": 5000}]
    )
    db.add(ver)
    db.commit()

    # 1. Call POST /v1/videos/{id}/regenerate
    resp = client.post(f"/v1/videos/{job.id}/regenerate?scene_number=1")
    assert resp.status_code == 200
    pkg_data = resp.json()
    assert pkg_data["version"] == 2

    # 2. Call POST /v1/videos/{id}/preview
    resp = client.post(f"/v1/videos/{job.id}/preview")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    assert "preview_path" in resp.json()
