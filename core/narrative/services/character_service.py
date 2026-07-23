import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.narrative.dto.narrative_dto import CharacterCreateDTO, CharacterResponseDTO
from core.narrative.repositories.character_repo import CharacterRepository

class CharacterService:
    """Service encapsulating Character domain logic."""
    def __init__(self, db: Session) -> None:
        self.repo = CharacterRepository(db)

    def create_character(self, dto: CharacterCreateDTO) -> CharacterResponseDTO:
        existing = self.repo.get_by_name(dto.universe_id, dto.name)
        if existing:
            return CharacterResponseDTO.model_validate(existing)
        entity = self.repo.create(**dto.model_dump())
        return CharacterResponseDTO.model_validate(entity)

    def get_character(self, character_id: uuid.UUID | str) -> Optional[CharacterResponseDTO]:
        entity = self.repo.get_by_id(character_id)
        return CharacterResponseDTO.model_validate(entity) if entity else None

    def list_by_universe(self, universe_id: uuid.UUID | str) -> List[CharacterResponseDTO]:
        entities = self.repo.get_by_universe(universe_id)
        return [CharacterResponseDTO.model_validate(e) for e in entities]
