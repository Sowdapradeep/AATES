import uuid
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict

class FinanceBaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by: str = "system"
    version: int = 1
    status: str = "active"
    metadata_json: Optional[dict[str, Any]] = None

class BudgetCreateDTO(BaseModel):
    name: str = "Master Studio Ledger"
    allocated_budget_usd: float = 100.0
    max_daily_limit_usd: float = 10.0
    max_episode_limit_usd: float = 1.50
    universe_id: Optional[uuid.UUID] = None

class BudgetResponseDTO(FinanceBaseDTO):
    name: str
    allocated_budget_usd: float
    current_spent_usd: float
    max_daily_limit_usd: float
    max_episode_limit_usd: float
    universe_id: Optional[uuid.UUID] = None

class TransactionCreateDTO(BaseModel):
    ledger_id: uuid.UUID
    job_id: Optional[str] = None
    category: str = "script"
    provider: str = "bedrock_nova"
    model_name: Optional[str] = None
    units_consumed: int = 1
    cost_usd: float = 0.0
    notes: Optional[str] = None

class TransactionResponseDTO(FinanceBaseDTO):
    ledger_id: uuid.UUID
    job_id: Optional[str] = None
    category: str
    provider: str
    model_name: Optional[str] = None
    units_consumed: int
    cost_usd: float
    notes: Optional[str] = None

class AuthorizationRequestDTO(BaseModel):
    category: str
    provider: str
    estimated_cost_usd: float = 0.05
    episode_id: Optional[str] = None

class AuthorizationResponseDTO(BaseModel):
    is_authorized: bool
    status: str
    allocated_cost_usd: float
    recommended_provider: str
    message: str
