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
    SubtitleJob,
    SubtitlePackage,
    SceneSubtitle,
    CaptionSegment,
    SubtitleTrack,
    SubtitleVersion,
    CaptionStyleProfile
)
from brain.agents.subtitle_agent import (
    is_valid_transition,
    is_transient_error,
    process_subtitle_job,
    validate_subtitle_segments
)
from providers.subtitle.registry import subtitle_registry
from providers.subtitle.alignment import AlignmentSubtitleProvider, format_timestamp_srt, format_timestamp_vtt, format_timestamp_ass
from providers.subtitle.mock import MockSubtitleProvider


# 1. State Transition Matrix Tests
def test_subtitle_state_transitions():
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
def test_subtitle_error_classification():
    assert is_transient_error("Subprocess thread busy: connection timeout") is True
    assert is_transient_error("HTTP 429: Rate limit exceeded") is True
    assert is_transient_error("ValueError: Empty caption text") is False


# 3. Provider Registry & Capability Inspection
def test_subtitle_provider_registry():
    align_prov = subtitle_registry.get_provider("alignment")
    assert isinstance(align_prov, AlignmentSubtitleProvider)
    assert align_prov.supports_alignment() is True

    mock_prov = subtitle_registry.get_provider("mock")
    assert isinstance(mock_prov, MockSubtitleProvider)
    assert mock_prov.supports_style() is True


# 4. Timestamp Formatter Tests
def test_subtitle_timestamp_formatters():
    # 1 hour 2 mins 3 secs 450 ms = 3723450 ms
    ms = 3723450
    assert format_timestamp_srt(ms) == "01:02:03,450"
    assert format_timestamp_vtt(ms) == "01:02:03.450"
    assert format_timestamp_ass(ms) == "1:02:03.45"


# 5. Smart Segmentation Engine Tests
@pytest.mark.asyncio
async def test_subtitle_segmentation_rules():
    provider = AlignmentSubtitleProvider()
    text = "Artificial intelligence automated publishing platform creates video content seamlessly."
    
    words = [
        {"word": w, "start_ms": idx * 400, "end_ms": (idx + 1) * 400}
        for idx, w in enumerate(text.split())
    ]
    
    segments = await provider.segment(text, words, {"max_cpl": 35, "max_lines": 2})
    assert len(segments) >= 1
    
    for seg in segments:
        assert "text" in seg
        assert "reading_speed_cps" in seg
        assert "reading_speed_cpl" in seg
        assert "reading_speed_wpm" in seg
        assert seg["reading_speed_cps"] > 0


# 6. Quality Gate Rules Tests
def test_subtitle_quality_gates():
    valid_segments = [
        {
            "segment_number": 1,
            "start_ms": 0,
            "end_ms": 3000,
            "text": "Valid caption text",
            "reading_speed_cps": 12.0
        },
        {
            "segment_number": 2,
            "start_ms": 3000,
            "end_ms": 6000,
            "text": "Second caption block",
            "reading_speed_cps": 14.0
        }
    ]

    # Should pass
    validate_subtitle_segments(valid_segments, video_duration_ms=7000)

    # 1. Empty caption text
    bad = [dict(valid_segments[0], text="   ")]
    with pytest.raises(ValueError, match="Empty caption"):
        validate_subtitle_segments(bad)

    # 2. Caption flash (< 200ms)
    bad = [dict(valid_segments[0], end_ms=100)]
    with pytest.raises(ValueError, match="Caption flash detected"):
        validate_subtitle_segments(bad)

    # 3. Excessive caption duration (> 7000ms)
    bad = [dict(valid_segments[0], end_ms=8000)]
    with pytest.raises(ValueError, match="Long on-screen caption"):
        validate_subtitle_segments(bad)

    # 4. Excessive CPS (> 30 CPS)
    bad = [dict(valid_segments[0], reading_speed_cps=35.0)]
    with pytest.raises(ValueError, match="Excessive reading speed"):
        validate_subtitle_segments(bad)

    # 5. Overlapping timings
    bad = [
        valid_segments[0],
        dict(valid_segments[1], start_ms=2000) # Overlaps with 3000ms
    ]
    with pytest.raises(ValueError, match="Timing overlap"):
        validate_subtitle_segments(bad)


