import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.narrative.dto.narrative_dto import RelationshipCreateDTO, RelationshipResponseDTO
from core.narrative.repositories.relationship_repo import RelationshipRepository

class RelationshipService:
    """Service encapsulating Character Relationship domain logic."""
    def __init__(self, db: Session) -> None:
        self.repo = RelationshipRepository(db)

    def create_relationship(self, dto: RelationshipCreateDTO) -> RelationshipResponseDTO:
        existing = self.repo.get_between_characters(dto.character_a_id, dto.character_b_id)
        if existing:
            updated = self.repo.update(
                existing.id,
                relationship_type=dto.relationship_type,
                tension_level=dto.tension_level,
                history_notes=dto.history_notes
            )
            return RelationshipResponseDTO.model_validate(updated)
        entity = self.repo.create(**dto.model_dump())
        return RelationshipResponseDTO.model_validate(entity)

    def get_for_character(self, character_id: uuid.UUID | str) -> List[RelationshipResponseDTO]:
        entities = self.repo.get_for_character(character_id)
        return [RelationshipResponseDTO.model_validate(e) for e in entities]
