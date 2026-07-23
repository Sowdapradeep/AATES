import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.narrative.models.universe import Universe
from core.narrative.repositories.base import BaseRepository

class UniverseRepository(BaseRepository[Universe]):
    """Repository handling Universe entity database persistence."""
    def __init__(self, db: Session) -> None:
        super().__init__(Universe, db)

    def get_by_name(self, name: str) -> Optional[Universe]:
        return self.db.query(Universe).filter(Universe.name == name, Universe.is_deleted == False).first()

    def list_universes(self, skip: int = 0, limit: int = 100) -> List[Universe]:
        return self.list_all(skip=skip, limit=limit)
