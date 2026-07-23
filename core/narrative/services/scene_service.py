import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.narrative.dto.narrative_dto import SceneCreateDTO, SceneResponseDTO
from core.narrative.repositories.scene_repo import SceneRepository

class SceneService:
    def __init__(self, db: Session) -> None:
        self.repo = SceneRepository(db)

    def create_scene(self, dto: SceneCreateDTO) -> SceneResponseDTO:
        existing = self.repo.get_scene(dto.episode_id, dto.scene_number)
        if existing:
            return SceneResponseDTO.model_validate(existing)
        entity = self.repo.create(**dto.model_dump())
        return SceneResponseDTO.model_validate(entity)

    def list_by_episode(self, episode_id: uuid.UUID | str) -> List[SceneResponseDTO]:
        entities = self.repo.get_by_episode(episode_id)
        return [SceneResponseDTO.model_validate(e) for e in entities]