# 7. Format Exporter Tests (SRT, WebVTT, ASS, JSON)
@pytest.mark.asyncio
async def test_subtitle_export_formats():
    provider = AlignmentSubtitleProvider()
    segments = [
        {
            "segment_number": 1,
            "start_ms": 0,
            "end_ms": 3000,
            "text": "Welcome to AATES Subtitles."
        }
    ]

    os.makedirs("artifacts/subtitles", exist_ok=True)
    srt_p = "artifacts/subtitles/test_export.srt"
    vtt_p = "artifacts/subtitles/test_export.vtt"
    ass_p = "artifacts/subtitles/test_export.ass"
    json_p = "artifacts/subtitles/test_export.json"

    await provider.export(segments, "srt", srt_p)
    await provider.export(segments, "vtt", vtt_p)
    await provider.export(segments, "ass", ass_p)
    await provider.export(segments, "json", json_p)

    assert os.path.exists(srt_p)
    assert os.path.exists(vtt_p)
    assert os.path.exists(ass_p)
    assert os.path.exists(json_p)

    with open(srt_p, "r", encoding="utf-8") as f:
        assert "00:00:00,000 --> 00:00:03,000" in f.read()

    with open(vtt_p, "r", encoding="utf-8") as f:
        assert "WEBVTT" in f.read()


