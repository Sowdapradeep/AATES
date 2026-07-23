import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.narrative.models.episode import Episode
from core.narrative.repositories.base import BaseRepository, _to_uuid

class EpisodeRepository(BaseRepository[Episode]):
    """Repository handling Episode persistence."""
    def __init__(self, db: Session) -> None:
        super().__init__(Episode, db)

    def get_by_season(self, season_id: uuid.UUID | str) -> List[Episode]:
        s_id = _to_uuid(season_id)
        return self.db.query(Episode).filter(
            Episode.season_id == s_id,
            Episode.is_deleted == False
        ).order_by(Episode.episode_number.asc()).all()

    def get_episode(self, season_id: uuid.UUID | str, episode_number: int) -> Optional[Episode]:
        s_id = _to_uuid(season_id)
        return self.db.query(Episode).filter(
            Episode.season_id == s_id,
            Episode.episode_number == episode_number,
            Episode.is_deleted == False
        ).first()
