from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Any
from sqlalchemy.orm import Session
from core.database.session import get_db
from core.database.models import Asset
from contracts.dto.blueprint import SceneBlueprint
from contracts.dto.manifest import RenderManifestDTO, ScenePackageDTO
from brain.production.preproduction import storyboard_engine, shot_planner
from brain.production.audio import voice_engine, music_engine
from brain.production.qa import qa_engine
from brain.production.renderer import render_manifest_compiler, ffmpeg_rendering_engine

router = APIRouter()

class VoiceRequest(BaseModel):
    """Voice Speech synthesis payload parameters."""
    scene_id: str
    episode_id: str
    universe_id: str
    text: str
    voice_id: str
    emotional_tone: str

class MusicRequest(BaseModel):
    """Background soundtrack theme synthesis payload parameters."""
    scene_id: str
    episode_id: str
    universe_id: str
    mood: str
    duration: float

class QARequest(BaseModel):
    """QA Quality Gates payload tracking scene-level rendered assets validation logs."""
    scene_id: str
    scene_assets: dict[str, Any]

class ManifestRequest(BaseModel):
    """Compile Manifest compilation payload tracking completed scene packages."""
    episode_id: str
    universe_id: str
    season: int
    episode: int
    scene_packages: list[ScenePackageDTO]

@router.post("/production/storyboard")
async def generate_storyboard(scene: SceneBlueprint) -> Any:
    """Triggers storyboard engine generating visual reference specs."""
    return await storyboard_engine.generate_panels(scene)

@router.post("/production/shots")
async def plan_shots(scene: SceneBlueprint) -> Any:
    """Triggers shot planner defining duration timeline cuts."""
    return await shot_planner.plan_shots(scene)

@router.post("/production/voice")
async def generate_voice(payload: VoiceRequest, db: Session = Depends(get_db)) -> Any:
    """Synthesizes text dialogue speech lines using Cast voice profile identifiers."""
    asset = await voice_engine.generate_voice(
        scene_id=payload.scene_id,
        episode_id=payload.episode_id,
        universe_id=payload.universe_id,
        text=payload.text,
        voice_id=payload.voice_id,
        emotional_tone=payload.emotional_tone,
        db=db
    )
    return {"asset_id": str(asset.id), "storage_location": asset.storage_location, "cost": asset.cost}

@router.post("/production/music")
async def generate_music(payload: MusicRequest, db: Session = Depends(get_db)) -> Any:
    """Generates thematic backtracks matching current scene mood parameters."""
    asset = await music_engine.generate_music(
        scene_id=payload.scene_id,
        episode_id=payload.episode_id,
        universe_id=payload.universe_id,
        mood=payload.mood,
        duration=payload.duration,
        db=db
    )
    return {"asset_id": str(asset.id), "storage_location": asset.storage_location, "cost": asset.cost}

@router.post("/production/qa")
async def run_qa(payload: QARequest) -> Any:
    """Runs automated visual, audio, subtitle, and brand safety checks."""
    return await qa_engine.execute_all_gates(payload.scene_id, payload.scene_assets)

@router.post("/production/manifest")
async def compile_manifest(payload: ManifestRequest) -> Any:
    """Compiles completed scene packages into a standardized Render Manifest DTO."""
    return await render_manifest_compiler.compile_manifest(
        episode_id=payload.episode_id,
        universe_id=payload.universe_id,
        season=payload.season,
        episode=payload.episode,
        scene_packages=payload.scene_packages
    )

@router.post("/production/render")
async def trigger_render(payload: RenderManifestDTO, db: Session = Depends(get_db)) -> Any:
    """Instructs FFmpeg mix & concatenation workers to merge scene assets into Master Reel."""
    return await ffmpeg_rendering_engine.render_episode(payload, db=db)

@router.get("/production/assets")
def get_assets(db: Session = Depends(get_db)) -> Any:
    """Retrieves list of registered assets and lineage parent tracking references."""
    assets = db.query(Asset).order_by(Asset.created_at.desc()).limit(50).all()
    return [{
        "id": str(a.id),
        "type": a.type,
        "provider": a.provider,
        "model": a.model,
        "storage_location": a.storage_location,
        "cost": a.cost,
        "scene_id": a.scene_id,
        "parent_asset_id": str(a.parent_asset_id) if a.parent_asset_id else None,
        "checksum": a.checksum
    } for a in assets]
