import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from core.finance.models.cost_transaction import CostTransaction
from core.finance.repositories.base import BaseFinanceRepository, _to_uuid

class TransactionRepository(BaseFinanceRepository[CostTransaction]):
    """Repository handling CostTransaction database persistence."""
    def __init__(self, db: Session) -> None:
        super().__init__(CostTransaction, db)

    def list_by_job(self, job_id: str) -> List[CostTransaction]:
        return self.db.query(CostTransaction).filter(
            CostTransaction.job_id == job_id,
            CostTransaction.is_deleted == False
        ).all()

    def get_daily_spend_usd(self) -> float:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        res = self.db.query(func.sum(CostTransaction.cost_usd)).filter(
            CostTransaction.created_at >= today_start,
            CostTransaction.is_deleted == False
        ).scalar()
        return float(res or 0.0)

    def get_job_total_cost_usd(self, job_id: str) -> float:
        res = self.db.query(func.sum(CostTransaction.cost_usd)).filter(
            CostTransaction.job_id == job_id,
            CostTransaction.is_deleted == False
        ).scalar()
        return float(res or 0.0)
