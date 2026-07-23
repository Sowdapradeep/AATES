import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.narrative.models.character import Character
from core.narrative.repositories.base import BaseRepository, _to_uuid

class CharacterRepository(BaseRepository[Character]):
    """Repository handling Character entity persistence."""
    def __init__(self, db: Session) -> None:
        super().__init__(Character, db)

    def get_by_universe(self, universe_id: uuid.UUID | str) -> List[Character]:
        u_id = _to_uuid(universe_id)
        return self.db.query(Character).filter(Character.universe_id == u_id, Character.is_deleted == False).all()

    def get_by_name(self, universe_id: uuid.UUID | str, name: str) -> Optional[Character]:
        u_id = _to_uuid(universe_id)
        return self.db.query(Character).filter(
            Character.universe_id == u_id,
            Character.name == name,
            Character.is_deleted == False
        ).first()
