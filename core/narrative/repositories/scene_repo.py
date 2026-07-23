import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.narrative.models.scene import Scene
from core.narrative.repositories.base import BaseRepository, _to_uuid

class SceneRepository(BaseRepository[Scene]):
    """Repository handling Scene database persistence."""
    def __init__(self, db: Session) -> None:
        super().__init__(Scene, db)

    def get_by_episode(self, episode_id: uuid.UUID | str) -> List[Scene]:
        e_id = _to_uuid(episode_id)
        return self.db.query(Scene).filter(
            Scene.episode_id == e_id,
            Scene.is_deleted == False
        ).order_by(Scene.scene_number.asc()).all()

    def get_scene(self, episode_id: uuid.UUID | str, scene_number: int) -> Optional[Scene]:
        e_id = _to_uuid(episode_id)
        return self.db.query(Scene).filter(
            Scene.episode_id == e_id,
            Scene.scene_number == scene_number,
            Scene.is_deleted == False
        ).first()
