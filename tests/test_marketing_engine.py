import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database.session import Base
from apps.api.main import app
from core.marketing.models import AudienceSegment, MarketingCampaign
from core.marketing.repositories import AudienceRepository, CampaignRepository
from core.marketing.services import MarketingService
from core.marketing.dto import SegmentCreateDTO

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_marketing_v1.db"
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

# ── 1. Audience & Campaign Repository Tests ───────────────────────────────────
def test_marketing_repositories(db_session):
    aud_repo = AudienceRepository(db_session)
    camp_repo = CampaignRepository(db_session)

    seg = aud_repo.create(
        name="Tamil Cinema Enthusiasts",
        region="Tamil Nadu",
        demographics="18-35 Youth",
        preferred_genre="Drama"
    )
    assert seg.id is not None

    camp = camp_repo.create(
        title="Episode 1 Promo",
        segment_id=seg.id,
        target_platform="youtube_reels",
        viral_hook="Epic Tamil conflict revealed",
        hashtags=["#AATES", "#TamilShorts"]
    )
    assert camp.id is not None
    assert camp.segment_id == seg.id

# ── 2. Marketing Service AI Campaign Generation Test ──────────────────────────
def test_marketing_service_ai_campaign(db_session):
    service = MarketingService(db_session)
    camp_dto = service.generate_ai_campaign(
        title="Clash at Vellore Fort",
        genre="Historical Drama",
        target_platform="youtube_reels"
    )
    assert camp_dto.title == "Clash at Vellore Fort"
    assert camp_dto.viral_hook is not None
    assert len(camp_dto.hashtags) >= 1

# ── 3. REST API Endpoint Tests ────────────────────────────────────────────────
def test_marketing_api_endpoints(db_session):
    from core.database.session import get_db
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)

        # POST /v1/marketing/segment
        res1 = client.post("/v1/marketing/segment", json={
            "name": "Youth Segment",
            "region": "Chennai",
            "demographics": "College Youth",
            "preferred_genre": "Action"
        })
        assert res1.status_code == 201
        assert res1.json()["name"] == "Youth Segment"

        # POST /v1/marketing/campaign/generate
        res2 = client.post("/v1/marketing/campaign/generate", json={
            "title": "API Marketing Campaign",
            "genre": "Thriller",
            "target_platform": "instagram_reels"
        })
        assert res2.status_code == 200
        assert res2.json()["viral_hook"] is not None

        # GET /v1/marketing/campaigns
        res3 = client.get("/v1/marketing/campaigns")
        assert res3.status_code == 200
        assert len(res3.json()) >= 1
    finally:
        app.dependency_overrides.clear()
