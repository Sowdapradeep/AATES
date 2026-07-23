from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from core.config import settings

# SQLite does not support server-side pooling arguments; PostgreSQL does.
_is_sqlite = settings.db.url.startswith("sqlite")

if _is_sqlite:
    engine = create_engine(
        settings.db.url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )
else:
    engine = create_engine(
        settings.db.url,
        pool_size=settings.db.pool_size,
        max_overflow=settings.db.max_overflow,
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency getter to yield DB sessions with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
