import uuid
from typing import Any
from sqlalchemy import String, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.finance.models.base import FinanceBaseModel

class BudgetLedger(FinanceBaseModel):
    """
    BudgetLedger ORM Model.
    Master financial ledger enforcing real-time budget ceilings, daily spend caps,
    and studio financial health status (active, warning, frozen).
    """
    __tablename__ = "finance_budget_ledgers"

    name: Mapped[str] = mapped_column(String(255), default="Master Studio Ledger", nullable=False)
    allocated_budget_usd: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    current_spent_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_daily_limit_usd: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    max_episode_limit_usd: Mapped[float] = mapped_column(Float, default=1.50, nullable=False)
    universe_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    # Relationships
    transactions = relationship("CostTransaction", back_populates="ledger", cascade="all, delete-orphan")
