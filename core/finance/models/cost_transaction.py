import uuid
from typing import Any
from sqlalchemy import String, Float, Integer, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.finance.models.base import FinanceBaseModel

class CostTransaction(FinanceBaseModel):
    """
    CostTransaction ORM Model.
    Records individual API, token, voice synthesis, or rendering expense transactions.
    """
    __tablename__ = "finance_cost_transactions"

    ledger_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("finance_budget_ledgers.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(100), default="script", nullable=False) # script, image, voice, video, thumbnail
    provider: Mapped[str] = mapped_column(String(100), default="bedrock_nova", nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    units_consumed: Mapped[int] = mapped_column(Integer, default=1, nullable=False) # token count or character count
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    ledger = relationship("BudgetLedger", back_populates="transactions")
