import uuid
from typing import Any, Dict
from sqlalchemy.orm import Session
from core.finance.repositories.transaction_repo import TransactionRepository
from core.database.models import InstagramPublication, InstagramInsightSnapshot

class ROIService:
    """
    ROI Analysis & Profitability Service.
    Correlates production transaction spend against published content analytics.
    """
    def __init__(self, db: Session) -> None:
        self.db = db
        self.tx_repo = TransactionRepository(db)

    def calculate_job_roi(self, job_id: str) -> Dict[str, Any]:
        total_cost = self.tx_repo.get_job_total_cost_usd(job_id)
        
        # Query view count from publication insights if available
        views = 0
        try:
            snapshot = self.db.query(InstagramInsightSnapshot).order_by(InstagramInsightSnapshot.captured_at.desc()).first()
            if snapshot:
                views = snapshot.views or 0
        except Exception:
            pass

        # Estimate revenue at standard $2.00 CPM
        estimated_revenue_usd = round((views / 1000.0) * 2.00, 4)
        net_profit_usd = round(estimated_revenue_usd - total_cost, 4)
        roi_percentage = round((net_profit_usd / total_cost * 100.0), 2) if total_cost > 0 else 0.0

        return {
            "job_id": job_id,
            "total_production_cost_usd": total_cost,
            "views": views,
            "estimated_revenue_usd": estimated_revenue_usd,
            "net_profit_usd": net_profit_usd,
            "roi_percentage": roi_percentage,
            "status": "profitable" if net_profit_usd >= 0 else "loss"
        }
