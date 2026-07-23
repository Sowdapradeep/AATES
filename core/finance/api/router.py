import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database.session import get_db
from core.finance.dto.finance_dto import (
    BudgetResponseDTO, TransactionCreateDTO, TransactionResponseDTO,
    AuthorizationRequestDTO, AuthorizationResponseDTO
)
from core.finance.services.finance_service import FinanceService
from core.finance.services.governor_service import FinancialGovernorService
from core.finance.services.roi_service import ROIService

router = APIRouter(prefix="/v1/finance", tags=["Autonomous Governance & Finance"])

@router.get("/ledger", response_model=BudgetResponseDTO)
def get_master_ledger(db: Session = Depends(get_db)):
    service = FinanceService(db)
    return service.get_or_create_master_ledger()

@router.post("/transaction", response_model=TransactionResponseDTO, status_code=status.HTTP_201_CREATED)
def record_transaction(dto: TransactionCreateDTO, db: Session = Depends(get_db)):
    service = FinanceService(db)
    return service.record_transaction(dto)

@router.post("/authorize", response_model=AuthorizationResponseDTO)
def authorize_request(dto: AuthorizationRequestDTO, db: Session = Depends(get_db)):
    governor = FinancialGovernorService(db)
    return governor.authorize_request(dto)

@router.get("/health")
def get_financial_health(db: Session = Depends(get_db)):
    service = FinanceService(db)
    ledger = service.get_or_create_master_ledger()
    daily_spent = service.tx_repo.get_daily_spend_usd()
    return {
        "ledger_name": ledger.name,
        "status": ledger.status,
        "allocated_budget_usd": ledger.allocated_budget_usd,
        "total_spent_usd": ledger.current_spent_usd,
        "daily_spent_usd": daily_spent,
        "daily_limit_usd": ledger.max_daily_limit_usd,
        "episode_limit_usd": ledger.max_episode_limit_usd
    }

@router.get("/roi/{job_id}")
def calculate_roi(job_id: str, db: Session = Depends(get_db)):
    roi_service = ROIService(db)
    return roi_service.calculate_job_roi(job_id)
