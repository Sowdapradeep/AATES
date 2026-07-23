import uuid
from typing import List
from sqlalchemy.orm import Session
from core.narrative.dto.narrative_dto import TimelineEventCreateDTO, TimelineEventResponseDTO
from core.narrative.repositories.timeline_repo import TimelineRepository

class TimelineService:
    def __init__(self, db: Session) -> None:
        self.repo = TimelineRepository(db)

    def create_timeline_event(self, dto: TimelineEventCreateDTO) -> TimelineEventResponseDTO:
        entity = self.repo.create(**dto.model_dump())
        return TimelineEventResponseDTO.model_validate(entity)

    def list_by_universe(self, universe_id: uuid.UUID | str) -> List[TimelineEventResponseDTO]:
        entities = self.repo.get_by_universe(universe_id)
        return [TimelineEventResponseDTO.model_validate(e) for e in entities]
