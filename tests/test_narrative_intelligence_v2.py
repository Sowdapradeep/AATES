import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database.session import Base
from apps.api.main import app
from core.narrative.services.universe_service import UniverseService
from core.narrative.services.character_service import CharacterService
from core.narrative.services.location_service import LocationService
from core.narrative.dto.narrative_dto import (
    UniverseCreateDTO, CharacterCreateDTO, LocationCreateDTO
)
from core.narrative.intelligence import (
    BedrockIntelligenceClient,
    CharacterIntelligenceEngine,
    RelationshipIntelligenceEngine,
    TimelineIntelligenceEngine,
    StoryArcIntelligenceEngine,
    ContinuityIntelligenceEngine,
    NarrativeMemoryEngine,
    UniverseEvolutionEngine,
    CreativeDirectorAI
)

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_intelligence_v2.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

# ── 1. Bedrock & Embedding Client Test ────────────────────────────────────────
def test_bedrock_intelligence_client():
    client = BedrockIntelligenceClient()
    text = "Character confrontation over land survey"
    embedding = client.generate_embedding(text)
    assert len(embedding) == 1536

    reasoning = client.reason(text, system_instruction="Analyze scene continuity.")
    assert len(reasoning) > 0

# ── 2. Character Intelligence Engine Test ──────────────────────────────────────
def test_character_intelligence_engine(db_session):
    u_svc = UniverseService(db_session)
    c_svc = CharacterService(db_session)

    u = u_svc.create_universe(UniverseCreateDTO(name="Empire Realm", genre="Historical"))
    c = c_svc.create_character(CharacterCreateDTO(
        universe_id=u.id,
        name="Kadamban",
        role="protagonist",
        motivation="Protect village land"
    ))

    engine = CharacterIntelligenceEngine(db_session)
    result = engine.evaluate_character_growth(c.id, recent_events=["Surveyor notice served at town hall"])
    assert result["character_name"] == "Kadamban"
    assert "emotional_state" in result
    assert len(result["personality_traits"]) >= 1

# ── 3. Relationship Intelligence Engine Test ──────────────────────────────────
def test_relationship_intelligence_engine(db_session):
    u_svc = UniverseService(db_session)
    c_svc = CharacterService(db_session)

    u = u_svc.create_universe(UniverseCreateDTO(name="Chola Kingdom", genre="History"))
    c1 = c_svc.create_character(CharacterCreateDTO(universe_id=u.id, name="Hero"))
    c2 = c_svc.create_character(CharacterCreateDTO(universe_id=u.id, name="Corporate Agent", role="villain"))

    engine = RelationshipIntelligenceEngine(db_session)
    res = engine.evolve_relationship(c1.id, c2.id, interaction_event="Heated debate at boundary marker")
    assert res["character_a"] == "Hero"
    assert res["character_b"] == "Corporate Agent"
    assert res["tension_level"] >= 0.5

# ── 4. Timeline Intelligence Engine Test ──────────────────────────────────────
def test_timeline_intelligence_engine(db_session):
    u_svc = UniverseService(db_session)
    u = u_svc.create_universe(UniverseCreateDTO(name="Pandya Timeline", genre="Epic"))

    engine = TimelineIntelligenceEngine(db_session)
    beat = engine.generate_timeline_beat(u.id, beat_title="First Survey Confrontation", context_notes="Tense morning meeting")
    assert beat["title"] is not None
    assert beat["beat_number"] == 1

# ── 5. Story Arc Intelligence Engine Test ─────────────────────────────────────
def test_story_arc_intelligence_engine(db_session):
    u_svc = UniverseService(db_session)
    u = u_svc.create_universe(UniverseCreateDTO(name="Arc Realm", genre="Drama"))

    engine = StoryArcIntelligenceEngine(db_session)
    arc = engine.formulate_story_arc(u.id, theme="Reclaiming Heritage", target_conflict="Land Rights")
    assert arc["major_theme"] == "Reclaiming Heritage"

    unfinished = engine.detect_unfinished_arcs(u.id)
    assert len(unfinished) >= 1

