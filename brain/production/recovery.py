from sqlalchemy.orm import Session
from core.database.models import Asset

class ProductionWorkflowRecovery:
    """Core Production Recovery Manager loading existing generated scene assets to support resume checkpoints."""
    
    def get_existing_scene_assets(self, db: Session, episode_id: str, scene_id: str) -> dict[str, Asset]:
        """Queries database for existing scene assets, picking the highest blueprint version iterations."""
        assets = db.query(Asset).filter(
            Asset.episode_id == episode_id,
            Asset.scene_id == scene_id
        ).all()
        
        result = {}
        for a in assets:
            existing = result.get(a.type)
            # Pick the latest version iteration
            if not existing or a.blueprint_version > existing.blueprint_version:
                result[a.type] = a
        return result

production_recovery = ProductionWorkflowRecovery()
