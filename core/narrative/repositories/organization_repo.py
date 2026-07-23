import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.narrative.models.organization import Organization
from core.narrative.repositories.base import BaseRepository, _to_uuid

class OrganizationRepository(BaseRepository[Organization]):
    """Repository handling Organization faction entity database persistence."""
    def __init__(self, db: Session) -> None:
        super().__init__(Organization, db)

    def get_by_universe(self, universe_id: uuid.UUID | str) -> List[Organization]:
        u_id = _to_uuid(universe_id)
        return self.db.query(Organization).filter(Organization.universe_id == u_id, Organization.is_deleted == False).all()

    def get_by_name(self, universe_id: uuid.UUID | str, name: str) -> Optional[Organization]:
        u_id = _to_uuid(universe_id)
        return self.db.query(Organization).filter(
            Organization.universe_id == u_id,
            Organization.name == name,
            Organization.is_deleted == False
        ).first()
