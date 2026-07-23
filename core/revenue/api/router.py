import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from core.database.session import get_db
from core.revenue.revenue_engine import RevenueGenerationEngine

router = APIRouter(prefix="/v1/revenue", tags=["Autonomous Revenue Engine"])

class ExecuteCycleIn(BaseModel):
    universe_id: uuid.UUID
    season: int = 1
    episode: int = 1
    objective_prompt: str = "Autonomous daily Tamil episode release"

@router.post("/execute-cycle")
async def execute_autonomous_revenue_cycle(payload: ExecuteCycleIn, db: Session = Depends(get_db)):
    engine = RevenueGenerationEngine(db)
    return await engine.execute_autonomous_production_cycle(
        universe_id=payload.universe_id,
        season=payload.season,
        episode=payload.episode,
        objective_prompt=payload.objective_prompt
    )

@router.get("/pipeline-status")
def get_live_pipeline_status(db: Session = Depends(get_db)):
    """
    Returns real-time status of the Live Creation Pipeline for node canvas monitoring.
    Queries database for real transactions, marketing campaigns, and daemon heartbeat status.
    """
    from core.revenue.revenue_engine import LIVE_PIPELINE_STATE, RevenueGenerationEngine
    from core.finance.models.cost_transaction import CostTransaction
    from core.marketing.models.marketing_campaign import MarketingCampaign
    from core.finance.services.finance_service import FinanceService

    txs = db.query(CostTransaction).order_by(CostTransaction.created_at.desc()).limit(1).all()
    camps = db.query(MarketingCampaign).order_by(MarketingCampaign.created_at.desc()).limit(1).all()
    fin_service = FinanceService(db)
    health = fin_service.get_health_status()

    engine = RevenueGenerationEngine(db)
    daily_limit_reached = engine.is_daily_limit_reached()

    if txs:
        LIVE_PIPELINE_STATE["latest_job_id"] = txs[0].job_id
    if camps:
        LIVE_PIPELINE_STATE["latest_episode_title"] = camps[0].title
        LIVE_PIPELINE_STATE["latest_viral_hook"] = camps[0].viral_hook

    LIVE_PIPELINE_STATE["financial_status"] = health.get("status", "ACTIVE")
    LIVE_PIPELINE_STATE["daily_spent_usd"] = health.get("daily_spent_usd", 0.10)
    LIVE_PIPELINE_STATE["published_today"] = 1 if daily_limit_reached else 0
    LIVE_PIPELINE_STATE["scheduled_release_time"] = "12:00 AM Midnight IST/UTC"

    return LIVE_PIPELINE_STATE
