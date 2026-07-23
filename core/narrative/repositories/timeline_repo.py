import uuid
from typing import List
from sqlalchemy.orm import Session
from core.narrative.models.timeline import NarrativeTimelineEvent
from core.narrative.repositories.base import BaseRepository, _to_uuid

class TimelineRepository(BaseRepository[NarrativeTimelineEvent]):
    """Repository handling NarrativeTimelineEvent database persistence."""
    def __init__(self, db: Session) -> None:
        super().__init__(NarrativeTimelineEvent, db)

    def get_by_universe(self, universe_id: uuid.UUID | str) -> List[NarrativeTimelineEvent]:
        u_id = _to_uuid(universe_id)
        return self.db.query(NarrativeTimelineEvent).filter(
            NarrativeTimelineEvent.universe_id == u_id,
            NarrativeTimelineEvent.is_deleted == False
        ).order_by(NarrativeTimelineEvent.beat_number.asc()).all()
