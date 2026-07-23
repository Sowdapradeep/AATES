import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database.session import Base
from apps.api.main import app
from core.finance.models import BudgetLedger, CostTransaction
from core.finance.repositories import BudgetRepository, TransactionRepository
from core.finance.services import FinanceService, FinancialGovernorService, ROIService
from core.finance.dto import TransactionCreateDTO, AuthorizationRequestDTO

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_finance_v1.db"
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

# ── 1. Model & Repository Tests ───────────────────────────────────────────────
def test_budget_and_transaction_repositories(db_session):
    b_repo = BudgetRepository(db_session)
    t_repo = TransactionRepository(db_session)

    ledger = b_repo.create(
        name="Test Production Ledger",
        allocated_budget_usd=50.0,
        max_daily_limit_usd=5.0,
        max_episode_limit_usd=1.0
    )
    assert ledger.id is not None
    assert ledger.current_spent_usd == 0.0

    tx = t_repo.create(
        ledger_id=ledger.id,
        job_id="job_001",
        category="script",
        provider="bedrock_nova",
        cost_usd=0.25
    )
    assert tx.id is not None

    b_repo.record_spend(ledger.id, 0.25)
    updated_ledger = b_repo.get_by_id(ledger.id)
    assert updated_ledger.current_spent_usd == 0.25

# ── 2. Financial Governor Authorization Tests ──────────────────────────────────
def test_financial_governor_authorization(db_session):
    svc = FinanceService(db_session)
    ledger_dto = svc.get_or_create_master_ledger()
    governor = FinancialGovernorService(db_session)

    # Standard authorized request
    auth_res = governor.authorize_request(AuthorizationRequestDTO(
        category="image",
        provider="titan_image",
        estimated_cost_usd=0.08
    ))
    assert auth_res.is_authorized is True
    assert auth_res.status == "AUTHORIZED"

# ── 3. ROI Service Test ───────────────────────────────────────────────────────
def test_roi_service(db_session):
    svc = FinanceService(db_session)
    ledger_dto = svc.get_or_create_master_ledger()

    svc.record_transaction(TransactionCreateDTO(
        ledger_id=ledger_dto.id,
        job_id="job_roi_100",
        category="video",
        provider="ffmpeg",
        cost_usd=0.50
    ))

    roi_svc = ROIService(db_session)
    res = roi_svc.calculate_job_roi("job_roi_100")
    assert res["job_id"] == "job_roi_100"
    assert res["total_production_cost_usd"] == 0.50

# ── 4. REST API Endpoint Tests ────────────────────────────────────────────────
def test_finance_api_endpoints(db_session):
    from core.database.session import get_db
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)

        # GET /v1/finance/ledger
        res1 = client.get("/v1/finance/ledger")
        assert res1.status_code == 200
        l_data = res1.json()
        assert l_data["allocated_budget_usd"] > 0

        # POST /v1/finance/authorize
        res2 = client.post("/v1/finance/authorize", json={
            "category": "voice",
            "provider": "polly",
            "estimated_cost_usd": 0.02
        })
        assert res2.status_code == 200
        assert res2.json()["is_authorized"] is True

        # GET /v1/finance/health
        res3 = client.get("/v1/finance/health")
        assert res3.status_code == 200
        assert res3.json()["status"] == "active"
    finally:
        app.dependency_overrides.clear()
