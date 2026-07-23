import pytest
from fastapi.testclient import TestClient


def test_complete_autonomous_production_pipeline(client: TestClient) -> None:
    """End-to-End integration test exercising AATES from Idea to CEO Learning Loop.
    
    Flow of the pipeline:
    1. Idea/Planning: Create Universe & Season Beat structures.
    2. Story Bible: Register and update character information.
    3. Production Blueprint: Compile narrative blueprint for Episode 1.
    4. Production Studio: Generate visual layouts, dialog audio, music, QA gating, and render Master Reel.
    5. Operations & Distribution: Enqueue publications, simulate publishing, record analytics, and run CEO loop.
    """
    import uuid
    universe_id = str(uuid.uuid4())
    episode_id = str(uuid.uuid4())

    # ==========================================
    # 1. Idea / Planning
    # ==========================================
    logger_planning = client.post(
        "/v1/planning/universe",
        json={"name": "Karnan E2E", "genre": "action", "core_themes": ["honor", "dignity"]}
    )
    assert logger_planning.status_code == 200
    assert logger_planning.json()["universe_name"] == "Karnan E2E"

    season_plan = client.post(
        "/v1/planning/season",
        json={"universe_id": universe_id, "season_number": 1, "total_episodes": 3}
    )
    assert season_plan.status_code == 200

    # ==========================================
    # 2. Story Bible Audits
    # ==========================================
    bible_update = client.post(
        f"/v1/universes/{universe_id}/bible",
        json={
            "section": "characters",
            "key": "Karnan",
            "new_value": {"role": "warrior", "slang": "nellai"},
            "author": "Creative Director Agent",
            "reason": "Establish Karnan protagonist",
            "workflow_id": "wf-e2e-bible"
        }
    )
    assert bible_update.status_code == 200

    # ==========================================
    # 3. Creative Intelligence Blueprint
    # ==========================================
    # Initialize universe metadata seed in database
    uni_res = client.post(
        "/v1/creative/universe",
        json={"universe_id": universe_id, "name": "Karnan E2E", "genre": "action", "themes": ["honor"]}
    )
    assert uni_res.status_code == 200

    blueprint_res = client.post(
        "/v1/creative/blueprint",
        json={
            "universe_id": universe_id,
            "season": 1,
            "episode": 1,
            "episode_id": episode_id
        }
    )
    assert blueprint_res.status_code == 200
    blueprint = blueprint_res.json()
    assert blueprint["episode_id"] == episode_id
    assert len(blueprint["scenes"]) > 0
    scene = blueprint["scenes"][0]

    # ==========================================
    # 4. Production Studio Assets
    # ==========================================
    # Scene Storyboard panels planning
    storyboard_res = client.post("/v1/production/storyboard", json=scene)
    assert storyboard_res.status_code == 200
    panels = storyboard_res.json()
    assert len(panels) > 0

    # Scene Shot pacing layout
    shot_res = client.post("/v1/production/shots", json=scene)
    assert shot_res.status_code == 200

    # Tamil voice synthesis audio track
    voice_res = client.post(
        "/v1/production/voice",
        json={
            "scene_id": "scene_1",
            "episode_id": episode_id,
            "universe_id": universe_id,
            "text": "Vaanga polam, pesuvom.",
            "voice_id": "voice-id-eleven",
            "emotional_tone": "angry"
        }
    )
    assert voice_res.status_code == 200
    voice_asset_id = voice_res.json()["asset_id"]
    voice_location = voice_res.json()["storage_location"]

    # Background music backtrack
    music_res = client.post(
        "/v1/production/music",
        json={
            "scene_id": "scene_1",
            "episode_id": episode_id,
            "universe_id": universe_id,
            "mood": "tense",
            "duration": 5.0
        }
    )
    assert music_res.status_code == 200
    music_location = music_res.json()["storage_location"]

    # Quality Gates audit
    qa_res = client.post(
        "/v1/production/qa",
        json={
            "scene_id": "scene_1",
            "scene_assets": {
                "storyboard_panels": ["panel1"],
                "costume_target": "traditional dhoti",
                "costume_rendered": "traditional dhoti",
                "dialogue_text": "Vaanga polam, pesuvom.",
                "audio_duration": 3.5,
                "srt_content": "1\n00:00:00,500 --> 00:00:04,000\nVaanga polam"
            }
        }
    )
    assert qa_res.status_code == 200
    assert qa_res.json()["is_valid"] is True

    # Compile scene packages into Render Manifest
    manifest_res = client.post(
        "/v1/production/manifest",
        json={
            "episode_id": episode_id,
            "universe_id": universe_id,
            "season": 1,
            "episode": 1,
            "scene_packages": [
                {
                    "scene_id": "scene_1",
                    "metadata": {},
                    "video_asset_id": "s3://aates-assets/videos/clip-1002.mp4",
                    "voice_asset_ids": {"Kadamban": voice_location},
                    "music_asset_id": music_location,
                    "subtitle_asset_id": "s3://aates-assets/subtitles/scene-1.srt",
                    "qa_report": {"is_valid": True},
                    "checksums": {"video": "sha256-mockvideo-1002"}
                }
            ]
        }
    )
    assert manifest_res.status_code == 200
    manifest = manifest_res.json()

    # Trigger FFmpeg render mix & concatenation to generate Master Reel
    render_res = client.post("/v1/production/render", json=manifest)
    assert render_res.status_code == 200
    assert render_res.json()["status"] == "rendered_successfully"
    master_reel_path = render_res.json()["storage_location"]

    # ==========================================
    # 5. Operations & Distribution Loop
    # ==========================================
    # Create Campaign
    campaign_res = client.post(
        "/v1/operations/campaigns",
        json={
            "name": "E2E Launch Campaign",
            "universe_id": universe_id,
            "platforms": {"instagram_reel": True}
        }
    )
    assert campaign_res.status_code == 201
    campaign_id = campaign_res.json()["campaign_id"]

    # Enqueue Master Reel for publication
    enqueue_res = client.post(
        "/v1/operations/publish/enqueue",
        json={
            "episode_id": episode_id,
            "universe_id": universe_id,
            "master_reel_path": master_reel_path,
            "caption": "Karnan Episode 1 Premiere! #AATES #Tamil",
            "platforms": ["instagram_reel"],
            "campaign_id": campaign_id,
            "priority": 1
        }
    )
    assert enqueue_res.status_code == 200

    # Execute publishing queues
    execute_res = client.post(
        "/v1/operations/publish/execute",
        json={
            "episode_id": episode_id,
            "master_reel_path": master_reel_path,
            "caption": "Karnan Episode 1 Premiere! #AATES #Tamil"
        }
    )
    assert execute_res.status_code == 200
    assert len(execute_res.json()) > 0
    assert execute_res.json()[0]["status"] == "success"

    # Ingest performance analytics metrics
    analytics_res = client.post(
        "/v1/operations/analytics/record",
        json={
            "episode_id": episode_id,
            "platform": "instagram_reel",
            "views": 100,
            "watch_time": 40.0,
            "likes": 2,
            "comments": 0
        }
    )
    assert analytics_res.status_code == 200

    # Retrieve recommendation engine outcomes
    recommend_res = client.post(
        "/v1/operations/learning/recommend",
        json={"episode_id": episode_id}
    )
    assert recommend_res.status_code == 200
    recs = recommend_res.json()
    assert len(recs) > 0

    # Review/approve recommendation via CEO council agent
    review_res = client.post(
        "/v1/operations/learning/review",
        json={
            "recommendation_id": recs[0]["id"],
            "approved": True,
            "decision_text": "Approved via E2E pipeline run."
        }
    )
    assert review_res.status_code == 200
