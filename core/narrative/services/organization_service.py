import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.narrative.dto.narrative_dto import OrganizationCreateDTO, OrganizationResponseDTO
from core.narrative.repositories.organization_repo import OrganizationRepository

class OrganizationService:
    def __init__(self, db: Session) -> None:
        self.repo = OrganizationRepository(db)

    def create_organization(self, dto: OrganizationCreateDTO) -> OrganizationResponseDTO:
        existing = self.repo.get_by_name(dto.universe_id, dto.name)
        if existing:
            return OrganizationResponseDTO.model_validate(existing)
        entity = self.repo.create(**dto.model_dump())
        return OrganizationResponseDTO.model_validate(entity)

    def list_by_universe(self, universe_id: uuid.UUID | str) -> List[OrganizationResponseDTO]:
        entities = self.repo.get_by_universe(universe_id)
        return [OrganizationResponseDTO.model_validate(e) for e in entities]