# 8. Background Subtitle Job Processing Tests
@pytest.mark.asyncio
async def test_subtitle_agent_job_processing(db):
    res_job = ResearchJob(id=uuid.uuid4(), topic="Subtitles Tech", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="Subtitles Tech", summary="Subtitles summary")
    db.add(kp)
    db.commit()

    script_job = ScriptJob(id=uuid.uuid4(), knowledge_package_id=kp.id, provider="mock", platform="youtube", status="SUCCESS")
    db.add(script_job)
    db.commit()

    script_pkg = ScriptPackage(
        id=uuid.uuid4(), job_id=script_job.id, knowledge_package_id=kp.id,
        title="Subtitles 101", platform="youtube", language="en", hook="Hook", problem="Problem",
        story="Story", solution="Solution", cta="CTA", narration="Narration text.",
        scene_breakdown=[{"scene_number": 1, "narration": "Subtitle demonstration scene", "duration": 5.0}]
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

    temp_voice = "artifacts/subtitles/test_narration.mp3"
    with open(temp_voice, "wb") as f: f.write(b"MP3")

    voice_pkg = VoicePackage(
        id=uuid.uuid4(), job_id=voice_job.id, script_package_id=script_pkg.id,
        platform="youtube", language="en", total_scenes=1, overall_duration_ms=5000, quality_score=0.9
    )
    db.add(voice_pkg)
    db.flush()

    sv_voice = SceneVoice(
        id=uuid.uuid4(), voice_package_id=voice_pkg.id, scene_number=1, duration_ms=5000,
        narration="Subtitle demonstration scene text", local_path=temp_voice, storage_key="audio/test_narration.mp3",
        voice_id="Matthew", provider="mock", model="MockSpeech", language="en",
        word_alignment=[
            {"word": "Subtitle", "start_ms": 0, "end_ms": 1000},
            {"word": "demonstration", "start_ms": 1000, "end_ms": 3000},
            {"word": "scene", "start_ms": 3000, "end_ms": 5000}
        ]
    )
    db.add(sv_voice)
    db.commit()

    # Video package
    video_job = VideoJob(id=uuid.uuid4(), script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, renderer="mock", status="SUCCESS")
    db.add(video_job)
    db.commit()

    video_pkg = VideoPackage(id=uuid.uuid4(), job_id=video_job.id, script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, platform="youtube", resolution="1920x1080", aspect_ratio="16:9", duration_ms=5000, storage_key="video/outputs/output_1.mp4", version=1, quality_score=0.9)
    db.add(video_pkg)
    db.commit()

    # Subtitle Job
    sub_job = SubtitleJob(
        id=uuid.uuid4(),
        voice_package_id=voice_pkg.id,
        video_package_id=video_pkg.id,
        provider="alignment",
        status="PROCESSING",
        stage="VALIDATING"
    )
    db.add(sub_job)
    db.commit()

    # Process job
    await process_subtitle_job(db, sub_job)

    db.refresh(sub_job)
    assert sub_job.status == "SUCCESS"
    assert sub_job.stage == "COMPLETED"

    # Assert SubtitlePackage
    assert len(sub_job.packages) == 1
    pkg = sub_job.packages[0]
    assert pkg.version == 1
    assert pkg.scene_count == 1
    assert pkg.package_manifest is not None
    assert pkg.package_manifest["package_type"] == "SubtitlePackage"
    
    # Assert SceneSubtitle & CaptionSegment
    assert len(pkg.scene_subtitles) == 1
    sc_sub = pkg.scene_subtitles[0]
    assert sc_sub.scene_number == 1
    assert len(sc_sub.segments) >= 1

    # Assert SubtitleTrack
    assert len(pkg.tracks) == 1
    track = pkg.tracks[0]
    assert track.srt_path.endswith(".srt")
    assert os.path.exists(track.srt_path)

    # Assert SubtitleVersion
    assert len(pkg.versions) == 1
    assert pkg.versions[0].lineage_action == "INITIAL"


# 9. API Routing & Endpoints Tests
def test_api_subtitles_routes(client, db):
    res_job = ResearchJob(id=uuid.uuid4(), topic="API Subtitles", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="API Subtitles", summary="Summary API")
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

    # 1. POST /v1/subtitles (create)
    resp = client.post("/v1/subtitles", json={
        "voice_package_id": str(voice_pkg.id),
        "video_package_id": str(video_pkg.id),
        "language": "en",
        "provider": "alignment",
        "priority": 1
    })
    assert resp.status_code == 200
    job_data = resp.json()
    job_id = job_data["id"]
    assert job_data["status"] == "QUEUED"

    # 2. GET /v1/subtitles (list)
    resp = client.get("/v1/subtitles")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 3. GET /v1/subtitles/metrics (metrics)
    resp = client.get("/v1/subtitles/metrics")
    assert resp.status_code == 200
    assert resp.json()["jobs_queued"] >= 1

    # 4. GET /v1/subtitles/{id} (detail)
    resp = client.get(f"/v1/subtitles/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id

    # 5. Delete job
    resp = client.delete(f"/v1/subtitles/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


# 10. Re-segmentation & Export Download Endpoint Tests
def test_api_subtitles_export_and_regenerate(client, db):
    res_job = ResearchJob(id=uuid.uuid4(), topic="Export Test", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="Export Test", summary="Summary Export")
    db.add(kp)
    db.commit()

    script_job = ScriptJob(id=uuid.uuid4(), knowledge_package_id=kp.id, provider="mock", platform="youtube", status="SUCCESS")
    db.add(script_job)
    db.commit()

    script_pkg = ScriptPackage(id=uuid.uuid4(), job_id=script_job.id, knowledge_package_id=kp.id, title="Title", platform="youtube", language="en", hook="H", problem="P", story="S", solution="Sol", cta="C", narration="Export text.", scene_breakdown=[{"scene_number": 1, "duration": 4.0}])
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

    # Subtitle Job and SubtitlePackage
    sub_job = SubtitleJob(
        id=uuid.uuid4(), voice_package_id=voice_pkg.id, video_package_id=video_pkg.id,
        provider="alignment", status="SUCCESS", stage="COMPLETED"
    )
    db.add(sub_job)
    db.commit()

    pkg = SubtitlePackage(
        id=uuid.uuid4(), job_id=sub_job.id, voice_package_id=voice_pkg.id, video_package_id=video_pkg.id,
        language="en", caption_style="YouTube", subtitle_formats=["srt", "vtt", "ass", "json"],
        scene_count=1, total_captions=1, total_words=4, version=1, quality_score=0.95
    )
    db.add(pkg)
    db.commit()

    os.makedirs("artifacts/subtitles", exist_ok=True)
    srt_p = "artifacts/subtitles/test_route_export.srt"
    vtt_p = "artifacts/subtitles/test_route_export.vtt"
    ass_p = "artifacts/subtitles/test_route_export.ass"
    json_p = "artifacts/subtitles/test_route_export.json"

    with open(srt_p, "w", encoding="utf-8") as f: f.write("1\n00:00:00,000 --> 00:00:04,000\nExport text.\n")
    with open(vtt_p, "w", encoding="utf-8") as f: f.write("WEBVTT\n1\n00:00:00.000 --> 00:00:04.000\nExport text.\n")
    with open(ass_p, "w", encoding="utf-8") as f: f.write("[Events]\n")
    with open(json_p, "w", encoding="utf-8") as f: f.write("[]")

    sc_sub = SceneSubtitle(
        id=uuid.uuid4(), subtitle_package_id=pkg.id, scene_number=1, caption_text="Export text.",
        word_timings=[{"word": "Export", "start_ms": 0, "end_ms": 2000}, {"word": "text.", "start_ms": 2000, "end_ms": 4000}],
        sentence_timings=[{"sentence": "Export text.", "start_ms": 0, "end_ms": 4000}],
        reading_speed_wpm=120.0, reading_speed_cps=10.0, reading_speed_cpl=12.0
    )
    db.add(sc_sub)
    db.commit()

    track = SubtitleTrack(
        id=uuid.uuid4(), subtitle_package_id=pkg.id, track_name="Standard Track",
        language="en", srt_path=srt_p, webvtt_path=vtt_p, ass_path=ass_p, json_timeline_path=json_p
    )
    db.add(track)
    db.commit()

    # 1. POST /v1/subtitles/{id}/export?format_type=srt
    resp = client.post(f"/v1/subtitles/{sub_job.id}/export?format_type=srt")
    assert resp.status_code == 200

    # 2. POST /v1/subtitles/{id}/regenerate
    resp = client.post(f"/v1/subtitles/{sub_job.id}/regenerate?max_cpl=37")
    assert resp.status_code == 200
    assert resp.json()["version"] == 2
