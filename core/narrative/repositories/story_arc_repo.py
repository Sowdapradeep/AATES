import uuid
from typing import List
from sqlalchemy.orm import Session
from core.narrative.models.story_arc import StoryArc
from core.narrative.repositories.base import BaseRepository, _to_uuid

class StoryArcRepository(BaseRepository[StoryArc]):
    """Repository handling StoryArc persistence."""
    def __init__(self, db: Session) -> None:
        super().__init__(StoryArc, db)

    def get_by_universe(self, universe_id: uuid.UUID | str) -> List[StoryArc]:
        u_id = _to_uuid(universe_id)
        return self.db.query(StoryArc).filter(StoryArc.universe_id == u_id, StoryArc.is_deleted == False).all()
