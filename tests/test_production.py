from fastapi.testclient import TestClient

def test_storyboard_and_shot_planning(client: TestClient) -> None:
    """Verifies that visual panels and duration plans compile successfully."""
    scene = {
        "scene_number": 1,
        "location": "Forest Woods",
        "time_of_day": "DAY",
        "weather": "RAINY",
        "lighting_mood": "dark grey",
        "characters": ["Kadamban"],
        "emotions": ["anger"],
        "props": ["umbrella"],
        "costumes": {"Kadamban": "dirty shirt"},
        "camera_intent": "close-up face zoom",
        "visual_style": "high contrast",
        "dialogues": [],
        "music_mood": "sad flute",
        "sound_effects": ["rain sounds"],
        "continuity_notes": "none",
        "rendering_hints": {}
    }
    
    # Storyboard panels generation
    res = client.post("/v1/production/storyboard", json=scene)
    assert res.status_code == 200
    assert len(res.json()) > 0
    assert res.json()[0]["scene_id"] == "scene_1"

    # Shot planner guidelines check
    res_shots = client.post("/v1/production/shots", json=scene)
    assert res_shots.status_code == 200
    assert len(res_shots.json()) > 0
    assert res_shots.json()[0]["shot_id"] == "shot_1_1"

def test_voice_and_music_generation(client: TestClient) -> None:
    """Verifies speech synthesis and theme generators logs metrics correctly."""
    voice_res = client.post(
        "/v1/production/voice",
        json={
            "scene_id": "scene_1",
            "episode_id": "00000000-0000-0000-0000-000000000001",
            "universe_id": "00000000-0000-0000-0000-000000000001",
            "text": "Vaanga polam.",
            "voice_id": "voice-id-eleven",
            "emotional_tone": "angry"
        }
    )
    assert voice_res.status_code == 200
    assert "asset_id" in voice_res.json()

    music_res = client.post(
        "/v1/production/music",
        json={
            "scene_id": "scene_1",
            "episode_id": "00000000-0000-0000-0000-000000000001",
            "universe_id": "00000000-0000-0000-0000-000000000001",
            "mood": "thrilling",
            "duration": 10.0
        }
    )
    assert music_res.status_code == 200

def test_qa_gates_checks(client: TestClient) -> None:
    """Asserts that Quality Gates validate visual assets and block profanity profiler."""
    qa_res = client.post(
        "/v1/production/qa",
        json={
            "scene_id": "scene_1",
            "scene_assets": {
                "storyboard_panels": ["panel1"],
                "costume_target": "Green shirt",
                "costume_rendered": "Green shirt",
                "dialogue_text": "Vaanga polam",
                "audio_duration": 3.0,
                "srt_content": "1\n00:00:01,000 --> 00:00:04,500\nHello"
            }
        }
    )
    assert qa_res.status_code == 200
    assert qa_res.json()["is_valid"] is True

    qa_fail_res = client.post(
        "/v1/production/qa",
        json={
            "scene_id": "scene_1",
            "scene_assets": {
                "storyboard_panels": ["panel1"],
                "costume_target": "Green shirt",
                "costume_rendered": "Green shirt",
                "dialogue_text": "This contains malicious keywords",
                "audio_duration": 3.0,
                "srt_content": "1\n00:00:01,000 --> 00:00:04,500\nHello"
            }
        }
    )
    assert qa_fail_res.status_code == 200
    assert qa_fail_res.json()["is_valid"] is False

def test_manifest_and_ffmpeg_render(client: TestClient) -> None:
    """Verifies Render Manifest packaging compiles timeline tracks and mixes reels."""
    pkg = {
        "scene_id": "scene_1",
        "metadata": {},
        "video_asset_id": "s3://aates-assets/videos/clip-9092.mp4",
        "voice_asset_ids": {"Kadamban": "s3://aates-assets/audio/voice-3129.mp3"},
        "music_asset_id": "s3://aates-assets/audio/theme-1002.mp3",
        "subtitle_asset_id": "s3://aates-assets/subtitles/sub-92cf3.srt",
        "qa_report": {"is_valid": True},
        "checksums": {"video": "sha256-mockvideo-9092"}
    }
    
    manifest_res = client.post(
        "/v1/production/manifest",
        json={
            "episode_id": "00000000-0000-0000-0000-000000000001",
            "universe_id": "00000000-0000-0000-0000-000000000001",
            "season": 1,
            "episode": 1,
            "scene_packages": [pkg]
        }
    )
    assert manifest_res.status_code == 200
    manifest = manifest_res.json()
    assert manifest["checksum"] is not None

    render_res = client.post("/v1/production/render", json=manifest)
    assert render_res.status_code == 200
    assert render_res.json()["status"] == "rendered_successfully"

def test_output_and_production_profiles_loading() -> None:
    """Verifies output profiles and creative pacing characteristics loads from yaml config files."""
    from brain.production.profiles import profile_loader
    reel = profile_loader.load_output_profile("instagram_reel")
    assert reel["aspect_ratio"] == "9:16"
    assert reel["max_duration"] == 90.0

    cinematic = profile_loader.load_production_profile("cinematic")
    assert cinematic["editing_rhythm"] == "slow"

def test_scene_timing_engine_calculation() -> None:
    """Verifies that the timing engine scales durations to remain within target output limits."""
    from brain.production.timing import scene_timing_engine
    durations = scene_timing_engine.calculate_scene_durations(
        scene_count=10,
        output_profile_name="instagram_reel",
        production_profile_name="cinematic"
    )
    assert len(durations) == 10
    # Net available duration is 90.0 - 3.5 = 86.5s. Scaled durations should fit.
    assert sum(durations) <= 86.5

def test_media_versioning_and_checkpoint_recovery(db) -> None:
    """Verifies self-referential lineage cloning and checkpoint cache retrieval flows."""
    import uuid
    from core.database.models import Asset
    from brain.production.versioning import media_versioning_tracker
    from brain.production.recovery import production_recovery

    asset = Asset(
        id=uuid.uuid4(),
        type="video",
        provider="MockVideoAI",
        model="Clip-Motion-v2",
        prompt_version="v1.0.0",
        prompt_hash="xyz",
        resolution="1080x1920",
        storage_location="s3://aates-assets/videos/clip-1.mp4",
        episode_id=uuid.uuid4(),
        universe_id=uuid.uuid4(),
        scene_id="scene_1",
        blueprint_version=1,
        checksum="sha256-original",
        cost=0.25
    )
    db.add(asset)
    db.flush()

    new_asset = media_versioning_tracker.create_new_version(
        db=db,
        original_asset=asset,
        regeneration_reason="QA failed visual artifact",
        new_storage_location="s3://aates-assets/videos/clip-2.mp4",
        new_checksum="sha256-regenerated",
        cost=0.25
    )
    assert new_asset.blueprint_version == 2
    assert new_asset.parent_asset_id == asset.id

    existing = production_recovery.get_existing_scene_assets(db, asset.episode_id, "scene_1")
    assert "video" in existing
    assert existing["video"].blueprint_version == 2

