import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.narrative.dto.narrative_dto import SeasonCreateDTO, SeasonResponseDTO
from core.narrative.repositories.season_repo import SeasonRepository

class SeasonService:
    def __init__(self, db: Session) -> None:
        self.repo = SeasonRepository(db)

    def create_season(self, dto: SeasonCreateDTO) -> SeasonResponseDTO:
        existing = self.repo.get_season(dto.universe_id, dto.season_number)
        if existing:
            return SeasonResponseDTO.model_validate(existing)
        entity = self.repo.create(**dto.model_dump())
        return SeasonResponseDTO.model_validate(entity)

    def list_by_universe(self, universe_id: uuid.UUID | str) -> List[SeasonResponseDTO]:
        entities = self.repo.get_by_universe(universe_id)
        return [SeasonResponseDTO.model_validate(e) for e in entities]
