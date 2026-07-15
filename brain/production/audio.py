import uuid
import hashlib
from typing import Any
from sqlalchemy.orm import Session
from core.database.models import Asset, MonthlyCost
from providers.voice.mock import MockVoiceProvider
from providers.music.mock import MockMusicProvider

class VoiceEngine:
    """Core Voice Engine generating synchronized text-to-speech audio segments."""
    
    def __init__(self, provider: Any = None):
        self.provider = provider or MockVoiceProvider()

    async def generate_voice(
        self,
        scene_id: str,
        episode_id: str,
        universe_id: str,
        text: str,
        voice_id: str,
        emotional_tone: str,
        speaking_speed: float = 1.0,
        db: Session = None
    ) -> Asset:
        """Synthesizes speech lines and registers Asset logs entries."""
        res = await self.provider.synthesize_speech(
            text=text,
            voice_id=voice_id,
            emotional_tone=emotional_tone,
            speaking_speed=speaking_speed
        )

        e_uuid = uuid.UUID(episode_id) if isinstance(episode_id, str) else episode_id
        u_uuid = uuid.UUID(universe_id) if isinstance(universe_id, str) else universe_id

        asset = Asset(
            id=uuid.uuid4(),
            type="voice",
            provider=res["provider"],
            model=res["model"],
            prompt_version=res["prompt_version"],
            prompt_hash=hashlib.sha256(text.encode()).hexdigest(),
            seed=None,
            resolution=None,
            duration=3.5,
            storage_location=res["storage_location"],
            episode_id=e_uuid,
            universe_id=u_uuid,
            scene_id=scene_id,
            parent_asset_id=None,
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

class MusicEngine:
    """Core Music Engine generating thematic and ambient background sound tracks."""
    
    def __init__(self, provider: Any = None):
        self.provider = provider or MockMusicProvider()

    async def generate_music(
        self,
        scene_id: str,
        episode_id: str,
        universe_id: str,
        mood: str,
        duration: float,
        db: Session = None
    ) -> Asset:
        """Generates scene backtracks and records cost mappings."""
        res = await self.provider.generate_music(mood=mood, duration=duration)

        e_uuid = uuid.UUID(episode_id) if isinstance(episode_id, str) else episode_id
        u_uuid = uuid.UUID(universe_id) if isinstance(universe_id, str) else universe_id

        asset = Asset(
            id=uuid.uuid4(),
            type="music",
            provider=res["provider"],
            model=res["model"],
            prompt_version=res["prompt_version"],
            prompt_hash=hashlib.sha256(mood.encode()).hexdigest(),
            seed=None,
            resolution=None,
            duration=duration,
            storage_location=res["storage_location"],
            episode_id=e_uuid,
            universe_id=u_uuid,
            scene_id=scene_id,
            parent_asset_id=None,
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

class SFXEngine:
    """Core SFX Engine managing reusable library ambient audio effects."""
    
    async def generate_sfx(
        self,
        scene_id: str,
        episode_id: str,
        universe_id: str,
        effect_name: str,
        db: Session = None
    ) -> Asset:
        """Checks reuse archives and records minimal licensing fees."""
        sfx_key = int(hashlib.md5(effect_name.encode()).hexdigest()[:8], 16) % 1000
        mock_path = f"s3://aates-assets/library/sfx-{sfx_key}.wav"
        
        e_uuid = uuid.UUID(episode_id) if isinstance(episode_id, str) else episode_id
        u_uuid = uuid.UUID(universe_id) if isinstance(universe_id, str) else universe_id

        asset = Asset(
            id=uuid.uuid4(),
            type="sfx",
            provider="LibrarySFX",
            model="SFX-Archive-v1",
            prompt_version="1.0.0",
            prompt_hash=hashlib.sha256(effect_name.encode()).hexdigest(),
            seed=None,
            resolution=None,
            duration=1.5,
            storage_location=mock_path,
            episode_id=e_uuid,
            universe_id=u_uuid,
            scene_id=scene_id,
            parent_asset_id=None,
            blueprint_version=1,
            checksum=f"sha256-sfx-{sfx_key}",
            cost=0.005
        )

        if db:
            db.add(asset)
            month_str = "2026-07"
            m_cost = db.query(MonthlyCost).filter(MonthlyCost.month == month_str).first()
            if m_cost:
                m_cost.total_spent += 0.005
            db.flush()

        return asset

voice_engine = VoiceEngine()
music_engine = MusicEngine()
sfx_engine = SFXEngine()
