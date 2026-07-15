from pydantic import BaseModel
from typing import Any

class ScenePackageDTO(BaseModel):
    scene_id: str
    metadata: dict[str, Any]
    video_asset_id: str
    voice_asset_ids: dict[str, str]  # character_name -> asset_id
    music_asset_id: str | None = None
    sfx_asset_ids: list[str] = []
    subtitle_asset_id: str | None = None
    qa_report: dict[str, Any]
    checksums: dict[str, str]

class RenderTimelineEvent(BaseModel):
    time_offset: float
    duration: float
    asset_id: str
    asset_type: str
    volume: float = 1.0

class RenderManifestDTO(BaseModel):
    episode_id: str
    universe_id: str
    season: int
    episode: int
    scene_packages: list[ScenePackageDTO]
    timeline_events: list[RenderTimelineEvent]
    render_settings: dict[str, Any]
    output_settings: dict[str, Any]
    version: int
    checksum: str
