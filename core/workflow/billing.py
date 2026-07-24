import uuid
import logging
from datetime import UTC, datetime
from sqlalchemy.orm import Session
from core.database.models import Budget, ProviderCost, EpisodeCost, DailyCost, MonthlyCost

logger = logging.getLogger("billing_engine")

class BudgetLimitExceeded(Exception):
    """Exception raised when the budget limits for a universe have been exceeded."""
    pass


class BillingEngine:
    """Core billing coordinator tracking token, image, video, and audio synthesis API cost transactions."""

    def verify_budget_limit(self, db: Session, universe_id: str | None) -> None:
        """Verifies if the universe's spent amount has exceeded its allocated budget."""
        if not universe_id:
            return
            
        uni_uuid = uuid.UUID(universe_id) if isinstance(universe_id, str) else universe_id
        budget = db.query(Budget).filter(Budget.universe_id == uni_uuid).first()
        if budget:
            if budget.spent_amount >= budget.allocated_amount:
                from core.database.models import OperationsTimeline
                db.add(OperationsTimeline(
                    id=str(uuid.uuid4()),
                    event_type="budget_limit_exceeded",
                    payload={"universe_id": str(universe_id), "spent": budget.spent_amount, "allocated": budget.allocated_amount},
                    timestamp=datetime.now(UTC).replace(tzinfo=None)
                ))
                db.flush()
                logger.error(f"Billing: Budget limit exceeded for universe {universe_id}. Spent: {budget.spent_amount}, Allocated: {budget.allocated_amount}")
                raise BudgetLimitExceeded(
                    f"Universe budget limit exceeded. Spent: ${budget.spent_amount:.2f}, Allocated: ${budget.allocated_amount:.2f}"
                )
    
    def record_transaction(
        self,
        db: Session,
        provider_name: str,
        cost: float,
        episode_id: str | None = None,
        universe_id: str | None = None
    ) -> None:
        """Accumulates generated asset cost metrics across multiple dimensions.
        
        Updates:
        1. Provider total cost spent
        2. Episode total cost spent
        3. Universe allocated budget spent
        4. Daily total cost spent
        5. Monthly total cost spent
        """
        if cost <= 0.0:
            return
            
        logger.info(f"Billing: Recording cost transaction of ${cost:.5f} for provider '{provider_name}'")
        
        try:
            # 1. Update Provider Cost
            prov_cost = db.query(ProviderCost).filter(ProviderCost.provider_name == provider_name).first()
            if not prov_cost:
                prov_cost = ProviderCost(
                    id=uuid.uuid4(),
                    provider_name=provider_name,
                    total_spent=cost,
                    last_call_timestamp=datetime.now(UTC).replace(tzinfo=None)
                )
                db.add(prov_cost)
            else:
                prov_cost.total_spent += cost
                prov_cost.last_call_timestamp = datetime.now(UTC).replace(tzinfo=None)
                
            # 2. Update Episode Cost
            if episode_id:
                ep_uuid = uuid.UUID(episode_id) if isinstance(episode_id, str) else episode_id
                ep_cost = db.query(EpisodeCost).filter(EpisodeCost.episode_id == ep_uuid).first()
                if not ep_cost:
                    ep_cost = EpisodeCost(
                        id=uuid.uuid4(),
                        episode_id=ep_uuid,
                        total_spent=cost
                    )
                    db.add(ep_cost)
                else:
                    ep_cost.total_spent += cost

            # 3. Update Universe Budget
            if universe_id:
                uni_uuid = uuid.UUID(universe_id) if isinstance(universe_id, str) else universe_id
                budget = db.query(Budget).filter(Budget.universe_id == uni_uuid).first()
                if not budget:
                    # Allocate default starting budget
                    budget = Budget(
                        id=uuid.uuid4(),
                        universe_id=uni_uuid,
                        allocated_amount=500.00,
                        spent_amount=cost,
                        currency="USD"
                    )
                    db.add(budget)
                else:
                    budget.spent_amount += cost
                    
            # 4. Update Daily Cost (normalized to midnight)
            today_date = datetime.now(UTC).replace(tzinfo=None).replace(hour=0, minute=0, second=0, microsecond=0)
            d_cost = db.query(DailyCost).filter(DailyCost.date == today_date).first()
            if not d_cost:
                d_cost = DailyCost(
                    id=uuid.uuid4(),
                    date=today_date,
                    total_spent=cost
                )
                db.add(d_cost)
            else:
                d_cost.total_spent += cost

            # 5. Update Monthly Cost (YYYY-MM string format)
            month_str = datetime.now(UTC).replace(tzinfo=None).strftime("%Y-%m")
            m_cost = db.query(MonthlyCost).filter(MonthlyCost.month == month_str).first()
            if not m_cost:
                m_cost = MonthlyCost(
                    id=uuid.uuid4(),
                    month=month_str,
                    total_spent=cost
                )
                db.add(m_cost)
            else:
                m_cost.total_spent += cost
                
            db.flush()
            logger.debug("Billing transaction committed successfully.")
            
        except Exception as e:
            logger.error(f"Failed to record billing cost transaction: {str(e)}", exc_info=True)


# Global billing engine instance
billing_engine = BillingEngine()
