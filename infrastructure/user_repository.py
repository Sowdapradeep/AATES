from sqlalchemy.orm import Session
from core.database.models import User
from infrastructure.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    """Specific repository for managing User entities."""
    
    def get_by_email(self, db: Session, email: str) -> User | None:
        """Retrieves a user profile matching the given email address."""
        return db.query(self.model).filter(self.model.email == email).first()

user_repository = UserRepository(User)
