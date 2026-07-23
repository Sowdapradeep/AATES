import uuid
from typing import List
from sqlalchemy.orm import Session
from core.narrative.dto.narrative_dto import StoryArcCreateDTO, StoryArcResponseDTO
from core.narrative.repositories.story_arc_repo import StoryArcRepository

class StoryArcService:
    def __init__(self, db: Session) -> None:
        self.repo = StoryArcRepository(db)

    def create_story_arc(self, dto: StoryArcCreateDTO) -> StoryArcResponseDTO:
        entity = self.repo.create(**dto.model_dump())
        return StoryArcResponseDTO.model_validate(entity)

    def list_by_universe(self, universe_id: uuid.UUID | str) -> List[StoryArcResponseDTO]:
        entities = self.repo.get_by_universe(universe_id)
        return [StoryArcResponseDTO.model_validate(e) for e in entities]
