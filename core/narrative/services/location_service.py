import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.narrative.dto.narrative_dto import LocationCreateDTO, LocationResponseDTO
from core.narrative.repositories.location_repo import LocationRepository

class LocationService:
    def __init__(self, db: Session) -> None:
        self.repo = LocationRepository(db)

    def create_location(self, dto: LocationCreateDTO) -> LocationResponseDTO:
        existing = self.repo.get_by_name(dto.universe_id, dto.name)
        if existing:
            return LocationResponseDTO.model_validate(existing)
        entity = self.repo.create(**dto.model_dump())
        return LocationResponseDTO.model_validate(entity)

    def list_by_universe(self, universe_id: uuid.UUID | str) -> List[LocationResponseDTO]:
        entities = self.repo.get_by_universe(universe_id)
        return [LocationResponseDTO.model_validate(e) for e in entities]
