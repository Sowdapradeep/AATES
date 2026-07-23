import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database.session import Base
from apps.api.main import app
from brain.story_bible.bible import story_bible_engine
from core.narrative.models import (
    Universe, World, Character, Relationship, Location, Organization, StoryArc, TimelineEvent, Season, Episode, Scene
)
from core.narrative.repositories import (
    UniverseRepository, CharacterRepository, RelationshipRepository, LocationRepository
)
from core.narrative.services import (
    UniverseService, CharacterService, RelationshipService
)
from core.narrative.dto.narrative_dto import (
    UniverseCreateDTO, CharacterCreateDTO, RelationshipCreateDTO
)
from core.narrative.services.migration_service import NarrativeMigrationService

# Setup isolated test database engine
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_narrative.db"
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

# ── 1. Model & Base Mixin Tests ───────────────────────────────────────────────
def test_universe_model_instantiation(db_session):
    u = Universe(
        name="Chola Dynasty",
        genre="Historical Drama",
        core_themes=["Duty", "Empires"],
        world_rules=["Realism"]
    )
    db_session.add(u)
    db_session.commit()
    assert u.id is not None
    assert u.version == 1
    assert u.status == "active"
    assert u.is_deleted is False

# ── 2. Repository Tests ───────────────────────────────────────────────────────
def test_universe_repository_crud(db_session):
    repo = UniverseRepository(db_session)
    created = repo.create(name="Pandya Kingdom", genre="History")
    assert created.id is not None

    fetched = repo.get_by_id(created.id)
    assert fetched.name == "Pandya Kingdom"

    updated = repo.update(created.id, genre="Epic History")
    assert updated.genre == "Epic History"
    assert updated.version == 2

    soft_deleted = repo.soft_delete(created.id)
    assert soft_deleted is True
    assert repo.get_by_id(created.id) is None

def test_relationship_repository(db_session):
    u_repo = UniverseRepository(db_session)
    c_repo = CharacterRepository(db_session)
    r_repo = RelationshipRepository(db_session)

    u = u_repo.create(name="Test Realm")
    c1 = c_repo.create(universe_id=u.id, name="Hero")
    c2 = c_repo.create(universe_id=u.id, name="Villain")

    rel = r_repo.create(
        character_a_id=c1.id,
        character_b_id=c2.id,
        relationship_type="arch-nemesis",
        tension_level=0.95
    )
    assert rel.id is not None

    found = r_repo.get_between_characters(c1.id, c2.id)
    assert found is not None
    assert found.tension_level == 0.95

# ── 3. Service Tests ──────────────────────────────────────────────────────────
def test_character_service(db_session):
    u_service = UniverseService(db_session)
    c_service = CharacterService(db_session)

    u_res = u_service.create_universe(UniverseCreateDTO(name="Sci-Fi Tamil", genre="Sci-Fi"))
    c_res = c_service.create_character(CharacterCreateDTO(
        universe_id=u_res.id,
        name="Veera",
        role="protagonist",
        slang_preference="madurai"
    ))
    assert c_res.id is not None
    assert c_res.name == "Veera"

    chars = c_service.list_by_universe(u_res.id)
    assert len(chars) == 1

# ── 4. StoryBibleEngine Backward Compatibility & Dual Write Tests ─────────────
def test_story_bible_engine_fallback_and_dual_write(db_session):
    univ_id = "test-universe-99"

    # Update via StoryBibleEngine
    story_bible_engine.update_bible(
        universe_id=univ_id,
        section="characters",
        key="Kadamban",
        new_value={"name": "Kadamban", "role": "protagonist", "slang_preference": "kovai"},
        author="Creative Director Agent",
        reason="Initialize test hero",
        db=db_session
    )

    # Read back via StoryBibleEngine
    bible = story_bible_engine.get_bible(univ_id, db=db_session)
    assert "characters" in bible
    assert "Kadamban" in bible["characters"]

    # Verify Dual-Write created Character in Narrative ORM
    c_repo = CharacterRepository(db_session)
    u_repo = UniverseRepository(db_session)
    u_orm = u_repo.get_by_name(f"Universe-{univ_id}")
    assert u_orm is not None

    c_orm = c_repo.get_by_name(u_orm.id, "Kadamban")
    assert c_orm is not None
    assert c_orm.role == "protagonist"

# ── 5. Migration Service Test ─────────────────────────────────────────────────
def test_narrative_migration_service(db_session):
    univ_id = "legacy-universe-42"
    # Seed legacy Bible update
    story_bible_engine.update_bible(
        universe_id=univ_id,
        section="locations",
        key="Vellore Fort",
        new_value={"name": "Vellore Fort", "description": "Historic stone fortress", "mood": "Mysterious"},
        author="System Test",
        reason="Legacy seed",
        db=db_session
    )

    migrator = NarrativeMigrationService(db_session)
    result = migrator.migrate_bible(univ_id)
    assert result["status"] == "success"
    assert result["locations_migrated"] >= 1

# ── 6. REST API Compatibility & Narrative Router Tests ────────────────────────
def test_narrative_api_endpoints(db_session):
    from core.database.session import get_db
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        response = client.post("/v1/narrative/universes", json={
            "name": "API Test Empire",
            "genre": "Historical Drama",
            "core_themes": ["Glory", "Honor"],
            "world_rules": ["No Magic"]
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Test Empire"
        u_id = data["id"]

        # Verify GET /v1/narrative/universes/{id}
        res = client.get(f"/v1/narrative/universes/{u_id}")
        assert res.status_code == 200
        assert res.json()["name"] == "API Test Empire"

        # Verify legacy Story Bible API compatibility GET /v1/universes/{id}/bible
        bible_res = client.get(f"/v1/universes/{u_id}/bible")
        assert bible_res.status_code == 200
    finally:
        app.dependency_overrides.clear()

