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
    SceneVoice,
    VideoJob,
    VideoPackage,
    SubtitleJob,
    SubtitlePackage,
    MusicJob,
    MusicPackage,
    SceneMusic,
    MusicAsset,
    MusicTrack,
    MusicCue,
    AudioTimelineEvent,
    AudioAnalysis,
    AudioMixProfile,
    MusicVersion
)
from brain.agents.music_agent import (
    is_valid_transition,
    is_transient_error,
    process_music_job,
    validate_audio_mix
)
from providers.music.registry import music_registry
from providers.music.library import LocalLibraryMusicProvider
from providers.music.mock import MockMusicProvider


# 1. State Transition Matrix Tests
def test_music_state_transitions():
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
def test_music_error_classification():
    assert is_transient_error("Audio DSP subprocess busy: connection timeout") is True
    assert is_transient_error("HTTP 429: Rate limit exceeded") is True
    assert is_transient_error("ValueError: Empty audio track") is False


# 3. Provider Registry & Capability Inspection
def test_music_provider_registry():
    lib_prov = music_registry.get_provider("library")
    assert isinstance(lib_prov, LocalLibraryMusicProvider)
    assert lib_prov.supports_ducking() is True

    mock_prov = music_registry.get_provider("mock")
    assert isinstance(mock_prov, MockMusicProvider)
    assert mock_prov.supports_normalization() is True


# 4. Library Track Selection & Cue Mapping Tests
@pytest.mark.asyncio
async def test_music_track_selection():
    provider = LocalLibraryMusicProvider()
    scene_inputs = [
        {"scene_number": 1, "duration_ms": 5000, "timeline_start_ms": 0, "timeline_end_ms": 5000},
        {"scene_number": 2, "duration_ms": 6000, "timeline_start_ms": 5000, "timeline_end_ms": 11000}
    ]

    mapped = await provider.select_music(None, scene_inputs)
    assert len(mapped) == 2
    assert mapped[0]["scene_number"] == 1
    assert mapped[0]["cue"]["cue_purpose"] == "intro"
    assert mapped[1]["cue"]["cue_purpose"] == "outro"
    assert mapped[0]["track_name"] is not None


# 5. Quality Gate Rules Tests
def test_music_quality_gates():
    os.makedirs("artifacts/music", exist_ok=True)
    temp_master = "artifacts/music/test_gate_master.mp3"
    with open(temp_master, "wb") as f: f.write(b"AUDIO")

    profile = AudioMixProfile(target_lufs=-14.0, true_peak_db=-1.0)
    mix_res = {"master_path": temp_master}
    analysis = {"peak_db": -1.2, "lufs": -14.1}

    # Should pass
    validate_audio_mix(mix_res, analysis, profile)

    # 1. Missing master file
    with pytest.raises(ValueError, match="Master mixed MP3/WAV file missing"):
        validate_audio_mix({"master_path": "invalid/path.mp3"}, analysis, profile)

    # 2. Clipping (> -0.1 dBFS)
    bad_analysis = {"peak_db": 0.5, "lufs": -14.0}
    with pytest.raises(ValueError, match="Audio clipping detected"):
        validate_audio_mix(mix_res, bad_analysis, profile)

    # 3. LUFS deviation (> 3.0 LUFS)
    bad_lufs = {"peak_db": -1.2, "lufs": -8.0}
    with pytest.raises(ValueError, match="LUFS deviation"):
        validate_audio_mix(mix_res, bad_lufs, profile)


