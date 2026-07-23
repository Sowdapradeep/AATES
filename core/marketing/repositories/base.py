import uuid
from datetime import datetime
from typing import Generic, List, Optional, Type, TypeVar
from sqlalchemy.orm import Session
from core.marketing.models.base import MarketingBaseModel

ModelType = TypeVar("ModelType", bound=MarketingBaseModel)

def _to_uuid(val: uuid.UUID | str) -> uuid.UUID:
    if isinstance(val, str):
        try:
            return uuid.UUID(val)
        except ValueError:
            pass
    return val

class BaseMarketingRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session) -> None:
        self.model = model
        self.db = db

    def get_by_id(self, entity_id: uuid.UUID | str) -> Optional[ModelType]:
        u_id = _to_uuid(entity_id)
        return self.db.query(self.model).filter(self.model.id == u_id, self.model.is_deleted == False).first()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return self.db.query(self.model).filter(self.model.is_deleted == False).offset(skip).limit(limit).all()

    def create(self, **kwargs) -> ModelType:
        for k, v in list(kwargs.items()):
            if k.endswith("_id") and isinstance(v, str):
                kwargs[k] = _to_uuid(v)
        entity = self.model(**kwargs)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
