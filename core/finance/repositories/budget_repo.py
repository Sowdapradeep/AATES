from trio import _subprocess_platform
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.finance.models.budget_ledger import BudgetLedger
from core.finance.repositories.base import BaseFinanceRepository, _to_uuid

class BudgetRepository(BaseFinanceRepository[BudgetLedger]):
    """Repository handling BudgetLedger database persistence."""
    def __init__(self, db: Session) -> None:
        super().__init__(BudgetLedger, db)

    def get_master_ledger(self) -> Optional[BudgetLedger]:
        return self.db.query(BudgetLedger).filter(BudgetLedger.is_deleted == False).first()

    def record_spend(self, ledger_id: uuid.UUID | str, amount_usd: float) -> Optional[BudgetLedger]:
        ledger = self.get_by_id(ledger_id)
        if not ledger:
            return None
        ledger.current_spent_usd = round(ledger.current_spent_usd + amount_usd, 6)
        if ledger.current_spent_usd >= ledger.allocated_budget_usd:
            ledger.status = "frozen"
        elif ledger.current_spent_usd >= (ledger.allocated_budget_usd * 0.85):
            ledger.status = "warning"
        self.db.commit()
        self.db.refresh(ledger)
        return ledger
