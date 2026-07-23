import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.narrative.models.season import Season
from core.narrative.repositories.base import BaseRepository, _to_uuid

class SeasonRepository(BaseRepository[Season]):
    """Repository handling Season persistence."""
    def __init__(self, db: Session) -> None:
        super().__init__(Season, db)

    def get_by_universe(self, universe_id: uuid.UUID | str) -> List[Season]:
        u_id = _to_uuid(universe_id)
        return self.db.query(Season).filter(
            Season.universe_id == u_id,
            Season.is_deleted == False
        ).order_by(Season.season_number.asc()).all()

    def get_season(self, universe_id: uuid.UUID | str, season_number: int) -> Optional[Season]:
        u_id = _to_uuid(universe_id)
        return self.db.query(Season).filter(
            Season.universe_id == u_id,
            Season.season_number == season_number,
            Season.is_deleted == False
        ).first()
