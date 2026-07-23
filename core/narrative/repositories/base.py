import uuid
from datetime import datetime
from typing import Any, Generic, List, Optional, Type, TypeVar
from sqlalchemy.orm import Session
from core.narrative.models.base import NarrativeBaseModel

ModelType = TypeVar("ModelType", bound=NarrativeBaseModel)

def _to_uuid(val: uuid.UUID | str) -> uuid.UUID:
    if isinstance(val, str):
        try:
            return uuid.UUID(val)
        except ValueError:
            pass
    return val

class BaseRepository(Generic[ModelType]):
    """
    Generic Base Repository encapsulating database access operations.
    Handles CRUD, soft deletes, version increments, and pagination.
    """
    def __init__(self, model: Type[ModelType], db: Session) -> None:
        self.model = model
        self.db = db

    def get_by_id(self, entity_id: uuid.UUID | str, include_deleted: bool = False) -> Optional[ModelType]:
        u_id = _to_uuid(entity_id)
        query = self.db.query(self.model).filter(self.model.id == u_id)
        if not include_deleted:
            query = query.filter(self.model.is_deleted == False)
        return query.first()

    def list_all(self, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[ModelType]:
        query = self.db.query(self.model)
        if not include_deleted:
            query = query.filter(self.model.is_deleted == False)
        return query.offset(skip).limit(limit).all()

    def create(self, **kwargs) -> ModelType:
        # Convert any string UUID fields in kwargs to uuid.UUID instances
        for k, v in list(kwargs.items()):
            if k.endswith("_id") and isinstance(v, str):
                kwargs[k] = _to_uuid(v)
        entity = self.model(**kwargs)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity_id: uuid.UUID | str, **kwargs) -> Optional[ModelType]:
        entity = self.get_by_id(entity_id)
        if not entity:
            return None
        for key, value in kwargs.items():
            if hasattr(entity, key) and value is not None:
                if key.endswith("_id") and isinstance(value, str):
                    value = _to_uuid(value)
                setattr(entity, key, value)
        entity.version += 1
        entity.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity_id: uuid.UUID | str) -> bool:
        entity = self.get_by_id(entity_id)
        if not entity:
            return False
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.status = "deleted"
        self.db.commit()
        return True

    def hard_delete(self, entity_id: uuid.UUID | str) -> bool:
        entity = self.get_by_id(entity_id, include_deleted=True)
        if not entity:
            return False
        self.db.delete(entity)
        self.db.commit()
        return True