# 6. Background Music Job Processing Tests
@pytest.mark.asyncio
async def test_music_agent_job_processing(db):
    res_job = ResearchJob(id=uuid.uuid4(), topic="Music Tech", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="Music Tech", summary="Music summary")
    db.add(kp)
    db.commit()

    script_job = ScriptJob(id=uuid.uuid4(), knowledge_package_id=kp.id, provider="mock", platform="youtube", status="SUCCESS")
    db.add(script_job)
    db.commit()

    script_pkg = ScriptPackage(
        id=uuid.uuid4(), job_id=script_job.id, knowledge_package_id=kp.id,
        title="Music 101", platform="youtube", language="en", hook="Hook", problem="Problem",
        story="Story", solution="Solution", cta="CTA", narration="Narration text.",
        scene_breakdown=[{"scene_number": 1, "narration": "Music demonstration scene", "duration": 5.0}]
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

    temp_voice = "artifacts/music/test_narration.mp3"
    with open(temp_voice, "wb") as f: f.write(b"MP3")

    voice_pkg = VoicePackage(
        id=uuid.uuid4(), job_id=voice_job.id, script_package_id=script_pkg.id,
        platform="youtube", language="en", total_scenes=1, overall_duration_ms=5000, quality_score=0.9
    )
    db.add(voice_pkg)
    db.flush()

    sv_voice = SceneVoice(
        id=uuid.uuid4(), voice_package_id=voice_pkg.id, scene_number=1, duration_ms=5000,
        narration="Music demonstration scene text", local_path=temp_voice, storage_key="audio/test_narration.mp3",
        voice_id="Matthew", provider="mock", model="MockSpeech", language="en"
    )
    db.add(sv_voice)
    db.commit()

    video_job = VideoJob(id=uuid.uuid4(), script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, renderer="mock", status="SUCCESS")
    db.add(video_job)
    db.commit()

    video_pkg = VideoPackage(id=uuid.uuid4(), job_id=video_job.id, script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, platform="youtube", resolution="1920x1080", aspect_ratio="16:9", duration_ms=5000, storage_key="video/outputs/output_1.mp4", version=1, quality_score=0.9)
    db.add(video_pkg)
    db.commit()

    # Music Job
    music_job = MusicJob(
        id=uuid.uuid4(),
        script_package_id=script_pkg.id,
        voice_package_id=voice_pkg.id,
        video_package_id=video_pkg.id,
        provider="library",
        status="PROCESSING",
        stage="VALIDATING"
    )
    db.add(music_job)
    db.commit()

    # Process job
    await process_music_job(db, music_job)

    db.refresh(music_job)
    assert music_job.status == "SUCCESS"
    assert music_job.stage == "COMPLETED"

    # Assert MusicPackage & Audio Stems
    assert len(music_job.packages) == 1
    pkg = music_job.packages[0]
    assert pkg.version == 1
    assert pkg.scene_count == 1
    assert pkg.separated_music_track is not None
    assert pkg.narration_track is not None
    assert pkg.package_manifest is not None
    assert pkg.package_manifest["package_type"] == "MusicPackage"
    
    # Assert SceneMusic & MusicCue
    assert len(pkg.scene_musics) == 1
    sc_m = pkg.scene_musics[0]
    assert sc_m.scene_number == 1
    assert len(sc_m.cues) == 1

    # Assert AudioTimelineEvent & AudioAnalysis
    assert len(pkg.timeline_events) == 1
    assert pkg.analysis is not None
    assert pkg.analysis.lufs == -14.1

    # Assert MusicVersion
    assert len(pkg.versions) == 1
    assert pkg.versions[0].lineage_action == "INITIAL"


# 7. API Routing & Endpoints Tests
def test_api_music_routes(client, db):
    res_job = ResearchJob(id=uuid.uuid4(), topic="API Music", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="API Music", summary="Summary API")
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

    # 1. POST /v1/music (create)
    resp = client.post("/v1/music", json={
        "script_package_id": str(script_pkg.id),
        "voice_package_id": str(voice_pkg.id),
        "video_package_id": str(video_pkg.id),
        "provider": "library",
        "priority": 1
    })
    assert resp.status_code == 200
    job_data = resp.json()
    job_id = job_data["id"]
    assert job_data["status"] == "QUEUED"

    # 2. GET /v1/music (list)
    resp = client.get("/v1/music")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 3. GET /v1/music/metrics (metrics)
    resp = client.get("/v1/music/metrics")
    assert resp.status_code == 200
    assert resp.json()["jobs_queued"] >= 1

    # 4. GET /v1/music/{id} (detail)
    resp = client.get(f"/v1/music/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id

    # 5. Delete job
    resp = client.delete(f"/v1/music/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


# 8. Remix & Normalize Endpoints Tests
def test_api_music_remix_and_normalize(client, db):
    res_job = ResearchJob(id=uuid.uuid4(), topic="Remix Test", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="Remix Test", summary="Summary Remix")
    db.add(kp)
    db.commit()

    script_job = ScriptJob(id=uuid.uuid4(), knowledge_package_id=kp.id, provider="mock", platform="youtube", status="SUCCESS")
    db.add(script_job)
    db.commit()

    script_pkg = ScriptPackage(id=uuid.uuid4(), job_id=script_job.id, knowledge_package_id=kp.id, title="Title", platform="youtube", language="en", hook="H", problem="P", story="S", solution="Sol", cta="C", narration="Remix text.", scene_breakdown=[{"scene_number": 1, "duration": 4.0}])
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

    # Music Job and MusicPackage
    music_job = MusicJob(
        id=uuid.uuid4(), script_package_id=script_pkg.id, voice_package_id=voice_pkg.id, video_package_id=video_pkg.id,
        provider="library", status="SUCCESS", stage="COMPLETED"
    )
    db.add(music_job)
    db.commit()

    os.makedirs("artifacts/music", exist_ok=True)
    master_p = "artifacts/music/test_route_master.mp3"
    stem_p = "artifacts/music/test_route_music_stem.mp3"
    with open(master_p, "wb") as f: f.write(b"MASTER")
    with open(stem_p, "wb") as f: f.write(b"STEM")

    pkg = MusicPackage(
        id=uuid.uuid4(), job_id=music_job.id, script_package_id=script_pkg.id, voice_package_id=voice_pkg.id, video_package_id=video_pkg.id,
        storage_key=master_p, separated_music_track=stem_p, scene_count=1, duration_ms=4000, version=1, quality_score=0.96
    )
    db.add(pkg)
    db.commit()

    sc_m = SceneMusic(
        id=uuid.uuid4(), music_package_id=pkg.id, scene_number=1, track_name="Epic Horizons",
        genre="Cinematic", mood="Inspiring", energy="High", tempo_bpm=128, musical_key="D Minor",
        start_time_ms=0, end_time_ms=4000, music_volume_db=-14.0, narration_ducking_db=-12.0
    )
    db.add(sc_m)
    db.commit()

    # 1. POST /v1/music/{id}/preview
    resp = client.post(f"/v1/music/{music_job.id}/preview")
    assert resp.status_code == 200

    # 2. POST /v1/music/{id}/remix
    resp = client.post(f"/v1/music/{music_job.id}/remix?music_volume_db=-16.0&ducking_level_db=-14.0")
    assert resp.status_code == 200
    assert resp.json()["version"] == 2
