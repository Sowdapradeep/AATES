import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.finance.models.budget_ledger import BudgetLedger
from core.finance.dto.finance_dto import (
    BudgetCreateDTO, BudgetResponseDTO, TransactionCreateDTO, TransactionResponseDTO
)
from core.finance.repositories.budget_repo import BudgetRepository
from core.finance.repositories.transaction_repo import TransactionRepository

class FinanceService:
    """Service encapsulating master ledger and expense transaction logging."""
    def __init__(self, db: Session) -> None:
        self.db = db
        self.budget_repo = BudgetRepository(db)
        self.tx_repo = TransactionRepository(db)

    def get_or_create_master_ledger(self) -> BudgetResponseDTO:
        ledger = self.budget_repo.get_master_ledger()
        if not ledger:
            ledger = self.budget_repo.create(
                name="Master Studio Ledger",
                allocated_budget_usd=100.0,
                max_daily_limit_usd=10.0,
                max_episode_limit_usd=1.50
            )
        return BudgetResponseDTO.model_validate(ledger)

    def record_transaction(self, dto: TransactionCreateDTO) -> TransactionResponseDTO:
        tx = self.tx_repo.create(**dto.model_dump())
        self.budget_repo.record_spend(dto.ledger_id, dto.cost_usd)
        return TransactionResponseDTO.model_validate(tx)
