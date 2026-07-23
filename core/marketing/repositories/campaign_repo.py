import uuid
from typing import List
from sqlalchemy.orm import Session
from core.marketing.models.marketing_campaign import MarketingCampaign
from core.marketing.repositories.base import BaseMarketingRepository, _to_uuid

class CampaignRepository(BaseMarketingRepository[MarketingCampaign]):
    def __init__(self, db: Session) -> None:
        super().__init__(MarketingCampaign, db)

    def get_active_campaigns(self) -> List[MarketingCampaign]:
        return self.db.query(MarketingCampaign).filter(
            MarketingCampaign.is_deleted == False
        ).all()
