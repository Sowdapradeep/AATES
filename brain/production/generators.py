import uuid
import hashlib
from typing import Any
from sqlalchemy.orm import Session
from core.database.models import Asset, MonthlyCost
from providers.image.mock import MockImageProvider
from providers.video.mock import MockVideoProvider

class CharacterConsistencyEngine:
    """Core Character Consistency Engine mapping consistent seeds and visual traits tags."""
    
    async def get_character_seed_profile(self, character_name: str) -> dict[str, Any]:
        """Calculates deterministic seeds and profiles for consistent image generation."""
        traits_str = f"character-{character_name}-v1"
        seed_val = int(hashlib.md5(traits_str.encode()).hexdigest()[:8], 16) % 10000
        return {
            "name": character_name,
            "seed": seed_val,
            "face_anchor": "traditional Tamil face outline",
            "hair_style": "cropped dark hair",
            "clothing_style": "default_attire"
        }

class ImageEngine:
    """Core Image Engine generating storyboard frame assets with consistency constraints."""
    
    def __init__(self, provider: Any = None):
        self.provider = provider or MockImageProvider()
        self.consistency_engine = CharacterConsistencyEngine()

    async def generate_reference_frame(
        self,
        scene_id: str,
        episode_id: str,
        universe_id: str,
        prompt: str,
        character_name: str | None = None,
        parent_asset_id: str | None = None,
        db: Session = None
    ) -> Asset:
        """Invokes provider image generation and records asset lineage mapping logs."""
        seed_to_use = None
        if character_name:
            profile = await self.consistency_engine.get_character_seed_profile(character_name)
            seed_to_use = profile["seed"]
            prompt = f"{prompt}, face profile: {profile['face_anchor']}, hair: {profile['hair_style']}"

        res = await self.provider.generate_image(prompt=prompt, seed=seed_to_use)

        # Convert IDs safely
        e_uuid = uuid.UUID(episode_id) if isinstance(episode_id, str) else episode_id
        u_uuid = uuid.UUID(universe_id) if isinstance(universe_id, str) else universe_id
        p_uuid = uuid.UUID(parent_asset_id) if isinstance(parent_asset_id, str) else parent_asset_id

        asset = Asset(
            id=uuid.uuid4(),
            type="image",
            provider=res["provider"],
            model=res["model"],
            prompt_version=res["prompt_version"],
            prompt_hash=hashlib.sha256(prompt.encode()).hexdigest(),
            seed=res["seed"],
            resolution="1920x1080",
            duration=None,
            storage_location=res["storage_location"],
            episode_id=e_uuid,
            universe_id=u_uuid,
            scene_id=scene_id,
            parent_asset_id=p_uuid,
            blueprint_version=1,
            checksum=res["checksum"],
            cost=res["cost"]
        )

        if db:
            db.add(asset)
            # Update monthly cost calculations
            month_str = "2026-07"
            m_cost = db.query(MonthlyCost).filter(MonthlyCost.month == month_str).first()
            if not m_cost:
                m_cost = MonthlyCost(month=month_str, total_spent=res["cost"])
                db.add(m_cost)
            else:
                m_cost.total_spent += res["cost"]
            db.flush()

        return asset

class VideoEngine:
    """Core Video Engine transforming reference frames into motion video files."""
    
    def __init__(self, provider: Any = None):
        self.provider = provider or MockVideoProvider()

    async def generate_scene_video(
        self,
        scene_id: str,
        episode_id: str,
        universe_id: str,
        image_asset_id: str,
        image_location: str,
        prompt: str,
        db: Session = None
    ) -> Asset:
        """Invokes provider video animation generation and registers Asset row."""
        res = await self.provider.generate_video(image_location=image_location, prompt=prompt)

        e_uuid = uuid.UUID(episode_id) if isinstance(episode_id, str) else episode_id
        u_uuid = uuid.UUID(universe_id) if isinstance(universe_id, str) else universe_id
        i_uuid = uuid.UUID(image_asset_id) if isinstance(image_asset_id, str) else image_asset_id

        asset = Asset(
            id=uuid.uuid4(),
            type="video",
            provider=res["provider"],
            model=res["model"],
            prompt_version=res["prompt_version"],
            prompt_hash=hashlib.sha256(prompt.encode()).hexdigest(),
            seed=res["seed"],
            resolution="1920x1080",
            duration=4.0,
            storage_location=res["storage_location"],
            episode_id=e_uuid,
            universe_id=u_uuid,
            scene_id=scene_id,
            parent_asset_id=i_uuid,
            blueprint_version=1,
            checksum=res["checksum"],
            cost=res["cost"]
        )

        if db:
            db.add(asset)
            month_str = "2026-07"
            m_cost = db.query(MonthlyCost).filter(MonthlyCost.month == month_str).first()
            if m_cost:
                m_cost.total_spent += res["cost"]
            db.flush()

        return asset

image_engine = ImageEngine()
video_engine = VideoEngine()
