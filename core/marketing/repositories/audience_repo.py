import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.marketing.models.audience_segment import AudienceSegment
from core.marketing.repositories.base import BaseMarketingRepository, _to_uuid

class AudienceRepository(BaseMarketingRepository[AudienceSegment]):
    def __init__(self, db: Session) -> None:
        super().__init__(AudienceSegment, db)

    def get_by_name(self, name: str) -> Optional[AudienceSegment]:
        return self.db.query(AudienceSegment).filter(
            AudienceSegment.name == name,
            AudienceSegment.is_deleted == False
        ).first()
