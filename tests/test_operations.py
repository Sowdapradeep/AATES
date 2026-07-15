import uuid
import pytest
from fastapi.testclient import TestClient


EPISODE_ID = "00000000-0000-0000-0000-000000000001"
UNIVERSE_ID = "00000000-0000-0000-0000-000000000001"
MASTER_REEL_PATH = "s3://aates-assets/reels/master-reel-9019.mp4"


def test_campaign_creation(client: TestClient) -> None:
    """Verifies a campaign can be created with platform targets and status management."""
    res = client.post("/v1/operations/campaigns", json={
        "name": "Season 1 Launch",
        "description": "Kadamban Series Premiere Campaign",
        "universe_id": UNIVERSE_ID,
        "season": 1,
        "start_date": "2026-07-16T09:00:00",
        "end_date": "2026-07-30T23:59:59",
        "status": "draft",
        "priority": 1,
        "platforms": {"instagram_reel": True, "youtube_short": True}
    })
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "draft"
    assert "campaign_id" in data


def test_publishing_queue_and_execute(client: TestClient) -> None:
    """Validates that a Master Reel can be enqueued and published across platforms."""
    # Enqueue
    enqueue_res = client.post("/v1/operations/publish/enqueue", json={
        "episode_id": EPISODE_ID,
        "universe_id": UNIVERSE_ID,
        "master_reel_path": MASTER_REEL_PATH,
        "caption": "Kadamban S01E01 – The Forest Awakens! #Reel #Tamil",
        "platforms": ["instagram_reel", "youtube_short"],
        "priority": 1
    })
    assert enqueue_res.status_code == 200
    assert enqueue_res.json()["queued"] == 2

    # Execute publish
    exec_res = client.post("/v1/operations/publish/execute", json={
        "episode_id": EPISODE_ID,
        "master_reel_path": MASTER_REEL_PATH,
        "caption": "Kadamban S01E01 – The Forest Awakens! #Reel #Tamil"
    })
    assert exec_res.status_code == 200
    results = exec_res.json()
    assert len(results) == 2
    assert all(r["status"] == "success" for r in results)


def test_scheduling_window_check(client: TestClient) -> None:
    """Verifies that blackout hours are correctly identified and next valid slots returned."""
    # Blackout time (2am)
    res = client.post("/v1/operations/schedule/check", json={"scheduled_at": "2026-07-16T02:30:00"})
    assert res.status_code == 200
    assert res.json()["in_window"] is False

    # Valid window (9am)
    res2 = client.post("/v1/operations/schedule/check", json={"scheduled_at": "2026-07-16T09:00:00"})
    assert res2.status_code == 200
    assert res2.json()["in_window"] is True


def test_provider_health_monitoring(client: TestClient) -> None:
    """Asserts that all registered publishing providers return health metrics."""
    res = client.post("/v1/operations/monitoring/probe")
    assert res.status_code == 200
    health = res.json()
    assert len(health) >= 2
    for h in health:
        assert h["is_available"] is True
        assert h["latency_ms"] > 0


def test_analytics_snapshot_and_performance_score(client: TestClient) -> None:
    """Validates immutable analytics snapshots and performance score computation."""
    res = client.post("/v1/operations/analytics/record", json={
        "episode_id": EPISODE_ID,
        "platform": "instagram_reel",
        "views": 12500,
        "watch_time": 55000.0,
        "likes": 1800,
        "comments": 220,
        "shares": 340,
        "follower_growth": 95
    })
    assert res.status_code == 200
    data = res.json()
    assert "snapshot_id" in data
    assert data["performance_score"] > 0.0


def test_learning_recommendations_and_ceo_review(client: TestClient) -> None:
    """Validates the full learning loop: record poor analytics → recommendations → CEO approval."""
    # Record a poor performance snapshot first
    client.post("/v1/operations/analytics/record", json={
        "episode_id": EPISODE_ID,
        "platform": "instagram_reel",
        "views": 200,
        "watch_time": 100.0,
        "likes": 5,
        "comments": 1,
        "shares": 0,
        "follower_growth": 0
    })

    # Generate recommendations
    recs_res = client.post("/v1/operations/learning/recommend", json={"episode_id": EPISODE_ID})
    assert recs_res.status_code == 200
    recs = recs_res.json()
    assert len(recs) > 0
    assert recs[0]["confidence"] > 0.5

    # CEO approves first recommendation
    review_res = client.post("/v1/operations/learning/review", json={
        "recommendation_id": recs[0]["id"],
        "approved": True,
        "decision_text": "Agreed. Shorten the hook sequence to 2 seconds."
    })
    assert review_res.status_code == 200
    assert review_res.json()["status"] == "approved"


def test_operations_timeline_audit_trail(client: TestClient) -> None:
    """Confirms the operations timeline records publish and analytics events."""
    # Self-contained: generate at least one timeline event (analytics snapshot creates one)
    client.post("/v1/operations/analytics/record", json={
        "episode_id": EPISODE_ID,
        "platform": "instagram_reel",
        "views": 3000,
        "watch_time": 12000.0,
        "likes": 300,
        "comments": 40,
        "shares": 20,
        "follower_growth": 15
    })

    res = client.get(f"/v1/operations/timeline/{EPISODE_ID}")
    assert res.status_code == 200
    events = res.json()
    assert len(events) > 0
    event_types = [e["event_type"] for e in events]
    assert any("analytics" in t or "publish" in t or "recommend" in t for t in event_types)


def test_distribution_history_tracking(client: TestClient) -> None:
    """Verifies distribution history is maintained per episode with retry tracking."""
    # Self-contained: enqueue then execute before querying history
    client.post("/v1/operations/publish/enqueue", json={
        "episode_id": EPISODE_ID,
        "universe_id": UNIVERSE_ID,
        "master_reel_path": MASTER_REEL_PATH,
        "caption": "Test distribution history",
        "platforms": ["instagram_reel"],
        "priority": 0
    })
    client.post("/v1/operations/publish/execute", json={
        "episode_id": EPISODE_ID,
        "master_reel_path": MASTER_REEL_PATH,
        "caption": "Test distribution history"
    })

    res = client.get(f"/v1/operations/distribution/{EPISODE_ID}")
    assert res.status_code == 200
    history = res.json()
    assert len(history) > 0
    assert all("platform" in h and "status" in h for h in history)
