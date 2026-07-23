import uuid
from typing import Any, Dict
from sqlalchemy.orm import Session
from core.finance.services.finance_service import FinanceService
from core.finance.dto.finance_dto import AuthorizationRequestDTO, AuthorizationResponseDTO
from core.finance.repositories.transaction_repo import TransactionRepository

class FinancialGovernorService:
    """
    Real-Time Financial & Production Budget Governor.
    Authorizes AI requests, checks daily and per-episode budget ceilings,
    and dynamically re-routes requests to fallback/free providers if cost limits are approached.
    """
    def __init__(self, db: Session) -> None:
        self.db = db
        self.finance_service = FinanceService(db)
        self.tx_repo = TransactionRepository(db)

    def authorize_request(self, req: AuthorizationRequestDTO) -> AuthorizationResponseDTO:
        ledger = self.finance_service.get_or_create_master_ledger()
        daily_spent = self.tx_repo.get_daily_spend_usd()

        # Check total studio ledger budget status
        if ledger.status == "frozen" or ledger.current_spent_usd >= ledger.allocated_budget_usd:
            return AuthorizationResponseDTO(
                is_authorized=False,
                status="DENIED_LEDGER_FROZEN",
                allocated_cost_usd=0.0,
                recommended_provider="pollinations",
                message="Master studio budget ceiling reached. Autonomous fallbacks enforced."
            )

        # Check Daily Spend Limit
        if (daily_spent + req.estimated_cost_usd) > ledger.max_daily_limit_usd:
            return AuthorizationResponseDTO(
                is_authorized=True,
                status="DEGRADED_DAILY_CAP",
                allocated_cost_usd=0.0,
                recommended_provider="pollinations" if req.category == "image" else "groq",
                message="Daily spend limit reached. Automatically degrading to zero-cost provider."
            )

        # Check Episode Specific Spend Limit
        if req.episode_id:
            ep_cost = self.tx_repo.get_job_total_cost_usd(req.episode_id)
            if (ep_cost + req.estimated_cost_usd) > ledger.max_episode_limit_usd:
                return AuthorizationResponseDTO(
                    is_authorized=True,
                    status="DEGRADED_EPISODE_CAP",
                    allocated_cost_usd=0.0,
                    recommended_provider="pollinations" if req.category == "image" else "groq",
                    message="Per-episode budget ceiling reached. Fallback provider assigned."
                )

        return AuthorizationResponseDTO(
            is_authorized=True,
            status="AUTHORIZED",
            allocated_cost_usd=req.estimated_cost_usd,
            recommended_provider=req.provider,
            message="Request authorized under active budget limits."
        )
