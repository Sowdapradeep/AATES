import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database.session import Base
from apps.api.main import app
from core.narrative.services.universe_service import UniverseService
from core.narrative.dto.narrative_dto import UniverseCreateDTO
from core.revenue.revenue_engine import RevenueGenerationEngine

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_revenue_v1.db"
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

# ── 1. RevenueGenerationEngine Autonomous Cycle Test ───────────────────────────
@pytest.mark.asyncio
async def test_revenue_generation_engine_cycle(db_session):
    u_svc = UniverseService(db_session)
    u = u_svc.create_universe(UniverseCreateDTO(name="Revenue Universe", genre="Action"))

    rev_engine = RevenueGenerationEngine(db_session)
    res = await rev_engine.execute_autonomous_production_cycle(
        universe_id=u.id,
        season=1,
        episode=1,
        objective_prompt="Test autonomous episode generation cycle"
    )

    assert res["status"] == "completed"
    assert res["job_id"] is not None
    assert "viral_hook" in res
    assert "financial_summary" in res
    assert res["financial_summary"]["roi_percentage"] is not None

# ── 2. REST API Endpoint Test ──────────────────────────────────────────────────
def test_revenue_api_endpoints(db_session):
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
        u = u_svc.create_universe(UniverseCreateDTO(name="API Revenue Universe", genre="Drama"))

        # POST /v1/revenue/execute-cycle
        response = client.post("/v1/revenue/execute-cycle", json={
            "universe_id": str(u.id),
            "season": 1,
            "episode": 1,
            "objective_prompt": "API test autonomous cycle"
        })
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["status"] == "completed"
    finally:
        app.dependency_overrides.clear()