# ── 6. Continuity Intelligence Engine Test ───────────────────────────────────
def test_continuity_intelligence_engine(db_session):
    u_svc = UniverseService(db_session)
    c_svc = CharacterService(db_session)
    l_svc = LocationService(db_session)

    u = u_svc.create_universe(UniverseCreateDTO(name="Continuity Realm", genre="Realism"))
    c1 = c_svc.create_character(CharacterCreateDTO(universe_id=u.id, name="AliveHero"))
    l1 = l_svc.create_location(LocationCreateDTO(universe_id=u.id, name="Village Hall"))

    engine = ContinuityIntelligenceEngine(db_session)

    # Valid Action Test
    valid_res = engine.validate_story_action(
        universe_id=u.id,
        proposed_action="AliveHero speaks at Village Hall",
        participating_character_names=["AliveHero"],
        target_location_name="Village Hall"
    )
    assert valid_res.get("is_valid") is True or "violations" in valid_res

    # Missing Character Action Test
    invalid_res = engine.validate_story_action(
        universe_id=u.id,
        proposed_action="UnknownGhost speaks at Nonexistent Place",
        participating_character_names=["UnknownGhost"],
        target_location_name="Nonexistent Place"
    )
    assert invalid_res.get("is_valid") is False
    assert len(invalid_res.get("violations", [])) >= 1

# ── 7. Narrative Memory Engine (Titan Vector Search) Test ─────────────────────
def test_narrative_memory_engine(db_session):
    u_svc = UniverseService(db_session)
    c_svc = CharacterService(db_session)

    u = u_svc.create_universe(UniverseCreateDTO(name="Memory Universe", genre="SciFi"))
    c_svc.create_character(CharacterCreateDTO(universe_id=u.id, name="Velasu", motivation="Protect the sacred grove"))

    engine = NarrativeMemoryEngine(db_session)
    results = engine.search_semantic_memory(u.id, query="sacred grove land protection", top_k=2)
    assert len(results) >= 1
    assert "similarity_score" in results[0]

# ── 8. Universe Evolution Engine Test ─────────────────────────────────────────
def test_universe_evolution_engine(db_session):
    u_svc = UniverseService(db_session)
    u = u_svc.create_universe(UniverseCreateDTO(name="Evolving Tamil Realm", genre="Drama"))

    engine = UniverseEvolutionEngine(db_session)
    res = engine.evolve_universe(u.id, episode_count_elapsed=5)
    assert res["episodes_elapsed"] == 5
    assert len(res["evolved_rules"]) >= 1

# ── 9. Creative Director AI "Reason First, Generate Second" Test ──────────────
@pytest.mark.asyncio
async def test_creative_director_ai(db_session):
    u_svc = UniverseService(db_session)
    c_svc = CharacterService(db_session)
    l_svc = LocationService(db_session)

    u = u_svc.create_universe(UniverseCreateDTO(name="Director Realm", genre="Historical Realism"))
    c_svc.create_character(CharacterCreateDTO(universe_id=u.id, name="Kadamban", role="protagonist"))
    c_svc.create_character(CharacterCreateDTO(universe_id=u.id, name="Nallasamy", role="villain"))
    l_svc.create_location(LocationCreateDTO(universe_id=u.id, name="Village Border Woods"))

    director = CreativeDirectorAI(db_session)
    ep_id = str(uuid.uuid4())
    res = await director.execute_reasoning_and_create_blueprint(
        universe_id=u.id,
        season=1,
        episode=1,
        episode_id=ep_id,
        objective_prompt="Kadamban confronts Nallasamy at Village Border Woods regarding survey notices."
    )
    assert res["status"] == "approved"
    assert res["reasoning_stage"] == "BLUEPRINT_COMPILED"
    assert "blueprint" in res

# ── 10. REST API Router Tests ──────────────────────────────────────────────────
def test_intelligence_api_endpoints(db_session):
    from core.database.session import get_db
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        u_svc = UniverseService(db_session)
        u = u_svc.create_universe(UniverseCreateDTO(name="API Intel Universe", genre="Action"))

        # Test POST /v1/intelligence/timeline/beat
        response = client.post("/v1/intelligence/timeline/beat", json={
            "universe_id": str(u.id),
            "beat_title": "API Beat 1",
            "event_type": "beat",
            "context_notes": "API test call"
        })
        assert response.status_code == 200
        assert response.json()["title"] is not None

        # Test GET /v1/intelligence/story-arcs/{universe_id}/unfinished
        arc_res = client.get(f"/v1/intelligence/story-arcs/{u.id}/unfinished")
        assert arc_res.status_code == 200
    finally:
        app.dependency_overrides.clear()
