import uuid
from typing import List, Optional
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from core.narrative.models.relationship import Relationship
from core.narrative.repositories.base import BaseRepository, _to_uuid

class RelationshipRepository(BaseRepository[Relationship]):
    """Repository handling Character Relationship persistence."""
    def __init__(self, db: Session) -> None:
        super().__init__(Relationship, db)

    def get_between_characters(self, char_a_id: uuid.UUID | str, char_b_id: uuid.UUID | str) -> Optional[Relationship]:
        ca_id = _to_uuid(char_a_id)
        cb_id = _to_uuid(char_b_id)
        return self.db.query(Relationship).filter(
            or_(
                and_(Relationship.character_a_id == ca_id, Relationship.character_b_id == cb_id),
                and_(Relationship.character_a_id == cb_id, Relationship.character_b_id == ca_id)
            ),
            Relationship.is_deleted == False
        ).first()

    def get_for_character(self, char_id: uuid.UUID | str) -> List[Relationship]:
        c_id = _to_uuid(char_id)
        return self.db.query(Relationship).filter(
            or_(Relationship.character_a_id == c_id, Relationship.character_b_id == c_id),
            Relationship.is_deleted == False
        ).all()
