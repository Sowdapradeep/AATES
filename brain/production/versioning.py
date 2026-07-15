import uuid
import datetime
from sqlalchemy.orm import Session
from core.database.models import Asset

class MediaVersioningTracker:
    """Core Media Versioning Tracker tracking parent asset iterations and regeneration logs."""
    
    def create_new_version(
        self,
        db: Session,
        original_asset: Asset,
        regeneration_reason: str,
        new_storage_location: str,
        new_checksum: str,
        cost: float
    ) -> Asset:
        """Clones asset details, increments version parameters, and records parent linkage."""
        new_version = original_asset.blueprint_version + 1
        
        new_asset = Asset(
            id=uuid.uuid4(),
            type=original_asset.type,
            provider=original_asset.provider,
            model=original_asset.model,
            prompt_version=original_asset.prompt_version,
            prompt_hash=original_asset.prompt_hash,
            seed=original_asset.seed,
            resolution=original_asset.resolution,
            duration=original_asset.duration,
            storage_location=new_storage_location,
            episode_id=original_asset.episode_id,
            universe_id=original_asset.universe_id,
            scene_id=original_asset.scene_id,
            parent_asset_id=original_asset.id,
            blueprint_version=new_version,
            workflow_id=original_asset.workflow_id,
            checksum=new_checksum,
            cost=cost,
            created_at=datetime.datetime.utcnow()
        )
        
        db.add(new_asset)
        db.flush()
        return new_asset

media_versioning_tracker = MediaVersioningTracker()
