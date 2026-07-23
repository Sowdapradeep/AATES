import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.narrative.dto.narrative_dto import UniverseCreateDTO, UniverseUpdateDTO, UniverseResponseDTO
from core.narrative.repositories.universe_repo import UniverseRepository

class UniverseService:
    """Service encapsulating Universe management domain logic."""
    def __init__(self, db: Session) -> None:
        self.repo = UniverseRepository(db)

    def create_universe(self, dto: UniverseCreateDTO) -> UniverseResponseDTO:
        existing = self.repo.get_by_name(dto.name)
        if existing:
            return UniverseResponseDTO.model_validate(existing)
        entity = self.repo.create(**dto.model_dump())
        return UniverseResponseDTO.model_validate(entity)

    def get_universe(self, universe_id: uuid.UUID | str) -> Optional[UniverseResponseDTO]:
        entity = self.repo.get_by_id(universe_id)
        return UniverseResponseDTO.model_validate(entity) if entity else None

    def list_universes(self, skip: int = 0, limit: int = 100) -> List[UniverseResponseDTO]:
        entities = self.repo.list_universes(skip=skip, limit=limit)
        return [UniverseResponseDTO.model_validate(e) for e in entities]

    def update_universe(self, universe_id: uuid.UUID | str, dto: UniverseUpdateDTO) -> Optional[UniverseResponseDTO]:
        entity = self.repo.update(universe_id, **dto.model_dump(exclude_unset=True))
        return UniverseResponseDTO.model_validate(entity) if entity else None

    def delete_universe(self, universe_id: uuid.UUID | str) -> bool:
        return self.repo.soft_delete(universe_id)
