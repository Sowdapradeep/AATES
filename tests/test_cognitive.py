from fastapi.testclient import TestClient

def test_agents_list(client: TestClient) -> None:
    """Verifies that the /v1/agents endpoint lists all registered council members."""
    response = client.get("/v1/agents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 6
    names = [agent["name"] for agent in data]
    assert "CEO Agent" in names
    assert "Creative Director Agent" in names
    assert "Production Director Agent" in names
    assert "Technology Director Agent" in names
    assert "Analytics Director Agent" in names
    assert "Business Director Agent" in names

def test_universe_planning(client: TestClient) -> None:
    """Verifies that the Universe Planner generates world rules and directions."""
    response = client.post(
        "/v1/planning/universe",
        json={"name": "Karnan V1", "genre": "action", "core_themes": ["justice", "equality"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["universe_name"] == "Karnan V1"
    assert "world_rules" in data
    assert len(data["world_rules"]) > 0

def test_story_bible_audit_trail(client: TestClient) -> None:
    """Verifies versioned story bible edits increment version indicators and log audits."""
    # Retrieve initial story bible structure
    response = client.get("/v1/universes/univ-999/bible")
    assert response.status_code == 200
    initial_version = response.json().get("version", 1)

    # Perform audited update
    update_response = client.post(
        "/v1/universes/univ-999/bible",
        json={
            "section": "characters",
            "key": "Karnan",
            "new_value": {"role": "protagonist", "attributes": ["noble", "warrior"]},
            "author": "Creative Director Agent",
            "reason": "Define central character outline",
            "workflow_id": "wf-bible-update-test"
        }
    )
    assert update_response.status_code == 200
    assert update_response.json() == {"status": "success", "message": "Story Bible updated and audited successfully."}

    # Verify update persisted and version incremented
    get_response = client.get("/v1/universes/univ-999/bible")
    assert get_response.status_code == 200
    bible = get_response.json()
    assert bible["version"] > initial_version
    assert bible["characters"]["Karnan"]["role"] == "protagonist"

def test_planners_chain(client: TestClient) -> None:
    """Verifies all structured planners return clean Creative Plan layouts."""
    # Season Planner
    season_res = client.post(
        "/v1/planning/season",
        json={"universe_id": "univ-999", "season_number": 1, "total_episodes": 10}
    )
    assert season_res.status_code == 200
    assert "season_arc" in season_res.json()

    # Episode Planner
    episode_res = client.post(
        "/v1/planning/episode",
        json={"universe_id": "univ-999", "season": 1, "episode": 1}
    )
    assert episode_res.status_code == 200
    assert "story_beats" in episode_res.json()

    # Scene Planner
    scene_res = client.post(
        "/v1/planning/scene",
        json={"episode_id": "ep-101", "scene_number": 1}
    )
    assert scene_res.status_code == 200
    assert "scene_intent" in scene_res.json()
