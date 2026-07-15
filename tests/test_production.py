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
