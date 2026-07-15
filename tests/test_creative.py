from fastapi.testclient import TestClient

def test_creative_universe_generation(client: TestClient) -> None:
    """Verifies that Universe Generator creates core lore metadata seeds."""
    response = client.post(
        "/v1/creative/universe",
        json={"universe_id": "univ-202", "name": "Nellai Warrior", "genre": "action", "themes": ["honor", "dignity"]}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Nellai Warrior"

def test_dialogue_translation(client: TestClient) -> None:
    """Verifies Dialogue Engine applies regional Tamil slang vocabularies correctly."""
    response = client.post(
        "/v1/creative/dialogue/translate",
        json={"text": "Vaanga kandippa pesuvom.", "slang_type": "chennai"}
    )
    assert response.status_code == 200
    assert "translated" in response.json()
    assert "[MAJA!]" in response.json()["translated"]

def test_creative_validators(client: TestClient) -> None:
    """Verifies that Canon Validator flags magic plots against realism world rules after universe is created."""
    # First create/initialize the universe to insert the default realism rule in the Story Bible
    setup_res = client.post(
        "/v1/creative/universe",
        json={"universe_id": "univ-202", "name": "Nellai Warrior", "genre": "action", "themes": ["honor"]}
    )
    assert setup_res.status_code == 200

    # Execute validation check which should fail against realism rules
    response = client.post(
        "/v1/creative/validate/canon",
        json={"universe_id": "univ-202", "proposed_plot": "A wizard flies over the field with a magical wand."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert len(data["warnings"]) > 0
    assert "magic" in data["warnings"][0].lower()

def test_blueprint_generation(client: TestClient) -> None:
    """Verifies that the standard media-independent Production Blueprint compiles successfully."""
    # First verify/setup universe
    client.post(
        "/v1/creative/universe",
        json={"universe_id": "univ-202", "name": "Nellai Warrior", "genre": "action", "themes": ["honor"]}
    )

    response = client.post(
        "/v1/creative/blueprint",
        json={
            "universe_id": "univ-202",
            "season": 1,
            "episode": 1,
            "episode_id": "ep-101"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["episode_id"] == "ep-101"
    assert "scenes" in data
    assert len(data["scenes"]) == 1
    assert data["scenes"][0]["location"] == "Village Border Woods"

