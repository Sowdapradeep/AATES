import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.narrative.dto.narrative_dto import EpisodeCreateDTO, EpisodeResponseDTO
from core.narrative.repositories.episode_repo import EpisodeRepository

class EpisodeService:
    def __init__(self, db: Session) -> None:
        self.repo = EpisodeRepository(db)

    def create_episode(self, dto: EpisodeCreateDTO) -> EpisodeResponseDTO:
        existing = self.repo.get_episode(dto.season_id, dto.episode_number)
        if existing:
            return EpisodeResponseDTO.model_validate(existing)
        entity = self.repo.create(**dto.model_dump())
        return EpisodeResponseDTO.model_validate(entity)

    def list_by_season(self, season_id: uuid.UUID | str) -> List[EpisodeResponseDTO]:
        entities = self.repo.get_by_season(season_id)
        return [EpisodeResponseDTO.model_validate(e) for e in entities]
