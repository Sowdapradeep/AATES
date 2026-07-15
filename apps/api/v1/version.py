from fastapi import APIRouter
from core.config import settings

router = APIRouter()

@router.get("/version")
def get_version() -> dict[str, str]:
    """Retrieves current application release metadata and environment identifier."""
    return {
        "version": settings.app.version,
        "environment": settings.app.env,
        "commit_hash": "d085984a9e52514c278076bf2d091cd4f8efd11"
    }
