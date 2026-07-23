from core.marketing.models import MarketingBaseModel, AudienceSegment, MarketingCampaign
from core.marketing.repositories import BaseMarketingRepository, AudienceRepository, CampaignRepository
from core.marketing.services import MarketingService

__all__ = [
    "MarketingBaseModel", "AudienceSegment", "MarketingCampaign",
    "BaseMarketingRepository", "AudienceRepository", "CampaignRepository",
    "MarketingService",
]
