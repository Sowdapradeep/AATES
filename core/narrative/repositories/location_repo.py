import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.narrative.models.location import Location
from core.narrative.repositories.base import BaseRepository, _to_uuid

class LocationRepository(BaseRepository[Location]):
    """Repository handling Location entity database persistence."""
    def __init__(self, db: Session) -> None:
        super().__init__(Location, db)

    def get_by_universe(self, universe_id: uuid.UUID | str) -> List[Location]:
        u_id = _to_uuid(universe_id)
        return self.db.query(Location).filter(Location.universe_id == u_id, Location.is_deleted == False).all()

    def get_by_name(self, universe_id: uuid.UUID | str, name: str) -> Optional[Location]:
        u_id = _to_uuid(universe_id)
        return self.db.query(Location).filter(
            Location.universe_id == u_id,
            Location.name == name,
            Location.is_deleted == False
        ).first()
